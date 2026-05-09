#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime
import math

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices
from research.common.projection import projected_edge_signature, random_projection

TARGET_PROFILE = (3, 4, 6, 6, 8)
TARGET_FAMILY_COUNT = 5
FOCUSED_PROFILE = [1, 1, 1, 1, 6]


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def root_line_key(vec: np.ndarray, tol: float = 1e-9):
    idx = next(i for i, x in enumerate(vec) if abs(float(x)) > tol)
    if vec[idx] < 0:
        vec = -vec
    scale = float(vec[idx])
    normalized = vec / scale
    return tuple(round(float(x), 8) for x in normalized.tolist())


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def unique_line_representatives(vectors: np.ndarray) -> list[np.ndarray]:
    reps = []
    seen = set()
    for vec in vectors:
        key = root_line_key(vec.copy())
        if key not in seen:
            seen.add(key)
            reps.append(vec)
    return reps


def tesseract_axis_vectors() -> np.ndarray:
    vectors = []
    for i in range(4):
        for s in (-1.0, 1.0):
            vec = np.zeros(4, dtype=float)
            vec[i] = s
            vectors.append(vec)
    return np.array(vectors, dtype=float)


def canonical_tesseract_vertices() -> np.ndarray:
    vectors = []
    for signs in np.ndindex((2, 2, 2, 2)):
        vectors.append([1.0 if bit else -1.0 for bit in signs])
    return np.array(vectors, dtype=float)


def canonical_tesseract_edges(vertices: np.ndarray) -> list[tuple[int, int]]:
    edges = []
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            diff = np.abs(vertices[i] - vertices[j])
            if np.count_nonzero(diff) == 1 and np.isclose(float(np.sum(diff)), 2.0):
                edges.append((i, j))
    return edges


def clustered_family_counts(vectors: list[np.ndarray], projection: np.ndarray, tol: float = 1.5) -> list[int]:
    projected = [(projection @ vec.reshape(-1, 1)).reshape(-1) for vec in vectors]
    usable = [vec for vec in projected if np.linalg.norm(vec) > 1e-9]
    if not usable:
        return []
    decorated = sorted((angle_mod_180(vec), vec) for vec in usable)
    groups = [[decorated[0]]]
    for angle, vec in decorated[1:]:
        if abs(angle - groups[-1][-1][0]) <= tol:
            groups[-1].append((angle, vec))
        else:
            groups.append([(angle, vec)])
    return [len(group) for group in groups]


def profile_score(counts: list[int], target_total: int = 27, target_profile: tuple[int, ...] = TARGET_PROFILE) -> float:
    families = len(counts)
    if families == 0:
        return 1e9
    total = sum(counts)
    counts_sorted = sorted(counts)
    target_scaled = sorted(total * value / target_total for value in target_profile)
    usable_target = target_scaled[:families] if families < len(target_scaled) else target_scaled + [0.0] * (families - len(target_scaled))
    l1 = sum(abs(float(a) - float(b)) for a, b in zip(counts_sorted, usable_target))
    return 100.0 * abs(families - TARGET_FAMILY_COUNT) + l1


def load_branch_09_hint() -> dict[str, object] | None:
    path = ROOT / 'research' / 'B_symmetry_arrangement_models' / '09_f4_b4_hybrid' / 'data' / 'analyze_hybrid_refine.json'
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return {
        'source': '09 analyze_hybrid_refine.json',
        'best_focus_class': data['best_focus_class'],
        'current_read': data['interpretation']['current_read'],
        'best_record': data['best_focus_stats']['best'],
    }


def load_cross_branch_reference() -> dict[str, object]:
    result = {}
    p08 = ROOT / 'research' / 'B_symmetry_arrangement_models' / '08_f4_root_arrangement' / 'data' / 'finalize_f4_focus.json'
    if p08.exists():
        d08 = json.loads(p08.read_text())
        result['branch_08'] = {
            'best_class': d08['best_focus_class'],
            'family5_hit_rate': d08['best_focus_stats']['family5_hit_rate'],
            'exact_profile_hit_rate': d08['best_focus_stats']['exact_profile_hit_rate'],
        }
    p09 = ROOT / 'research' / 'B_symmetry_arrangement_models' / '09_f4_b4_hybrid' / 'data' / 'analyze_hybrid_refine.json'
    if p09.exists():
        d09 = json.loads(p09.read_text())
        result['branch_09'] = {
            'best_class': d09['best_focus_class'],
            'family5_hit_rate': d09['best_focus_stats']['family5_hit_rate'],
            'exact_profile_hit_rate': d09['best_focus_stats']['exact_profile_hit_rate'],
        }
    return result


def sample_tc_classes(
    tesseract_axes: list[np.ndarray],
    cell_lines: list[np.ndarray],
    classes: list[tuple[int, int]],
    per_class_samples: int,
    seed: int,
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    rng = np.random.default_rng(seed)
    class_hits: dict[str, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    for t_count, c_count in classes:
        key = f"T{t_count}_C{c_count}"
        hits_family5 = 0
        hits_exact_profile = 0
        family_histogram: dict[int, int] = {}
        best = None
        for _ in range(per_class_samples):
            chosen_axes = [tesseract_axes[i] for i in rng.choice(len(tesseract_axes), size=t_count, replace=False)]
            chosen_cell = [cell_lines[i] for i in rng.choice(len(cell_lines), size=c_count, replace=False)]
            projection = random_projection(rng)
            counts = clustered_family_counts(chosen_axes + chosen_cell, projection, tol=1.5)
            sorted_counts = sorted(counts)
            score = profile_score(counts)
            rec = {
                'class': key,
                'tesseract_count': t_count,
                'cell_count': c_count,
                'family_count': len(counts),
                'family_multiplicities': sorted_counts,
                'profile_score': score,
                'exact_profile_hit': sorted_counts == FOCUSED_PROFILE,
            }
            records.append(rec)
            family_histogram[len(counts)] = family_histogram.get(len(counts), 0) + 1
            if len(counts) == TARGET_FAMILY_COUNT:
                hits_family5 += 1
            if sorted_counts == FOCUSED_PROFILE:
                hits_exact_profile += 1
            if best is None or (rec['profile_score'], abs(rec['family_count'] - TARGET_FAMILY_COUNT)) < (
                best['profile_score'],
                abs(best['family_count'] - TARGET_FAMILY_COUNT),
            ):
                best = rec
        class_hits[key] = {
            'hits_family5': hits_family5,
            'hits_exact_profile_11116': hits_exact_profile,
            'family5_hit_rate': hits_family5 / per_class_samples,
            'exact_profile_hit_rate': hits_exact_profile / per_class_samples,
            'family_histogram': dict(sorted(family_histogram.items())),
            'best': best,
        }
    records.sort(key=lambda rec: (rec['profile_score'], abs(rec['family_count'] - TARGET_FAMILY_COUNT)))
    return class_hits, records


def run_baseline(variant_dir: Path) -> int:
    axes = unique_line_representatives(tesseract_axis_vectors())
    cell_lines = unique_line_representatives(canonical_24cell_vertices())
    hint = load_branch_09_hint()
    data = {
        'tesseract_axis_line_count': len(axes),
        'cell_direction_line_count': len(cell_lines),
        'reduced_model': 'tesseract axis scaffold + 24-cell direction shell',
        'motivation': 'Branch 09 suggests that axis+long structure may already carry the signal, so branch 05 can now be tested directly as a geometric interaction model.',
        'branch_09_hint': hint,
    }
    data_dir = variant_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / 'baseline_interaction_model.json'
    md_path = data_dir / 'baseline_interaction_model.md'
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    hint_lines = []
    if hint is not None:
        hint_lines = [
            f"- branch 09 best focus class: `{hint['best_focus_class']}`",
            f"- branch 09 read: `{hint['current_read']}`",
            f"- branch 09 best witness: `{hint['best_record']}`",
        ]
    md_path.write_text(
        f"""# 24-cell / Tesseract Interaction Baseline

- tesseract axis lines: `{len(axes)}`
- 24-cell direction lines: `{len(cell_lines)}`
- reduced model: `{data['reduced_model']}`
- motivation: {data['motivation']}

## Imported Hint From Branch 09
{chr(10).join(hint_lines) if hint_lines else '- branch 09 hint not available yet'}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — baseline
Цель: открыть `05_24cell_tesseract_interaction` не как абстракцию, а как явную reduced-модель axis+shell interaction.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_interaction_model.json`
- `data/baseline_interaction_model.md`
Что считаю:
- число осевых линий тессеракта;
- число directional lines 24-cell;
- переносится ли сигнал из ветки `09` в более прямую геометрическую постановку.
Формулы / reasoning:
- если hybrid-ветка фактически редуцируется к axis+long без пользы от half-shell, то следующая честная проверка — прямой geometric interaction `tesseract + 24-cell`.
Промежуточные результаты:
- tesseract axis lines: `{len(axes)}`
- 24-cell direction lines: `{len(cell_lines)}`
- imported hint from 09: `{hint['current_read'] if hint else 'n/a'}`
Что это значит:
- ветка `05` получила явную математическую постановку, а не просто красивое имя.
Сложность:
- низкая.
Следующий шаг:
- сделать class-level sampling по `T/C` смесям и сравнить их с лучшими `A/L` гибридными классами.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: active

## Summary

Baseline is now in place for the reduced 24-cell/tesseract interaction model.

## Best Witness

- `data/baseline_interaction_model.json`

## Blocking Issues

Need the first class-level search over `T/C` mixtures.
''')

    print(f"variant={variant_dir.name}")
    print('stage=baseline')
    print(f'baseline={json_path}')
    return 0


def run_search(variant_dir: Path) -> int:
    axes = unique_line_representatives(tesseract_axis_vectors())
    cell_lines = unique_line_representatives(canonical_24cell_vertices())
    classes = [(4, 6), (3, 8), (4, 8), (2, 8), (4, 4)]
    per_class_samples = 2500
    class_hits, records = sample_tc_classes(axes, cell_lines, classes, per_class_samples, seed=150)
    ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]['hits_family5'], -kv[1]['hits_exact_profile_11116'], kv[1]['best']['profile_score']),
    )
    best_class, best_stats = ranked[0]

    report = {
        'classes': [f"T{t}_C{c}" for t, c in classes],
        'per_class_samples': per_class_samples,
        'sampling_seed': 150,
        'focus_exact_profile': FOCUSED_PROFILE,
        'class_hits': class_hits,
        'top_records': records[:20],
        'best_class': best_class,
        'best_stats': best_stats,
    }
    data_dir = variant_dir / 'data'
    report_path = data_dir / 'search_interaction_sampling.json'
    summary_path = data_dir / 'search_interaction_sampling.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [
        f"- `{key}` -> family5_hits=`{value['hits_family5']}` ({value['family5_hit_rate']:.4f}), exact_profile_hits=`{value['hits_exact_profile_11116']}` ({value['exact_profile_hit_rate']:.4f}), best=`{value['best']}`"
        for key, value in ranked
    ]
    summary_path.write_text(
        f"""# 24-cell / Tesseract Interaction Search

- classes: `{report['classes']}`
- samples per class: `{per_class_samples}`
- best class: `{best_class}`

## Ranked Classes
{chr(10).join(class_lines)}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — search-axis-shell-interaction
Цель: проверить, даёт ли прямая смесь осей тессеракта и directional shell 24-cell тот же тип сигнала, что и `09`.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage search`
Артефакты:
- `data/search_interaction_sampling.json`
- `data/search_interaction_sampling.md`
Что считаю:
- sampling по классам `T/C`;
- частоты попаданий в `family_count=5`;
- частоты exact-profile `[1,1,1,1,6]`.
Формулы / reasoning:
- это геометрическая распаковка сильнейшего сигнала из `09` без half-shell слоя;
- если `05` повторяет или усиливает сигнал `09`, hybrid-ветка может оказаться лишь промежуточным мостом.
Промежуточные результаты:
- best class: `{best_class}`
- family5 hits / exact-profile hits: `{best_stats['hits_family5']}` / `{best_stats['hits_exact_profile_11116']}`
- best witness: `{best_stats['best']}`
Что это значит:
- теперь понятно, превращается ли axis+long intuition в самостоятельную геометрическую ветку.
Сложность:
- средняя.
Следующий шаг:
- сделать local neighbourhood-refinement вокруг `T4_C4` и `T4_C6`.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text(
        '# Result\n\n'
        'Status: active\n\n'
        '## Summary\n\n'
        f'Baseline and first class-level search are now in place for the reduced 24-cell/tesseract interaction model. The current leader is `{best_class}`.\n\n'
        '## Best Witness\n\n'
        '- `data/baseline_interaction_model.json`\n'
        '- `data/search_interaction_sampling.json`\n\n'
        '## Blocking Issues\n\n'
        'Need local refinement around `T4_C4` and `T4_C6`.\n'
    )

    print(f"variant={variant_dir.name}")
    print('stage=search')
    print(f'report={report_path}')
    return 0


def run_analyze(variant_dir: Path) -> int:
    axes = unique_line_representatives(tesseract_axis_vectors())
    cell_lines = unique_line_representatives(canonical_24cell_vertices())
    focus_classes = [(4, 4), (4, 5), (4, 6), (4, 7), (3, 4), (3, 5), (3, 6), (2, 8)]
    focus_samples = 3000
    class_hits, records = sample_tc_classes(axes, cell_lines, focus_classes, focus_samples, seed=151)
    ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]['hits_family5'], -kv[1]['hits_exact_profile_11116'], kv[1]['best']['profile_score']),
    )
    best_family5_class, best_family5_stats = ranked[0]
    exact_ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]['hits_exact_profile_11116'], -kv[1]['hits_family5'], kv[1]['best']['profile_score']),
    )
    best_exact_class, best_exact_stats = exact_ranked[0]
    references = load_cross_branch_reference()

    comparison = {
        'branch_08': references.get('branch_08'),
        'branch_09': references.get('branch_09'),
        'branch_05_best_family5_class': best_family5_class,
        'branch_05_best_family5_rate': best_family5_stats['family5_hit_rate'],
        'branch_05_best_exact_class': best_exact_class,
        'branch_05_best_exact_rate': best_exact_stats['exact_profile_hit_rate'],
    }

    report = {
        'focus_classes': [f"T{t}_C{c}" for t, c in focus_classes],
        'focus_samples_per_class': focus_samples,
        'sampling_seed': 151,
        'focus_exact_profile': FOCUSED_PROFILE,
        'class_hits': class_hits,
        'top_records': records[:20],
        'best_family5_class': best_family5_class,
        'best_family5_stats': best_family5_stats,
        'best_exact_class': best_exact_class,
        'best_exact_stats': best_exact_stats,
        'comparison_to_08_09': comparison,
    }
    data_dir = variant_dir / 'data'
    report_path = data_dir / 'analyze_interaction_refine.json'
    summary_path = data_dir / 'analyze_interaction_refine.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [
        f"- `{key}` -> family5_hits=`{value['hits_family5']}` ({value['family5_hit_rate']:.4f}), exact_profile_hits=`{value['hits_exact_profile_11116']}` ({value['exact_profile_hit_rate']:.4f}), best=`{value['best']}`"
        for key, value in ranked
    ]
    compare_lines = []
    if references.get('branch_08'):
        compare_lines.append(f"- branch 08 best class: `{references['branch_08']['best_class']}`; family5=`{references['branch_08']['family5_hit_rate']:.4f}`; exact=`{references['branch_08']['exact_profile_hit_rate']:.4f}`")
    if references.get('branch_09'):
        compare_lines.append(f"- branch 09 best class: `{references['branch_09']['best_class']}`; family5=`{references['branch_09']['family5_hit_rate']:.4f}`; exact=`{references['branch_09']['exact_profile_hit_rate']:.4f}`")
    compare_lines.append(f"- branch 05 best family5 class: `{best_family5_class}`; family5=`{best_family5_stats['family5_hit_rate']:.4f}`")
    compare_lines.append(f"- branch 05 best exact-profile class: `{best_exact_class}`; exact=`{best_exact_stats['exact_profile_hit_rate']:.4f}`")
    summary_path.write_text(
        f"""# 24-cell / Tesseract Interaction Refinement

- focus classes: `{report['focus_classes']}`
- samples per class: `{focus_samples}`
- best family5 class: `{best_family5_class}`
- best exact-profile class: `{best_exact_class}`

## Ranked Focus Classes
{chr(10).join(class_lines)}

## Comparison To Branches 08 / 09
{chr(10).join(compare_lines)}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — analyze-local-ridge
Цель: проверить, существует ли локальный ridge вокруг `T4_C4`/`T4_C6`, а не только два удачных класса.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_interaction_refine.json`
- `data/analyze_interaction_refine.md`
Что считаю:
- neighbourhood-scan вокруг лучших `T/C` классов;
- отдельно максимум по family5-rate и отдельно максимум по exact-profile-rate;
- сравнение с ветками `08` и `09`.
Формулы / reasoning:
- если вокруг `T4_C4/T4_C6` есть устойчивый ridge, то это уже не случайная находка, а сильная геометрическая ветка;
- важно разделить “чаще даёт 5 семейств” и “чаще даёт exact profile `[1,1,1,1,6]`”.
Промежуточные результаты:
- best family5 class: `{best_family5_class}`
- best exact-profile class: `{best_exact_class}`
- family5 / exact rates: `{best_family5_stats['family5_hit_rate']:.4f}` / `{best_exact_stats['exact_profile_hit_rate']:.4f}`
Что это значит:
- теперь `05` можно сравнивать с `08/09` уже не по одной точке, а по локальной структуре вокруг сильных классов.
Сложность:
- средняя.
Следующий шаг:
- если `05` остаётся лидером, делать её главным front-runner и переносить остальные ветки в supporting role.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text(
        '# Result\n\n'
        'Status: active\n\n'
        '## Summary\n\n'
        f'Local refinement is now in place for branch `05`. The best family5 class is `{best_family5_class}`, while the best exact-profile class is `{best_exact_class}`.\n\n'
        '## Best Witness\n\n'
        '- `data/search_interaction_sampling.json`\n'
        '- `data/analyze_interaction_refine.json`\n\n'
        '## Blocking Issues\n\n'
        'Need final decision whether branch `05` is now the primary front-runner over `08` and `09`.\n'
    )

    print(f"variant={variant_dir.name}")
    print('stage=analyze')
    print(f'report={report_path}')
    return 0


def run_finalize(variant_dir: Path) -> int:
    tesseract_vertices = canonical_tesseract_vertices()
    tesseract_edges = canonical_tesseract_edges(tesseract_vertices)
    cell_vertices = canonical_24cell_vertices()
    cell_edges = canonical_24cell_edges(cell_vertices)

    combined_vertices = np.vstack([tesseract_vertices, cell_vertices])
    offset = len(tesseract_vertices)
    combined_edges = list(tesseract_edges) + [(i + offset, j + offset) for i, j in cell_edges]

    samples = 1000
    rng = np.random.default_rng(152)
    histogram: dict[int, int] = {}
    best = None
    target_lines = 27
    for _ in range(samples):
        projection = random_projection(rng)
        sig = projected_edge_signature(combined_vertices, combined_edges, projection)
        family_count = int(sig["absolute_family_count"])
        histogram[family_count] = histogram.get(family_count, 0) + 1
        candidate = {
            "family_count": family_count,
            "projected_edge_count": int(sig["projected_edge_count"]),
            "projected_vertex_count": int(sig["projected_vertex_count"]),
            "family_centers_deg": sig["family_centers_deg"],
            "projection": sig["projection"],
            "score": 100.0 * abs(family_count - TARGET_FAMILY_COUNT) + abs(int(sig["projected_edge_count"]) - target_lines),
        }
        if best is None or (candidate["score"], candidate["family_count"]) < (best["score"], best["family_count"]):
            best = candidate

    report = {
        "samples": samples,
        "tesseract_vertex_count": int(len(tesseract_vertices)),
        "tesseract_edge_count": int(len(tesseract_edges)),
        "cell_vertex_count": int(len(cell_vertices)),
        "cell_edge_count": int(len(cell_edges)),
        "combined_vertex_count": int(len(combined_vertices)),
        "combined_edge_count": int(len(combined_edges)),
        "family_count_histogram": dict(sorted(histogram.items())),
        "best_projection": best,
    }
    data_dir = variant_dir / 'data'
    report_path = data_dir / 'finalize_full_union_scan.json'
    summary_path = data_dir / 'finalize_full_union_scan.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    summary_path.write_text(
        f"""# Full Edge-Union Scan\n\n- samples: `{samples}`\n- tesseract vertices / edges: `{len(tesseract_vertices)}` / `{len(tesseract_edges)}`\n- 24-cell vertices / edges: `{len(cell_vertices)}` / `{len(cell_edges)}`\n- combined vertices / edges: `{len(combined_vertices)}` / `{len(combined_edges)}`\n- family-count histogram: `{dict(sorted(histogram.items()))}`\n- best projection: `{best}`\n"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — finalize-full-edge-union
Цель: проверить, survives ли сильный shell-сигнал ветки `05` на уровне полного edge-union `tesseract + 24-cell`.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage finalize`
Артефакты:
- `data/finalize_full_union_scan.json`
- `data/finalize_full_union_scan.md`
Что считаю:
- случайные 2D-проекции полного объединения рёбер тессеракта и 24-cell;
- распределение по absolute family count;
- best candidate по family-gap и line-gap.
Формулы / reasoning:
- reduced shell-модель уже сильная, но её нужно проверить на более жёстком полном graph-level readout;
- если full union completely explodes по числу семей, shell-сигнал надо трактовать как scaffold, а не как готовый witness.
Промежуточные результаты:
- family-count histogram: `{dict(sorted(histogram.items()))}`
- best projection: `{best}`
Что это значит:
- теперь понятно, живёт ли сильный `05`-сигнал только на direction-shell уровне или переносится на full edge-union.
Сложность:
- средняя.
Следующий шаг:
- если full union слишком богат, думать о subgraph/readout внутри ветки `05`, а не отказываться от неё целиком.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text(
        '# Result\n\n'
        'Status: active\n\n'
        '## Summary\n\n'
        'Branch `05` now has reduced-shell search, local ridge refinement, and a first full edge-union scan.\n\n'
        '## Best Witness\n\n'
        '- `data/analyze_interaction_refine.json`\n'
        '- `data/finalize_full_union_scan.json`\n\n'
        '## Blocking Issues\n\n'
        'Need to decide whether the next move is full-union subgraph selection or to keep branch `05` primarily as the strongest scaffold-level model.\n'
    )

    print(f"variant={variant_dir.name}")
    print('stage=finalize')
    print(f'report={report_path}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['baseline', 'prune', 'search', 'analyze', 'finalize'], default='baseline')
    args = parser.parse_args()
    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == 'baseline':
        return run_baseline(variant_dir)
    if args.stage == 'search':
        return run_search(variant_dir)
    if args.stage == 'analyze':
        return run_analyze(variant_dir)
    if args.stage == 'prune':
        return run_baseline(variant_dir)
    if args.stage == 'finalize':
        return run_finalize(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print('TODO: implement hypothesis-specific workflow')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
