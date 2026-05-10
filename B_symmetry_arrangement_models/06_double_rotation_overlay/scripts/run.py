#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime
import math
from collections import defaultdict

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.lattice_signature import build_signature
from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices
from research.common.projection import projected_edge_signature, random_projection


TARGET_LINE_COUNT = 27
TARGET_FAMILY_COUNT = 5
TARGET_ANCHOR_COUNT = 15
RATIO_CLASSES = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 4)]
BASE_ANGLES_DEG = [7.5, 15.0, 22.5, 30.0]
PLANE_DECOMPOSITIONS = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
PROJECTION_SEEDS = list(range(20))


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def rotation_in_plane(i: int, j: int, theta: float) -> np.ndarray:
    matrix = np.eye(4)
    c = math.cos(theta)
    s = math.sin(theta)
    matrix[i, i] = c
    matrix[j, j] = c
    matrix[i, j] = -s
    matrix[j, i] = s
    return matrix


def double_rotation_matrix(plane_choice, alpha: float, beta: float) -> np.ndarray:
    (i1, j1), (i2, j2) = plane_choice
    return rotation_in_plane(i1, j1, alpha) @ rotation_in_plane(i2, j2, beta)


def overlay_signature(vertices: np.ndarray, edges: list[tuple[int, int]], projection: np.ndarray, rotation: np.ndarray) -> dict[str, object]:
    rotated = (rotation @ vertices.T).T
    combined_vertices = np.vstack([vertices, rotated])
    offset = len(vertices)
    combined_edges = list(edges) + [(i + offset, j + offset) for i, j in edges]
    sig = projected_edge_signature(combined_vertices, combined_edges, projection)
    sig["line_gap"] = abs(sig["projected_edge_count"] - TARGET_LINE_COUNT)
    sig["family_gap"] = abs(sig["absolute_family_count"] - TARGET_FAMILY_COUNT)
    sig["vertex_gap"] = abs(sig["projected_vertex_count"] - TARGET_ANCHOR_COUNT)
    sig["resonance_score"] = 100 * sig["family_gap"] + sig["line_gap"] + 0.5 * sig["vertex_gap"] + 10 * sig["zero_edges"]
    return sig


def ratio_label(ratio: tuple[int, int]) -> str:
    return f"{ratio[0]}:{ratio[1]}"


def plane_label(plane_choice) -> str:
    return f"{plane_choice[0][0]}{plane_choice[0][1]}|{plane_choice[1][0]}{plane_choice[1][1]}"


def run_baseline(variant_dir: Path) -> int:
    signature = build_signature()
    data = {
        "target_absolute_family_count": len(signature["family_counts"]),
        "target_anchor_node_count": signature["anchor_node_count"],
        "target_false_intersection_count": signature["false_intersection_count"],
        "target_maximal_line_count": signature["maximal_line_count"],
        "parameter_axes": [
            "projection_plane_in_Gr(2,4)",
            "rotation_angle_alpha",
            "rotation_angle_beta",
            "rotation_plane_choice",
        ],
        "stratified_scan": {
            "ratio_classes": [ratio_label(r) for r in RATIO_CLASSES],
            "base_angles_deg": BASE_ANGLES_DEG,
            "plane_decompositions": [plane_label(p) for p in PLANE_DECOMPOSITIONS],
            "projection_seed_count": len(PROJECTION_SEEDS),
            "frozen_overlay_mode": "edge_union",
        },
    }
    data_dir = variant_dir / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / "baseline_double_rotation_space.json"
    md_path = data_dir / "baseline_double_rotation_space.md"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    md_path.write_text(
        f"""# Double Rotation Baseline

- target absolute family count: `{data['target_absolute_family_count']}`
- target maximal line count: `{data['target_maximal_line_count']}`
- parameter axes: `{data['parameter_axes']}`
- ratio classes: `{data['stratified_scan']['ratio_classes']}`
- base angles: `{data['stratified_scan']['base_angles_deg']}`
- plane decompositions: `{data['stratified_scan']['plane_decompositions']}`
- projection seeds: `{data['stratified_scan']['projection_seed_count']}`
- overlay mode for first scan: `{data['stratified_scan']['frozen_overlay_mode']}`
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — baseline
Goal: to fix the working space of parameters for the double-rotation branch and transfer it from exhaustive search to stratified sampling.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_double_rotation_space.json`
- `data/baseline_double_rotation_space.md`
What I think:
- which parameter axes actually participate in the branch;
- which ratio classes and plane classes should be scanned first.
Formulas/reasoning:
- instead of a complete search, a stratified sample is taken by ratio classes, plane decompositions, base angles and projection seeds;
- the first scan deliberately freezes the overlay mode in `edge_union`, so as not to swell with unnecessary dimensions.
Intermediate results:
- ratio classes: `{data['stratified_scan']['ratio_classes']}`
- projection seeds: `{data['stratified_scan']['projection_seed_count']}`
What does it mean:
- branch `06` becomes working again, but not through stupid brute force, but through meaningful sampling-coverage of combination classes.
Complexity:
- average.
Next step:
- do a stratified search and look at the distribution of resonance indicators by class.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline parameter space recorded for the double-rotation branch. The branch is reopened through stratified sampling rather than rejected via full-space brute-force logic.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_double_rotation_space.json`\n\n"
        "## Blocking Issues\n\n"
        "Need the first stratified search distribution.\n"
    )

    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"space={json_path}")
    return 0


def run_search(variant_dir: Path) -> int:
    vertices = canonical_24cell_vertices()
    edges = canonical_24cell_edges(vertices)
    class_stats: dict[str, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    family_hist: dict[int, int] = defaultdict(int)

    for ratio in RATIO_CLASSES:
        ratio_name = ratio_label(ratio)
        for plane_choice in PLANE_DECOMPOSITIONS:
            plane_name = plane_label(plane_choice)
            class_key = f"ratio={ratio_name}|planes={plane_name}"
            stats = {
                "count": 0,
                "target_hits": 0,
                "family_sum": 0.0,
                "best": None,
            }
            for base_deg in BASE_ANGLES_DEG:
                alpha = math.radians(base_deg * ratio[0])
                beta = math.radians(base_deg * ratio[1])
                rotation = double_rotation_matrix(plane_choice, alpha, beta)
                for seed in PROJECTION_SEEDS:
                    rng = np.random.default_rng(seed)
                    projection = random_projection(rng)
                    sig = overlay_signature(vertices, edges, projection, rotation)
                    record = {
                        "ratio_class": ratio_name,
                        "plane_class": plane_name,
                        "base_angle_deg": base_deg,
                        "alpha_deg": math.degrees(alpha),
                        "beta_deg": math.degrees(beta),
                        "projection_seed": seed,
                        **sig,
                    }
                    records.append(record)
                    family_hist[sig["absolute_family_count"]] += 1
                    stats["count"] += 1
                    stats["family_sum"] += sig["absolute_family_count"]
                    if sig["absolute_family_count"] == TARGET_FAMILY_COUNT:
                        stats["target_hits"] += 1
                    if stats["best"] is None or record["resonance_score"] < stats["best"]["resonance_score"]:
                        stats["best"] = record
            stats["mean_family_count"] = stats["family_sum"] / stats["count"] if stats["count"] else None
            del stats["family_sum"]
            class_stats[class_key] = stats

    records.sort(key=lambda r: (r["resonance_score"], r["family_gap"], r["line_gap"], r["zero_edges"]))
    top_records = records[:20]
    total_samples = len(records)
    overall_target_hits = sum(1 for rec in records if rec["absolute_family_count"] == TARGET_FAMILY_COUNT)
    best_overall = top_records[0]

    report = {
        "total_samples": total_samples,
        "family_count_histogram": dict(sorted(family_hist.items())),
        "overall_target_hits": overall_target_hits,
        "best_overall": best_overall,
        "top_records": top_records,
        "class_stats": class_stats,
    }

    data_dir = variant_dir / "data"
    report_path = data_dir / "search_stratified_sampling_report.json"
    summary_path = data_dir / "search_stratified_sampling_report.md"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))

    best_classes = sorted(class_stats.items(), key=lambda kv: kv[1]["best"]["resonance_score"])[:5]
    best_class_lines = [
        f"- `{key}` -> best family=`{stats['best']['absolute_family_count']}`, line_count=`{stats['best']['projected_edge_count']}`, score=`{stats['best']['resonance_score']}`"
        for key, stats in best_classes
    ]
    summary_path.write_text(
        f"""# Double Rotation Stratified Search

- total samples: `{total_samples}`
- family-count histogram: `{dict(sorted(family_hist.items()))}`
- overall target hits (`family_count=5`): `{overall_target_hits}`
- best overall: `{best_overall}`

## Best Classes
{chr(10).join(best_class_lines)}
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — search-stratified-sampling
Goal: replace the crude “too many combinations” with real sampling based on the main classes of combinations.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage search`
Artifacts:
- `data/search_stratified_sampling_report.json`
- `data/search_stratified_sampling_report.md`
What I think:
- stratified sampling by ratio classes, plane decompositions, base angles and projection seeds;
- for each combination I consider family-count, projected edge count and a simple resonance score relative to the target grid.
Formulas/reasoning:
- this is not a complete search and not a proof;
- this is the law of large numbers in working form: first we look at the distribution by main classes of combinations and look for where resonance generally occurs.
Intermediate results:
- total samples: `{total_samples}`
- family-count histogram: `{dict(sorted(family_hist.items()))}`
- overall target hits: `{overall_target_hits}`
- best overall family/line/score: `{best_overall['absolute_family_count']}` / `{best_overall['projected_edge_count']}` / `{best_overall['resonance_score']}`
What does it mean:
- branch `06` is no longer discarded blindly;
- now you can see the distribution by class and you can decide whether there are real resonance zones for deeper digging.
Complexity:
- average, but controlled.
Next step:
- go to analysis: which ratio/plane classes are really the best and whether it makes sense to locally narrow the search around them.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "A stratified search over the main double-rotation classes has been completed. The branch is no longer parked by complexity alone; it now has an empirical distribution over the major parameter classes.\n\n"
        "## Best Witness\n\n"
        "- `data/search_stratified_sampling_report.json`\n"
        "- `data/search_stratified_sampling_report.md`\n\n"
        "## Blocking Issues\n\n"
        "Need the class-level analysis to decide whether any resonance zone is strong enough for local refinement.\n"
    )

    print(f"variant={variant_dir.name}")
    print("stage=search")
    print(f"report={report_path}")
    return 0


def run_analyze(variant_dir: Path) -> int:
    report_path = variant_dir / "data" / "search_stratified_sampling_report.json"
    report = json.loads(report_path.read_text())
    class_stats = report["class_stats"]
    ranked = sorted(class_stats.items(), key=lambda kv: kv[1]["best"]["resonance_score"])
    top5 = ranked[:5]
    top_ratio_stats: dict[str, dict[str, float]] = {}
    for key, stats in class_stats.items():
        ratio = key.split("|")[0].split("=")[1]
        slot = top_ratio_stats.setdefault(ratio, {"count": 0, "target_hits": 0, "best_score": None})
        slot["count"] += stats["count"]
        slot["target_hits"] += stats["target_hits"]
        best_score = stats["best"]["resonance_score"]
        if slot["best_score"] is None or best_score < slot["best_score"]:
            slot["best_score"] = best_score

    analysis = {
        "overall_target_hits": report["overall_target_hits"],
        "family_count_histogram": report["family_count_histogram"],
        "top5_classes": [{"class": key, **stats} for key, stats in top5],
        "ratio_summary": top_ratio_stats,
        "best_overall": report["best_overall"],
    }

    out_json = variant_dir / "data" / "analyze_stratified_classes.json"
    out_md = variant_dir / "data" / "analyze_stratified_classes.md"
    out_json.write_text(json.dumps(analysis, indent=2, ensure_ascii=True))
    ratio_lines = [f"- `{ratio}` -> target_hits=`{stats['target_hits']}`, best_score=`{stats['best_score']}`" for ratio, stats in sorted(top_ratio_stats.items())]
    class_lines = [f"- `{item['class']}` -> best family=`{item['best']['absolute_family_count']}`, best score=`{item['best']['resonance_score']}`" for item in analysis['top5_classes']]
    out_md.write_text(
        f"""# Double Rotation Analysis

- overall target hits: `{analysis['overall_target_hits']}`
- family-count histogram: `{analysis['family_count_histogram']}`
- best overall: `{analysis['best_overall']}`

## Ratio Summary
{chr(10).join(ratio_lines)}

## Top 5 Classes
{chr(10).join(class_lines)}
"""
    )

    log_path = variant_dir / "log.md"
    log = log_path.read_text().rstrip() + f"""

## {now_string()} — analyze-stratified-classes
Goal: to analyze the distribution by class-level sampling and understand whether double rotation has real resonance zones.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage analyze`
Artifacts:
- `data/analyze_stratified_classes.json`
- `data/analyze_stratified_classes.md`
What I think:
- top classes by resonance score;
- summary by ratio classes;
- overall target hits by family-count.\nFormulas / reasoning:
- if at least some ratio/plane classes are systemically better, it makes sense to refine the branch locally;
- if the distribution is flat and there are no hits, the branch is weakened, but according to the data, and not due to fear of 10 million combinations.
Intermediate results:
- overall target hits: `{analysis['overall_target_hits']}`
- best overall family/score: `{analysis['best_overall']['absolute_family_count']}` / `{analysis['best_overall']['resonance_score']}`
- ratio summary: `{top_ratio_stats}`
What does it mean:
- branch `06` now passed an honest statistical screen;
- using this data, you can already decide whether it is parked again, or whether it has a specific zone for local deepening.
Complexity:
- low.
Next step:
- if there is a target hits or an explicit leader class, narrow the search locally around it; otherwise, return the branch to parked, but with real distributions in hand.
"""
    log_path.write_text(log)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "The double-rotation branch now has a real class-level statistical screen instead of a coarse complexity rejection. We have empirical distributions over ratio and plane classes, and can decide next steps from data.\n\n"
        "## Best Witness\n\n"
        "- `data/search_stratified_sampling_report.json`\n"
        "- `data/analyze_stratified_classes.json`\n\n"
        "## Blocking Issues\n\n"
        "Need to inspect whether the top classes show real resonance or only weak near-misses.\n"
    )

    print(f"variant={variant_dir.name}")
    print("stage=analyze")
    print(f"report={out_json}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["baseline", "prune", "search", "analyze", "finalize"], default="baseline")
    args = parser.parse_args()
    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == "baseline":
        return run_baseline(variant_dir)
    if args.stage == "search":
        return run_search(variant_dir)
    if args.stage == "analyze":
        return run_analyze(variant_dir)
    if args.stage == "prune":
        return run_search(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print("TODO: implement hypothesis-specific workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
