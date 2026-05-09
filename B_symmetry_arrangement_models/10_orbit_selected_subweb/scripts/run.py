#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
import itertools
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
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


def canonical_24cell_vertices() -> np.ndarray:
    verts = set()
    for perm in set(itertools.permutations([1, 1, 0, 0], 4)):
        nz = [i for i, v in enumerate(perm) if v != 0]
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                p = list(perm)
                p[nz[0]] *= s1
                p[nz[1]] *= s2
                verts.add(tuple(float(x) for x in p))
    return np.array(sorted(verts), dtype=float)


def random_projection(rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(4, 4))
    q, _ = np.linalg.qr(matrix)
    return np.vstack([q[0], q[1]])


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


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


def load_branch05_refs() -> tuple[dict | None, dict | None]:
    analyze = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'analyze_interaction_refine.json'
    full = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'finalize_full_union_scan.json'
    analyze_data = json.loads(analyze.read_text()) if analyze.exists() else None
    full_data = json.loads(full.read_text()) if full.exists() else None
    return analyze_data, full_data


def orbit_buckets(axis_dim_count: int) -> dict[int, list[np.ndarray]]:
    cell_lines = unique_line_representatives(canonical_24cell_vertices())
    selected_dims = set(range(axis_dim_count))
    buckets = {0: [], 1: [], 2: []}
    for vec in cell_lines:
        support = {i for i, x in enumerate(vec) if abs(float(x)) > 1e-9}
        buckets[len(support & selected_dims)].append(vec)
    return buckets


def axis_subset_lines(axis_dim_count: int) -> list[np.ndarray]:
    axis_lines = unique_line_representatives(tesseract_axis_vectors())
    return axis_lines[:axis_dim_count]


def generate_templates() -> list[dict[str, object]]:
    templates = []
    # k=2: buckets c2,c1,c0 with capacities 2,8,2; totals near best branch-05 cell counts 4..6
    caps2 = {2: 2, 1: 8, 0: 2}
    for total in (4, 5, 6):
        for c2 in range(caps2[2] + 1):
            for c1 in range(caps2[1] + 1):
                c0 = total - c2 - c1
                if 0 <= c0 <= caps2[0]:
                    templates.append({"axis_dims": 2, "bucket_counts": {2: c2, 1: c1, 0: c0}})
    # k=3: buckets c2,c1 with capacities 6,6
    caps3 = {2: 6, 1: 6}
    for total in (4, 5, 6):
        for c2 in range(caps3[2] + 1):
            c1 = total - c2
            if 0 <= c1 <= caps3[1]:
                templates.append({"axis_dims": 3, "bucket_counts": {2: c2, 1: c1, 0: 0}})
    # k=4 degenerates to all overlap-2, included as control
    for total in (4, 5, 6):
        templates.append({"axis_dims": 4, "bucket_counts": {2: total, 1: 0, 0: 0}})
    # dedup
    uniq = {}
    for tmpl in templates:
        key = (tmpl['axis_dims'], tmpl['bucket_counts'][2], tmpl['bucket_counts'][1], tmpl['bucket_counts'][0])
        uniq[key] = tmpl
    return [uniq[k] for k in sorted(uniq)]


def template_key(template: dict[str, object]) -> str:
    bc = template['bucket_counts']
    return f"A{template['axis_dims']}_B2-{bc[2]}_B1-{bc[1]}_B0-{bc[0]}"


def sample_template(template: dict[str, object], per_template_samples: int, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    axis_lines = axis_subset_lines(template['axis_dims'])
    buckets = orbit_buckets(template['axis_dims'])
    hits_family5 = 0
    hits_exact = 0
    family_hist: dict[int, int] = {}
    best = None
    for _ in range(per_template_samples):
        selected = list(axis_lines)
        feasible = True
        for bucket_id, count in template['bucket_counts'].items():
            if count > len(buckets[bucket_id]):
                feasible = False
                break
            if count > 0:
                chosen_idx = rng.choice(len(buckets[bucket_id]), size=count, replace=False)
                selected.extend([buckets[bucket_id][i] for i in chosen_idx])
        if not feasible:
            continue
        projection = random_projection(rng)
        counts = clustered_family_counts(selected, projection, tol=1.5)
        sorted_counts = sorted(counts)
        rec = {
            'template': template_key(template),
            'axis_dims': template['axis_dims'],
            'bucket_counts': template['bucket_counts'],
            'family_count': len(counts),
            'family_multiplicities': sorted_counts,
            'profile_score': profile_score(counts),
            'exact_profile_hit': sorted_counts == FOCUSED_PROFILE,
        }
        family_hist[len(counts)] = family_hist.get(len(counts), 0) + 1
        if len(counts) == TARGET_FAMILY_COUNT:
            hits_family5 += 1
        if sorted_counts == FOCUSED_PROFILE:
            hits_exact += 1
        if best is None or (rec['profile_score'], abs(rec['family_count'] - TARGET_FAMILY_COUNT)) < (
            best['profile_score'], abs(best['family_count'] - TARGET_FAMILY_COUNT)
        ):
            best = rec
    return {
        'template': template_key(template),
        'axis_dims': template['axis_dims'],
        'bucket_counts': template['bucket_counts'],
        'hits_family5': hits_family5,
        'hits_exact_profile_11116': hits_exact,
        'family5_hit_rate': hits_family5 / per_template_samples,
        'exact_profile_hit_rate': hits_exact / per_template_samples,
        'family_histogram': dict(sorted(family_hist.items())),
        'best': best,
    }


def run_baseline(variant_dir: Path) -> int:
    t_lines = unique_line_representatives(tesseract_axis_vectors())
    c_lines = unique_line_representatives(canonical_24cell_vertices())
    analyze_05, _ = load_branch05_refs()
    imported = None
    if analyze_05 is not None:
        imported = {
            'best_family5_class': analyze_05['best_family5_class'],
            'best_family5_rate': analyze_05['best_family5_stats']['family5_hit_rate'],
            'best_exact_class': analyze_05['best_exact_class'],
            'best_exact_rate': analyze_05['best_exact_stats']['exact_profile_hit_rate'],
        }
    payload = {
        'orbit_blocks': {
            'tesseract_axis_lines': len(t_lines),
            'cell_direction_lines': len(c_lines),
        },
        'bucket_layout_examples': {
            'axis_dims_2': {k: len(v) for k, v in orbit_buckets(2).items()},
            'axis_dims_3': {k: len(v) for k, v in orbit_buckets(3).items()},
            'axis_dims_4': {k: len(v) for k, v in orbit_buckets(4).items()},
        },
        'working_orbit_language': ['choose axis-dimension subset size', 'choose counts from overlap buckets B2/B1/B0'],
        'motivation': 'Branch 05 shows strong scaffold-level signal but full union is too rich; branch 10 formalizes pruning as symmetry-guided orbit selection rather than arbitrary deletion.',
        'imported_branch05_signal': imported,
    }
    data_dir = variant_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / 'baseline_orbit_blocks.json'
    md_path = data_dir / 'baseline_orbit_blocks.md'
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    md_path.write_text(
        f"""# Orbit-Selected Subweb Baseline

- tesseract axis lines: `{len(t_lines)}`
- 24-cell direction lines: `{len(c_lines)}`
- bucket layout axis_dims=2: `{payload['bucket_layout_examples']['axis_dims_2']}`
- bucket layout axis_dims=3: `{payload['bucket_layout_examples']['axis_dims_3']}`
- bucket layout axis_dims=4: `{payload['bucket_layout_examples']['axis_dims_4']}`
- working orbit language: `{payload['working_orbit_language']}`
- motivation: {payload['motivation']}
- imported branch 05 signal: `{imported}`
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — baseline
Цель: формализовать, из каких orbit-блоков вообще может состоять selected subweb внутри богатого `tesseract + 24-cell` union.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_orbit_blocks.json`
- `data/baseline_orbit_blocks.md`
Что считаю:
- минимальные orbit-блоки, с которыми сейчас реально работаем;
- перенос сигнала из ветки `05` в orbit-язык.
Формулы / reasoning:
- если full union слишком богат, нужен язык симметрийно мотивированного отбора;
- на текущем шаге естественные блоки — это осевые линии тессеракта и overlap-бакеты directional lines 24-cell.
Промежуточные результаты:
- tesseract axis lines: `{len(t_lines)}`
- 24-cell direction lines: `{len(c_lines)}`
- bucket layout axis_dims=2: `{payload['bucket_layout_examples']['axis_dims_2']}`
Что это значит:
- ветка `10` получила минимальную осмысленную постановку, а не пустой placeholder.
Сложность:
- низкая.
Следующий шаг:
- сделать prune: показать, почему orbit-selection сейчас выглядит необходимым, а не декоративным.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('# Result\n\nStatus: active\n\n## Summary\n\nBaseline orbit blocks are now explicit for the selected-subweb branch.\n\n## Best Witness\n\n- `data/baseline_orbit_blocks.json`\n\n## Blocking Issues\n\nNeed prune justification from branch 05 full-union richness.\n')
    print(f"variant={variant_dir.name}")
    print('stage=baseline')
    print(f'baseline={json_path}')
    return 0


def run_prune(variant_dir: Path) -> int:
    analyze_05, full_05 = load_branch05_refs()
    if not (analyze_05 and full_05):
        raise SystemExit('branch 05 artifacts missing for prune stage')
    best_family_count = full_05['best_projection']['family_count']
    best_scaffold_rate = analyze_05['best_family5_stats']['family5_hit_rate']
    report = {
        'full_union_best_family_count': best_family_count,
        'full_union_histogram': full_05['family_count_histogram'],
        'branch05_best_family5_class': analyze_05['best_family5_class'],
        'branch05_best_family5_rate': best_scaffold_rate,
        'assessment': 'orbit_selection_plausible' if best_family_count > 5 and best_scaffold_rate > 0.001 else 'weak_orbit_selection_case',
        'reason': 'The raw full union remains much richer than the target lattice, while selected scaffold classes show strong family-5 resonance. That gap is exactly what an orbit-selected-subweb branch is meant to explain.',
    }
    data_dir = variant_dir / 'data'
    json_path = data_dir / 'prune_orbit_selection_case.json'
    md_path = data_dir / 'prune_orbit_selection_case.md'
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    md_path.write_text(
        f"""# Orbit Selection Prune

- full-union best family count: `{best_family_count}`
- full-union histogram: `{full_05['family_count_histogram']}`
- branch 05 best family5 class: `{analyze_05['best_family5_class']}`
- branch 05 best family5 rate: `{best_scaffold_rate:.6f}`
- assessment: `{report['assessment']}`
- reason: {report['reason']}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — prune
Цель: зафиксировать, почему `orbit_selected_subweb` сейчас нужен по данным, а не просто как запасная идея.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage prune`
Артефакты:
- `data/prune_orbit_selection_case.json`
- `data/prune_orbit_selection_case.md`
Что считаю:
- разрыв между богатством raw full union и силой selected scaffold-классов из ветки `05`.
Формулы / reasoning:
- если raw union стабильно слишком богат, а selected classes уже дают сильный резонанс, значит нужен язык осмысленного отбора, а не полный граф.
Промежуточные результаты:
- full-union best family count: `{best_family_count}`
- branch05 best family5 rate: `{best_scaffold_rate:.6f}`
- assessment: `{report['assessment']}`
Что это значит:
- ветка `10` теперь не декоративная: у неё есть прямой data-driven повод жить.
Сложность:
- низкая.
Следующий шаг:
- переходить к search по орбитальному языку отбора, а не только по числу T/C линий.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('# Result\n\nStatus: active\n\n## Summary\n\nBaseline and prune are now in place for the orbit-selected-subweb branch.\n\n## Best Witness\n\n- `data/baseline_orbit_blocks.json`\n- `data/prune_orbit_selection_case.json`\n\n## Blocking Issues\n\nNeed a real search language for symmetry-guided subweb selection inside the rich full union.\n')
    print(f"variant={variant_dir.name}")
    print('stage=prune')
    print(f'prune={json_path}')
    return 0


def run_search(variant_dir: Path) -> int:
    templates = generate_templates()
    per_template_samples = 1500
    results = []
    for idx, template in enumerate(templates):
        results.append(sample_template(template, per_template_samples, seed=300 + idx))
    ranked = sorted(
        results,
        key=lambda r: (-r['hits_family5'], -r['hits_exact_profile_11116'], r['best']['profile_score'] if r['best'] else 1e9),
    )
    top = ranked[:15]
    payload = {
        'template_count': len(templates),
        'per_template_samples': per_template_samples,
        'templates': [template_key(t) for t in templates],
        'results': results,
        'top_results': top,
    }
    data_dir = variant_dir / 'data'
    json_path = data_dir / 'search_orbit_templates.json'
    md_path = data_dir / 'search_orbit_templates.md'
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    lines = [
        f"- `{r['template']}` -> family5=`{r['hits_family5']}` ({r['family5_hit_rate']:.4f}), exact=`{r['hits_exact_profile_11116']}` ({r['exact_profile_hit_rate']:.4f}), best=`{r['best']}`"
        for r in top
    ]
    md_path.write_text(
        f"""# Orbit Template Search

- template count: `{len(templates)}`
- samples per template: `{per_template_samples}`

## Top Results
{chr(10).join(lines)}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — search
Цель: перейти от общего лозунга `selected subweb` к реальному orbit-языку отбора.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage search`
Артефакты:
- `data/search_orbit_templates.json`
- `data/search_orbit_templates.md`
Что считаю:
- search по template-ам вида `axis_dims + bucket_counts(B2,B1,B0)`.
Формулы / reasoning:
- вместо произвольного выбора C-линий вводится орбитальная параметризация через overlap-бакеты относительно выбранного axis-subset.
Промежуточные результаты:
- top orbit template: `{top[0]['template']}`
- hits family5 / exact: `{top[0]['hits_family5']}` / `{top[0]['hits_exact_profile_11116']}`
Что это значит:
- теперь у ветки `10` есть первый реальный search-слой, а не только baseline/prune.
Сложность:
- средняя.
Следующий шаг:
- сравнить лучшие orbit-template-ы с сильными классами ветки `05` и посмотреть, не даёт ли orbit-язык более компактное объяснение.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('# Result\n\nStatus: active\n\n## Summary\n\nOrbit-template search is now in place for the selected-subweb branch.\n\n## Best Witness\n\n- `data/search_orbit_templates.json`\n\n## Blocking Issues\n\nNeed comparison against branch 05 class-level winners.\n')
    print(f"variant={variant_dir.name}")
    print('stage=search')
    print(f'search={json_path}')
    return 0


def run_analyze(variant_dir: Path) -> int:
    search_path = variant_dir / 'data' / 'search_orbit_templates.json'
    analyze_05, _ = load_branch05_refs()
    if not search_path.exists() or analyze_05 is None:
        raise SystemExit('missing search or branch05 artifacts')
    data = json.loads(search_path.read_text())
    ranked = data['top_results']
    comparison = {
        'branch05_best_family5_class': analyze_05['best_family5_class'],
        'branch05_best_family5_rate': analyze_05['best_family5_stats']['family5_hit_rate'],
        'branch05_best_exact_class': analyze_05['best_exact_class'],
        'branch05_best_exact_rate': analyze_05['best_exact_stats']['exact_profile_hit_rate'],
        'branch10_best_template': ranked[0]['template'],
        'branch10_best_family5_rate': ranked[0]['family5_hit_rate'],
        'branch10_best_exact_rate': ranked[0]['exact_profile_hit_rate'],
        'branch10_beats_05_on_family5': ranked[0]['family5_hit_rate'] > analyze_05['best_family5_stats']['family5_hit_rate'],
        'branch10_beats_05_on_exact': ranked[0]['exact_profile_hit_rate'] > analyze_05['best_exact_stats']['exact_profile_hit_rate'],
    }
    payload = {
        'comparison': comparison,
        'top_results': ranked[:10],
        'interpretation': 'orbit-language is promising if it compresses branch 05 winners into a smaller symmetry-motivated description, even if raw hit-rate is lower',
    }
    data_dir = variant_dir / 'data'
    json_path = data_dir / 'analyze_orbit_templates.json'
    md_path = data_dir / 'analyze_orbit_templates.md'
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    md_path.write_text(
        f"""# Orbit Template Analysis

- branch 05 best family5 class: `{comparison['branch05_best_family5_class']}` rate=`{comparison['branch05_best_family5_rate']:.4f}`
- branch 05 best exact class: `{comparison['branch05_best_exact_class']}` rate=`{comparison['branch05_best_exact_rate']:.4f}`
- branch 10 best template: `{comparison['branch10_best_template']}` rate=`{comparison['branch10_best_family5_rate']:.4f}`
- branch 10 best exact rate: `{comparison['branch10_best_exact_rate']:.4f}`
- branch 10 beats 05 on family5: `{comparison['branch10_beats_05_on_family5']}`
- branch 10 beats 05 on exact: `{comparison['branch10_beats_05_on_exact']}`
- interpretation: {payload['interpretation']}
"""
    )

    log_path = variant_dir / 'log.md'
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — analyze
Цель: понять, даёт ли orbit-template язык не просто search-результат, а более компактное объяснение сильных branch-05 сигналов.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_orbit_templates.json`
- `data/analyze_orbit_templates.md`
Что считаю:
- сравнение лучших orbit-template-ов с сильнейшими class-level winners из ветки `05`.
Формулы / reasoning:
- branch `10` не обязана бить `05` по сырому hit-rate;
- её задача — дать более осмысленный symmetry-guided язык отбора, если он объясняет те же зоны резонанса компактнее.
Промежуточные результаты:
- branch10 best template: `{comparison['branch10_best_template']}`
- family5 / exact rates: `{comparison['branch10_best_family5_rate']:.4f}` / `{comparison['branch10_best_exact_rate']:.4f}`
Что это значит:
- понятно, усиливает ли `10` интерпретацию `05`, или пока остаётся только красивой оболочкой.
Сложность:
- низкая.
Следующий шаг:
- если `10` даёт компактный orbit-язык для лучших `05` зон, можно переносить фокус на subgraph/readout внутри полного union уже через эту parameterization.
"""
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('# Result\n\nStatus: active\n\n## Summary\n\nOrbit-template search and analysis are now in place for branch 10.\n\n## Best Witness\n\n- `data/search_orbit_templates.json`\n- `data/analyze_orbit_templates.json`\n\n## Blocking Issues\n\nNeed to decide whether branch 10 is already strong enough to guide branch 05 subgraph/readout selection.\n')
    print(f"variant={variant_dir.name}")
    print('stage=analyze')
    print(f'analyze={json_path}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['baseline', 'prune', 'search', 'analyze', 'finalize'], default='baseline')
    args = parser.parse_args()
    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == 'baseline':
        return run_baseline(variant_dir)
    if args.stage == 'prune':
        return run_prune(variant_dir)
    if args.stage == 'search':
        return run_search(variant_dir)
    if args.stage == 'analyze':
        return run_analyze(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print('TODO: implement hypothesis-specific workflow')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
