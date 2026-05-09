#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_rust_persistent, shutdown_rust_kernel_server
from research.common.meta_search import now_string

GA_PATH = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
STATE_PATH = ROOT / "research" / "async_state" / "branch05_ridge" / "ga_aco_state.json"
SUMMARY_PATH = ROOT / "research" / "async_state" / "branch05_ridge" / "ga_aco_summary.md"
RULE_PATH = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "deterministic_a2_subweb_rule.json"
OUT_SNAPSHOT_JSON = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "ga_aco_frontier_snapshot.json"
OUT_SNAPSHOT_MD = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "ga_aco_frontier_snapshot.md"
OUT_SCAN_JSON = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "multi_trunk_witness_scan.json"
OUT_SCAN_MD = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "multi_trunk_witness_scan.md"

CANONICAL_COUNTS = [1, 1, 1, 1, 2]
PROJECTION_BATCH = 4096
NEGATIVE_BATCH = 2048
MIN_SHORTLIST_EVAL_COUNT = 2000
SHORTLIST_LIMIT = 8
TARGET_SUBSETS = ["02", "12", "13", "23"]


@dataclass
class CandidateSpec:
    template_key: str
    axis_subset_key: str
    selections: dict[str, list[int]]
    source: str

    @property
    def bucket_counts(self) -> dict[str, int]:
        return {bucket: len(self.selections[bucket]) for bucket in ("2", "1", "0")}

    @property
    def total_cell_count(self) -> int:
        return sum(self.bucket_counts.values())

    @property
    def axis_size(self) -> int:
        return len(self.axis_subset_key)


def load_ga_module():
    spec = importlib.util.spec_from_file_location("ga05_multi_trunk_scan", GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ga05_multi_trunk_scan"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_summary_progress(summary_text: str) -> dict[str, str]:
    keys = [
        "updated",
        "status",
        "kernel backend",
        "generation",
        "generation progress",
        "candidate evaluations",
        "candidate progress",
        "projection evaluations",
        "templates touched",
        "root branches touched",
        "root-branch coverage",
        "elapsed wall seconds",
        "generations/sec",
        "ETA",
    ]
    parsed: dict[str, str] = {}
    for key in keys:
        m = re.search(rf"- {re.escape(key)}: `([^`]*)`", summary_text)
        if m:
            parsed[key] = m.group(1)
    return parsed


def normalize_selections(selections: dict[str, list[int]]) -> dict[str, list[int]]:
    return {
        "2": sorted(int(x) for x in selections["2"]),
        "1": sorted(int(x) for x in selections["1"]),
        "0": sorted(int(x) for x in selections["0"]),
    }


def eval_running_rates(stats: dict) -> tuple[float, float]:
    eval_count = max(1, int(stats.get("eval_count", 0)))
    return float(stats.get("family5_sum", 0.0)) / eval_count, float(stats.get("exact_sum", 0.0)) / eval_count


def candidate_from_spec(spec: CandidateSpec) -> dict:
    return {
        "template_key": spec.template_key,
        "axis_subset_key": spec.axis_subset_key,
        "axis_size": spec.axis_size,
        "total_cell_count": spec.total_cell_count,
        "bucket_counts": spec.bucket_counts,
        "selections": spec.selections,
    }


def evaluate(module, spec: CandidateSpec, seed: int, projection_batch: int) -> dict:
    metrics = evaluate_vectors_rust_persistent(
        module.selected_vectors(candidate_from_spec(spec)),
        projection_batch=projection_batch,
        seed=seed,
    )
    metrics["preserves_canonical_counts"] = metrics["best_counts"] == CANONICAL_COUNTS
    return metrics


def union_specs(name: str, axis_subset_key: str, parts: list[CandidateSpec]) -> CandidateSpec:
    union = {"2": set(), "1": set(), "0": set()}
    for part in parts:
        for bucket in ("2", "1", "0"):
            union[bucket].update(part.selections[bucket])
    return CandidateSpec(
        template_key=name,
        axis_subset_key=axis_subset_key,
        selections={bucket: sorted(union[bucket]) for bucket in ("2", "1", "0")},
        source="+".join(part.template_key for part in parts),
    )


def line_diff(base: CandidateSpec, other: CandidateSpec) -> dict[str, dict[str, list[int]]]:
    diff: dict[str, dict[str, list[int]]] = {}
    for bucket in ("2", "1", "0"):
        base_set = set(base.selections[bucket])
        other_set = set(other.selections[bucket])
        diff[bucket] = {
            "extra": sorted(other_set - base_set),
            "missing": sorted(base_set - other_set),
        }
    return diff


def main() -> int:
    module = load_ga_module()
    state = json.loads(STATE_PATH.read_text())
    summary_text = SUMMARY_PATH.read_text()
    rule = json.loads(RULE_PATH.read_text())

    snapshot_ts = now_string("%Y-%m-%d %H:%M:%S")
    summary_meta = parse_summary_progress(summary_text)

    root_branch_stats: dict = state["root_branch_stats"]
    shortlist = []
    for key, stats in sorted(root_branch_stats.items()):
        best = stats.get("best")
        if best is None:
            continue
        if not str(stats.get("template_key", "")).startswith("A2_"):
            continue
        if best.get("best_counts") != CANONICAL_COUNTS:
            continue
        if int(stats.get("eval_count", 0)) < MIN_SHORTLIST_EVAL_COUNT:
            continue
        running_family5, running_exact = eval_running_rates(stats)
        shortlist.append(
            {
                "root_branch_key": key,
                "template_key": stats["template_key"],
                "axis_subset_key": stats["axis_subset_key"],
                "eval_count": int(stats["eval_count"]),
                "running_family5_rate": running_family5,
                "running_exact_rate": running_exact,
                "best_family5_rate": float(best["family5_rate"]),
                "best_exact_rate": float(best["exact_rate"]),
                "best_counts": best["best_counts"],
                "best_selections": best["selections"],
            }
        )
    shortlist.sort(key=lambda row: (-row["running_family5_rate"], -row["eval_count"], row["root_branch_key"]))
    shortlist = shortlist[:SHORTLIST_LIMIT]

    snapshot_payload = {
        "captured_at": snapshot_ts,
        "summary_meta": summary_meta,
        "best_overall": state.get("best_overall"),
        "best_exact": state.get("best_exact"),
        "shortlist_filter": {
            "template_prefix": "A2_",
            "min_eval_count": MIN_SHORTLIST_EVAL_COUNT,
            "best_counts_required": CANONICAL_COUNTS,
            "limit": SHORTLIST_LIMIT,
        },
        "shortlist": shortlist,
    }
    OUT_SNAPSHOT_JSON.write_text(json.dumps(snapshot_payload, indent=2, ensure_ascii=True))

    md_lines = [
        "# GA+ACO Frontier Snapshot",
        "",
        f"- captured at: `{snapshot_ts}`",
        f"- generation: `{summary_meta.get('generation', 'n/a')}`",
        f"- generation progress: `{summary_meta.get('generation progress', 'n/a')}`",
        f"- candidate evaluations: `{summary_meta.get('candidate evaluations', 'n/a')}`",
        f"- root-branch coverage: `{summary_meta.get('root-branch coverage', 'n/a')}`",
        f"- ETA: `{summary_meta.get('ETA', 'n/a')}`",
        "",
        "## Current Best Overall",
        "",
        f"- `{state.get('best_overall')}`",
        "",
        "## A2 Shortlist",
        "",
    ]
    for row in shortlist:
        md_lines.append(
            f"- `{row['root_branch_key']}`: evals=`{row['eval_count']}`, run_family5=`{row['running_family5_rate']:.6f}`, best_family5=`{row['best_family5_rate']:.6f}`, selections=`{row['best_selections']}`"
        )
    OUT_SNAPSHOT_MD.write_text("\n".join(md_lines) + "\n")

    base_templates = [
        "A2_B2-0_B1-3_B0-1",
        "A2_B2-0_B1-4_B0-0",
        "A2_B2-0_B1-2_B0-2",
    ]
    subset_specs: dict[str, dict[str, CandidateSpec]] = {}
    for subset_key in TARGET_SUBSETS:
        subset_specs[subset_key] = {}
        for template_key in base_templates:
            if subset_key == "02":
                selections = rule["canonical_templates"][template_key]["selections"]
            else:
                selections = rule["orbit_transfers"][subset_key]["templates"][template_key]["mapped_selections"]
            subset_specs[subset_key][template_key] = CandidateSpec(
                template_key=template_key,
                axis_subset_key=subset_key,
                selections=normalize_selections(selections),
                source="rule",
            )

    config_parts = {
        "core_only": ["A2_B2-0_B1-3_B0-1"],
        "core_plus_b1": ["A2_B2-0_B1-3_B0-1", "A2_B2-0_B1-4_B0-0"],
        "core_plus_b0": ["A2_B2-0_B1-3_B0-1", "A2_B2-0_B1-2_B0-2"],
        "dual_outer": ["A2_B2-0_B1-4_B0-0", "A2_B2-0_B1-2_B0-2"],
        "triple_union": ["A2_B2-0_B1-3_B0-1", "A2_B2-0_B1-4_B0-0", "A2_B2-0_B1-2_B0-2"],
    }

    merge_rows = []
    seed = 910000
    for subset_key in TARGET_SUBSETS:
        base_spec = subset_specs[subset_key]["A2_B2-0_B1-3_B0-1"]
        for config_name, part_keys in config_parts.items():
            parts = [subset_specs[subset_key][part] for part in part_keys]
            merged = union_specs(config_name, subset_key, parts)
            metrics = evaluate(module, merged, seed=seed, projection_batch=PROJECTION_BATCH)
            seed += 1
            merge_rows.append(
                {
                    "subset_key": subset_key,
                    "config_name": config_name,
                    "part_templates": part_keys,
                    "candidate": candidate_from_spec(merged),
                    "metrics": metrics,
                    "line_diff_vs_core": line_diff(base_spec, merged),
                }
            )

    multi_rows = [row for row in merge_rows if row["config_name"] != "core_only"]
    best_multi = max(
        multi_rows,
        key=lambda row: (
            float(row["metrics"]["family5_rate"]),
            int(row["metrics"]["preserves_canonical_counts"]),
            -float(row["metrics"]["mean_profile_score"]),
        ),
    )

    best_spec_dict = best_multi["candidate"]
    best_spec = CandidateSpec(
        template_key=best_spec_dict["template_key"],
        axis_subset_key=best_spec_dict["axis_subset_key"],
        selections=normalize_selections(best_spec_dict["selections"]),
        source="best_multi",
    )
    base_for_best = subset_specs[best_spec.axis_subset_key]["A2_B2-0_B1-3_B0-1"]

    negative_neighbors = []
    for bucket in ("2", "1", "0"):
        base_set = set(base_for_best.selections[bucket])
        extra = [line_id for line_id in best_spec.selections[bucket] if line_id not in base_set]
        for line_id in extra:
            alt = {
                "2": list(best_spec.selections["2"]),
                "1": list(best_spec.selections["1"]),
                "0": list(best_spec.selections["0"]),
            }
            alt[bucket] = [x for x in alt[bucket] if x != line_id]
            alt_spec = CandidateSpec(
                template_key=f"ABLATE_EXTRA_{bucket}_{line_id}",
                axis_subset_key=best_spec.axis_subset_key,
                selections=normalize_selections(alt),
                source="negative_ablation",
            )
            metrics = evaluate(module, alt_spec, seed=seed, projection_batch=NEGATIVE_BATCH)
            seed += 1
            negative_neighbors.append(
                {
                    "name": alt_spec.template_key,
                    "candidate": candidate_from_spec(alt_spec),
                    "metrics": metrics,
                    "line_diff_vs_best_multi": line_diff(best_spec, alt_spec),
                }
            )

    scan_payload = {
        "captured_at": snapshot_ts,
        "projection_batch": PROJECTION_BATCH,
        "negative_batch": NEGATIVE_BATCH,
        "canonical_counts": CANONICAL_COUNTS,
        "target_subsets": TARGET_SUBSETS,
        "configs": config_parts,
        "merge_rows": merge_rows,
        "best_multi": best_multi,
        "negative_neighbors": negative_neighbors,
    }
    OUT_SCAN_JSON.write_text(json.dumps(scan_payload, indent=2, ensure_ascii=True))

    lines = [
        "# Multi-Trunk Witness Scan",
        "",
        f"- captured at: `{snapshot_ts}`",
        f"- projection batch: `{PROJECTION_BATCH}`",
        f"- canonical counts target: `{CANONICAL_COUNTS}`",
        "",
        "## Shortlist Context",
        "",
        f"- shortlist source: `{OUT_SNAPSHOT_JSON}`",
        f"- shortlist size: `{len(shortlist)}`",
        "",
        "## Merge Configs",
        "",
    ]
    for config_name, parts in config_parts.items():
        lines.append(f"- `{config_name}` -> `{parts}`")

    lines.extend(["", "## Evaluations", ""])
    for row in merge_rows:
        m = row["metrics"]
        lines.extend(
            [
                f"### `{row['subset_key']}:{row['config_name']}`",
                "",
                f"- selections: `{row['candidate']['selections']}`",
                f"- bucket counts: `{row['candidate']['bucket_counts']}`",
                f"- family5 rate: `{m['family5_rate']:.6f}`",
                f"- exact rate: `{m['exact_rate']:.6f}`",
                f"- best counts: `{m['best_counts']}`",
                f"- preserves canonical: `{m['preserves_canonical_counts']}`",
                f"- mean profile score: `{m['mean_profile_score']:.6f}`",
                f"- line diff vs core: `{row['line_diff_vs_core']}`",
                "",
            ]
        )

    bm = best_multi["metrics"]
    lines.extend(
        [
            "## Best Multi-Trunk Candidate",
            "",
            f"- id: `{best_multi['subset_key']}:{best_multi['config_name']}`",
            f"- candidate: `{best_multi['candidate']['selections']}`",
            f"- family5 rate: `{bm['family5_rate']:.6f}`",
            f"- exact rate: `{bm['exact_rate']:.6f}`",
            f"- best counts: `{bm['best_counts']}`",
            f"- preserves canonical: `{bm['preserves_canonical_counts']}`",
            "",
            "## Minimal Negative Neighbors",
            "",
        ]
    )
    if not negative_neighbors:
        lines.append("- no extra lines to ablate in best multi candidate")
    else:
        for row in negative_neighbors:
            m = row["metrics"]
            lines.append(
                f"- `{row['name']}` -> family5=`{m['family5_rate']:.6f}`, exact=`{m['exact_rate']:.6f}`, best_counts=`{m['best_counts']}`, preserves_canonical=`{m['preserves_canonical_counts']}`"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "- this scan checks whether unioning orbit-stable A2 trunks can improve coverage without destroying canonical profile behavior;",
            "- line-level diffs and neighbor ablations provide a compact negative certificate around the best multi-trunk attempt.",
        ]
    )
    OUT_SCAN_MD.write_text("\n".join(lines) + "\n")
    shutdown_rust_kernel_server()
    print(OUT_SNAPSHOT_JSON)
    print(OUT_SNAPSHOT_MD)
    print(OUT_SCAN_JSON)
    print(OUT_SCAN_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
