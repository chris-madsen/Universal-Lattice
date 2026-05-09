#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GA_PATH = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
OUT_JSON = ROOT / "research" / "B_symmetry_arrangement_models" / "12_topology_signature_filter" / "data" / "topology_signature_space_report.json"
OUT_MD = ROOT / "research" / "B_symmetry_arrangement_models" / "12_topology_signature_filter" / "data" / "topology_signature_space_report.md"


def load_ga_module():
    spec = importlib.util.spec_from_file_location("ga05_topology_signature_space", GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ga05_topology_signature_space"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def candidate_from_parts(module, template_key: str, axis_subset_key: str, selections: dict[str, list[int]]) -> dict:
    tmpl = module.TEMPLATE_MAP[template_key]
    return {
        "template_key": template_key,
        "axis_subset_key": axis_subset_key,
        "axis_size": tmpl.axis_size,
        "total_cell_count": tmpl.total_cell_count,
        "bucket_counts": dict(tmpl.bucket_counts),
        "selections": selections,
        "source": "topology_space_scan",
    }


def generate_selections(module, template_key: str, axis_subset_key: str):
    tmpl = module.TEMPLATE_MAP[template_key]
    buckets = module.SUBSET_BUCKETS[axis_subset_key]
    b2_pool = buckets["2"]
    b1_pool = buckets["1"]
    b0_pool = buckets["0"]
    for b2 in itertools.combinations(b2_pool, tmpl.bucket_counts["2"]):
        for b1 in itertools.combinations(b1_pool, tmpl.bucket_counts["1"]):
            for b0 in itertools.combinations(b0_pool, tmpl.bucket_counts["0"]):
                yield {
                    "2": sorted(int(x) for x in b2),
                    "1": sorted(int(x) for x in b1),
                    "0": sorted(int(x) for x in b0),
                }


def main() -> int:
    module = load_ga_module()

    unique_signatures: set[str] = set()
    root_rows = []
    template_rows: dict[str, dict[str, int]] = {}

    total_candidates = 0
    for root in module.ROOT_BRANCHES:
        template_key = root["template_key"]
        subset_key = root["axis_subset_key"]

        root_total = 0
        root_sigs: set[str] = set()

        for selections in generate_selections(module, template_key, subset_key):
            cand = candidate_from_parts(module, template_key, subset_key, selections)
            sig = module.topological_signature(cand)
            root_total += 1
            total_candidates += 1
            root_sigs.add(sig)
            unique_signatures.add(sig)

        root_unique = len(root_sigs)
        root_rows.append(
            {
                "root_branch_key": root["key"],
                "template_key": template_key,
                "axis_subset_key": subset_key,
                "raw_candidates": root_total,
                "unique_signatures": root_unique,
                "compression_ratio": (root_total / root_unique) if root_unique else None,
            }
        )

        tr = template_rows.setdefault(template_key, {"raw_candidates": 0, "unique_signatures": 0})
        tr["raw_candidates"] += root_total
        tr["unique_signatures"] += root_unique

    overall_unique = len(unique_signatures)
    payload = {
        "total_root_branches": len(module.ROOT_BRANCHES),
        "total_templates": len(module.TEMPLATES),
        "raw_candidate_space": total_candidates,
        "unique_topological_signatures": overall_unique,
        "overall_compression_ratio": (total_candidates / overall_unique) if overall_unique else None,
        "root_rows": root_rows,
        "template_rows": [
            {
                "template_key": key,
                "raw_candidates": row["raw_candidates"],
                "unique_signatures": row["unique_signatures"],
                "compression_ratio": (row["raw_candidates"] / row["unique_signatures"]) if row["unique_signatures"] else None,
            }
            for key, row in sorted(template_rows.items())
        ],
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    top_roots = sorted(root_rows, key=lambda r: (r["compression_ratio"] or 0.0), reverse=True)[:15]
    top_templates = sorted(payload["template_rows"], key=lambda r: (r["compression_ratio"] or 0.0), reverse=True)[:15]

    lines = [
        "# Topology Signature Space Report",
        "",
        f"- total root branches: `{payload['total_root_branches']}`",
        f"- total templates: `{payload['total_templates']}`",
        f"- raw candidate space: `{payload['raw_candidate_space']}`",
        f"- unique topological signatures: `{payload['unique_topological_signatures']}`",
        f"- overall compression ratio: `{payload['overall_compression_ratio']:.6f}`",
        "",
        "## Top Root Branch Compression",
        "",
    ]

    for row in top_roots:
        lines.append(
            f"- `{row['root_branch_key']}`: raw=`{row['raw_candidates']}`, unique=`{row['unique_signatures']}`, ratio=`{row['compression_ratio']:.6f}`"
        )

    lines.extend(["", "## Top Template Compression", ""])
    for row in top_templates:
        lines.append(
            f"- `{row['template_key']}`: raw=`{row['raw_candidates']}`, unique=`{row['unique_signatures']}`, ratio=`{row['compression_ratio']:.6f}`"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
