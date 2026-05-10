#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import (
    configured_kernel_backend,
    evaluate_vectors_python,
    evaluate_vectors_rust_persistent,
    init_rust_kernel_server,
)
from research.common.meta_search import humanize_duration_hm, low_pass_harmonic_prior_from_matrix, now_string
from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices

STATE_VERSION = 1
DEFAULT_STATE_DIR = ROOT / "research" / "async_state" / "h12_polytope_pair"
BRANCH_DIR = ROOT / "research" / "B_symmetry_arrangement_models" / "12_polytope_pair_double_rotation_match"

SOURCE_PAIRS = (("24", "24"), ("24", "T"), ("24", "16"), ("T", "T"), ("T", "16"), ("16", "16"))
RATIOS = ((1, 1), (1, 2), (1, 3), (2, 3), (3, 4), (1, 4))
BASE_ANGLES_DEG = (7.5, 15.0, 18.0, 22.5, 30.0, 36.0, 45.0, 60.0, 72.0, 90.0)
PLANE_DECOMPOSITIONS = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))
READOUT_MODES = ("edge_union", "line_arrangement_core", "direction_shell_readout")
PROJECTION_FAMILIES = ("coordinate", "coxeter_f4", "golden_h4", "central_bundle")
PROJECTION_COUNTS = {"coordinate": 6, "coxeter_f4": 12, "golden_h4": 12, "central_bundle": 18}
TOTAL_PROJECTED_CANDIDATES = (
    len(SOURCE_PAIRS)
    * len(RATIOS)
    * len(BASE_ANGLES_DEG)
    * len(PLANE_DECOMPOSITIONS)
    * len(READOUT_MODES)
    * sum(PROJECTION_COUNTS.values())
)

TARGET_NODE_ORDER = [(x, y) for x in (0.0, 1.0, 2.0) for y in (0.0, 1.0, 1.5, 2.0, 3.0)]
TARGET_NODE_INDEX = {p: i for i, p in enumerate(TARGET_NODE_ORDER)}
TARGET_CENTER = (1.0, 1.5)


@dataclass(frozen=True)
class CandidateSpec:
    source_pair: tuple[str, str]
    ratio: tuple[int, int]
    base_angle_deg: float
    plane_idx: int
    readout_mode: str
    projection_family: str
    projection_idx: int

    @property
    def key(self) -> str:
        return (
            f"{self.source_pair[0]}-{self.source_pair[1]}|"
            f"r{self.ratio[0]}:{self.ratio[1]}|"
            f"a{self.base_angle_deg:g}|"
            f"p{self.plane_idx}|"
            f"{self.readout_mode}|"
            f"{self.projection_family}:{self.projection_idx}"
        )


def normalize_segment(a: tuple[float, float], b: tuple[float, float]) -> tuple[int, int]:
    ia = TARGET_NODE_INDEX[a]
    ib = TARGET_NODE_INDEX[b]
    return (ia, ib) if ia < ib else (ib, ia)


def target_segments() -> set[tuple[int, int]]:
    segments: set[tuple[int, int]] = set()
    for x in (0.0, 1.0, 2.0):
        segments.add(normalize_segment((x, 0.0), (x, 3.0)))
    for p in (
        (0.0, 0.0),
        (0.0, 1.0),
        (0.0, 2.0),
        (0.0, 3.0),
        (2.0, 0.0),
        (2.0, 1.0),
        (2.0, 2.0),
        (2.0, 3.0),
    ):
        segments.add(normalize_segment(TARGET_CENTER, p))
    return segments


TARGET_SEGMENTS = target_segments()
TARGET_CENTRAL_RAYS = {seg for seg in TARGET_SEGMENTS if TARGET_NODE_INDEX[TARGET_CENTER] in seg}
TARGET_VERTICAL_MASTS = {
    normalize_segment((0.0, 0.0), (0.0, 3.0)),
    normalize_segment((1.0, 0.0), (1.0, 3.0)),
    normalize_segment((2.0, 0.0), (2.0, 3.0)),
}


def orientation_deg_by_points(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    return 0.0 if abs(angle - 180.0) < 1e-9 else angle


def circular_distance_deg(a: float, b: float) -> float:
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def target_angle_classes() -> list[float]:
    return sorted({round(orientation_deg_by_points(TARGET_NODE_ORDER[i], TARGET_NODE_ORDER[j]), 6) for i, j in TARGET_SEGMENTS})


TARGET_ANGLE_CLASSES = target_angle_classes()


def target_summary() -> dict:
    return {
        "segment_count": len(TARGET_SEGMENTS),
        "node_count": len(TARGET_NODE_ORDER),
        "vertical_mast_count": len(TARGET_VERTICAL_MASTS),
        "central_ray_count": len(TARGET_CENTRAL_RAYS),
        "center": list(TARGET_CENTER),
        "angle_classes_deg": TARGET_ANGLE_CLASSES,
    }


def canonical_tesseract_vertices() -> np.ndarray:
    return np.array([[1.0 if bit else -1.0 for bit in bits] for bits in itertools.product((0, 1), repeat=4)], dtype=float)


def canonical_tesseract_edges(vertices: np.ndarray) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            diff = np.abs(vertices[i] - vertices[j])
            if np.count_nonzero(diff) == 1 and np.isclose(float(np.sum(diff)), 2.0):
                edges.append((i, j))
    return edges


def canonical_16cell_vertices() -> np.ndarray:
    vertices = []
    for i in range(4):
        for sign in (-1.0, 1.0):
            vec = np.zeros(4, dtype=float)
            vec[i] = sign
            vertices.append(vec)
    return np.array(vertices, dtype=float)


def canonical_16cell_edges(vertices: np.ndarray) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            if not np.allclose(vertices[i], -vertices[j]):
                edges.append((i, j))
    return edges


def source_polytope(name: str) -> tuple[np.ndarray, list[tuple[int, int]]]:
    if name == "24":
        vertices = canonical_24cell_vertices()
        return vertices, canonical_24cell_edges(vertices)
    if name == "T":
        vertices = canonical_tesseract_vertices()
        return vertices, canonical_tesseract_edges(vertices)
    if name == "16":
        vertices = canonical_16cell_vertices()
        return vertices, canonical_16cell_edges(vertices)
    raise ValueError(f"unknown source: {name}")


def rotation_in_plane(i: int, j: int, theta: float) -> np.ndarray:
    matrix = np.eye(4)
    c = math.cos(theta)
    s = math.sin(theta)
    matrix[i, i] = c
    matrix[j, j] = c
    matrix[i, j] = -s
    matrix[j, i] = s
    return matrix


def double_rotation_matrix(plane_idx: int, alpha: float, beta: float) -> np.ndarray:
    (i1, j1), (i2, j2) = PLANE_DECOMPOSITIONS[plane_idx]
    return rotation_in_plane(i1, j1, alpha) @ rotation_in_plane(i2, j2, beta)


def root_line_key(vec: np.ndarray, tol: float = 1e-9) -> tuple[float, ...]:
    idx = next((i for i, x in enumerate(vec) if abs(float(x)) > tol), None)
    if idx is None:
        return tuple([0.0] * len(vec))
    if vec[idx] < 0:
        vec = -vec
    return tuple(round(float(x / vec[idx]), 8) for x in vec.tolist())


def unique_line_representatives(vectors: Iterable[np.ndarray]) -> list[np.ndarray]:
    seen: set[tuple[float, ...]] = set()
    result: list[np.ndarray] = []
    for vec in vectors:
        arr = np.asarray(vec, dtype=float)
        if np.linalg.norm(arr) < 1e-9:
            continue
        key = root_line_key(arr)
        if key in seen:
            continue
        seen.add(key)
        result.append(arr)
    return result


def edge_direction_vectors(vertices: np.ndarray, edges: list[tuple[int, int]]) -> list[np.ndarray]:
    return unique_line_representatives(vertices[j] - vertices[i] for i, j in edges)


def candidate_vectors(spec: CandidateSpec) -> list[np.ndarray]:
    first_vertices, first_edges = source_polytope(spec.source_pair[0])
    second_vertices, second_edges = source_polytope(spec.source_pair[1])
    alpha = math.radians(spec.base_angle_deg * spec.ratio[0])
    beta = math.radians(spec.base_angle_deg * spec.ratio[1])
    rotation = double_rotation_matrix(spec.plane_idx, alpha, beta)
    second_rotated = (rotation @ second_vertices.T).T

    if spec.readout_mode == "edge_union":
        vectors = edge_direction_vectors(first_vertices, first_edges)
        vectors.extend(edge_direction_vectors(second_rotated, second_edges))
    elif spec.readout_mode == "line_arrangement_core":
        vectors = edge_direction_vectors(first_vertices, first_edges)
        vectors.extend(edge_direction_vectors(second_rotated, second_edges))
        vectors.extend(unique_line_representatives(first_vertices))
        vectors.extend(unique_line_representatives(second_rotated))
    elif spec.readout_mode == "direction_shell_readout":
        vectors = unique_line_representatives(first_vertices)
        vectors.extend(unique_line_representatives(second_rotated))
    else:
        raise ValueError(f"unknown readout mode: {spec.readout_mode}")
    return unique_line_representatives(vectors)


def qr_projection(rows: list[list[float]]) -> np.ndarray:
    basis = []
    for row in rows:
        vec = np.array(row, dtype=float)
        for prev in basis:
            vec = vec - np.dot(vec, prev) * prev
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            basis.append(vec / norm)
        if len(basis) == 2:
            break
    if len(basis) < 2:
        raise ValueError("projection rows are degenerate")
    return np.vstack(basis)


def deterministic_projection(family: str, idx: int) -> np.ndarray:
    if family == "coordinate":
        pairs = list(itertools.combinations(range(4), 2))
        a, b = pairs[idx]
        rows = np.zeros((2, 4), dtype=float)
        rows[0, a] = 1.0
        rows[1, b] = 1.0
        return rows
    if family == "coxeter_f4":
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        seeds = [
            ([1, 1, 0, 0], [0, 0, 1, -1]),
            ([1, -1, 0, 0], [0, 0, 1, 1]),
            ([1, 0, 1, 0], [0, 1, 0, -1]),
            ([1, 0, -1, 0], [0, 1, 0, 1]),
            ([1, 0, 0, 1], [0, 1, -1, 0]),
            ([1, 0, 0, -1], [0, 1, 1, 0]),
            ([1, 1, 1, 1], [1, -1, 1, -1]),
            ([1, 1, -1, -1], [1, -1, -1, 1]),
            ([2, 1, 0, -1], [0, 1, 2, 1]),
            ([2, -1, 0, 1], [0, 1, -2, 1]),
            ([phi, 1, 0, 0], [0, 0, phi, -1]),
            ([phi, -1, 0, 0], [0, 0, phi, 1]),
        ]
        return qr_projection([list(map(float, x)) for x in seeds[idx]])
    if family == "golden_h4":
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        inv = 1.0 / phi
        seeds = [
            ([1, phi, 0, inv], [0, inv, phi, -1]),
            ([1, -phi, 0, inv], [0, inv, -phi, -1]),
            ([phi, 0, 1, inv], [inv, 1, 0, -phi]),
            ([phi, 0, -1, inv], [inv, -1, 0, -phi]),
            ([1, inv, phi, 0], [phi, -1, inv, 0]),
            ([1, inv, -phi, 0], [phi, 1, inv, 0]),
            ([phi, 1, inv, 0], [0, inv, -1, phi]),
            ([phi, -1, inv, 0], [0, inv, 1, phi]),
            ([1, phi, inv, 0], [inv, -1, 0, phi]),
            ([1, -phi, inv, 0], [inv, 1, 0, phi]),
            ([phi, inv, 0, 1], [1, 0, -phi, inv]),
            ([phi, inv, 0, -1], [-1, 0, -phi, inv]),
        ]
        return qr_projection([list(map(float, x)) for x in seeds[idx]])
    if family == "central_bundle":
        slopes = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
        s = slopes[idx % len(slopes)]
        shift = idx // len(slopes)
        rows = [
            [1.0, s, 0.25 * shift, -0.5],
            [-s, 1.0, 0.5, 0.25 * (shift + 1)],
        ]
        return qr_projection(rows)
    raise ValueError(f"unknown projection family: {family}")


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def cluster_angles(values: list[float], tol: float = 1.5) -> list[float]:
    values = sorted(float(v) % 180.0 for v in values)
    if not values:
        return []
    groups = [[values[0]]]
    for value in values[1:]:
        if abs(value - groups[-1][-1]) <= tol:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(group) / len(group) for group in groups]


def projected_family_angles(vectors: list[np.ndarray], projection: np.ndarray) -> list[float]:
    projected = [(projection @ vec.reshape(-1, 1)).reshape(-1) for vec in vectors]
    angles = [angle_mod_180(vec) for vec in projected if np.linalg.norm(vec) > 1e-9]
    return cluster_angles(angles, tol=1.5)


def has_intermediate_collinear_point(a: tuple[float, float], b: tuple[float, float], eps: float = 1e-9) -> bool:
    x1, y1 = a
    x2, y2 = b
    for x, y in TARGET_NODE_ORDER:
        if (x, y) == a or (x, y) == b:
            continue
        area2 = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if abs(area2) > eps:
            continue
        if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
            return True
    return False


def segments_from_family_angles(family_angles: list[float], tol: float = 2.0) -> set[tuple[int, int]]:
    segments: set[tuple[int, int]] = set()
    if not family_angles:
        return segments
    for a, b in itertools.combinations(TARGET_NODE_ORDER, 2):
        seg = normalize_segment(a, b)
        angle = orientation_deg_by_points(a, b)
        if min(circular_distance_deg(angle, fam) for fam in family_angles) > tol:
            continue
        # Keep long target primitives (notably the 3 full vertical masts) even if
        # there are intermediate lattice nodes on the same line segment.
        if has_intermediate_collinear_point(a, b) and seg not in TARGET_SEGMENTS:
            continue
        segments.add(seg)
    return segments


def topology_signature_for_segments(segments: set[tuple[int, int]]) -> str:
    degrees = [0 for _ in TARGET_NODE_ORDER]
    for a, b in segments:
        degrees[a] += 1
        degrees[b] += 1
    center_idx = TARGET_NODE_INDEX[TARGET_CENTER]
    payload = {
        "edges": sorted([list(seg) for seg in segments]),
        "degree_profile": sorted(degrees),
        "center_degree": degrees[center_idx],
        "segment_count": len(segments),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def segment_angles(segments: set[tuple[int, int]]) -> list[float]:
    return sorted({round(orientation_deg_by_points(TARGET_NODE_ORDER[a], TARGET_NODE_ORDER[b]), 6) for a, b in segments})


def jaccard_size(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a or b else 1.0


def compare_segments(candidate: set[tuple[int, int]], family_angles: list[float]) -> dict:
    matched = candidate & TARGET_SEGMENTS
    missing = TARGET_SEGMENTS - candidate
    extra = candidate - TARGET_SEGMENTS
    central_matched = len(candidate & TARGET_CENTRAL_RAYS)
    mast_matched = len(candidate & TARGET_VERTICAL_MASTS)
    cand_angles = segment_angles(candidate)
    angle_overlap = set(cand_angles) & set(TARGET_ANGLE_CLASSES)
    angle_jaccard = len(angle_overlap) / len(set(cand_angles) | set(TARGET_ANGLE_CLASSES)) if cand_angles or TARGET_ANGLE_CLASSES else 1.0
    topology_match = not missing and not extra
    central_fan_complete = central_matched == len(TARGET_CENTRAL_RAYS)
    vertical_masts_complete = mast_matched == len(TARGET_VERTICAL_MASTS)
    segment_jaccard = jaccard_size(candidate, TARGET_SEGMENTS)
    score = (
        400.0 * segment_jaccard
        + 200.0 * (central_matched / len(TARGET_CENTRAL_RAYS))
        + 150.0 * (mast_matched / len(TARGET_VERTICAL_MASTS))
        + 150.0 * angle_jaccard
        - 8.0 * len(missing)
        - 3.0 * len(extra)
    )
    return {
        "topology_match": topology_match,
        "segment_jaccard": segment_jaccard,
        "matched_segments": len(matched),
        "missing_segments": len(missing),
        "extra_segments": len(extra),
        "central_rays_matched": central_matched,
        "central_rays_total": len(TARGET_CENTRAL_RAYS),
        "central_fan_complete": central_fan_complete,
        "vertical_masts_matched": mast_matched,
        "vertical_masts_total": len(TARGET_VERTICAL_MASTS),
        "vertical_masts_complete": vertical_masts_complete,
        "candidate_segment_count": len(candidate),
        "target_segment_count": len(TARGET_SEGMENTS),
        "candidate_angle_classes": cand_angles,
        "target_angle_classes": TARGET_ANGLE_CLASSES,
        "angle_class_jaccard": angle_jaccard,
        "projected_family_angles": [round(x, 6) for x in family_angles],
        "grid_match_score": score,
        "matched_segment_ids": sorted([list(x) for x in matched]),
        "missing_segment_ids": sorted([list(x) for x in missing]),
        "extra_segment_ids": sorted([list(x) for x in extra]),
    }


def all_specs() -> list[CandidateSpec]:
    result = []
    for pair in SOURCE_PAIRS:
        for ratio in RATIOS:
            for angle in BASE_ANGLES_DEG:
                for plane_idx in range(len(PLANE_DECOMPOSITIONS)):
                    for readout_mode in READOUT_MODES:
                        for family in PROJECTION_FAMILIES:
                            for projection_idx in range(PROJECTION_COUNTS[family]):
                                result.append(
                                    CandidateSpec(
                                        source_pair=pair,
                                        ratio=ratio,
                                        base_angle_deg=angle,
                                        plane_idx=plane_idx,
                                        readout_mode=readout_mode,
                                        projection_family=family,
                                        projection_idx=projection_idx,
                                    )
                                )
    return result


SPECS = all_specs()


def spec_to_json(spec: CandidateSpec) -> dict:
    return {
        "source_pair": list(spec.source_pair),
        "ratio": list(spec.ratio),
        "base_angle_deg": spec.base_angle_deg,
        "plane_idx": spec.plane_idx,
        "plane_decomposition": [list(x) for x in PLANE_DECOMPOSITIONS[spec.plane_idx]],
        "readout_mode": spec.readout_mode,
        "projection_family": spec.projection_family,
        "projection_idx": spec.projection_idx,
        "key": spec.key,
    }


def harmonic_angle_prior() -> dict[float, float]:
    matrix = np.array([[1.0 if angle in (15.0, 30.0, 45.0, 60.0, 90.0) else 0.45 for angle in BASE_ANGLES_DEG]])
    smooth = low_pass_harmonic_prior_from_matrix(matrix, keep_rows=1, keep_cols=4, floor=0.1)[0]
    return {float(angle): float(value) for angle, value in zip(BASE_ANGLES_DEG, smooth)}


ANGLE_PRIOR = harmonic_angle_prior()


def initial_pheromone() -> dict[str, dict[str, float]]:
    return {
        "source_pair": {f"{a}-{b}": (2.0 if (a, b) in (("24", "T"), ("24", "24"), ("24", "16")) else 1.0) for a, b in SOURCE_PAIRS},
        "ratio": {f"{a}:{b}": (1.7 if (a, b) in ((1, 1), (1, 2), (2, 3)) else 1.0) for a, b in RATIOS},
        "angle": {f"{angle:g}": ANGLE_PRIOR[float(angle)] for angle in BASE_ANGLES_DEG},
        "plane": {str(i): 1.0 for i in range(len(PLANE_DECOMPOSITIONS))},
        "readout": {mode: (1.4 if mode != "edge_union" else 1.0) for mode in READOUT_MODES},
        "projection": {
            family: (1.5 if family in ("central_bundle", "coxeter_f4") else 1.0) for family in PROJECTION_FAMILIES
        },
    }


def candidate_weight(spec: CandidateSpec, pheromone: dict[str, dict[str, float]]) -> float:
    return (
        pheromone["source_pair"].get(f"{spec.source_pair[0]}-{spec.source_pair[1]}", 1.0)
        * pheromone["ratio"].get(f"{spec.ratio[0]}:{spec.ratio[1]}", 1.0)
        * pheromone["angle"].get(f"{spec.base_angle_deg:g}", 1.0)
        * pheromone["plane"].get(str(spec.plane_idx), 1.0)
        * pheromone["readout"].get(spec.readout_mode, 1.0)
        * pheromone["projection"].get(spec.projection_family, 1.0)
    )


def update_pheromone(pheromone: dict[str, dict[str, float]], spec: CandidateSpec, score: float) -> None:
    deposit = max(0.0, min(2.0, score / 500.0))
    keys = [
        ("source_pair", f"{spec.source_pair[0]}-{spec.source_pair[1]}"),
        ("ratio", f"{spec.ratio[0]}:{spec.ratio[1]}"),
        ("angle", f"{spec.base_angle_deg:g}"),
        ("plane", str(spec.plane_idx)),
        ("readout", spec.readout_mode),
        ("projection", spec.projection_family),
    ]
    for group, key in keys:
        pheromone[group][key] = 0.995 * pheromone[group].get(key, 1.0) + deposit


def neighbor_indices(spec: CandidateSpec, index_by_key: dict[str, int]) -> list[int]:
    neighbors: list[CandidateSpec] = []
    angle_pos = BASE_ANGLES_DEG.index(spec.base_angle_deg)
    for delta in (-1, 1):
        pos = angle_pos + delta
        if 0 <= pos < len(BASE_ANGLES_DEG):
            neighbors.append(
                CandidateSpec(
                    source_pair=spec.source_pair,
                    ratio=spec.ratio,
                    base_angle_deg=BASE_ANGLES_DEG[pos],
                    plane_idx=spec.plane_idx,
                    readout_mode=spec.readout_mode,
                    projection_family=spec.projection_family,
                    projection_idx=spec.projection_idx,
                )
            )
    for plane_idx in range(len(PLANE_DECOMPOSITIONS)):
        if plane_idx != spec.plane_idx:
            neighbors.append(
                CandidateSpec(
                    source_pair=spec.source_pair,
                    ratio=spec.ratio,
                    base_angle_deg=spec.base_angle_deg,
                    plane_idx=plane_idx,
                    readout_mode=spec.readout_mode,
                    projection_family=spec.projection_family,
                    projection_idx=spec.projection_idx,
                )
            )
    for mode in READOUT_MODES:
        if mode != spec.readout_mode:
            neighbors.append(
                CandidateSpec(
                    source_pair=spec.source_pair,
                    ratio=spec.ratio,
                    base_angle_deg=spec.base_angle_deg,
                    plane_idx=spec.plane_idx,
                    readout_mode=mode,
                    projection_family=spec.projection_family,
                    projection_idx=spec.projection_idx,
                )
            )
    return [index_by_key[n.key] for n in neighbors if n.key in index_by_key]


def initialize_state(args: argparse.Namespace) -> dict:
    return {
        "version": STATE_VERSION,
        "status": "created",
        "created_at": now_string(),
        "updated_at": now_string(),
        "generation": 0,
        "target_generations": int(args.target_generations),
        "population_size": int(args.population_size),
        "ant_count": int(args.ant_count),
        "log_every": int(args.log_every),
        "projection_batch": int(args.projection_batch),
        "kernel_backend": str(args.kernel_backend),
        "pending_indices": list(range(len(SPECS))),
        "visited_count": 0,
        "total_candidates": len(SPECS),
        "unique_topological_signatures": {},
        "topology_match_count": 0,
        "segment_match_count": 0,
        "total_projection_evaluations": 0,
        "elapsed_wall_seconds": 0.0,
        "next_seed": 12012001,
        "rng_seed": 12012001,
        "best_overall": None,
        "best_grid_match": None,
        "best_candidates": [],
        "pair_stats": {},
        "ratio_stats": {},
        "readout_stats": {},
        "pheromone": initial_pheromone(),
        "target": target_summary(),
    }


def load_state(path: Path, args: argparse.Namespace) -> dict:
    if path.exists():
        state = json.loads(path.read_text())
        if state.get("version") != STATE_VERSION:
            raise RuntimeError(f"state version mismatch in {path}")
        state["target_generations"] = int(args.target_generations)
        state["population_size"] = int(args.population_size)
        state["ant_count"] = int(args.ant_count)
        state["log_every"] = int(args.log_every)
        state["projection_batch"] = int(args.projection_batch)
        state["kernel_backend"] = str(args.kernel_backend)
        return state
    return initialize_state(args)


def choose_batch(state: dict, rng: np.random.Generator, batch_size: int) -> list[int]:
    pending = state["pending_indices"]
    if not pending:
        return []
    chosen: list[int] = []
    pending_set = set(pending)
    index_by_key = {spec.key: idx for idx, spec in enumerate(SPECS)}
    for row in state.get("best_candidates", [])[: max(1, state["population_size"] // 2)]:
        base_idx = int(row["candidate_index"])
        for nidx in neighbor_indices(SPECS[base_idx], index_by_key):
            if nidx in pending_set and nidx not in chosen:
                chosen.append(nidx)
                if len(chosen) >= batch_size:
                    break
        if len(chosen) >= batch_size:
            break
    remaining_slots = batch_size - len(chosen)
    if remaining_slots <= 0:
        return chosen
    candidates = [idx for idx in pending if idx not in set(chosen)]
    if not candidates:
        return chosen
    weights = np.array([candidate_weight(SPECS[idx], state["pheromone"]) for idx in candidates], dtype=float)
    if np.all(weights <= 0):
        weights = np.ones_like(weights)
    weights /= weights.sum()
    pick_count = min(remaining_slots, len(candidates))
    picks = rng.choice(len(candidates), size=pick_count, replace=False, p=weights)
    chosen.extend(candidates[int(i)] for i in picks)
    return chosen


def evaluate_candidate(index: int, spec: CandidateSpec, projection_batch: int, seed: int, kernel_backend: str) -> dict:
    vectors = candidate_vectors(spec)
    projection = deterministic_projection(spec.projection_family, spec.projection_idx)
    family_angles = projected_family_angles(vectors, projection)
    segments = segments_from_family_angles(family_angles)
    comparison = compare_segments(segments, family_angles)
    topo_sig = topology_signature_for_segments(segments)
    if kernel_backend == "rust_persistent":
        family_stability = evaluate_vectors_rust_persistent(vectors, projection_batch=projection_batch, seed=seed)
    else:
        family_stability = evaluate_vectors_python(vectors, projection_batch=projection_batch, seed=seed)
    score = float(comparison["grid_match_score"]) + 40.0 * float(family_stability.get("family5_rate", 0.0))
    if comparison["topology_match"]:
        score += 1000.0
    if comparison["central_fan_complete"]:
        score += 150.0
    if comparison["vertical_masts_complete"]:
        score += 120.0
    return {
        "candidate_index": index,
        "spec": spec_to_json(spec),
        "topological_signature": topo_sig,
        "score": score,
        "comparison": comparison,
        "family_stability": family_stability,
        "segment_ids": sorted([list(seg) for seg in segments]),
    }


def bump_stats(stats: dict, key: str, row: dict) -> None:
    entry = stats.setdefault(
        key,
        {
            "eval_count": 0,
            "best_score": -1e18,
            "topology_matches": 0,
            "segment_matches": 0,
            "central_fan_complete": 0,
            "vertical_masts_complete": 0,
            "best": None,
        },
    )
    entry["eval_count"] += 1
    if row["comparison"]["topology_match"]:
        entry["topology_matches"] += 1
    if row["comparison"]["matched_segments"] == row["comparison"]["target_segment_count"]:
        entry["segment_matches"] += 1
    if row["comparison"]["central_fan_complete"]:
        entry["central_fan_complete"] += 1
    if row["comparison"]["vertical_masts_complete"]:
        entry["vertical_masts_complete"] += 1
    if row["score"] > entry["best_score"]:
        entry["best_score"] = row["score"]
        entry["best"] = row


def update_state_with_result(state: dict, row: dict) -> None:
    spec = CandidateSpec(
        source_pair=tuple(row["spec"]["source_pair"]),
        ratio=tuple(row["spec"]["ratio"]),
        base_angle_deg=float(row["spec"]["base_angle_deg"]),
        plane_idx=int(row["spec"]["plane_idx"]),
        readout_mode=row["spec"]["readout_mode"],
        projection_family=row["spec"]["projection_family"],
        projection_idx=int(row["spec"]["projection_idx"]),
    )
    state["unique_topological_signatures"].setdefault(row["topological_signature"], {"count": 0, "best_score": -1e18})
    sig_row = state["unique_topological_signatures"][row["topological_signature"]]
    sig_row["count"] += 1
    sig_row["best_score"] = max(float(sig_row["best_score"]), float(row["score"]))
    if row["comparison"]["topology_match"]:
        state["topology_match_count"] += 1
    if row["comparison"]["matched_segments"] == row["comparison"]["target_segment_count"]:
        state["segment_match_count"] += 1
    if state["best_overall"] is None or row["score"] > state["best_overall"]["score"]:
        state["best_overall"] = row
    if (
        row["comparison"]["matched_segments"],
        -row["comparison"]["missing_segments"],
        -row["comparison"]["extra_segments"],
        row["score"],
    ) > (
        state["best_grid_match"]["comparison"]["matched_segments"] if state["best_grid_match"] else -1,
        -state["best_grid_match"]["comparison"]["missing_segments"] if state["best_grid_match"] else -999,
        -state["best_grid_match"]["comparison"]["extra_segments"] if state["best_grid_match"] else -999,
        state["best_grid_match"]["score"] if state["best_grid_match"] else -1e18,
    ):
        state["best_grid_match"] = row
    state["best_candidates"].append(row)
    state["best_candidates"].sort(
        key=lambda x: (
            -x["comparison"]["matched_segments"],
            x["comparison"]["missing_segments"],
            x["comparison"]["extra_segments"],
            -x["score"],
        )
    )
    state["best_candidates"] = state["best_candidates"][:30]
    pair_key = f"{spec.source_pair[0]}-{spec.source_pair[1]}"
    ratio_key = f"{spec.ratio[0]}:{spec.ratio[1]}"
    bump_stats(state["pair_stats"], pair_key, row)
    bump_stats(state["ratio_stats"], ratio_key, row)
    bump_stats(state["readout_stats"], spec.readout_mode, row)
    update_pheromone(state["pheromone"], spec, row["score"])


def progress_summary(state: dict) -> dict:
    total = max(1, int(state["total_candidates"]))
    visited = int(state["visited_count"])
    elapsed = float(state["elapsed_wall_seconds"])
    rate = visited / elapsed if elapsed > 0 else 0.0
    remaining = max(0, total - visited)
    eta = remaining / rate if rate > 0 else None
    return {
        "candidate_progress": 100.0 * visited / total,
        "generation_progress": 100.0 * state["generation"] / max(1, state["target_generations"]),
        "rate": rate,
        "eta": eta,
        "eta_human": humanize_duration_hm(eta),
    }


def write_summary(state: dict, path: Path) -> None:
    prog = progress_summary(state)
    best = state.get("best_grid_match")
    best_line = "`none yet`" if best is None else f"`{best['spec']['key']}` score=`{best['score']:.3f}` matched=`{best['comparison']['matched_segments']}/11` missing=`{best['comparison']['missing_segments']}` extra=`{best['comparison']['extra_segments']}`"
    lines = [
        "# H12 Polytope-Pair Double-Rotation Search",
        "",
        f"- updated: `{state['updated_at']}`",
        f"- status: `{state['status']}`",
        f"- kernel backend: `{state['kernel_backend']}`",
        f"- generation: `{state['generation']}` / `{state['target_generations']}`",
        f"- generation progress: `{prog['generation_progress']:.4f}%`",
        f"- candidates checked: `{state['visited_count']}` / `{state['total_candidates']}`",
        f"- candidate progress: `{prog['candidate_progress']:.4f}%`",
        f"- unique topological signatures: `{len(state['unique_topological_signatures'])}`",
        f"- topology matches: `{state['topology_match_count']}`",
        f"- full target segment matches: `{state['segment_match_count']}`",
        f"- projection evaluations through Rust/Python kernel: `{state['total_projection_evaluations']}`",
        f"- elapsed: `{humanize_duration_hm(state['elapsed_wall_seconds'])}`",
        f"- ETA: `{prog['eta_human']}`",
        f"- best grid match: {best_line}",
        "",
        "## Target Simplified Lattice",
        "",
        f"- nodes: `{state['target']['node_count']}`",
        f"- segments: `{state['target']['segment_count']}`",
        f"- vertical masts: `{state['target']['vertical_mast_count']}`",
        f"- central rays: `{state['target']['central_ray_count']}`",
        f"- angle classes: `{state['target']['angle_classes_deg']}`",
        "",
        "## Best Source Pairs",
    ]
    for key, stats in sorted(state["pair_stats"].items(), key=lambda kv: (-kv[1]["best_score"], kv[0]))[:8]:
        lines.append(
            f"- `{key}`: evals=`{stats['eval_count']}`, best_score=`{stats['best_score']:.3f}`, topology_matches=`{stats['topology_matches']}`, segment_matches=`{stats['segment_matches']}`"
        )
    lines.extend(["", "## Best Ratios"])
    for key, stats in sorted(state["ratio_stats"].items(), key=lambda kv: (-kv[1]["best_score"], kv[0]))[:8]:
        lines.append(
            f"- `{key}`: evals=`{stats['eval_count']}`, best_score=`{stats['best_score']:.3f}`, topology_matches=`{stats['topology_matches']}`"
        )
    lines.extend(["", "## What The Current Best Matches"])
    if best is None:
        lines.append("- no candidate evaluated yet")
    else:
        c = best["comparison"]
        lines.extend(
            [
                f"- simplified grid matched exactly: `{c['topology_match']}`",
                f"- vertical masts: `{c['vertical_masts_matched']}` / `{c['vertical_masts_total']}`",
                f"- central rays: `{c['central_rays_matched']}` / `{c['central_rays_total']}`",
                f"- segments: `{c['matched_segments']}` matched, `{c['missing_segments']}` missing, `{c['extra_segments']}` extra",
                f"- angle-class jaccard: `{c['angle_class_jaccard']:.6f}`",
            ]
        )
    path.write_text("\n".join(lines) + "\n")


def append_log(state: dict, path: Path, note: str) -> None:
    prog = progress_summary(state)
    best = state.get("best_grid_match")
    if best is None:
best_text = "no candidates yet"
    else:
        c = best["comparison"]
        best_text = (
            f"{best['spec']['key']} | matched {c['matched_segments']}/11, "
            f"missing {c['missing_segments']}, extra {c['extra_segments']}, "
            f"central {c['central_rays_matched']}/8, masts {c['vertical_masts_matched']}/3"
        )
    entry = f"""
## {now_string()} — generation {state['generation']}
What is counted:
- candidates checked: `{state['visited_count']}` / `{state['total_candidates']}` (`{prog['candidate_progress']:.4f}%`)
- unique topological signatures: `{len(state['unique_topological_signatures'])}`
- topology matches: `{state['topology_match_count']}`
- full target segment matches: `{state['segment_match_count']}`
- projection evaluations: `{state['total_projection_evaluations']}`
- ETA: `{prog['eta_human']}`
Best candidate:
- {best_text}
What does it mean:
- we check whether the resulting mesh matches the simplified one: 3 masts, 8 central rays, 11 segments, 15 nodes and corner classes.
Note:
- {note}
"""
    with path.open("a") as fh:
        fh.write(entry)


def write_best_candidates(state: dict, path: Path) -> None:
    path.write_text(json.dumps(state["best_candidates"], indent=2, ensure_ascii=True))


def write_branch_status(state: dict) -> None:
    BRANCH_DIR.mkdir(parents=True, exist_ok=True)
    result = BRANCH_DIR / "result.md"
    best = state.get("best_grid_match")
    best_text = "No candidates evaluated yet."
    if best is not None:
        c = best["comparison"]
        best_text = (
            f"Current best: `{best['spec']['key']}` with `{c['matched_segments']}/11` target segments, "
            f"`{c['central_rays_matched']}/8` central rays, `{c['vertical_masts_matched']}/3` vertical masts, "
            f"`{c['missing_segments']}` missing and `{c['extra_segments']}` extra."
        )
    result.write_text(
        "# Result\n\n"
        f"Status: {state['status']}\n\n"
        "## Summary\n\n"
        "H12 is implemented as the real polytope-pair double-rotation search against the simplified central-bundle lattice. "
        "Affine grids are not multiplied into the search; topology signatures remove equivalent candidates before any later affine/similarity fit.\n\n"
        "## Current Best\n\n"
        f"{best_text}\n\n"
        "## Live State\n\n"
        "- `research/async_state/h12_polytope_pair/state.json`\n"
        "- `research/async_state/h12_polytope_pair/summary.md`\n"
        "- `research/async_state/h12_polytope_pair/best_candidates.json`\n"
    )


def run_loop(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    summary_path = state_dir / "summary.md"
    log_path = state_dir / "log.md"
    best_path = state_dir / "best_candidates.json"
    if not log_path.exists():
        log_path.write_text("# H12 Search Log\n")
    state = load_state(state_path, args)
    state["status"] = "running"
    if args.kernel_backend == "rust_persistent":
        init_rust_kernel_server()
    rng = np.random.default_rng(int(state["rng_seed"]) + int(state["generation"]))
    start = time.time()
    while state["pending_indices"] and state["generation"] < state["target_generations"]:
        batch_size = state["population_size"] + state["ant_count"]
        batch = choose_batch(state, rng, batch_size)
        if not batch:
            break
        pending_set = set(state["pending_indices"])
        for idx in batch:
            pending_set.discard(idx)
        state["pending_indices"] = sorted(pending_set)
        notes: list[str] = []
        for idx in batch:
            seed = int(state["next_seed"])
            state["next_seed"] += 1
            row = evaluate_candidate(idx, SPECS[idx], state["projection_batch"], seed, state["kernel_backend"])
            update_state_with_result(state, row)
            state["visited_count"] += 1
            state["total_projection_evaluations"] += state["projection_batch"]
        state["generation"] += 1
        state["elapsed_wall_seconds"] += time.time() - start
        start = time.time()
        state["updated_at"] = now_string()
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
        write_summary(state, summary_path)
        write_best_candidates(state, best_path)
        write_branch_status(state)
        if state["generation"] % state["log_every"] == 0:
            append_log(state, log_path, "; ".join(notes) if notes else "regular checkpoint")
        if args.max_candidates is not None and state["visited_count"] >= args.max_candidates:
            state["status"] = "paused"
            break
    if not state["pending_indices"] or state["generation"] >= state["target_generations"]:
        state["status"] = "completed"
    state["updated_at"] = now_string()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
    write_summary(state, summary_path)
    write_best_candidates(state, best_path)
    write_branch_status(state)
    append_log(state, log_path, "final checkpoint for this process run")
    if args.idle_when_complete and state["status"] == "completed":
        append_log(state, log_path, "search completed; service stays alive because Restart=always is used")
        while True:
            time.sleep(3600)
    return 0


def run_count() -> int:
    payload = {
        "source_pairs": len(SOURCE_PAIRS),
        "ratios": len(RATIOS),
        "base_angles": len(BASE_ANGLES_DEG),
        "plane_decompositions": len(PLANE_DECOMPOSITIONS),
        "readout_modes": len(READOUT_MODES),
        "projection_families": dict(PROJECTION_COUNTS),
        "structural_families": len(SOURCE_PAIRS) * len(RATIOS) * len(BASE_ANGLES_DEG) * len(PLANE_DECOMPOSITIONS) * len(READOUT_MODES),
        "projected_candidates": len(SPECS),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


def run_target() -> int:
    print(json.dumps(target_summary(), indent=2, ensure_ascii=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--target-generations", type=int, default=2400)
    parser.add_argument("--population-size", type=int, default=28)
    parser.add_argument("--ant-count", type=int, default=44)
    parser.add_argument("--projection-batch", type=int, default=24)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--kernel-backend", choices=["python", "rust_persistent"], default=configured_kernel_backend())
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--idle-when-complete", action="store_true")
    parser.add_argument("--count", action="store_true")
    parser.add_argument("--target", action="store_true")
    args = parser.parse_args()
    if args.count:
        return run_count()
    if args.target:
        return run_target()
    return run_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
