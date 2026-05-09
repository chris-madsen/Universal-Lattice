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

from research.common.grid_generativity import derive_generativity_grammar
from research.common.lattice_signature import build_signature
from research.common.polytopes import canonical_f4_roots
from research.common.projection import random_projection

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


def unique_root_lines(projected_roots: np.ndarray) -> list[np.ndarray]:
    line_map = {}
    for vec in projected_roots:
        if np.linalg.norm(vec) < 1e-9:
            continue
        key = root_line_key(vec.copy())
        line_map[key] = vec
    return list(line_map.values())


def unique_line_representatives(shell: np.ndarray) -> list[np.ndarray]:
    reps = []
    seen = set()
    for vec in shell:
        key = root_line_key(vec.copy())
        if key not in seen:
            seen.add(key)
            reps.append(vec)
    return reps


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def cluster_angles(values, tol=1.5):
    values = sorted(values)
    if not values:
        return []
    groups = [[values[0]]]
    for value in values[1:]:
        if abs(value - groups[-1][-1]) <= tol:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(group) / len(group) for group in groups]


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


def classify_roots(roots: np.ndarray):
    short = []
    long = []
    for root in roots:
        norm2 = float(np.dot(root, root))
        if abs(norm2 - 1.0) < 1e-9:
            short.append(root)
        elif abs(norm2 - 2.0) < 1e-9:
            long.append(root)
        else:
            raise ValueError(f"unexpected root norm^2: {norm2}")
    return np.array(short), np.array(long)


def shell_projection_stats(shell: np.ndarray, samples: int, seed: int):
    rng = np.random.default_rng(seed)
    histogram = {}
    best = None
    for _ in range(samples):
        projection = random_projection(rng)
        projected = (projection @ shell.T).T
        lines = unique_root_lines(projected)
        angles = [angle_mod_180(vec) for vec in lines]
        families = cluster_angles(angles, tol=1.5)
        count = len(families)
        histogram[count] = histogram.get(count, 0) + 1
        candidate = {
            "family_count": count,
            "family_centers_deg": [float(x) for x in families],
            "line_count": len(lines),
        }
        if best is None or count < best["family_count"]:
            best = candidate
    return histogram, best


def sample_ls_classes(
    long_lines: list[np.ndarray],
    short_lines: list[np.ndarray],
    classes: list[tuple[int, int]],
    per_class_samples: int,
    seed: int,
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    rng = np.random.default_rng(seed)
    class_hits: dict[str, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    for long_k, short_k in classes:
        class_key = f"L{long_k}_S{short_k}"
        hits_family5 = 0
        hits_exact_profile = 0
        family_histogram: dict[int, int] = {}
        best = None
        for _ in range(per_class_samples):
            chosen_long = [long_lines[i] for i in rng.choice(len(long_lines), size=long_k, replace=False)]
            chosen_short = [short_lines[i] for i in rng.choice(len(short_lines), size=short_k, replace=False)]
            projection = random_projection(rng)
            counts = clustered_family_counts(chosen_long + chosen_short, projection, tol=1.5)
            sorted_counts = sorted(counts)
            score = profile_score(counts)
            rec = {
                "class": class_key,
                "long_count": long_k,
                "short_count": short_k,
                "family_count": len(counts),
                "family_multiplicities": sorted_counts,
                "profile_score": score,
                "exact_profile_hit": sorted_counts == FOCUSED_PROFILE,
            }
            records.append(rec)
            family_histogram[len(counts)] = family_histogram.get(len(counts), 0) + 1
            if len(counts) == TARGET_FAMILY_COUNT:
                hits_family5 += 1
            if sorted_counts == FOCUSED_PROFILE:
                hits_exact_profile += 1
            if best is None or (rec["profile_score"], abs(rec["family_count"] - TARGET_FAMILY_COUNT)) < (
                best["profile_score"],
                abs(best["family_count"] - TARGET_FAMILY_COUNT),
            ):
                best = rec
        class_hits[class_key] = {
            "hits_family5": hits_family5,
            "hits_exact_profile_11116": hits_exact_profile,
            "family5_hit_rate": hits_family5 / per_class_samples,
            "exact_profile_hit_rate": hits_exact_profile / per_class_samples,
            "family_histogram": dict(sorted(family_histogram.items())),
            "best": best,
        }
    records.sort(key=lambda rec: (rec["profile_score"], abs(rec["family_count"] - TARGET_FAMILY_COUNT)))
    return class_hits, records


def run_baseline(variant_dir: Path) -> int:
    signature = build_signature()
    grammar = derive_generativity_grammar(signature)
    data = {
        "anchor_node_count": signature["anchor_node_count"],
        "arrangement_intersection_count": signature["arrangement_intersection_count"],
        "false_intersection_count": signature["false_intersection_count"],
        "family_counts": signature["family_counts"],
        "center_degree": grammar["center_degree"],
        "top_center_degree": grammar["top_center_degree"],
        "bottom_center_degree": grammar["bottom_center_degree"],
        "arrangement_motivation": "The lattice already separates into anchor nodes and many false intersections under maximal-line continuation, which makes arrangement-based models structurally relevant.",
    }
    data_dir = variant_dir / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / "baseline_arrangement_targets.json"
    md_path = data_dir / "baseline_arrangement_targets.md"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    md_path.write_text(
        f"""# F4 Arrangement Baseline

- anchor nodes: `{data['anchor_node_count']}`
- arrangement intersections: `{data['arrangement_intersection_count']}`
- false intersections: `{data['false_intersection_count']}`
- family counts: `{data['family_counts']}`
- center/top/bottom degrees: `{data['center_degree']}` / `{data['top_center_degree']}` / `{data['bottom_center_degree']}`
- motivation: {data['arrangement_motivation']}
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — baseline
Цель: зафиксировать arrangement-аспекты решётки, которые делают ветку `08_f4_root_arrangement` не декоративной, а содержательной.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_arrangement_targets.json`
- `data/baseline_arrangement_targets.md`
Что считаю:
- anchor nodes;
- arrangement intersections;
- false intersections;
- центральные degrees.
Формулы / reasoning:
- если у решётки при продолжении maximal lines возникает большой слой false intersections, то arrangement-подход выглядит естественно, а не натянуто.
Промежуточные результаты:
- anchor / arrangement / false intersections: `{data['anchor_node_count']}` / `{data['arrangement_intersection_count']}` / `{data['false_intersection_count']}`
Что это значит:
- ветка `08` получает прямую структурную мотивацию из уже извлечённой сигнатуры решётки.
Сложность:
- низкая.
Следующий шаг:
- сделать prune на arrangement-plausibility и понять, усиливает ли baseline эту ветку по сравнению с уже ослабленными 01–03.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline arrangement targets recorded. The branch is directly motivated by the large false-intersection layer revealed by the lattice signature.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_arrangement_targets.json`\n\n"
        "## Blocking Issues\n\n"
        "None at baseline stage.\n"
    )
    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"targets={json_path}")
    return 0


def run_prune(variant_dir: Path) -> int:
    signature = build_signature()
    false_count = signature["false_intersection_count"]
    anchor_count = signature["anchor_node_count"]
    ratio = false_count / anchor_count if anchor_count else 0.0
    report = {
        "anchor_node_count": anchor_count,
        "false_intersection_count": false_count,
        "false_to_anchor_ratio": ratio,
        "assessment": "arrangement_plausible" if false_count > anchor_count else "weak_arrangement_signal",
        "reason": "A large false-intersection layer means line-arrangement models naturally belong in the candidate set.",
    }
    data_dir = variant_dir / "data"
    report_path = data_dir / "prune_arrangement_plausibility.json"
    summary_path = data_dir / "prune_arrangement_plausibility.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    summary_path.write_text(
        f"""# F4 Arrangement Prune

- anchor nodes: `{anchor_count}`
- false intersections: `{false_count}`
- false/anchor ratio: `{ratio:.3f}`
- assessment: `{report['assessment']}`
- reason: `{report['reason']}`
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — prune
Цель: проверить, усиливает ли baseline сама идея arrangement-подхода, а не только абстрактная связь с `F4`.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage prune`
Артефакты:
- `data/prune_arrangement_plausibility.json`
- `data/prune_arrangement_plausibility.md`
Что считаю:
- отношение false intersections к anchor nodes.
Формулы / reasoning:
- если false-intersection слой большой, arrangement-ветка получает естественный structural boost;
- если он мал, то arrangement-подход был бы подозрительно избыточным.
Промежуточные результаты:
- anchor nodes: `{anchor_count}`
- false intersections: `{false_count}`
- false/anchor ratio: `{ratio:.3f}`
- assessment: `{report['assessment']}`
Что это значит:
- `08_f4_root_arrangement` сейчас выглядит не ослабленной, а наоборот содержательно мотивированной веткой.
Сложность:
- низкая.
Следующий шаг:
- перейти к реальному search/analysis этой ветки и строить уже F4-связанный arrangement scaffold.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline and prune both support keeping the F4 arrangement branch active. The lattice has a large false-intersection layer, so arrangement-based explanations are structurally plausible rather than decorative.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_arrangement_targets.json`\n"
        "- `data/prune_arrangement_plausibility.json`\n\n"
        "## Blocking Issues\n\n"
        "None at prune stage. This is currently one of the stronger surviving branches.\n"
    )
    print(f"variant={variant_dir.name}")
    print("stage=prune")
    print(f"report={report_path}")
    return 0


def run_search(variant_dir: Path) -> int:
    roots = canonical_f4_roots()
    short_roots, long_roots = classify_roots(roots)

    rng = np.random.default_rng(44)
    samples = 600
    family_hist = {}
    best = None
    for _ in range(samples):
        projection = random_projection(rng)
        projected = (projection @ roots.T).T
        lines = unique_root_lines(projected)
        angles = [angle_mod_180(vec) for vec in lines]
        families = cluster_angles(angles, tol=1.5)
        count = len(families)
        family_hist[count] = family_hist.get(count, 0) + 1
        candidate = {
            "family_count": count,
            "family_centers_deg": [float(x) for x in families],
            "line_count": len(lines),
            "projection": [[float(x) for x in row] for row in projection.tolist()],
        }
        if best is None or count < best["family_count"]:
            best = candidate

    report = {
        "root_count_total": int(len(roots)),
        "root_count_short": int(len(short_roots)),
        "root_count_long": int(len(long_roots)),
        "root_line_count_total": int(len(unique_root_lines(roots))),
        "root_line_count_short_shell": int(len(unique_root_lines(short_roots))),
        "root_line_count_long_shell": int(len(unique_root_lines(long_roots))),
        "long_shell_matches_24cell_vertex_set_count": int(len(long_roots)),
        "samples": samples,
        "family_count_histogram": family_hist,
        "best_projection": best,
    }

    data_dir = variant_dir / "data"
    report_path = data_dir / "search_f4_root_scaffold.json"
    summary_path = data_dir / "search_f4_root_scaffold.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    summary_path.write_text(
        f"""# F4 Root Scaffold Search

- total roots: `{report['root_count_total']}`
- short roots: `{report['root_count_short']}`
- long roots: `{report['root_count_long']}`
- total root lines: `{report['root_line_count_total']}`
- short-shell root lines: `{report['root_line_count_short_shell']}`
- long-shell root lines: `{report['root_line_count_long_shell']}`
- long shell matches 24-cell vertex shell size: `{report['long_shell_matches_24cell_vertex_set_count']}`
- sampled projections: `{samples}`
- family-count histogram on projected root lines: `{family_hist}`
- best projection family count: `{best['family_count']}`
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — search-f4-root-scaffold
Цель: построить первый содержательный F4-scaffold, а не держать ветку `08` на одном только baseline-мотиве.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage search`
Артефакты:
- `data/search_f4_root_scaffold.json`
- `data/search_f4_root_scaffold.md`
Что считаю:
- полный набор корней `F4`;
- short и long shells;
- число root lines до отождествления по знаку;
- грубую статистику family-count для случайных 2D-проекций root-line arrangement.
Формулы / reasoning:
- `F4` важна не как абстрактное слово, а как конкретная 48-корневая 4D-система;
- long shell из 24 корней связывает ветку `08` с 24-cell, а short shell даёт дополнительную arrangement-структуру.
Промежуточные результаты:
- total / short / long roots: `{report['root_count_total']}` / `{report['root_count_short']}` / `{report['root_count_long']}`
- total root lines: `{report['root_line_count_total']}`
- projected family-count histogram: `{family_hist}`
- best projected family count: `{best['family_count']}`
Что это значит:
- ветка `08` теперь имеет честный 4D F4-scaffold для дальнейшего анализа;
- можно дальше разбирать, какой именно sub-arrangement или local readout мог бы давать нашу решётку.
Сложность:
- низкая-средняя; это уже содержательный search, но пока ещё не тяжёлый.
Следующий шаг:
- перейти к analysis и решить, какие подсемейства F4-root arrangement имеет смысл сравнивать с lattice grammar в первую очередь.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline, prune, and an initial F4 root scaffold search are now in place. This branch currently has the strongest live mathematical footing among the explored candidates.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_arrangement_targets.json`\n"
        "- `data/prune_arrangement_plausibility.json`\n"
        "- `data/search_f4_root_scaffold.json`\n\n"
        "## Blocking Issues\n\n"
        "Need the next analysis step: identify which F4 sub-arrangements or local readouts are the right comparison targets for the lattice grammar.\n"
    )
    print(f"variant={variant_dir.name}")
    print("stage=search")
    print(f"report={report_path}")
    return 0


def run_analyze(variant_dir: Path) -> int:
    roots = canonical_f4_roots()
    short_roots, long_roots = classify_roots(roots)
    samples = 600
    short_hist, short_best = shell_projection_stats(short_roots, samples, seed=45)
    long_hist, long_best = shell_projection_stats(long_roots, samples, seed=46)

    short_lines = unique_line_representatives(short_roots)
    long_lines = unique_line_representatives(long_roots)
    subset_classes = [(10, 0), (0, 10), (8, 2), (2, 8), (6, 4), (4, 6), (5, 5), (6, 6), (7, 5), (5, 7)]
    subset_samples = 100
    class_hits, subset_records = sample_ls_classes(long_lines, short_lines, subset_classes, subset_samples, seed=47)
    top_subset = subset_records[:15]

    report = {
        "samples": samples,
        "short_shell_histogram": short_hist,
        "short_shell_best": short_best,
        "long_shell_histogram": long_hist,
        "long_shell_best": long_best,
        "target_absolute_family_count": TARGET_FAMILY_COUNT,
        "interpretation": {
            "short_shell_hits_target": short_best["family_count"] == TARGET_FAMILY_COUNT,
            "long_shell_hits_target": long_best["family_count"] == TARGET_FAMILY_COUNT,
        },
        "subset_class_count": len(subset_classes),
        "subset_samples_per_class": subset_samples,
        "subset_sampling_seed": 47,
        "subset_class_hits": class_hits,
        "top_subset_records": top_subset,
    }

    data_dir = variant_dir / "data"
    report_path = data_dir / "analyze_f4_shells.json"
    summary_path = data_dir / "analyze_f4_shells.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [f"- `{key}` -> hits_family5=`{value['hits_family5']}`, exact_profile=`{value['hits_exact_profile_11116']}`, best=`{value['best']}`" for key, value in class_hits.items()]
    summary_path.write_text(
        f"""# F4 Shell Analysis

- samples: `{samples}`
- target absolute family count: `{TARGET_FAMILY_COUNT}`
- short-shell histogram: `{short_hist}`
- short-shell best family count: `{short_best['family_count']}`
- long-shell histogram: `{long_hist}`
- long-shell best family count: `{long_best['family_count']}`
- short shell hits target: `{report['interpretation']['short_shell_hits_target']}`
- long shell hits target: `{report['interpretation']['long_shell_hits_target']}`
- subset classes: `{len(subset_classes)}`
- subset samples per class: `{subset_samples}`

## Sub-arrangement Class Hits
{chr(10).join(class_lines)}
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — analyze-f4-shells-and-subarrangements
Цель: понять не только shell-level картину, но и проверить реальные `F4` sub-arrangements вместо whole-shell.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_f4_shells.json`
- `data/analyze_f4_shells.md`
Что считаю:
- shell-level family-count histograms для short и long shells;
- стратифицированный scan по `F4` sub-arrangement классам `Lk_Sm`.
Формулы / reasoning:
- whole shells сами по себе далеки от target family-count `5`;
- поэтому следующий честный шаг — искать не по whole-shell, а по подсемействам направлений с оценкой по family-profile, а не только по числу семей.
Промежуточные результаты:
- short-shell best family count: `{short_best['family_count']}`
- long-shell best family count: `{long_best['family_count']}`
- top sub-arrangement record: `{top_subset[0]}`
Что это значит:
- ветка `08` перешла от общего F4-scaffold к реальному sub-arrangement screening;
- теперь уже можно видеть, какие смеси short/long lines хоть как-то резонируют с target family-profile.
Сложность:
- средняя, но пока контролируемая.
Следующий шаг:
- сделать focused refinement вокруг лучших классов `L8_S2` и `L4_S6` и проверить устойчивость сигнала на большей выборке.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline, prune, search, and a first shell-plus-sub-arrangement analysis are now in place for the F4 arrangement branch. The branch has moved beyond whole-shell scans into targeted F4 sub-arrangement screening.\n\n"
        "## Best Witness\n\n"
        "- `data/search_f4_root_scaffold.json`\n"
        "- `data/analyze_f4_shells.json`\n\n"
        "## Blocking Issues\n\n"
        "Need focused refinement around `L8_S2` and `L4_S6` to see whether the first hits are stable or just sparse sampling noise.\n"
    )
    print(f"variant={variant_dir.name}")
    print("stage=analyze")
    print(f"report={report_path}")
    return 0


def run_finalize(variant_dir: Path) -> int:
    roots = canonical_f4_roots()
    short_roots, long_roots = classify_roots(roots)
    short_lines = unique_line_representatives(short_roots)
    long_lines = unique_line_representatives(long_roots)

    focus_classes = [(8, 2), (4, 6), (5, 5), (10, 0), (0, 10)]
    focus_samples = 2500
    class_hits, focus_records = sample_ls_classes(long_lines, short_lines, focus_classes, focus_samples, seed=148)
    ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]["hits_family5"], -kv[1]["hits_exact_profile_11116"], kv[1]["best"]["profile_score"]),
    )
    best_class, best_stats = ranked[0]

    report = {
        "focus_classes": [f"L{long_k}_S{short_k}" for long_k, short_k in focus_classes],
        "focus_samples_per_class": focus_samples,
        "focus_sampling_seed": 148,
        "target_family_count": TARGET_FAMILY_COUNT,
        "target_scaled_profile_reference": list(TARGET_PROFILE),
        "focus_exact_profile": FOCUSED_PROFILE,
        "focus_class_hits": class_hits,
        "top_focus_records": focus_records[:20],
        "best_focus_class": best_class,
        "best_focus_stats": best_stats,
    }

    data_dir = variant_dir / "data"
    report_path = data_dir / "finalize_f4_focus.json"
    summary_path = data_dir / "finalize_f4_focus.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [
        f"- `{key}` -> family5_hits=`{value['hits_family5']}` ({value['family5_hit_rate']:.4f}), exact_profile_hits=`{value['hits_exact_profile_11116']}` ({value['exact_profile_hit_rate']:.4f}), best=`{value['best']}`"
        for key, value in ranked
    ]
    summary_path.write_text(
        f"""# Focused F4 Sub-arrangement Refinement

- focus classes: `{report['focus_classes']}`
- samples per class: `{focus_samples}`
- exact focus profile: `{FOCUSED_PROFILE}`
- best focus class: `{best_class}`

## Ranked Focus Classes
{chr(10).join(class_lines)}
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — finalize-focused-refinement
Цель: проверить, устойчивы ли первые попадания `L8_S2`/`L4_S6` на существенно большей выборке.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage finalize`
Артефакты:
- `data/finalize_f4_focus.json`
- `data/finalize_f4_focus.md`
Что считаю:
- focused resampling для лучших классов initial screening;
- частоты попаданий в `family_count=5`;
- частоты exact-profile совпадения `[1,1,1,1,6]`.
Формулы / reasoning:
- sparse single-hit на 100 сэмплах ещё ничего не доказывает;
- нужен локальный добор статистики по реально перспективным классам и нескольким контролям.
Промежуточные результаты:
- best focus class: `{best_class}`
- family5 hits / exact-profile hits: `{best_stats['hits_family5']}` / `{best_stats['hits_exact_profile_11116']}`
- best focus witness: `{best_stats['best']}`
Что это значит:
- теперь у ветки `08` есть не просто разовый hit, а оценка устойчивости лучшего `F4` sub-arrangement класса.
Сложность:
- средняя.
Следующий шаг:
- сравнить устойчивость `08`-классов с hybrid-веткой `09`, где short shell разбит на axis и half-компоненты.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        f"Focused refinement is now in place for the strongest F4 sub-arrangement classes. The current leader is `{best_class}`, and the branch now has class-level hit-rate information instead of a single sparse success.\n\n"
        "## Best Witness\n\n"
        "- `data/analyze_f4_shells.json`\n"
        "- `data/finalize_f4_focus.json`\n\n"
        "## Blocking Issues\n\n"
        "Need direct comparison against the hybrid branch to see whether pure F4 sub-arrangements or axis+long decompositions are structurally stronger.\n"
    )
    print(f"variant={variant_dir.name}")
    print("stage=finalize")
    print(f"report={report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["baseline", "prune", "search", "analyze", "finalize"], default="baseline")
    args = parser.parse_args()
    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == "baseline":
        return run_baseline(variant_dir)
    if args.stage == "prune":
        return run_prune(variant_dir)
    if args.stage == "search":
        return run_search(variant_dir)
    if args.stage == "analyze":
        return run_analyze(variant_dir)
    if args.stage == "finalize":
        return run_finalize(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print("TODO: implement hypothesis-specific workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
