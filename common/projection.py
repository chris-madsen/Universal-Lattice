#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

import numpy as np


def random_projection(rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(4, 4))
    q, _ = np.linalg.qr(matrix)
    return np.vstack([q[0], q[1]])


def project_points(points4: np.ndarray, projection: np.ndarray) -> np.ndarray:
    return (projection @ points4.T).T


def dedup_points(points: np.ndarray, tol: float = 1e-8) -> Tuple[np.ndarray, Dict[int, int]]:
    key_to_id = {}
    pts = []
    idx_map = {}
    scale = 1.0 / tol
    for i, p in enumerate(points):
        key = (int(round(float(p[0]) * scale)), int(round(float(p[1]) * scale)))
        if key not in key_to_id:
            key_to_id[key] = len(pts)
            pts.append([float(p[0]), float(p[1])])
        idx_map[i] = key_to_id[key]
    return np.array(pts, dtype=float), idx_map


def angle_deg(p1: np.ndarray, p2: np.ndarray) -> float:
    d = p2 - p1
    return (math.degrees(math.atan2(float(d[1]), float(d[0]))) + 180.0) % 180.0


def cluster_angles(angles: Iterable[float], tol: float = 1.5) -> List[float]:
    values = sorted(angles)
    if not values:
        return []
    groups: List[List[float]] = [[values[0]]]
    for value in values[1:]:
        if abs(value - groups[-1][-1]) <= tol:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [sum(group) / len(group) for group in groups]


def projected_edge_signature(points4: np.ndarray, edges4: List[Tuple[int, int]], projection: np.ndarray) -> Dict[str, object]:
    points2 = project_points(points4, projection)
    deduped, idx_map = dedup_points(points2, tol=1e-8)

    pair_set = {}
    zero_edges = 0
    for i, j in edges4:
        u, v = idx_map[i], idx_map[j]
        if u == v:
            zero_edges += 1
            continue
        a, b = (u, v) if u < v else (v, u)
        pair_set[(a, b)] = pair_set.get((a, b), 0) + 1

    angles = []
    for u, v in pair_set.keys():
        angles.append(angle_deg(deduped[u], deduped[v]))

    families = cluster_angles(angles, tol=1.5)
    return {
        "projected_vertex_count": int(len(deduped)),
        "projected_edge_count": int(len(pair_set)),
        "zero_edges": int(zero_edges),
        "absolute_family_count": int(len(families)),
        "family_centers_deg": [float(x) for x in families],
        "projection": [[float(x) for x in row] for row in projection.tolist()],
    }
