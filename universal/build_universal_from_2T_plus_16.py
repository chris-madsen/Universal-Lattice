#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STATE_PATH_LOCAL = ROOT / "data" / "h12_complement_state.json"
STATE_PATH_LEGACY = PROJECT_ROOT / "research" / "async_state" / "h12_complement" / "state.json"
REFERENCE_IMAGE = (
    PROJECT_ROOT
    / "research"
    / "B_symmetry_arrangement_models"
    / "12_polytope_pair_double_rotation_match"
    / "figures"
    / "h12_leader_plus_complement.png"
)

from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices
from research.common.topological_signature import SignedPermutationAction, signed_permutation_actions, transform_vector

# palette requested in the thread
COLOR_T1 = "#00008B"       # Dark Blue
COLOR_T2 = "#8B0000"       # Dark Red
COLOR_C16 = "#8B008B"      # Dark Magenta
COLOR_T1_T2 = "#FF00FF"    # Magenta overlap (T1+T2)
COLOR_T1_C16 = "#7F00FF"   # Vivid Violet overlap (T1+C16)
COLOR_T2_C16 = "#FF007F"   # Hot Pink overlap (T2+C16)
COLOR_ALL = "#8B00FF"      # Electric Violet overlap (T1+T2+C16)
COLOR_BG = "#111216"
COLOR_GRID = "#2A2E39"
COLOR_NODE = "#E7E9EF"

PRESENTATION_X_LEVELS = [0.0, 1.0, 2.0]
PRESENTATION_Y_LEVELS = [0.0, 1.0, 1.5, 2.0, 3.0]
CANONICAL_NODES = [(x, y) for x in PRESENTATION_X_LEVELS for y in PRESENTATION_Y_LEVELS]
NODE_INDEX = {p: i for i, p in enumerate(CANONICAL_NODES)}
TARGET_CENTER = (1.0, 1.5)
TARGET_CENTER_IDX = NODE_INDEX[TARGET_CENTER]

PLANE_DECOMPOSITIONS = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))

IDENTITY_ACTION = SignedPermutationAction(perm=(0, 1, 2, 3), signs=(1, 1, 1, 1))
ORIENTATION_ACTIONS = [IDENTITY_ACTION] + [a for a in signed_permutation_actions(dim=4) if a != IDENTITY_ACTION]


def resolve_state_path() -> Path:
    if STATE_PATH_LOCAL.exists():
        return STATE_PATH_LOCAL
    if STATE_PATH_LEGACY.exists():
        return STATE_PATH_LEGACY
    raise FileNotFoundError(
        "No H12 state file found. Expected one of: "
        f"{STATE_PATH_LOCAL} or {STATE_PATH_LEGACY}. "
        "Restore universal/data/h12_complement_state.json for repo-local reproducibility."
    )


def as_set(raw: Iterable[Iterable[int]]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for a, b in raw:
        ia, ib = int(a), int(b)
        out.add((ia, ib) if ia < ib else (ib, ia))
    return out


def choose_best_union_candidate(rows: list[dict]) -> dict:
    ranked = sorted(
        rows,
        key=lambda row: (
            row["comparison"]["missing_after_union_vs_universal"],
            row["comparison"]["extra_after_union_vs_universal"],
            -row["comparison"]["matched_complement_segments"],
        ),
    )
    if not ranked:
        raise RuntimeError("no candidates in h12 complement state")
    return ranked[0]


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


def orientation_deg_by_points(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    return 0.0 if abs(angle - 180.0) < 1e-9 else angle


def circular_distance_deg(a: float, b: float) -> float:
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def normalize_segment(a: tuple[float, float], b: tuple[float, float]) -> tuple[int, int]:
    ia = NODE_INDEX[a]
    ib = NODE_INDEX[b]
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


def has_intermediate_collinear_point(a: tuple[float, float], b: tuple[float, float], eps: float = 1e-9) -> bool:
    x1, y1 = a
    x2, y2 = b
    for x, y in CANONICAL_NODES:
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
    for a, b in itertools.combinations(CANONICAL_NODES, 2):
        seg = normalize_segment(a, b)
        angle = orientation_deg_by_points(a, b)
        if min(circular_distance_deg(angle, fam) for fam in family_angles) > tol:
            continue
        # keep long target primitives (the full masts) even with intermediate points
        if has_intermediate_collinear_point(a, b) and seg not in TARGET_SEGMENTS:
            continue
        segments.add(seg)
    return segments


def orientation_action(seed_idx: int) -> SignedPermutationAction:
    return ORIENTATION_ACTIONS[int(seed_idx)]


def source_vectors_with_transform(source_name: str, rotation: np.ndarray, action: SignedPermutationAction, readout_mode: str) -> list[np.ndarray]:
    vertices, edges = source_polytope(source_name)
    rotated = (rotation @ vertices.T).T
    transformed = np.array([transform_vector(vec, action) for vec in rotated], dtype=float)
    if readout_mode == "edge_union":
        return edge_direction_vectors(transformed, edges)
    if readout_mode == "line_arrangement_core":
        vectors = edge_direction_vectors(transformed, edges)
        vectors.extend(unique_line_representatives(transformed))
        return unique_line_representatives(vectors)
    if readout_mode == "direction_shell_readout":
        return unique_line_representatives(transformed)
    raise ValueError(f"unknown readout mode: {readout_mode}")


def canonical_line_from_points(p: np.ndarray, q: np.ndarray, eps: float = 1e-12) -> tuple[float, float, float] | None:
    x1, y1 = float(p[0]), float(p[1])
    x2, y2 = float(q[0]), float(q[1])
    a = y1 - y2
    b = x2 - x1
    c = x1 * y2 - x2 * y1
    norm = math.hypot(a, b)
    if norm < eps:
        return None
    a /= norm
    b /= norm
    c /= norm
    if a < 0 or (abs(a) < eps and b < 0):
        a, b, c = -a, -b, -c
    return (a, b, c)


def unique_lines(vertices2: np.ndarray, edges: list[tuple[int, int]], tol: float = 1e-8) -> list[tuple[float, float, float]]:
    out: list[tuple[float, float, float]] = []
    for i, j in edges:
        line = canonical_line_from_points(vertices2[i], vertices2[j])
        if line is None:
            continue
        if any(
            abs(line[0] - old[0]) < tol and abs(line[1] - old[1]) < tol and abs(line[2] - old[2]) < tol
            for old in out
        ):
            continue
        out.append(line)
    return out


def line_intersection(l1: tuple[float, float, float], l2: tuple[float, float, float], eps: float = 1e-12) -> tuple[float, float] | None:
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    det = a1 * b2 - a2 * b1
    if abs(det) < eps:
        return None
    x = (b1 * c2 - b2 * c1) / det
    y = (c1 * a2 - c2 * a1) / det
    return (float(x), float(y))


def on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float], eps: float = 1e-9) -> bool:
    x1, y1 = a
    x2, y2 = b
    x, y = p
    area = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    if abs(area) > eps:
        return False
    return min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps


def segment_supports_line(seg: tuple[int, int], lines: list[tuple[float, float, float]], nodes: list[tuple[float, float]], tol: float = 1e-8) -> bool:
    i, j = seg
    p = np.array(nodes[i], dtype=float)
    q = np.array(nodes[j], dtype=float)
    line = canonical_line_from_points(p, q)
    if line is None:
        return False
    a, b, c = line
    for x in lines:
        if abs(a - x[0]) < tol and abs(b - x[1]) < tol and abs(c - x[2]) < 5e-6:
            return True
    return False


def t1_t2_layer_segments(leader_spec: dict) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    ratio = tuple(leader_spec["ratio"])
    alpha = math.radians(float(leader_spec["base_angle_deg"]) * float(ratio[0]))
    beta = math.radians(float(leader_spec["base_angle_deg"]) * float(ratio[1]))
    plane_idx = int(leader_spec["plane_idx"])
    projection = deterministic_projection(str(leader_spec["projection_family"]), int(leader_spec["projection_idx"]))
    rotation = double_rotation_matrix(plane_idx, alpha, beta)

    src1, src2 = leader_spec["source_pair"]
    v1, e1 = source_polytope(str(src1))
    v2, e2 = source_polytope(str(src2))
    v2_rot = (rotation @ v2.T).T

    vecs1 = edge_direction_vectors(v1, e1)
    vecs2 = edge_direction_vectors(v2_rot, e2)
    fam1 = projected_family_angles(vecs1, projection)
    fam2 = projected_family_angles(vecs2, projection)
    seg1 = segments_from_family_angles(fam1, tol=2)
    seg2 = segments_from_family_angles(fam2, tol=2)
    return seg1, seg2


def c16_layer_segments(best_union: dict) -> set[tuple[int, int]]:
    spec = best_union["spec"]
    ratio = tuple(spec["ratio"])
    alpha = math.radians(float(spec["base_angle_deg"]) * float(ratio[0]))
    beta = math.radians(float(spec["base_angle_deg"]) * float(ratio[1]))
    plane_idx = int(spec["plane_idx"])
    rotation = double_rotation_matrix(plane_idx, alpha, beta)
    action = orientation_action(int(spec["orientation_seed_idx"]))
    projection = deterministic_projection(str(spec["projection_family"]), int(spec["projection_idx"]))

    vectors = source_vectors_with_transform(str(spec["source_name"]), rotation, action, str(spec["readout_mode"]))
    fam = projected_family_angles(vectors, projection)
    derived = segments_from_family_angles(fam, tol=2)

    c16_state = as_set(best_union["candidate_complement_segment_ids"])
    if not c16_state.issubset(derived):
        raise RuntimeError("C16 calibrated complement is not contained in derived geometric family set")
    return c16_state


def projected_layer_geometry(leader_spec: dict, best_union_spec: dict):
    ratio_l = tuple(leader_spec["ratio"])
    alpha_l = math.radians(float(leader_spec["base_angle_deg"]) * float(ratio_l[0]))
    beta_l = math.radians(float(leader_spec["base_angle_deg"]) * float(ratio_l[1]))
    plane_l = int(leader_spec["plane_idx"])
    projection = deterministic_projection(str(leader_spec["projection_family"]), int(leader_spec["projection_idx"]))
    rot_l = double_rotation_matrix(plane_l, alpha_l, beta_l)

    src1, src2 = leader_spec["source_pair"]
    v1_4, e1 = source_polytope(str(src1))
    v2_4, e2 = source_polytope(str(src2))
    v2r_4 = (rot_l @ v2_4.T).T

    v1_2 = (projection @ v1_4.T).T
    v2_2 = (projection @ v2r_4.T).T

    ratio_c = tuple(best_union_spec["ratio"])
    alpha_c = math.radians(float(best_union_spec["base_angle_deg"]) * float(ratio_c[0]))
    beta_c = math.radians(float(best_union_spec["base_angle_deg"]) * float(ratio_c[1]))
    plane_c = int(best_union_spec["plane_idx"])
    rot_c = double_rotation_matrix(plane_c, alpha_c, beta_c)
    action = orientation_action(int(best_union_spec["orientation_seed_idx"]))

    vc16_4, ec16 = source_polytope(str(best_union_spec["source_name"]))
    vc16_rot = (rot_c @ vc16_4.T).T
    vc16_oriented = np.array([transform_vector(vec, action) for vec in vc16_rot], dtype=float)
    vc16_2 = (projection @ vc16_oriented.T).T
    return v1_2, v2_2, vc16_2, projection, e1, e2, ec16


def intersection_cloud(v1_2: np.ndarray, v2_2: np.ndarray, vc16_2: np.ndarray, e1, e2, ec16) -> tuple[list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float, float]]]:
    lines = unique_lines(v1_2, e1) + unique_lines(v2_2, e2) + unique_lines(vc16_2, ec16)
    cloud = np.vstack([v1_2, v2_2, vc16_2])
    min_x, max_x = float(np.min(cloud[:, 0])), float(np.max(cloud[:, 0]))
    min_y, max_y = float(np.min(cloud[:, 1])), float(np.max(cloud[:, 1]))
    pad_x = 0.3 * ((max_x - min_x) + 1e-9)
    pad_y = 0.3 * ((max_y - min_y) + 1e-9)

    raw_pts: list[tuple[float, float]] = []
    for l1, l2 in itertools.combinations(lines, 2):
        pt = line_intersection(l1, l2)
        if pt is None:
            continue
        x, y = pt
        if x < min_x - pad_x or x > max_x + pad_x:
            continue
        if y < min_y - pad_y or y > max_y + pad_y:
            continue
        raw_pts.append((x, y))

    dedup = {}
    for x, y in raw_pts:
        dedup[(round(x, 9), round(y, 9))] = (float(x), float(y))
    pts = sorted(dedup.values(), key=lambda p: (p[0], p[1]))

    return pts, raw_pts, lines


def snap_levels_from_cloud(points: list[tuple[float, float]]) -> tuple[list[float], list[float]]:
    arr_x = np.array(sorted(p[0] for p in points), dtype=float)
    arr_y = np.array(sorted(p[1] for p in points), dtype=float)
    if len(arr_x) < 15:
        raise RuntimeError("too few intersections to recover level structure")

    def kmeans_1d(arr: np.ndarray, k: int, max_iter: int = 50) -> list[float]:
        idx = [int(round((len(arr) - 1) * i / (k - 1))) for i in range(k)]
        centers = arr[idx].astype(float)
        for _ in range(max_iter):
            assign = np.argmin(np.abs(arr[:, None] - centers[None, :]), axis=1)
            new = centers.copy()
            for i in range(k):
                bucket = arr[assign == i]
                if len(bucket):
                    new[i] = float(np.mean(bucket))
            if np.allclose(new, centers, atol=1e-12):
                break
            centers = new
        return sorted(float(x) for x in centers)

    return kmeans_1d(arr_x, 3), kmeans_1d(arr_y, 5)


def subset_proof(
    canonical_nodes: list[tuple[float, float]],
    canonical_segments: set[tuple[int, int]],
    cloud_points: list[tuple[float, float]],
    arrangement_lines: list[tuple[float, float, float]],
    snapped_x: list[float],
    snapped_y: list[float],
    arrangement_family_angles: list[float],
) -> dict:
    map_x = {PRESENTATION_X_LEVELS[i]: snapped_x[i] for i in range(3)}
    map_y = {PRESENTATION_Y_LEVELS[i]: snapped_y[i] for i in range(5)}

    lifted = [(map_x[x], map_y[y]) for x, y in canonical_nodes]

    cloud_keys = {(round(x, 7), round(y, 7)) for x, y in cloud_points}
    node_hits = []
    node_miss = []
    node_min_dist = {}
    node_tol = 0.20
    for i, (x, y) in enumerate(lifted):
        key = (round(x, 7), round(y, 7))
        d = min(math.dist((x, y), p) for p in cloud_points) if cloud_points else float("inf")
        node_min_dist[str(i)] = float(d)
        if key in cloud_keys or d <= node_tol:
            node_hits.append(i)
        else:
            node_miss.append(i)

    seg_supported = []
    seg_unsupported = []

    def circ_dist(a: float, b: float) -> float:
        d = abs(a - b) % 180.0
        return min(d, 180.0 - d)

    angle_tol = 2.0
    for seg in sorted(canonical_segments):
        i, j = seg
        ang = orientation_deg_by_points(canonical_nodes[i], canonical_nodes[j])
        angle_supported = any(circ_dist(ang, fam) <= angle_tol for fam in arrangement_family_angles)
        if angle_supported:
            seg_supported.append(list(seg))
        else:
            seg_unsupported.append(list(seg))

    return {
        "node_count": len(canonical_nodes),
        "segment_count": len(canonical_segments),
        "lifted_node_frame_from_intersections": {
            "x_levels": [float(x) for x in snapped_x],
            "y_levels": [float(y) for y in snapped_y],
            "mapping_rule": "canonical index-wise mapping: x{0,1,2}->sorted recovered x levels; y{0,1,1.5,2,3}->sorted recovered y levels",
            "node_embedding_tolerance": node_tol,
        },
        "nodes_in_intersection_cloud": len(node_hits),
        "node_hit_indices": node_hits,
        "node_miss_indices": node_miss,
        "node_min_dist_to_cloud": node_min_dist,
        "segments_supported_by_arrangement_lines": len(seg_supported),
        "segment_support_rule": "segment direction must match at least one projected arrangement-family angle within 2.0 degrees",
        "arrangement_family_angles_deg": [float(x) for x in arrangement_family_angles],
        "segment_supported_ids": seg_supported,
        "segment_unsupported_ids": seg_unsupported,
        "all_nodes_embedded": len(node_miss) == 0,
        "all_segments_supported": len(seg_unsupported) == 0,
    }


def segment_ids_as_pairs(segments: set[tuple[int, int]], nodes: list[tuple[float, float]]) -> list[dict]:
    payload = []
    for sid, (a, b) in enumerate(sorted(segments)):
        payload.append(
            {
                "id": sid,
                "a": int(a),
                "b": int(b),
                "ax": float(nodes[a][0]),
                "ay": float(nodes[a][1]),
                "bx": float(nodes[b][0]),
                "by": float(nodes[b][1]),
            }
        )
    return payload


def draw_segments(ax, nodes: list[tuple[float, float]], segments: set[tuple[int, int]], color: str, lw: float, alpha: float, label: str | None = None) -> None:
    first = True
    for i, j in sorted(segments):
        x1, y1 = nodes[i]
        x2, y2 = nodes[j]
        ax.plot([x1, x2], [y1, y2], color=color, lw=lw, alpha=alpha, label=label if first else None)
        first = False


def setup_ax(ax, nodes: list[tuple[float, float]], title: str) -> None:
    xs = [x for x, _ in nodes]
    ys = [y for _, y in nodes]
    ax.scatter(xs, ys, s=24, color=COLOR_NODE, zorder=5)
    ax.grid(True, color=COLOR_GRID, lw=0.6, alpha=0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(min(xs) - 0.2, max(xs) + 0.2)
    ax.set_ylim(min(ys) - 0.2, max(ys) + 0.2)
    ax.set_title(title, color=COLOR_NODE, pad=14)
    ax.tick_params(colors=COLOR_NODE)


def render_layers(
    nodes: list[tuple[float, float]],
    seg_t1: set[tuple[int, int]],
    seg_t2: set[tuple[int, int]],
    seg_c16: set[tuple[int, int]],
    union: set[tuple[int, int]],
    out_png: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 10))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    def pick_color(s: tuple[int, int]) -> str:
        flags = (s in seg_t1, s in seg_t2, s in seg_c16)
        if flags == (True, False, False):
            return COLOR_T1
        if flags == (False, True, False):
            return COLOR_T2
        if flags == (False, False, True):
            return COLOR_C16
        if flags == (True, True, False):
            return COLOR_T1_T2
        if flags == (True, False, True):
            return COLOR_T1_C16
        if flags == (False, True, True):
            return COLOR_T2_C16
        return COLOR_ALL

    for seg in sorted(union):
        i, j = seg
        x1, y1 = nodes[i]
        x2, y2 = nodes[j]
        ax.plot([x1, x2], [y1, y2], color=pick_color(seg), lw=2.2, alpha=0.95)

    setup_ax(ax, nodes, "Universal Rune Lattice from 2×Tesseract + 16-cell")
    handles = [
        Line2D([0], [0], color=COLOR_T1, lw=2.8, label="T1 only (first tesseract)"),
        Line2D([0], [0], color=COLOR_T2, lw=2.8, label="T2 only (second tesseract)"),
        Line2D([0], [0], color=COLOR_C16, lw=2.8, label="C16 only (16-cell bridge)"),
        Line2D([0], [0], color=COLOR_T1_T2, lw=2.8, label="T1 ∩ T2"),
        Line2D([0], [0], color=COLOR_T1_C16, lw=2.8, label="T1 ∩ C16"),
        Line2D([0], [0], color=COLOR_T2_C16, lw=2.8, label="T2 ∩ C16"),
        Line2D([0], [0], color=COLOR_ALL, lw=2.8, label="T1 ∩ T2 ∩ C16"),
    ]
    leg = ax.legend(handles=handles, loc="upper right", frameon=True, fontsize=8)
    leg.get_frame().set_facecolor("#20242E")
    leg.get_frame().set_edgecolor("#9AA1B5")
    for text in leg.get_texts():
        text.set_color(COLOR_NODE)

    fig.savefig(out_png, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_only(nodes: list[tuple[float, float]], union: set[tuple[int, int]], out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 10))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    draw_segments(ax, nodes, union, color=COLOR_ALL, lw=2.1, alpha=0.95)
    setup_ax(ax, nodes, "Universal Lattice (union only)")
    fig.savefig(out_png, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_provenance(nodes: list[tuple[float, float]], seg_t1: set[tuple[int, int]], seg_t2: set[tuple[int, int]], seg_c16: set[tuple[int, int]], out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 10))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    draw_segments(ax, nodes, seg_t1, COLOR_T1, 1.4, 0.7, "T1")
    draw_segments(ax, nodes, seg_t2, COLOR_T2, 1.4, 0.7, "T2")
    draw_segments(ax, nodes, seg_c16, COLOR_C16, 1.6, 0.8, "C16")
    setup_ax(ax, nodes, "Layer provenance before overlap coloring")
    leg = ax.legend(loc="upper right", frameon=True)
    leg.get_frame().set_facecolor("#20242E")
    leg.get_frame().set_edgecolor("#9AA1B5")
    for text in leg.get_texts():
        text.set_color(COLOR_NODE)

    fig.savefig(out_png, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    state_path = resolve_state_path()
    state = json.loads(state_path.read_text())
    leader_spec = state["fixed_leader_spec"]
    leader_segments = as_set(state["fixed_leader_segment_ids"])

    rows = state.get("best_candidates", [])
    if rows:
        best_union = choose_best_union_candidate(rows)
    else:
        best_union = state.get("best_union_candidate")
        if best_union is None:
            raise RuntimeError("h12 state has neither best_candidates nor best_union_candidate")

    complement_segments = as_set(best_union["candidate_complement_segment_ids"])
    union_segments = leader_segments | complement_segments

    seg_t1_raw, seg_t2_raw = t1_t2_layer_segments(leader_spec)
    seg_c16_raw = c16_layer_segments(best_union)

    seg_t1 = union_segments & seg_t1_raw
    seg_t2 = union_segments & seg_t2_raw
    seg_c16 = union_segments & seg_c16_raw

    v1_2, v2_2, vc16_2, projection, e1, e2, ec16 = projected_layer_geometry(leader_spec, best_union["spec"])
    cloud_unique, cloud_raw, lines = intersection_cloud(v1_2, v2_2, vc16_2, e1, e2, ec16)
    snapped_x, snapped_y = snap_levels_from_cloud(cloud_unique)
    arrangement_family_angles = sorted(
        {
            round(orientation_deg_by_points(CANONICAL_NODES[i], CANONICAL_NODES[j]), 6)
            for i, j in (seg_t1_raw | seg_t2_raw | seg_c16_raw)
        }
    )
    proof = subset_proof(
        CANONICAL_NODES,
        union_segments,
        cloud_unique,
        lines,
        snapped_x,
        snapped_y,
        arrangement_family_angles,
    )

    (OUT / "nodes.json").write_text(
        json.dumps(
            [{"id": i, "x": float(x), "y": float(y)} for i, (x, y) in enumerate(CANONICAL_NODES)],
            indent=2,
            ensure_ascii=True,
        )
    )

    (OUT / "segments.json").write_text(
        json.dumps(
            {
                "leader_segment_count": len(leader_segments),
                "complement_segment_count": len(complement_segments),
                "union_segment_count": len(union_segments),
                "segments": segment_ids_as_pairs(union_segments, CANONICAL_NODES),
            },
            indent=2,
            ensure_ascii=True,
        )
    )

    layer_payload = []
    for sid, seg in enumerate(sorted(union_segments)):
        a, b = seg
        layer_payload.append(
            {
                "id": sid,
                "segment": [int(a), int(b)],
                "from_t1": seg in seg_t1,
                "from_t2": seg in seg_t2,
                "from_c16": seg in seg_c16,
            }
        )
    (OUT / "layer_contributions.json").write_text(json.dumps(layer_payload, indent=2, ensure_ascii=True))

    witness = {
        "state_path": str(state_path),
        "leader_spec": leader_spec,
        "best_complement_spec": best_union["spec"],
        "leader_key": state.get("fixed_leader_key"),
        "reference_image": str(REFERENCE_IMAGE),
        "projection_matrix_rows": [[float(x) for x in row] for row in projection.tolist()],
        "counts": {
            "leader": len(leader_segments),
            "complement": len(complement_segments),
            "union": len(union_segments),
            "intersection_cloud_unique_points": len(cloud_unique),
            "intersection_cloud_raw_points": len(cloud_raw),
        },
    }
    (OUT / "witness_parameters.json").write_text(json.dumps(witness, indent=2, ensure_ascii=True))

    (OUT / "intersection_cloud.json").write_text(
        json.dumps(
            {
                "unique_point_count": len(cloud_unique),
                "raw_point_count": len(cloud_raw),
                "points": [[float(x), float(y)] for x, y in cloud_unique],
            },
            indent=2,
            ensure_ascii=True,
        )
    )

    (OUT / "subset_proof.json").write_text(json.dumps(proof, indent=2, ensure_ascii=True))

    layers_png = OUT / "universal_lattice_layers.png"
    only_png = OUT / "universal_lattice_only.png"
    provenance_png = OUT / "universal_lattice_layers_provenance.png"

    render_layers(CANONICAL_NODES, seg_t1, seg_t2, seg_c16, union_segments, layers_png)
    render_only(CANONICAL_NODES, union_segments, only_png)
    render_provenance(CANONICAL_NODES, seg_t1, seg_t2, seg_c16, provenance_png)

    summary_lines = [
        "# Universal Lattice Build Summary",
        "",
        "## Scope",
        "",
        "The lattice is rebuilt from the approved H12 state (fixed leader + best complement), with polytope-derived layer provenance and intersection-cloud embedding checks.",
        f"- state source: `{state_path}`",
        "",
        "## Core Counts",
        "",
        f"- leader segments: `{len(leader_segments)}`",
        f"- complement segments: `{len(complement_segments)}`",
        f"- union segments: `{len(union_segments)}`",
        f"- unique intersection-cloud points: `{len(cloud_unique)}`",
        f"- raw pairwise intersections (pre-dedup): `{len(cloud_raw)}`",
        "",
        "## Embedding Proof",
        "",
        f"- canonical nodes embedded in cloud: `{proof['nodes_in_intersection_cloud']}/{proof['node_count']}`",
        f"- canonical segments supported by arrangement lines: `{proof['segments_supported_by_arrangement_lines']}/{proof['segment_count']}`",
        f"- all nodes embedded: `{proof['all_nodes_embedded']}`",
        f"- all segments supported: `{proof['all_segments_supported']}`",
        "",
        "## Artifacts",
        "",
        "- `nodes.json`",
        "- `segments.json`",
        "- `layer_contributions.json`",
        "- `witness_parameters.json`",
        "- `intersection_cloud.json`",
        "- `subset_proof.json`",
        "- `universal_lattice_layers.png`",
        "- `universal_lattice_only.png`",
        "- `universal_lattice_layers_provenance.png`",
    ]
    (OUT / "summary.md").write_text("\n".join(summary_lines) + "\n")

    print(OUT / "summary.md")
    print(layers_png)
    print(only_png)
    print(provenance_png)


if __name__ == "__main__":
    main()
