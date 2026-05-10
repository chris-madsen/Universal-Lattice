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
from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices
from research.common.projection import project_points, random_projection


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def vertex_neighbors(edge_list, vertex_index):
    neighbors = []
    for i, j in edge_list:
        if i == vertex_index:
            neighbors.append(j)
        elif j == vertex_index:
            neighbors.append(i)
    return sorted(neighbors)


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


def star_signature(points4, center_idx, neighbors, projection):
    points2 = project_points(points4, projection)
    center = points2[center_idx]
    oriented_angles = []
    absolute_angles = []
    zero_edges = 0
    for n in neighbors:
        vec = points2[n] - center
        length = float(np.linalg.norm(vec))
        if length < 1e-9:
            zero_edges += 1
            continue
        angle360 = (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 360.0) % 360.0
        angle180 = angle360 % 180.0
        oriented_angles.append(angle360)
        absolute_angles.append(angle180)
    oriented = cluster_angles(oriented_angles, tol=1.5)
    absolute = cluster_angles(absolute_angles, tol=1.5)
    return {
        "zero_edges": zero_edges,
        "oriented_ray_count": len(oriented),
        "absolute_family_count": len(absolute),
        "oriented_centers_deg": [float(x) for x in oriented],
        "absolute_centers_deg": [float(x) for x in absolute],
    }


def run_baseline(variant_dir: Path) -> int:
    signature = build_signature()
    grammar = derive_generativity_grammar(signature)
    nodes = signature["anchor_nodes"]
    center = next(node for node in nodes if node["point"]["label"] == "(1,3/2)")
    top_center = next(node for node in nodes if node["point"]["label"] == "(1,3)")
    bottom_center = next(node for node in nodes if node["point"]["label"] == "(1,0)")
    corners = {node["point"]["label"]: node["degree"] for node in nodes if node["point"]["label"] in {"(0,0)", "(0,3)", "(2,0)", "(2,3)"}}

    data = {
        "target_anchor_node_count": signature["anchor_node_count"],
        "target_false_intersection_count": signature["false_intersection_count"],
        "target_center_degree": center["degree"],
        "target_top_center_degree": top_center["degree"],
        "target_bottom_center_degree": bottom_center["degree"],
        "target_corner_degrees": corners,
        "target_family_counts": signature["family_counts"],
        "target_mast_attachment_levels": grammar["mast_attachment_levels"],
    }

    data_dir = variant_dir / "data"
    data_dir.mkdir(exist_ok=True)
    summary_path = data_dir / "baseline_local_targets.md"
    json_path = data_dir / "baseline_local_targets.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    summary_path.write_text(f'''# Local Vertex Baseline Targets\n\n- center degree: `{data['target_center_degree']}`\n- top center degree: `{data['target_top_center_degree']}`\n- bottom center degree: `{data['target_bottom_center_degree']}`\n- corner degrees: `{data['target_corner_degrees']}`\n- family counts: `{data['target_family_counts']}`\n- mast attachment levels: `{data['target_mast_attachment_levels']}`\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text().rstrip() + f'''\n\n## {now_string()} - baseline\nGoal: fix the target local-signatures lattice for the vertex local web branch.\nHypothesis: `02_local_vertex_web`\nScript: `research/A_geometric_models/02_local_vertex_web/scripts/run.py --stage baseline`\nArtifacts:\n- `data/baseline_local_targets.json`\n- `data/baseline_local_targets.md`\nWhat I think:\n- local degrees of key nodes;\n- basic family-counts;\n- levels of attachment points on masts.\nFormulas / reasoning:\n- if the local web branch is correct, it should explain the local grammar of the lattice, and not the entire raw web at once.\nIntermediate results:\n- center/top/bottom degrees: `{data['target_center_degree']}` / `{data['target_top_center_degree']}` / `{data['target_bottom_center_degree']}`\n- corner degrees: `{data['target_corner_degrees']}`\nWhat does this mean:\n- branch `02` now has a formal target for comparison with local 24-cell star projections.\nDifficulty:\n- low.\nNext step:\n- go to prune and check if the projected star can be one 24-cell tops give the desired local fan-profile.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: active

## Summary

Baseline local targets extracted from the reference lattice.

## Best Witness

- `data/baseline_local_targets.json`
- `data/baseline_local_targets.md`

## Blocking Issues

None at baseline stage.
''')

    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"targets={json_path}")
    return 0


def run_prune(variant_dir: Path) -> int:
    vertices = canonical_24cell_vertices()
    edges = canonical_24cell_edges(vertices)
    center_idx = 0
    neighbors = vertex_neighbors(edges, center_idx)

    rng = np.random.default_rng(43)
    samples = 1200
    records = []
    oriented_hist = {}
    absolute_hist = {}
    for _ in range(samples):
        projection = random_projection(rng)
        rec = star_signature(vertices, center_idx, neighbors, projection)
        records.append(rec)
        oriented_hist[rec['oriented_ray_count']] = oriented_hist.get(rec['oriented_ray_count'], 0) + 1
        absolute_hist[rec['absolute_family_count']] = absolute_hist.get(rec['absolute_family_count'], 0) + 1

    target_oriented = 5
    target_absolute = 3
    match_count = sum(1 for rec in records if rec['oriented_ray_count'] == target_oriented and rec['absolute_family_count'] == target_absolute)
    records.sort(key=lambda r: (abs(r['oriented_ray_count'] - target_oriented), abs(r['absolute_family_count'] - target_absolute), r['zero_edges']))
    best = records[0]
    report = {
        'samples': samples,
        'vertex_degree_24cell': len(neighbors),
        'target_oriented_ray_count': target_oriented,
        'target_absolute_family_count': target_absolute,
        'oriented_histogram': oriented_hist,
        'absolute_histogram': absolute_hist,
        'joint_match_count': match_count,
        'best_candidate': best,
    }

    data_dir = variant_dir / 'data'
    report_path = data_dir / 'prune_local_star_scan.json'
    summary_path = data_dir / 'prune_local_star_summary.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    summary_path.write_text(f'''# Local Vertex Prune Summary\n\n- samples: `{samples}`\n- canonical 24-cell vertex degree: `{len(neighbors)}`\n- target oriented ray count: `{target_oriented}`\n- target absolute family count: `{target_absolute}`\n- joint exact matches: `{match_count}`\n- oriented histogram: `{oriented_hist}`\n- absolute histogram: `{absolute_hist}`\n- best candidate: `{best}`\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text () `research/A_geometric_models/02_local_vertex_web/scripts/run.py --stage prune`\nArtifacts:\n- `data/prune_local_star_scan.json`\n- `data/prune_local_star_summary.md`\nWhat I think:\n- in canonical 24-cell, each vertex has degree `8`;\n- projected local star of one vertex;\n- oriented rays and absolute families around the center of the star are considered.\nFormulas / reasoning:\n- top/bottom/center nodes of the current lattice have degree `5`;\n- this is not equal to the degree of a 24-cell vertex, but after projection some of the rays can coincide in direction;\n- prune is needed to understand whether at least local fan-profile level `5 oriented rays / 3 absolute is achievable families`.\nIntermediate results:\n- joint exact matches: `{match_count}` from `{samples}`\n- oriented histogram: `{oriented_hist}`\n- absolute histogram: `{absolute_hist}`\n- best candidate: `{best}`\nWhat does this mean:\n- branch `02` either remains strong, or also begins to crack already on the local level.\nDifficulty:\n- low-medium; the calculation is local and cheap.\nNext step:\n- if the local star regularly hits the target local-profile, you can drag `02` into search;\n- if not, move to `03_affine_normalized_24cell`.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text(f'''# Result

Status: active

## Summary

Baseline and prune completed for the local-vertex hypothesis. Sampled local star projections of a 24-cell vertex were compared against the target local fan-profile.

## Best Witness

- `data/baseline_local_targets.json`
- `data/prune_local_star_scan.json`

## Blocking Issues

Need to inspect whether the joint local-profile match count is strong enough to justify deeper search.
''')

    print(f"variant={variant_dir.name}")
    print("stage=prune")
    print(f"report={report_path}")
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
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print('TODO: implement hypothesis-specific workflow')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
