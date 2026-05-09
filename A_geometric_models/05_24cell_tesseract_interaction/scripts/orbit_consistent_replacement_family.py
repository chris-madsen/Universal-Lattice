#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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
OUT_JSON = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "orbit_consistent_replacement_family.json"
OUT_MD = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "orbit_consistent_replacement_family.md"

CANONICAL_COUNTS = [1, 1, 1, 1, 2]
SUBSETS = ["02", "12", "13", "23"]
PROJECTION_BATCH = 3072


@dataclass
class CandidateSpec:
    subset_key: str
    selections: dict[str, list[int]]

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
    spec = importlib.util.spec_from_file_location("ga05_orbit_consistent_repl", GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ga05_orbit_consistent_repl"] = module
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
        "template_key": "A2_orbit_replacement",
        "axis_subset_key": spec.subset_key,
        "axis_size": spec.axis_size,
        "total_cell_count": spec.total_cell_count,
        "bucket_counts": spec.bucket_counts,
        "selections": spec.selections,
    }


def evaluate(module, spec: CandidateSpec, seed: int) -> dict:
    metrics = evaluate_vectors_rust_persistent(
        module.selected_vectors(to_candidate_dict(spec)),
        projection_batch=PROJECTION_BATCH,
        seed=seed,
    )
    metrics["preserves_canonical_counts"] = metrics["best_counts"] == CANONICAL_COUNTS
    return metrics


def transform_vec(vec: np.ndarray, perm: list[int], signs: list[int]) -> np.ndarray:
    return np.array([float(signs[i]) * float(vec[perm[i]]) for i in range(4)], dtype=float)


def main() -> int:
    module = load_ga_module()
    rule = json.loads(RULE_PATH.read_text())
    captured_at = now_string("%Y-%m-%d %H:%M:%S")

    line_map = {module.root_line_key(vec.copy()): idx for idx, vec in enumerate(module.CELL_VECS)}

    core_by_subset: dict[str, CandidateSpec] = {}
    for subset_key in SUBSETS:
        if subset_key == "02":
            sel = rule["canonical_templates"]["A2_B2-0_B1-3_B0-1"]["selections"]
        else:
            sel = rule["orbit_transfers"][subset_key]["templates"]["A2_B2-0_B1-3_B0-1"]["mapped_selections"]
        core_by_subset[subset_key] = CandidateSpec(subset_key=subset_key, selections=normalize_selections(sel))

    seed = 930000
    core_metrics: dict[str, dict] = {}
    for subset_key in SUBSETS:
        core_metrics[subset_key] = evaluate(module, core_by_subset[subset_key], seed)
        seed += 1

    pools_02 = module.SUBSET_BUCKETS["02"]
    base_core = core_by_subset["02"]
    base_candidates = []
    for bucket in ("2", "1", "0"):
        present = list(base_core.selections[bucket])
        missing = [int(x) for x in pools_02[bucket] if int(x) not in set(present)]
        for out_line in present:
            for in_line in missing:
                cand_sel = {k: list(v) for k, v in base_core.selections.items()}
                cand_sel[bucket] = [x for x in cand_sel[bucket] if x != out_line]
                cand_sel[bucket].append(in_line)
                base_candidates.append(
                    {
                        "bucket": bucket,
                        "out_line": out_line,
                        "in_line": in_line,
                        "candidate_02": CandidateSpec(subset_key="02", selections=normalize_selections(cand_sel)),
                    }
                )

    families = []
    for idx, base in enumerate(base_candidates):
        per_subset = {}
        all_canonical = True
        family5_vals = []
        improvements = []
        for subset_key in SUBSETS:
            if subset_key == "02":
                spec = base["candidate_02"]
            else:
                transfer = rule["orbit_transfers"][subset_key]
                perm = transfer["permutation"]
                signs = transfer["signs"]
                mapped = {"2": [], "1": [], "0": []}
                for bucket in ("2", "1", "0"):
                    for line_id in base["candidate_02"].selections[bucket]:
                        vec = module.CELL_VECS[line_id]
                        mapped_key = module.root_line_key(transform_vec(vec, perm, signs))
                        mapped[bucket].append(line_map[mapped_key])
                spec = CandidateSpec(subset_key=subset_key, selections=normalize_selections(mapped))
            metrics = evaluate(module, spec, seed + idx * 17 + int(subset_key))
            per_subset[subset_key] = {"candidate": to_candidate_dict(spec), "metrics": metrics}
            all_canonical = all_canonical and bool(metrics["preserves_canonical_counts"])
            family5_vals.append(float(metrics["family5_rate"]))
            improvements.append(float(metrics["family5_rate"]) - float(core_metrics[subset_key]["family5_rate"]))

        families.append(
            {
                "base_move": {"bucket": base["bucket"], "out_line": base["out_line"], "in_line": base["in_line"]},
                "all_canonical": all_canonical,
                "avg_family5_rate": float(sum(family5_vals) / len(family5_vals)),
                "min_family5_rate": float(min(family5_vals)),
                "avg_improvement_vs_core": float(sum(improvements) / len(improvements)),
                "per_subset": per_subset,
            }
        )

    families_sorted = sorted(
        families,
        key=lambda row: (
            int(row["all_canonical"]),
            row["avg_family5_rate"],
            row["min_family5_rate"],
            row["avg_improvement_vs_core"],
        ),
        reverse=True,
    )
    best = families_sorted[0] if families_sorted else None

    payload = {
        "captured_at": captured_at,
        "projection_batch": PROJECTION_BATCH,
        "canonical_counts": CANONICAL_COUNTS,
        "core_metrics": core_metrics,
        "family_count": len(families),
        "best_family": best,
        "top_families": families_sorted[:12],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    lines = [
        "# Orbit-Consistent Replacement Family",
        "",
        f"- captured at: `{captured_at}`",
        f"- projection batch: `{PROJECTION_BATCH}`",
        f"- tested replacement families: `{len(families)}`",
        "",
        "## Core Baseline",
        "",
    ]
    for subset_key in SUBSETS:
        m = core_metrics[subset_key]
        lines.append(
            f"- `{subset_key}` core -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, canonical=`{m['preserves_canonical_counts']}`"
        )

    lines.extend(["", "## Best Family", ""])
    if best is None:
        lines.append("- no candidate families")
    else:
        mv = best["base_move"]
        lines.extend(
            [
                f"- base move on `02`: `replace {mv['bucket']}:{mv['out_line']}->{mv['in_line']}`",
                f"- all canonical: `{best['all_canonical']}`",
                f"- avg family5: `{best['avg_family5_rate']:.6f}`",
                f"- min family5: `{best['min_family5_rate']:.6f}`",
                f"- avg improvement vs core: `{best['avg_improvement_vs_core']:.6f}`",
                "",
            ]
        )
        for subset_key in SUBSETS:
            entry = best["per_subset"][subset_key]
            m = entry["metrics"]
            lines.append(
                f"- `{subset_key}` -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, canonical=`{m['preserves_canonical_counts']}`, selections=`{entry['candidate']['selections']}`"
            )

    lines.extend(["", "## Top Families", ""])
    for row in families_sorted[:12]:
        mv = row["base_move"]
        lines.append(
            f"- `replace {mv['bucket']}:{mv['out_line']}->{mv['in_line']}` -> canonical_all=`{row['all_canonical']}`, avg_family5=`{row['avg_family5_rate']:.6f}`, min_family5=`{row['min_family5_rate']:.6f}`, avg_delta=`{row['avg_improvement_vs_core']:.6f}`"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "- this converts per-subset gated replacements into one orbit-consistent rule family;",
            "- if canonical survives across all subsets with nonnegative aggregate delta, this is a constructive upgrade layer over the core.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")
    shutdown_rust_kernel_server()
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
