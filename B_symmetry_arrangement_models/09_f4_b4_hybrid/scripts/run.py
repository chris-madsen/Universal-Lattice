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


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def split_f4_shells():
    roots = canonical_f4_roots()
    axis = []
    half = []
    long = []
    for root in roots:
        nz = [abs(float(x)) > 1e-9 for x in root]
        norm2 = float(np.dot(root, root))
        if abs(norm2 - 2.0) < 1e-9:
            long.append(root)
        elif abs(norm2 - 1.0) < 1e-9 and sum(nz) == 1:
            axis.append(root)
        elif abs(norm2 - 1.0) < 1e-9:
            half.append(root)
        else:
            raise ValueError(f"unexpected root: {root}")
    return np.array(axis), np.array(half), np.array(long)


def unique_line_representatives(shell: np.ndarray) -> list[np.ndarray]:
    reps = []
    seen = set()
    for vec in shell:
        key = root_line_key(vec.copy())
        if key not in seen:
            seen.add(key)
            reps.append(vec)
    return reps


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


def sample_alh_classes(
    axis_lines: list[np.ndarray],
    long_lines: list[np.ndarray],
    half_lines: list[np.ndarray],
    classes: list[tuple[int, int, int]],
    per_class_samples: int,
    seed: int,
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    rng = np.random.default_rng(seed)
    class_hits: dict[str, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    for a_count, l_count, h_count in classes:
        key = f"A{a_count}_L{l_count}_H{h_count}"
        hits_family5 = 0
        hits_exact_profile = 0
        family_histogram: dict[int, int] = {}
        best = None
        for _ in range(per_class_samples):
            chosen_axis = [axis_lines[i] for i in rng.choice(len(axis_lines), size=a_count, replace=False)]
            chosen_long = [long_lines[i] for i in rng.choice(len(long_lines), size=l_count, replace=False)]
            chosen_half = [half_lines[i] for i in rng.choice(len(half_lines), size=h_count, replace=False)]
            projection = random_projection(rng)
            counts = clustered_family_counts(chosen_axis + chosen_long + chosen_half, projection, tol=1.5)
            sorted_counts = sorted(counts)
            score = profile_score(counts)
            rec = {
                "class": key,
                "axis_count": a_count,
                "long_count": l_count,
                "half_count": h_count,
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
        class_hits[key] = {
            "hits_family5": hits_family5,
            "hits_exact_profile_11116": hits_exact_profile,
            "family5_hit_rate": hits_family5 / per_class_samples,
            "exact_profile_hit_rate": hits_exact_profile / per_class_samples,
            "family_histogram": dict(sorted(family_histogram.items())),
            "best": best,
        }
    records.sort(key=lambda rec: (rec["profile_score"], abs(rec["family_count"] - TARGET_FAMILY_COUNT)))
    return class_hits, records


def load_branch_08_summary() -> dict[str, object] | None:
    base = ROOT / 'research' / 'B_symmetry_arrangement_models' / '08_f4_root_arrangement' / 'data'
    focus = base / 'finalize_f4_focus.json'
    if focus.exists():
        data = json.loads(focus.read_text())
        return {
            'source': 'finalize_f4_focus.json',
            'best_class': data['best_focus_class'],
            'family5_hits': data['best_focus_stats']['hits_family5'],
            'family5_hit_rate': data['best_focus_stats']['family5_hit_rate'],
            'exact_profile_hits': data['best_focus_stats']['hits_exact_profile_11116'],
            'exact_profile_hit_rate': data['best_focus_stats']['exact_profile_hit_rate'],
            'best_record': data['best_focus_stats']['best'],
        }
    analyze = base / 'analyze_f4_shells.json'
    if analyze.exists():
        data = json.loads(analyze.read_text())
        top = data['top_subset_records'][0]
        hits = data['subset_class_hits'][top['class']]
        return {
            'source': 'analyze_f4_shells.json',
            'best_class': top['class'],
            'family5_hits': hits['hits_family5'],
            'family5_hit_rate': hits['hits_family5'] / data['subset_samples_per_class'],
            'exact_profile_hits': hits.get('hits_exact_profile_11116', 0),
            'exact_profile_hit_rate': hits.get('hits_exact_profile_11116', 0) / data['subset_samples_per_class'],
            'best_record': hits['best'],
        }
    return None


def run_baseline(variant_dir: Path) -> int:
    axis, half, long = split_f4_shells()
    axis_lines = unique_line_representatives(axis)
    half_lines = unique_line_representatives(half)
    long_lines = unique_line_representatives(long)
    data = {
        'axis_root_count': int(len(axis)),
        'half_root_count': int(len(half)),
        'long_root_count': int(len(long)),
        'axis_line_count': int(len(axis_lines)),
        'half_line_count': int(len(half_lines)),
        'long_line_count': int(len(long_lines)),
        'motivation': 'B4-like axis+long structure gives a natural vertical-vs-diagonal split; F4 adds the half-integer shell as a refinement layer.',
    }
    data_dir = variant_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / 'baseline_hybrid_shells.json'
    md_path = data_dir / 'baseline_hybrid_shells.md'
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    md_path.write_text(f'''# F4/B4 Hybrid Baseline\n\n- axis roots / lines: `{data['axis_root_count']}` / `{data['axis_line_count']}`\n- half-integer roots / lines: `{data['half_root_count']}` / `{data['half_line_count']}`\n- long roots / lines: `{data['long_root_count']}` / `{data['long_line_count']}`\n- motivation: {data['motivation']}\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text () `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage baseline`\nArtifacts:\n- `data/baseline_hybrid_shells.json`\n- `data/baseline_hybrid_shells.md`\nWhat I think:\n- counts by axis / half / long shells.\nFormula / reasoning:\n- axes correspond well to the idea of a vertical scaffold;\n- long shell corresponds to the diagonal 24-cell part;\n- half shell gives an additional refinement layer.\nIntermediate results:\n- axis lines: `{data['axis_line_count']}`\n- half lines: `{data['half_line_count']}`\n- long lines: `{data['long_line_count']}`\nWhat does this mean:\n- the hybrid branch received an explicit internal decomposition for subsequent search.\nComplexity:\n- low.\nNext step:\n- go to sampling-search for classes `A/L/H`.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: active

## Summary

Baseline shell decomposition recorded for the F4/B4 hybrid branch.

## Best Witness

- `data/baseline_hybrid_shells.json`

## Blocking Issues

Need the first hybrid sampling search.
''')

    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"baseline={json_path}")
    return 0


def run_search(variant_dir: Path) -> int:
    axis, half, long = split_f4_shells()
    axis_lines = unique_line_representatives(axis)
    half_lines = unique_line_representatives(half)
    long_lines = unique_line_representatives(long)

    classes = [
        (3, 8, 0),
        (4, 6, 0),
        (4, 8, 0),
        (3, 6, 2),
        (4, 6, 2),
        (4, 8, 2),
        (2, 8, 2),
        (3, 8, 2),
        (4, 4, 4),
    ]
    per_class_samples = 100
    class_hits, records = sample_alh_classes(axis_lines, long_lines, half_lines, classes, per_class_samples, seed=48)
    top_records = records[:15]
    ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]['hits_family5'], -kv[1]['hits_exact_profile_11116'], kv[1]['best']['profile_score']),
    )

    report = {
        'classes': [f"A{a}_L{l}_H{h}" for a, l, h in classes],
        'per_class_samples': per_class_samples,
        'sampling_seed': 48,
        'class_hits': class_hits,
        'top_records': top_records,
    }
    data_dir = variant_dir / 'data'
    report_path = data_dir / 'search_hybrid_sampling.json'
    summary_path = data_dir / 'search_hybrid_sampling.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [f"- `{key}` -> hits_family5=`{value['hits_family5']}`, exact_profile=`{value['hits_exact_profile_11116']}`, best=`{value['best']}`" for key, value in ranked]
    summary_path.write_text(f'''# F4/B4 Hybrid Search\n\n- per-class samples: `{per_class_samples}`\n\n## Class Hits\n{chr(10).join(class_lines)}\n\n## Top Records\n- `{top_records[0]}`\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text () `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage search`\nArtifacts:\n- `data/search_hybrid_sampling.json`\n- `data/search_hybrid_sampling.md`\nWhat I think:\n- sampling by classes `A/L/H`.\nFormula / reasoning:\n- this is a natural continuation of the `08` branch: they found resonant `L/S`-mixtures, and here the short shell is clearly decomposed into axis and half-integer parts.\nIntermediate results:\n- top record: `{top_records[0]}`\nWhat does this mean:\n- it is clear whether the explicit hybrid decomposition enhances the signal compared to pure `F4` branch.\nDifficulty:\n- moderate, but manageable.\nNext step:\n- do focused refinement for the best `A/L/H` classes and compare them with branch `08`.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: active

## Summary

Baseline and first hybrid sampling search are now in place. The branch is no longer just a conceptual backup; it now has empirical class-level records.

## Best Witness

- `data/baseline_hybrid_shells.json`
- `data/search_hybrid_sampling.json`

## Blocking Issues

Need focused refinement for the strongest `A/L/H` classes and direct comparison against branch `08`.
''')

    print(f"variant={variant_dir.name}")
    print("stage=search")
    print(f"report={report_path}")
    return 0


def run_analyze(variant_dir: Path) -> int:
    axis, half, long = split_f4_shells()
    axis_lines = unique_line_representatives(axis)
    half_lines = unique_line_representatives(half)
    long_lines = unique_line_representatives(long)

    focus_classes = [
        (4, 6, 0),
        (3, 8, 0),
        (4, 4, 4),
        (3, 6, 2),
        (4, 6, 2),
    ]
    focus_samples = 2500
    class_hits, records = sample_alh_classes(axis_lines, long_lines, half_lines, focus_classes, focus_samples, seed=149)
    ranked = sorted(
        class_hits.items(),
        key=lambda kv: (-kv[1]['hits_family5'], -kv[1]['hits_exact_profile_11116'], kv[1]['best']['profile_score']),
    )
    best_class, best_stats = ranked[0]
    best_record = best_stats['best']
    branch_08 = load_branch_08_summary()

    half_helpful = any(
        value['best']['half_count'] > 0 and value['best']['profile_score'] <= best_record['profile_score']
        for value in class_hits.values()
    )

    comparison = None
    if branch_08 is not None:
        comparison = {
            'branch_08_source': branch_08['source'],
            'branch_08_best_class': branch_08['best_class'],
            'branch_08_family5_hit_rate': branch_08['family5_hit_rate'],
            'branch_08_exact_profile_hit_rate': branch_08['exact_profile_hit_rate'],
            'branch_09_best_class': best_class,
            'branch_09_family5_hit_rate': best_stats['family5_hit_rate'],
            'branch_09_exact_profile_hit_rate': best_stats['exact_profile_hit_rate'],
            'hybrid_beats_08_on_family5_rate': best_stats['family5_hit_rate'] > branch_08['family5_hit_rate'],
            'hybrid_beats_08_on_exact_profile_rate': best_stats['exact_profile_hit_rate'] > branch_08['exact_profile_hit_rate'],
        }

    report = {
        'focus_classes': [f"A{a}_L{l}_H{h}" for a, l, h in focus_classes],
        'focus_samples_per_class': focus_samples,
        'focus_sampling_seed': 149,
        'focus_exact_profile': FOCUSED_PROFILE,
        'class_hits': class_hits,
        'top_records': records[:20],
        'best_focus_class': best_class,
        'best_focus_stats': best_stats,
        'interpretation': {
            'best_class_uses_half_shell': best_record['half_count'] > 0,
            'any_half_class_matches_or_beats_best_score': half_helpful,
            'current_read': 'axis+long currently dominates the hybrid branch' if best_record['half_count'] == 0 else 'half-shell remains competitive',
        },
        'comparison_to_branch_08': comparison,
    }
    data_dir = variant_dir / 'data'
    report_path = data_dir / 'analyze_hybrid_refine.json'
    summary_path = data_dir / 'analyze_hybrid_refine.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    class_lines = [
        f"- `{key}` -> family5_hits=`{value['hits_family5']}` ({value['family5_hit_rate']:.4f}), exact_profile_hits=`{value['hits_exact_profile_11116']}` ({value['exact_profile_hit_rate']:.4f}), best=`{value['best']}`"
        for key, value in ranked
    ]
    comparison_lines = []
    if comparison is not None:
        comparison_lines = [
            f"- branch 08 source: `{comparison['branch_08_source']}`",
            f"- branch 08 best class: `{comparison['branch_08_best_class']}`",
            f"- branch 08 family5 hit rate: `{comparison['branch_08_family5_hit_rate']:.4f}`",
            f"- branch 09 family5 hit rate: `{comparison['branch_09_family5_hit_rate']:.4f}`",
            f"- branch 08 exact-profile hit rate: `{comparison['branch_08_exact_profile_hit_rate']:.4f}`",
            f"- branch 09 exact-profile hit rate: `{comparison['branch_09_exact_profile_hit_rate']:.4f}`",
        ]
    summary_path.write_text(f'''# Focused F4/B4 Hybrid Refinement\n\n- focus classes: `{report['focus_classes']}`\n- samples per class: `{focus_samples}`\n- best focus class: `{best_class}`\n- interpretation: `{report['interpretation']['current_read']}`\n\n## Ranked Focus Classes\n{chr(10).join(class_lines)}\n\n## Comparison To Branch 08\n{chr(10).join(comparison_lines) if comparison_lines else '- branch 08 summary not available'}\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text().rstrip() + f'''\n\n## {now_string()} - analyze-focused-hybrid\nGoal: test the stability of the best hybrid classes and directly compare them with `08_f4_root_arrangement`.\nHypothesis: `09_f4_b4_hybrid`\nScript: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage analyze`\nArtifacts:\n- `data/analyze_hybrid_refine.json`\n- `data/analyze_hybrid_refine.md`\nWhat I think:\n- focused resampling of the best `A/L/H` classes;\n- hit rates in `family_count=5`;\n- frequencies exact-profile `[1,1,1,1,6]`;\n- direct comparison with branch `08`.\nFormulas / reasoning:\n- initial single-hit on 100 samples is too weak to draw conclusions;\n- you need to get statistics and separately check whether half-shell really helps, or the best hybrid is actually reduced to axis+long.\nIntermediate results:\n- best focus class: `{best_class}`\n- family5 hits / exact-profile hits: `{best_stats['hits_family5']}` / `{best_stats['hits_exact_profile_11116']}`\n- best focus witness: `{best_record}`\nWhat does this mean:\n- now you can honestly compare pure `F4` sub-arrangement and hybrid `F4/B4` interpretations, and not argue at the level of beautiful words.\nDifficulty:\n- average.\nNext step:\n- if axis+long dominates again, this strengthens the transition to `05_24cell_tesseract_interaction`; if half-shell starts to win, deepen `09` further.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text(
        '# Result\n\n'
        'Status: active\n\n'
        '## Summary\n\n'
        f'Focused refinement is now in place for the strongest hybrid classes. The current leader is `{best_class}`, and the branch now has hit-rate data plus a direct comparison against branch `08`.\n\n'
        '## Best Witness\n\n'
        '- `data/search_hybrid_sampling.json`\n'
        '- `data/analyze_hybrid_refine.json`\n\n'
        '## Blocking Issues\n\n'
        'Need to decide whether the hybrid signal really adds explanatory power or just rephrases an axis+long scaffold that should be handed off to branch `05`.\n'
    )

    print(f"variant={variant_dir.name}")
    print("stage=analyze")
    print(f"report={report_path}")
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
    if args.stage == 'prune':
        return run_search(variant_dir)
    if args.stage == 'analyze':
        return run_analyze(variant_dir)
    if args.stage == 'finalize':
        return run_analyze(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print('TODO: implement hypothesis-specific workflow')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
