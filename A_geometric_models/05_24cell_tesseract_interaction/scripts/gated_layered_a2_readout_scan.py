#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_rust_persistent, shutdown_rust_kernel_server
from research.common.meta_search import now_string

GA_PATH = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
RULE_PATH = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "deterministic_a2_subweb_rule.json"
OUT_JSON = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "gated_layered_a2_readout_scan.json"
OUT_MD = ROOT / "research" / "A_geometric_models" / "05_24cell_tesseract_interaction" / "data" / "gated_layered_a2_readout_scan.md"

CANONICAL_COUNTS = [1, 1, 1, 1, 2]
TARGET_SUBSETS = ["02", "12", "13", "23"]
CORE_BATCH = 4096
MOVE_BATCH = 2048
DEPTH2_BATCH = 1024
GATE_FAMILY5_RATIO = 0.9


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

    def key(self) -> str:
        parts = [self.subset_key]
        for bucket in ("2", "1", "0"):
            parts.append(f"{bucket}:{','.join(str(x) for x in self.selections[bucket])}")
        return "|".join(parts)


def load_ga_module():
    spec = importlib.util.spec_from_file_location("ga05_gated_layered_scan", GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ga05_gated_layered_scan"] = module
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
        "template_key": "A2_gated_layered",
        "axis_subset_key": spec.subset_key,
        "axis_size": spec.axis_size,
        "total_cell_count": spec.total_cell_count,
        "bucket_counts": spec.bucket_counts,
        "selections": spec.selections,
    }


def evaluate(module, spec: CandidateSpec, seed: int, batch: int) -> dict:
    metrics = evaluate_vectors_rust_persistent(
        module.selected_vectors(to_candidate_dict(spec)),
        projection_batch=batch,
        seed=seed,
    )
    metrics["preserves_canonical_counts"] = metrics["best_counts"] == CANONICAL_COUNTS
    return metrics


def line_diff(base: CandidateSpec, other: CandidateSpec) -> dict[str, dict[str, list[int]]]:
    out: dict[str, dict[str, list[int]]] = {}
    for bucket in ("2", "1", "0"):
        b = set(base.selections[bucket])
        o = set(other.selections[bucket])
        out[bucket] = {"extra": sorted(o - b), "missing": sorted(b - o)}
    return out


def gate_pass(metrics: dict, core_metrics: dict) -> bool:
    if not metrics["preserves_canonical_counts"]:
        return False
    return float(metrics["family5_rate"]) >= float(core_metrics["family5_rate"]) * GATE_FAMILY5_RATIO


def apply_add(spec: CandidateSpec, bucket: str, line_id: int) -> CandidateSpec:
    nxt = {k: list(v) for k, v in spec.selections.items()}
    if line_id not in nxt[bucket]:
        nxt[bucket].append(line_id)
    return CandidateSpec(subset_key=spec.subset_key, selections=normalize_selections(nxt))


def apply_replace(spec: CandidateSpec, bucket: str, out_line: int, in_line: int) -> CandidateSpec:
    nxt = {k: list(v) for k, v in spec.selections.items()}
    nxt[bucket] = [x for x in nxt[bucket] if x != out_line]
    if in_line not in nxt[bucket]:
        nxt[bucket].append(in_line)
    return CandidateSpec(subset_key=spec.subset_key, selections=normalize_selections(nxt))


def main() -> int:
    module = load_ga_module()
    rule = json.loads(RULE_PATH.read_text())

    captured_at = now_string("%Y-%m-%d %H:%M:%S")
    seed = 920000
    subset_reports = []

    for subset_key in TARGET_SUBSETS:
        if subset_key == "02":
            core_sel = rule["canonical_templates"]["A2_B2-0_B1-3_B0-1"]["selections"]
        else:
            core_sel = rule["orbit_transfers"][subset_key]["templates"]["A2_B2-0_B1-3_B0-1"]["mapped_selections"]
        core = CandidateSpec(subset_key=subset_key, selections=normalize_selections(core_sel))
        core_metrics = evaluate(module, core, seed=seed, batch=CORE_BATCH)
        seed += 1

        add_moves = []
        replace_moves = []
        safe_depth1 = []
        seen_depth1 = {core.key()}
        subset_bucket_pool = module.SUBSET_BUCKETS[subset_key]

        for bucket in ("2", "1", "0"):
            pool = [int(x) for x in subset_bucket_pool[bucket]]
            present = set(core.selections[bucket])
            missing = [line_id for line_id in pool if line_id not in present]
            for line_id in missing:
                cand = apply_add(core, bucket, line_id)
                metrics = evaluate(module, cand, seed=seed, batch=MOVE_BATCH)
                seed += 1
                row = {
                    "move_type": "add",
                    "bucket": bucket,
                    "line_id": line_id,
                    "candidate": to_candidate_dict(cand),
                    "metrics": metrics,
                    "line_diff_vs_core": line_diff(core, cand),
                    "gate_pass": gate_pass(metrics, core_metrics),
                }
                add_moves.append(row)
                if row["gate_pass"] and cand.key() not in seen_depth1:
                    seen_depth1.add(cand.key())
                    safe_depth1.append({"move": row, "spec": cand, "metrics": metrics})

        for bucket in ("2", "1", "0"):
            pool = [int(x) for x in subset_bucket_pool[bucket]]
            present = list(core.selections[bucket])
            missing = [line_id for line_id in pool if line_id not in set(present)]
            for out_line in present:
                for in_line in missing:
                    cand = apply_replace(core, bucket, out_line, in_line)
                    metrics = evaluate(module, cand, seed=seed, batch=MOVE_BATCH)
                    seed += 1
                    row = {
                        "move_type": "replace",
                        "bucket": bucket,
                        "out_line": out_line,
                        "in_line": in_line,
                        "candidate": to_candidate_dict(cand),
                        "metrics": metrics,
                        "line_diff_vs_core": line_diff(core, cand),
                        "gate_pass": gate_pass(metrics, core_metrics),
                    }
                    replace_moves.append(row)
                    if row["gate_pass"] and cand.key() not in seen_depth1:
                        seen_depth1.add(cand.key())
                        safe_depth1.append({"move": row, "spec": cand, "metrics": metrics})

        safe_depth2 = []
        seen_depth2 = set()
        for d1 in safe_depth1:
            base = d1["spec"]
            for bucket in ("2", "1", "0"):
                pool = [int(x) for x in subset_bucket_pool[bucket]]
                present = set(base.selections[bucket])
                missing = [line_id for line_id in pool if line_id not in present]
                for line_id in missing:
                    cand = apply_add(base, bucket, line_id)
                    ck = cand.key()
                    if ck in seen_depth2:
                        continue
                    seen_depth2.add(ck)
                    metrics = evaluate(module, cand, seed=seed, batch=DEPTH2_BATCH)
                    seed += 1
                    row = {
                        "parent_move": d1["move"],
                        "move_type": "add",
                        "bucket": bucket,
                        "line_id": line_id,
                        "candidate": to_candidate_dict(cand),
                        "metrics": metrics,
                        "line_diff_vs_core": line_diff(core, cand),
                        "gate_pass": gate_pass(metrics, core_metrics),
                    }
                    if row["gate_pass"]:
                        safe_depth2.append(row)

        top_add = sorted(add_moves, key=lambda row: (-row["metrics"]["family5_rate"], row["bucket"], row["line_id"]))[:6]
        top_replace = sorted(
            replace_moves,
            key=lambda row: (-row["metrics"]["family5_rate"], row["bucket"], row["out_line"], row["in_line"]),
        )[:8]

        subset_reports.append(
            {
                "subset_key": subset_key,
                "core": {"candidate": to_candidate_dict(core), "metrics": core_metrics},
                "gate": {"family5_ratio_threshold": GATE_FAMILY5_RATIO},
                "counts": {
                    "add_moves_total": len(add_moves),
                    "replace_moves_total": len(replace_moves),
                    "safe_depth1_total": len(safe_depth1),
                    "safe_depth2_total": len(safe_depth2),
                },
                "top_add_moves": top_add,
                "top_replace_moves": top_replace,
                "safe_depth1": [
                    {
                        "move": row["move"],
                        "candidate": to_candidate_dict(row["spec"]),
                        "metrics": row["metrics"],
                        "line_diff_vs_core": line_diff(core, row["spec"]),
                    }
                    for row in sorted(safe_depth1, key=lambda r: (-r["metrics"]["family5_rate"], r["move"]["move_type"]))[:20]
                ],
                "safe_depth2": sorted(safe_depth2, key=lambda row: (-row["metrics"]["family5_rate"], row["bucket"]))[:20],
            }
        )

    payload = {
        "captured_at": captured_at,
        "canonical_counts": CANONICAL_COUNTS,
        "batches": {"core": CORE_BATCH, "move": MOVE_BATCH, "depth2": DEPTH2_BATCH},
        "gate": {"family5_ratio_threshold": GATE_FAMILY5_RATIO},
        "subsets": subset_reports,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    lines = [
        "# Gated Layered A2 Readout Scan",
        "",
        f"- captured at: `{captured_at}`",
        f"- canonical counts target: `{CANONICAL_COUNTS}`",
        f"- gate: preserve canonical + family5 >= `core * {GATE_FAMILY5_RATIO}`",
        "",
    ]

    for report in subset_reports:
        core_metrics = report["core"]["metrics"]
        lines.extend(
            [
                f"## Subset `{report['subset_key']}`",
                "",
                f"- core family5: `{core_metrics['family5_rate']:.6f}`",
                f"- core exact: `{core_metrics['exact_rate']:.6f}`",
                f"- core best counts: `{core_metrics['best_counts']}`",
                f"- add moves tested: `{report['counts']['add_moves_total']}`",
                f"- replace moves tested: `{report['counts']['replace_moves_total']}`",
                f"- safe depth-1 states: `{report['counts']['safe_depth1_total']}`",
                f"- safe depth-2 states: `{report['counts']['safe_depth2_total']}`",
                "",
                "### Top Add Moves",
                "",
            ]
        )
        for row in report["top_add_moves"]:
            m = row["metrics"]
            lines.append(
                f"- add `{row['bucket']}:{row['line_id']}` -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, gate=`{row['gate_pass']}`"
            )
        lines.extend(["", "### Top Replace Moves", ""])
        for row in report["top_replace_moves"]:
            m = row["metrics"]
            lines.append(
                f"- replace `{row['bucket']}:{row['out_line']}->{row['in_line']}` -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, gate=`{row['gate_pass']}`"
            )
        lines.extend(["", "### Safe Depth-1", ""])
        if not report["safe_depth1"]:
            lines.append("- none")
        else:
            for row in report["safe_depth1"]:
                m = row["metrics"]
                mv = row["move"]
                if mv["move_type"] == "add":
                    move_label = f"add {mv['bucket']}:{mv['line_id']}"
                else:
                    move_label = f"replace {mv['bucket']}:{mv['out_line']}->{mv['in_line']}"
                lines.append(
                    f"- `{move_label}` -> family5=`{m['family5_rate']:.6f}`, exact=`{m['exact_rate']:.6f}`, best_counts=`{m['best_counts']}`"
                )
        lines.extend(["", "### Safe Depth-2", ""])
        if not report["safe_depth2"]:
            lines.append("- none")
        else:
            for row in report["safe_depth2"]:
                m = row["metrics"]
                lines.append(
                    f"- add `{row['bucket']}:{row['line_id']}` after parent -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`"
                )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "- this scan moves from raw unions to gated local moves around the core and checks where canonical behavior survives;",
            "- safe moves are candidates for layered constructive expansion; failed moves are immediate negative certificates.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")
    shutdown_rust_kernel_server()
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
