#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_rust_persistent, shutdown_rust_kernel_server
from research.common.meta_search import now_string

GA_PATH = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
RULE_PATH = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "deterministic_a2_subweb_rule.json"
STATE_PATH = ROOT / "research" / "async_state" / "branch05_ridge" / "ga_aco_state.json"
SUMMARY_PATH = ROOT / "research" / "async_state" / "branch05_ridge" / "ga_aco_summary.md"

OUT_JSON = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "witness_layer_v2_package.json"
OUT_MD = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "witness_layer_v2_package.md"

CANONICAL_COUNTS = [1, 1, 1, 1, 2]
SUBSETS = ["02", "12", "13", "23"]
PROJECTION_BATCH = 12288
ROBUSTNESS_SEEDS = [971001, 971002, 971003]
MIN_LIVE_EVAL_COUNT = 20
NON_INFERIOR_MARGIN = -0.005


@dataclass
class CandidateSpec:
    subset_key: str
    selections: dict[str, list[int]]
    template_key: str = "A2_orbit_replacement"

    @property
    def axis_size(self) -> int:
        return len(self.subset_key)

    @property
    def bucket_counts(self) -> dict[str, int]:
        return {bucket: len(self.selections[bucket]) for bucket in ("2", "1", "0")}

    @property
    def total_cell_count(self) -> int:
        return sum(self.bucket_counts.values())


def load_ga_module():
    spec = importlib.util.spec_from_file_location("ga05_finalize_witness_v2", GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ga05_finalize_witness_v2"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def normalize_selections(selections: dict[str, list[int]]) -> dict[str, list[int]]:
    return {
        "2": sorted(int(x) for x in selections["2"]),
        "1": sorted(int(x) for x in selections["1"]),
        "0": sorted(int(x) for x in selections["0"]),
    }


def to_candidate_dict(spec: CandidateSpec) -> dict:
    return {
        "template_key": spec.template_key,
        "axis_subset_key": spec.subset_key,
        "axis_size": spec.axis_size,
        "total_cell_count": spec.total_cell_count,
        "bucket_counts": spec.bucket_counts,
        "selections": spec.selections,
    }


def transform_vec(vec: np.ndarray, perm: list[int], signs: list[int]) -> np.ndarray:
    return np.array([float(signs[i]) * float(vec[perm[i]]) for i in range(4)], dtype=float)


def line_diff(base: dict[str, list[int]], other: dict[str, list[int]]) -> dict[str, dict[str, list[int]]]:
    out: dict[str, dict[str, list[int]]] = {}
    for bucket in ("2", "1", "0"):
        a = set(base[bucket])
        b = set(other[bucket])
        out[bucket] = {
            "extra": sorted(b - a),
            "missing": sorted(a - b),
        }
    return out


def eval_candidate(module, spec: CandidateSpec, seed: int) -> dict:
    result = evaluate_vectors_rust_persistent(
        module.selected_vectors(to_candidate_dict(spec)),
        projection_batch=PROJECTION_BATCH,
        seed=seed,
    )
    result["preserves_canonical_counts"] = result["best_counts"] == CANONICAL_COUNTS
    return result


def aggregate_metrics(rows: list[dict]) -> dict:
    family5 = [float(row["family5_rate"]) for row in rows]
    exact = [float(row["exact_rate"]) for row in rows]
    profile = [float(row["mean_profile_score"]) for row in rows]
    return {
        "mean_family5_rate": float(statistics.fmean(family5)),
        "std_family5_rate": float(statistics.pstdev(family5)) if len(family5) > 1 else 0.0,
        "mean_exact_rate": float(statistics.fmean(exact)),
        "mean_profile_score": float(statistics.fmean(profile)),
        "canonical_all_seeds": bool(all(bool(row["preserves_canonical_counts"]) for row in rows)),
    }


def evaluate_multi_seed(module, spec: CandidateSpec) -> dict:
    by_seed = []
    for seed in ROBUSTNESS_SEEDS:
        by_seed.append({"seed": seed, "metrics": eval_candidate(module, spec, seed=seed)})
    agg = aggregate_metrics([row["metrics"] for row in by_seed])
    return {
        "candidate": to_candidate_dict(spec),
        "projection_batch": PROJECTION_BATCH,
        "seeds": ROBUSTNESS_SEEDS,
        "by_seed": by_seed,
        "aggregate": agg,
    }


def parse_updated(summary_text: str) -> str:
    for line in summary_text.splitlines():
        prefix = "- updated: `"
        if line.startswith(prefix) and line.endswith("`"):
            return line[len(prefix) : -1]
    return "n/a"


def best_live_winners_by_subset(state: dict) -> dict[str, dict]:
    winners: dict[str, dict] = {}
    for stats in state.get("root_branch_stats", {}).values():
        eval_count = int(stats.get("eval_count", 0))
        best = stats.get("best")
        if eval_count < MIN_LIVE_EVAL_COUNT or not best:
            continue
        subset_key = str(stats.get("axis_subset_key", ""))
        if subset_key not in SUBSETS:
            continue
        if best.get("best_counts") != CANONICAL_COUNTS:
            continue
        run_family5 = float(stats.get("family5_sum", 0.0)) / max(1, eval_count)
        row = {
            "root_branch_key": f"{stats['template_key']}@{subset_key}",
            "eval_count": eval_count,
            "running_family5_rate": run_family5,
            "candidate": {
                "template_key": stats["template_key"],
                "axis_subset_key": subset_key,
                "axis_size": len(subset_key),
                "total_cell_count": int(best["total_cell_count"]),
                "bucket_counts": {k: int(v) for k, v in best["bucket_counts"].items()},
                "selections": normalize_selections(best["selections"]),
            },
        }
        prev = winners.get(subset_key)
        if prev is None or row["running_family5_rate"] > prev["running_family5_rate"]:
            winners[subset_key] = row
    return winners


def main() -> int:
    module = load_ga_module()
    rule = json.loads(RULE_PATH.read_text())
    state = json.loads(STATE_PATH.read_text())
    summary_text = SUMMARY_PATH.read_text()
    captured_at = now_string("%Y-%m-%d %H:%M:%S")

    line_map = {module.root_line_key(vec.copy()): idx for idx, vec in enumerate(module.CELL_VECS)}

    core_by_subset: dict[str, CandidateSpec] = {}
    for subset_key in SUBSETS:
        if subset_key == "02":
            sel = rule["canonical_templates"]["A2_B2-0_B1-3_B0-1"]["selections"]
        else:
            sel = rule["orbit_transfers"][subset_key]["templates"]["A2_B2-0_B1-3_B0-1"]["mapped_selections"]
        core_by_subset[subset_key] = CandidateSpec(subset_key=subset_key, selections=normalize_selections(sel), template_key="A2_core")

    core_eval = {subset_key: evaluate_multi_seed(module, spec) for subset_key, spec in core_by_subset.items()}

    pools_02 = module.SUBSET_BUCKETS["02"]
    base_core_02 = core_by_subset["02"]

    replacement_families = []
    for bucket in ("2", "1", "0"):
        present = list(base_core_02.selections[bucket])
        missing = [int(x) for x in pools_02[bucket] if int(x) not in set(present)]
        for out_line in present:
            for in_line in missing:
                moved = {k: list(v) for k, v in base_core_02.selections.items()}
                moved[bucket] = [x for x in moved[bucket] if x != out_line] + [in_line]
                moved = normalize_selections(moved)

                per_subset: dict[str, dict] = {}
                subset_specs: dict[str, CandidateSpec] = {}
                deltas = []
                canonical_all = True
                min_family5 = 1.0
                for subset_key in SUBSETS:
                    if subset_key == "02":
                        spec = CandidateSpec(subset_key="02", selections=moved, template_key="A2_repl")
                    else:
                        transfer = rule["orbit_transfers"][subset_key]
                        perm = transfer["permutation"]
                        signs = transfer["signs"]
                        mapped = {"2": [], "1": [], "0": []}
                        for b in ("2", "1", "0"):
                            for line_id in moved[b]:
                                vec = module.CELL_VECS[line_id]
                                mapped_key = module.root_line_key(transform_vec(vec, perm, signs))
                                mapped[b].append(line_map[mapped_key])
                        spec = CandidateSpec(subset_key=subset_key, selections=normalize_selections(mapped), template_key="A2_repl")

                    subset_specs[subset_key] = spec
                    eval_block = evaluate_multi_seed(module, spec)
                    per_subset[subset_key] = eval_block
                    agg = eval_block["aggregate"]
                    core_agg = core_eval[subset_key]["aggregate"]
                    delta = float(agg["mean_family5_rate"] - core_agg["mean_family5_rate"])
                    deltas.append(delta)
                    min_family5 = min(min_family5, float(agg["mean_family5_rate"]))
                    canonical_all = canonical_all and bool(agg["canonical_all_seeds"])

                replacement_families.append(
                    {
                        "move": {"bucket": bucket, "out_line": out_line, "in_line": in_line},
                        "canonical_all_subsets": canonical_all,
                        "avg_delta_vs_core": float(statistics.fmean(deltas)),
                        "avg_family5_rate": float(statistics.fmean([per_subset[s]["aggregate"]["mean_family5_rate"] for s in SUBSETS])),
                        "min_family5_rate": float(min_family5),
                        "per_subset": per_subset,
                        "subset_specs": {s: to_candidate_dict(spec) for s, spec in subset_specs.items()},
                    }
                )

    replacement_families.sort(
        key=lambda row: (
            int(row["canonical_all_subsets"]),
            row["avg_delta_vs_core"],
            row["avg_family5_rate"],
            row["min_family5_rate"],
        ),
        reverse=True,
    )

    best_family = replacement_families[0]

    live_winners = best_live_winners_by_subset(state)
    comparison_by_subset = {}
    subset_non_inferior_flags = {}
    for subset_key in SUBSETS:
        replacement_eval = best_family["per_subset"][subset_key]
        replacement_agg = replacement_eval["aggregate"]

        winner = live_winners.get(subset_key)
        if winner is None:
            comparison_by_subset[subset_key] = {
                "status": "missing_live_winner",
                "replacement": replacement_eval,
            }
            subset_non_inferior_flags[subset_key] = False
            continue

        winner_spec = CandidateSpec(
            subset_key=subset_key,
            selections=winner["candidate"]["selections"],
            template_key=winner["candidate"]["template_key"],
        )
        winner_eval = evaluate_multi_seed(module, winner_spec)
        winner_agg = winner_eval["aggregate"]

        delta_family5 = float(replacement_agg["mean_family5_rate"] - winner_agg["mean_family5_rate"])
        delta_profile = float(replacement_agg["mean_profile_score"] - winner_agg["mean_profile_score"])
        non_inferior = bool(
            replacement_agg["canonical_all_seeds"]
            and winner_agg["canonical_all_seeds"]
            and delta_family5 >= NON_INFERIOR_MARGIN
        )
        subset_non_inferior_flags[subset_key] = non_inferior

        comparison_by_subset[subset_key] = {
            "status": "ok",
            "live_winner": {
                "root_branch_key": winner["root_branch_key"],
                "eval_count": winner["eval_count"],
                "running_family5_rate": winner["running_family5_rate"],
                "candidate": winner["candidate"],
                "evaluation": winner_eval,
            },
            "replacement": replacement_eval,
            "delta": {
                "family5_rate": delta_family5,
                "mean_profile_score": delta_profile,
            },
            "non_inferior": non_inferior,
        }

    add_back_negatives = {}
    mapped_out_line_by_subset = {}
    best_move = best_family["move"]

    for subset_key in SUBSETS:
        repl_candidate = best_family["per_subset"][subset_key]["candidate"]["selections"]
        transfer = rule["orbit_transfers"].get(subset_key)
        out_line = best_move["out_line"]
        if subset_key == "02":
            mapped_out_line = out_line
        else:
            assert transfer is not None
            perm = transfer["permutation"]
            signs = transfer["signs"]
            vec = module.CELL_VECS[out_line]
            mapped_key = module.root_line_key(transform_vec(vec, perm, signs))
            mapped_out_line = line_map[mapped_key]
        mapped_out_line_by_subset[subset_key] = int(mapped_out_line)

        augmented = {k: list(v) for k, v in repl_candidate.items()}
        if mapped_out_line not in augmented[best_move["bucket"]]:
            augmented[best_move["bucket"]].append(mapped_out_line)
        aug_spec = CandidateSpec(subset_key=subset_key, selections=normalize_selections(augmented), template_key="ADD_BACK_REMOVED")
        add_back_negatives[subset_key] = evaluate_multi_seed(module, aug_spec)

    nearby_dominated = []
    for row in replacement_families[1:4]:
        nearby_dominated.append(
            {
                "move": row["move"],
                "canonical_all_subsets": row["canonical_all_subsets"],
                "avg_delta_vs_core": row["avg_delta_vs_core"],
                "avg_family5_rate": row["avg_family5_rate"],
                "delta_vs_best_family5": float(row["avg_family5_rate"] - best_family["avg_family5_rate"]),
            }
        )

    overlay_diff = {}
    for subset_key in SUBSETS:
        core_sel = core_eval[subset_key]["candidate"]["selections"]
        repl_sel = best_family["per_subset"][subset_key]["candidate"]["selections"]
        overlay_diff[subset_key] = line_diff(core_sel, repl_sel)

    subset_deltas = [
        float(comparison_by_subset[s]["delta"]["family5_rate"])
        for s in SUBSETS
        if comparison_by_subset[s].get("status") == "ok"
    ]
    aggregate_delta = float(statistics.fmean(subset_deltas)) if subset_deltas else None

    non_inferior_vs_live = bool(
        all(subset_non_inferior_flags.get(s, False) for s in SUBSETS)
        and aggregate_delta is not None
        and aggregate_delta >= NON_INFERIOR_MARGIN
    )

    payload = {
        "captured_at": captured_at,
        "sources": {
            "rule": str(RULE_PATH),
            "ga_aco_state": str(STATE_PATH),
            "ga_aco_summary": str(SUMMARY_PATH),
            "ga_aco_summary_updated": parse_updated(summary_text),
        },
        "evaluation_config": {
            "projection_batch": PROJECTION_BATCH,
            "seeds": ROBUSTNESS_SEEDS,
            "canonical_counts": CANONICAL_COUNTS,
            "non_inferior_margin_family5": NON_INFERIOR_MARGIN,
            "min_live_eval_count": MIN_LIVE_EVAL_COUNT,
        },
        "core_baseline": core_eval,
        "replacement_search": {
            "family_count": len(replacement_families),
            "best_family": best_family,
            "top_families": replacement_families[:8],
        },
        "witness_layer_v2": {
            "rule": {
                "base_template": "A2_B2-0_B1-3_B0-1",
                "base_subset": "02",
                "best_move": best_move,
                "mapped_out_line_by_subset": mapped_out_line_by_subset,
            },
            "overlay_diff_vs_core": overlay_diff,
            "nearby_negative_certificates": {
                "add_back_removed_line": add_back_negatives,
                "dominated_neighbor_moves": nearby_dominated,
            },
        },
        "comparison_vs_live_winners": comparison_by_subset,
        "decision_signals": {
            "canonical_all_subsets_all_seeds": bool(best_family["canonical_all_subsets"]),
            "non_inferior_vs_live_winners": non_inferior_vs_live,
            "aggregate_family5_delta_vs_live": aggregate_delta,
            "subset_non_inferior_flags": subset_non_inferior_flags,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    lines = [
        "# Witness Layer v2 Package",
        "",
        f"- captured at: `{captured_at}`",
        f"- projection batch: `{PROJECTION_BATCH}`",
        f"- seeds: `{ROBUSTNESS_SEEDS}`",
        f"- canonical counts target: `{CANONICAL_COUNTS}`",
        "",
        "## Best Orbit-Consistent Family",
        "",
        f"- base move on `02`: `replace {best_move['bucket']}:{best_move['out_line']}->{best_move['in_line']}`",
        f"- canonical on all subsets/seeds: `{best_family['canonical_all_subsets']}`",
        f"- avg family5: `{best_family['avg_family5_rate']:.6f}`",
        f"- min family5: `{best_family['min_family5_rate']:.6f}`",
        f"- avg delta vs core: `{best_family['avg_delta_vs_core']:.6f}`",
        "",
        "## Overlay/Diff vs Core",
        "",
    ]
    for subset_key in SUBSETS:
        diff = overlay_diff[subset_key]
        agg = best_family["per_subset"][subset_key]["aggregate"]
        lines.append(
            f"- `{subset_key}` diff=`{diff}`; family5=`{agg['mean_family5_rate']:.6f}`; canonical_all_seeds=`{agg['canonical_all_seeds']}`"
        )

    lines.extend(["", "## Nearby Negative Certificates", "", "### Add-Back Removed Line", ""])
    for subset_key in SUBSETS:
        agg = add_back_negatives[subset_key]["aggregate"]
        lines.append(
            f"- `{subset_key}` add-back -> family5=`{agg['mean_family5_rate']:.6f}`, canonical_all_seeds=`{agg['canonical_all_seeds']}`, best_counts(one seed)=`{add_back_negatives[subset_key]['by_seed'][0]['metrics']['best_counts']}`"
        )

    lines.extend(["", "### Dominated Neighbor Moves", ""])
    for row in nearby_dominated:
        mv = row["move"]
        lines.append(
            f"- `replace {mv['bucket']}:{mv['out_line']}->{mv['in_line']}` -> avg_family5=`{row['avg_family5_rate']:.6f}`, avg_delta_vs_core=`{row['avg_delta_vs_core']:.6f}`, delta_vs_best=`{row['delta_vs_best_family5']:.6f}`"
        )

    lines.extend(["", "## Comparison vs Live Winners", ""])
    for subset_key in SUBSETS:
        row = comparison_by_subset[subset_key]
        if row["status"] != "ok":
            lines.append(f"- `{subset_key}` -> no live winner passing filters")
            continue
        rep = row["replacement"]["aggregate"]
        live = row["live_winner"]["evaluation"]["aggregate"]
        lines.append(
            f"- `{subset_key}` live=`{row['live_winner']['root_branch_key']}`; replacement family5=`{rep['mean_family5_rate']:.6f}` vs live=`{live['mean_family5_rate']:.6f}`; delta=`{row['delta']['family5_rate']:.6f}`; non_inferior=`{row['non_inferior']}`"
        )

    lines.extend(
        [
            "",
            "## Decision Signals",
            "",
            f"- canonical all subsets/seeds: `{payload['decision_signals']['canonical_all_subsets_all_seeds']}`",
            f"- non-inferior vs live winners: `{payload['decision_signals']['non_inferior_vs_live_winners']}`",
            f"- aggregate family5 delta vs live: `{payload['decision_signals']['aggregate_family5_delta_vs_live']}`",
            f"- subset flags: `{payload['decision_signals']['subset_non_inferior_flags']}`",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n")
    shutdown_rust_kernel_server()
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
