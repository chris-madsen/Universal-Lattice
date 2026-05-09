#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.async_jobs.h12_polytope_pair_search import (
    BASE_ANGLES_DEG,
    PLANE_DECOMPOSITIONS,
    PROJECTION_COUNTS,
    PROJECTION_FAMILIES,
    RATIOS,
    READOUT_MODES,
    angle_mod_180,
    candidate_vectors,
    deterministic_projection,
    double_rotation_matrix,
    edge_direction_vectors,
    projected_family_angles,
    segments_from_family_angles,
    source_polytope,
    topology_signature_for_segments,
    unique_line_representatives,
)
from research.common.family_kernel import (
    configured_kernel_backend,
    evaluate_vectors_python,
    evaluate_vectors_rust_persistent,
    init_rust_kernel_server,
)
from research.common.meta_search import humanize_duration_hm, low_pass_harmonic_prior_from_matrix, now_string
from research.common.topological_signature import SignedPermutationAction, signed_permutation_actions, transform_vector

STATE_VERSION = 1
DEFAULT_STATE_DIR = ROOT / "research" / "async_state" / "h12_complement"
BRANCH_DIR = ROOT / "research" / "B_symmetry_arrangement_models" / "12_polytope_pair_double_rotation_match"
LEADER_STATE_PATH = ROOT / "research" / "async_state" / "h12_polytope_pair" / "best_candidates.json"
LEADER_KEY = "T-T|r1:2|a22.5|p0|edge_union|central_bundle:3"
DEFAULT_POPULATION = 28
DEFAULT_ANTS = 44
DEFAULT_PROJECTION_BATCH = 96
DEFAULT_LOG_EVERY = 5
DEFAULT_TOPOLOGY_MAX_EVALS = 1
DEFAULT_KERNEL_BACKEND = configured_kernel_backend()

XS = (0.0, 1.0, 2.0)
YS = (0.0, 1.0, 1.5, 2.0, 3.0)
TARGET_NODE_ORDER = [(x, y) for x in XS for y in YS]
TARGET_NODE_INDEX = {p: i for i, p in enumerate(TARGET_NODE_ORDER)}


@dataclass(frozen=True)
class ComplementSpec:
    stage_name: str
    source_name: str
    ratio: tuple[int, int]
    base_angle_deg: float
    plane_idx: int
    readout_mode: str
    projection_family: str
    projection_idx: int
    orientation_seed_idx: int

    @property
    def key(self) -> str:
        return (
            f"{self.stage_name}|{self.source_name}|r{self.ratio[0]}:{self.ratio[1]}|"
            f"a{self.base_angle_deg:g}|p{self.plane_idx}|{self.readout_mode}|"
            f"{self.projection_family}:{self.projection_idx}|o{self.orientation_seed_idx}"
        )


def normalize_segment(a: tuple[float, float], b: tuple[float, float]) -> tuple[int, int]:
    ia = TARGET_NODE_INDEX[a]
    ib = TARGET_NODE_INDEX[b]
    return (ia, ib) if ia < ib else (ib, ia)


def on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float], eps: float = 1e-9) -> bool:
    (x1, y1), (x2, y2) = a, b
    x, y = p
    area = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    if abs(area) > eps:
        return False
    return min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps


def tparam(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]) -> float:
    (x1, y1), (x2, y2) = a, b
    x, y = p
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) >= abs(dy):
        return 0.0 if abs(dx) < 1e-12 else (x - x1) / dx
    return 0.0 if abs(dy) < 1e-12 else (y - y1) / dy


def segmentize(lines: list[tuple[tuple[float, float], tuple[float, float]]]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for a, b in lines:
        col = [p for p in TARGET_NODE_ORDER if on_segment(a, b, p)]
        col.sort(key=lambda p: tparam(a, b, p))
        for p, q in zip(col, col[1:]):
            i = TARGET_NODE_INDEX[p]
            j = TARGET_NODE_INDEX[q]
            if i != j:
                out.add((i, j) if i < j else (j, i))
    return out


def simplified_segments() -> set[tuple[int, int]]:
    center = (1.0, 1.5)
    rays = (
        (0.0, 0.0),
        (0.0, 1.0),
        (0.0, 2.0),
        (0.0, 3.0),
        (2.0, 0.0),
        (2.0, 1.0),
        (2.0, 2.0),
        (2.0, 3.0),
    )
    segments: set[tuple[int, int]] = set()
    for x in XS:
        segments.add(normalize_segment((x, 0.0), (x, 3.0)))
    for p in rays:
        segments.add(normalize_segment(center, p))
    return segments


def universal_segments() -> set[tuple[int, int]]:
    lines: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for x in XS:
        lines.append(((x, 0.0), (x, 3.0)))
    for ty in (0.0, 1.0, 1.5, 2.0):
        lines.append(((0.0, 3.0), (2.0, ty)))
    for ty in (0.0, 1.0, 1.5, 2.0):
        lines.append(((2.0, 3.0), (0.0, ty)))
    for ty in (1.0, 1.5, 2.0, 3.0):
        lines.append(((0.0, 0.0), (2.0, ty)))
    for ty in (1.0, 1.5, 2.0, 3.0):
        lines.append(((2.0, 0.0), (0.0, ty)))
    for p in ((0.0, 2.0), (2.0, 2.0), (0.0, 1.5), (2.0, 1.5)):
        lines.append(((1.0, 3.0), p))
    for p in ((0.0, 1.0), (2.0, 1.0), (0.0, 1.5), (2.0, 1.5)):
        lines.append(((1.0, 0.0), p))
    lines.append(((0.0, 1.0), (2.0, 2.0)))
    lines.append(((2.0, 1.0), (0.0, 2.0)))
    return segmentize(lines)


def segment_angles(segments: set[tuple[int, int]]) -> list[float]:
    angles = set()
    for i, j in segments:
        (x1, y1), (x2, y2) = TARGET_NODE_ORDER[i], TARGET_NODE_ORDER[j]
        angles.add(round((math.degrees(math.atan2(y2 - y1, x2 - x1)) + 180.0) % 180.0, 6))
    return sorted(angles)


def angle_jaccard(a: set[tuple[int, int]], b: set[tuple[int, int]]) -> float:
    sa = set(segment_angles(a))
    sb = set(segment_angles(b))
    return len(sa & sb) / len(sa | sb) if sa or sb else 1.0


def node_coverage(segments: set[tuple[int, int]]) -> int:
    covered = set()
    for i, j in segments:
        covered.add(i)
        covered.add(j)
    return len(covered)


def load_leader_record() -> dict:
    rows = json.loads(LEADER_STATE_PATH.read_text())
    for row in rows:
        if row.get("spec", {}).get("key") == LEADER_KEY:
            return row
    if not rows:
        raise RuntimeError(f"empty leader state: {LEADER_STATE_PATH}")
    return rows[0]


def projection_entries_all() -> list[tuple[str, int]]:
    entries: list[tuple[str, int]] = []
    for family in PROJECTION_FAMILIES:
        for idx in range(PROJECTION_COUNTS[family]):
            entries.append((family, idx))
    return entries


IDENTITY_ACTION = SignedPermutationAction(perm=(0, 1, 2, 3), signs=(1, 1, 1, 1))
ORIENTATION_ACTIONS = [IDENTITY_ACTION] + [a for a in signed_permutation_actions(dim=4) if a != IDENTITY_ACTION]

LEADER_RECORD = load_leader_record()
LEADER_SEGMENTS = {tuple(seg) for seg in LEADER_RECORD["segment_ids"]}
SIMPLIFIED_SEGMENTS = simplified_segments()
UNIVERSAL_SEGMENTS = universal_segments()
MISSING_SEGMENTS = UNIVERSAL_SEGMENTS - LEADER_SEGMENTS
MISSING_ANGLE_CLASSES = segment_angles(MISSING_SEGMENTS)

LEADER_SPEC_DICT = LEADER_RECORD["spec"]
LEADER_SPEC = type("LeaderPairSpec", (), {})()
LEADER_SPEC.source_pair = tuple(LEADER_SPEC_DICT["source_pair"])
LEADER_SPEC.ratio = tuple(LEADER_SPEC_DICT["ratio"])
LEADER_SPEC.base_angle_deg = float(LEADER_SPEC_DICT["base_angle_deg"])
LEADER_SPEC.plane_idx = int(LEADER_SPEC_DICT["plane_idx"])
LEADER_SPEC.readout_mode = str(LEADER_SPEC_DICT["readout_mode"])
LEADER_SPEC.projection_family = str(LEADER_SPEC_DICT["projection_family"])
LEADER_SPEC.projection_idx = int(LEADER_SPEC_DICT["projection_idx"])
LEADER_VECTORS = candidate_vectors(LEADER_SPEC)
LEADER_PROJECTION = deterministic_projection(LEADER_SPEC.projection_family, LEADER_SPEC.projection_idx)


def orientation_action(seed_idx: int) -> SignedPermutationAction:
    return ORIENTATION_ACTIONS[seed_idx]


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


def build_base_stages() -> list[dict]:
    fixed_projection = [(LEADER_SPEC.projection_family, LEADER_SPEC.projection_idx)]
    return [
        {"name": "A16_base", "source_name": "16", "readout_modes": ["edge_union"], "projection_entries": fixed_projection, "orientation_limit": 1},
        {"name": "A16_readout", "source_name": "16", "readout_modes": list(READOUT_MODES), "projection_entries": fixed_projection, "orientation_limit": 1},
        {"name": "A16_projection", "source_name": "16", "readout_modes": list(READOUT_MODES), "projection_entries": projection_entries_all(), "orientation_limit": 1},
        {"name": "BT_base", "source_name": "T", "readout_modes": ["edge_union"], "projection_entries": fixed_projection, "orientation_limit": 1},
        {"name": "BT_readout", "source_name": "T", "readout_modes": list(READOUT_MODES), "projection_entries": fixed_projection, "orientation_limit": 1},
        {"name": "BT_projection", "source_name": "T", "readout_modes": list(READOUT_MODES), "projection_entries": projection_entries_all(), "orientation_limit": 1},
    ]


def build_orientation_stage(source_name: str, limit: int) -> dict:
    return {
        "name": f"C{source_name}_seed{limit}",
        "source_name": source_name,
        "readout_modes": list(READOUT_MODES),
        "projection_entries": projection_entries_all(),
        "orientation_limit": limit,
    }


def stage_total(stage: dict) -> int:
    return (
        len(RATIOS)
        * len(BASE_ANGLES_DEG)
        * len(PLANE_DECOMPOSITIONS)
        * len(stage["readout_modes"])
        * len(stage["projection_entries"])
        * int(stage["orientation_limit"])
    )


def stage_spec_from_index(stage: dict, index: int) -> ComplementSpec:
    orientation_limit = int(stage["orientation_limit"])
    projection_entries = list(stage["projection_entries"])
    readout_modes = list(stage["readout_modes"])

    orientation_idx = index % orientation_limit
    index //= orientation_limit
    projection_idx_local = index % len(projection_entries)
    index //= len(projection_entries)
    readout_idx = index % len(readout_modes)
    index //= len(readout_modes)
    plane_idx = index % len(PLANE_DECOMPOSITIONS)
    index //= len(PLANE_DECOMPOSITIONS)
    angle_idx = index % len(BASE_ANGLES_DEG)
    index //= len(BASE_ANGLES_DEG)
    ratio_idx = index % len(RATIOS)
    family, projection_idx = projection_entries[projection_idx_local]
    return ComplementSpec(
        stage_name=str(stage["name"]),
        source_name=str(stage["source_name"]),
        ratio=tuple(RATIOS[ratio_idx]),
        base_angle_deg=float(BASE_ANGLES_DEG[angle_idx]),
        plane_idx=int(plane_idx),
        readout_mode=str(readout_modes[readout_idx]),
        projection_family=str(family),
        projection_idx=int(projection_idx),
        orientation_seed_idx=int(orientation_idx),
    )


def stage_index_from_spec(stage: dict, spec: ComplementSpec) -> int | None:
    try:
        ratio_idx = RATIOS.index(tuple(spec.ratio))
        angle_idx = BASE_ANGLES_DEG.index(float(spec.base_angle_deg))
        plane_idx = int(spec.plane_idx)
        readout_idx = list(stage["readout_modes"]).index(spec.readout_mode)
        projection_idx_local = list(stage["projection_entries"]).index((spec.projection_family, spec.projection_idx))
    except ValueError:
        return None
    if not (0 <= spec.orientation_seed_idx < int(stage["orientation_limit"])):
        return None
    total = ratio_idx
    total = total * len(BASE_ANGLES_DEG) + angle_idx
    total = total * len(PLANE_DECOMPOSITIONS) + plane_idx
    total = total * len(stage["readout_modes"]) + readout_idx
    total = total * len(stage["projection_entries"]) + projection_idx_local
    total = total * int(stage["orientation_limit"]) + int(spec.orientation_seed_idx)
    return total


def initial_stage_pheromone(stage: dict) -> dict:
    angle_matrix = np.array([[1.0 if angle in (15.0, 22.5, 30.0, 36.0, 45.0) else 0.45 for angle in BASE_ANGLES_DEG]], dtype=float)
    smooth = low_pass_harmonic_prior_from_matrix(angle_matrix, keep_rows=1, keep_cols=4, floor=0.1)[0]
    angle_pheromone = {f"{angle:g}": float(weight) for angle, weight in zip(BASE_ANGLES_DEG, smooth)}
    ratio_pheromone = {f"{a}:{b}": (1.5 if (a, b) in ((1, 1), (1, 2), (2, 3), (1, 4)) else 1.0) for a, b in RATIOS}
    plane_pheromone = {str(i): 1.0 for i in range(len(PLANE_DECOMPOSITIONS))}
    readout_pheromone = {}
    for mode in stage["readout_modes"]:
        if mode == "edge_union":
            readout_pheromone[mode] = 1.6
        elif mode == "line_arrangement_core":
            readout_pheromone[mode] = 1.25
        else:
            readout_pheromone[mode] = 1.0
    projection_pheromone = {}
    for family, _ in stage["projection_entries"]:
        if family == LEADER_SPEC.projection_family:
            projection_pheromone.setdefault(family, 1.5)
        elif family == "central_bundle":
            projection_pheromone.setdefault(family, 1.25)
        elif family == "coxeter_f4":
            projection_pheromone.setdefault(family, 1.1)
        else:
            projection_pheromone.setdefault(family, 1.0)
    orientation_pheromone = {str(i): (1.5 if i == 0 else 1.0 / math.sqrt(i + 1)) for i in range(int(stage["orientation_limit"]))}
    return {
        "angle": angle_pheromone,
        "ratio": ratio_pheromone,
        "plane": plane_pheromone,
        "readout": readout_pheromone,
        "projection": projection_pheromone,
        "orientation": orientation_pheromone,
    }


def candidate_weight(spec: ComplementSpec, pheromone: dict[str, dict[str, float]]) -> float:
    return (
        pheromone["angle"].get(f"{spec.base_angle_deg:g}", 1.0)
        * pheromone["ratio"].get(f"{spec.ratio[0]}:{spec.ratio[1]}", 1.0)
        * pheromone["plane"].get(str(spec.plane_idx), 1.0)
        * pheromone["readout"].get(spec.readout_mode, 1.0)
        * pheromone["projection"].get(spec.projection_family, 1.0)
        * pheromone["orientation"].get(str(spec.orientation_seed_idx), 1.0)
    )


def update_stage_pheromone(pheromone: dict[str, dict[str, float]], spec: ComplementSpec, score: float) -> None:
    deposit = max(0.0, min(2.5, score / 600.0))
    keys = [
        ("angle", f"{spec.base_angle_deg:g}"),
        ("ratio", f"{spec.ratio[0]}:{spec.ratio[1]}"),
        ("plane", str(spec.plane_idx)),
        ("readout", spec.readout_mode),
        ("projection", spec.projection_family),
        ("orientation", str(spec.orientation_seed_idx)),
    ]
    for group, key in keys:
        pheromone[group][key] = 0.995 * pheromone[group].get(key, 1.0) + deposit


def neighbor_indices(stage: dict, spec: ComplementSpec) -> list[int]:
    out: list[int] = []
    angle_pos = BASE_ANGLES_DEG.index(spec.base_angle_deg)
    for delta in (-1, 1):
        pos = angle_pos + delta
        if 0 <= pos < len(BASE_ANGLES_DEG):
            idx = stage_index_from_spec(
                stage,
                ComplementSpec(
                    stage_name=spec.stage_name,
                    source_name=spec.source_name,
                    ratio=spec.ratio,
                    base_angle_deg=BASE_ANGLES_DEG[pos],
                    plane_idx=spec.plane_idx,
                    readout_mode=spec.readout_mode,
                    projection_family=spec.projection_family,
                    projection_idx=spec.projection_idx,
                    orientation_seed_idx=spec.orientation_seed_idx,
                ),
            )
            if idx is not None:
                out.append(idx)
    for plane_idx in range(len(PLANE_DECOMPOSITIONS)):
        if plane_idx == spec.plane_idx:
            continue
        idx = stage_index_from_spec(
            stage,
            ComplementSpec(
                stage_name=spec.stage_name,
                source_name=spec.source_name,
                ratio=spec.ratio,
                base_angle_deg=spec.base_angle_deg,
                plane_idx=plane_idx,
                readout_mode=spec.readout_mode,
                projection_family=spec.projection_family,
                projection_idx=spec.projection_idx,
                orientation_seed_idx=spec.orientation_seed_idx,
            ),
        )
        if idx is not None:
            out.append(idx)
    for mode in stage["readout_modes"]:
        if mode == spec.readout_mode:
            continue
        idx = stage_index_from_spec(
            stage,
            ComplementSpec(
                stage_name=spec.stage_name,
                source_name=spec.source_name,
                ratio=spec.ratio,
                base_angle_deg=spec.base_angle_deg,
                plane_idx=spec.plane_idx,
                readout_mode=mode,
                projection_family=spec.projection_family,
                projection_idx=spec.projection_idx,
                orientation_seed_idx=spec.orientation_seed_idx,
            ),
        )
        if idx is not None:
            out.append(idx)
    if int(stage["orientation_limit"]) > 1:
        for delta in (-1, 1):
            pos = spec.orientation_seed_idx + delta
            if 0 <= pos < int(stage["orientation_limit"]):
                idx = stage_index_from_spec(
                    stage,
                    ComplementSpec(
                        stage_name=spec.stage_name,
                        source_name=spec.source_name,
                        ratio=spec.ratio,
                        base_angle_deg=spec.base_angle_deg,
                        plane_idx=spec.plane_idx,
                        readout_mode=spec.readout_mode,
                        projection_family=spec.projection_family,
                        projection_idx=spec.projection_idx,
                        orientation_seed_idx=pos,
                    ),
                )
                if idx is not None:
                    out.append(idx)
    return out


def complement_signature_payload(union_segments: set[tuple[int, int]], complement_segments: set[tuple[int, int]]) -> str:
    payload = {
        "union": topology_signature_for_segments(union_segments),
        "complement_edges": sorted([list(seg) for seg in complement_segments]),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def spec_to_json(spec: ComplementSpec) -> dict:
    return {
        "stage_name": spec.stage_name,
        "source_name": spec.source_name,
        "ratio": list(spec.ratio),
        "base_angle_deg": spec.base_angle_deg,
        "plane_idx": spec.plane_idx,
        "plane_decomposition": [list(x) for x in PLANE_DECOMPOSITIONS[spec.plane_idx]],
        "readout_mode": spec.readout_mode,
        "projection_family": spec.projection_family,
        "projection_idx": spec.projection_idx,
        "orientation_seed_idx": spec.orientation_seed_idx,
        "key": spec.key,
    }


def complexity_score(spec: ComplementSpec, stage: dict) -> float:
    score = 0.0
    if spec.readout_mode == "line_arrangement_core":
        score += 1.0
    elif spec.readout_mode == "direction_shell_readout":
        score += 1.5
    if len(stage["projection_entries"]) > 1:
        score += 1.25
    if int(stage["orientation_limit"]) > 1:
        score += 1.5 + math.log2(spec.orientation_seed_idx + 1.0)
    return score


def source_stage_rank(source_name: str) -> int:
    return 0 if source_name == "16" else 1


def evaluate_candidate_geometry(spec: ComplementSpec, stage: dict) -> dict:
    alpha = math.radians(spec.base_angle_deg * spec.ratio[0])
    beta = math.radians(spec.base_angle_deg * spec.ratio[1])
    rotation = double_rotation_matrix(spec.plane_idx, alpha, beta)
    action = orientation_action(spec.orientation_seed_idx)
    added_vectors = source_vectors_with_transform(spec.source_name, rotation, action, spec.readout_mode)
    union_vectors = unique_line_representatives(LEADER_VECTORS + added_vectors)
    projection = deterministic_projection(spec.projection_family, spec.projection_idx)
    family_angles = projected_family_angles(union_vectors, projection)
    union_segments = segments_from_family_angles(family_angles)
    candidate_complement = union_segments - LEADER_SEGMENTS

    matched_complement = len(candidate_complement & MISSING_SEGMENTS)
    missing_complement = len(MISSING_SEGMENTS - candidate_complement)
    extra_complement = len(candidate_complement - MISSING_SEGMENTS)
    union_missing = len(UNIVERSAL_SEGMENTS - union_segments)
    union_extra = len(union_segments - UNIVERSAL_SEGMENTS)
    leader_missing = len(LEADER_SEGMENTS - union_segments)
    nodes_used = node_coverage(union_segments)
    complement_angle_match = angle_jaccard(candidate_complement, MISSING_SEGMENTS)
    union_angle_match = angle_jaccard(union_segments, UNIVERSAL_SEGMENTS)
    exact_complement = missing_complement == 0 and extra_complement == 0
    exact_union = union_missing == 0 and union_extra == 0
    complexity = complexity_score(spec, stage)

    score = (
        700.0 * (matched_complement / max(1, len(MISSING_SEGMENTS)))
        + 250.0 * ((len(LEADER_SEGMENTS) - leader_missing) / max(1, len(LEADER_SEGMENTS)))
        + 220.0 * (nodes_used / len(TARGET_NODE_ORDER))
        + 180.0 * complement_angle_match
        + 120.0 * union_angle_match
        - 35.0 * missing_complement
        - 10.0 * extra_complement
        - 45.0 * leader_missing
        - 15.0 * union_missing
        - 4.0 * union_extra
        - 20.0 * complexity
    )
    if exact_complement:
        score += 4000.0
    if exact_union:
        score += 5000.0

    return {
        "spec": spec_to_json(spec),
        "source_name": spec.source_name,
        "topological_signature": complement_signature_payload(union_segments, candidate_complement),
        "family_angles_deg": [round(float(x), 6) for x in family_angles],
        "union_segment_ids": sorted([list(seg) for seg in union_segments]),
        "candidate_complement_segment_ids": sorted([list(seg) for seg in candidate_complement]),
        "score_pre_kernel": score,
        "comparison": {
            "matched_complement_segments": matched_complement,
            "missing_complement_segments": missing_complement,
            "extra_complement_segments": extra_complement,
            "matched_after_union": len(union_segments & UNIVERSAL_SEGMENTS),
            "missing_after_union_vs_universal": union_missing,
            "extra_after_union_vs_universal": union_extra,
            "leader_missing_after_union": leader_missing,
            "node_coverage": nodes_used,
            "node_coverage_ratio": nodes_used / len(TARGET_NODE_ORDER),
            "angle_class_match": complement_angle_match,
            "union_angle_class_match": union_angle_match,
            "candidate_segment_count": len(candidate_complement),
            "union_segment_count": len(union_segments),
            "description_complexity": complexity,
            "exact_complement": exact_complement,
            "exact_union": exact_union,
        },
        "union_segments_set": union_segments,
        "candidate_complement_set": candidate_complement,
        "union_vectors": union_vectors,
    }


def complete_candidate(row: dict, projection_batch: int, seed: int, kernel_backend: str) -> dict:
    union_vectors = row.pop("union_vectors")
    if kernel_backend == "rust_persistent":
        family_stability = evaluate_vectors_rust_persistent(union_vectors, projection_batch=projection_batch, seed=seed)
    else:
        family_stability = evaluate_vectors_python(union_vectors, projection_batch=projection_batch, seed=seed)
    score = float(row["score_pre_kernel"]) + 35.0 * float(family_stability.get("family5_rate", 0.0)) + 200.0 * float(
        family_stability.get("exact_rate", 0.0)
    )
    row["family_stability"] = family_stability
    row["score"] = score
    row["evaluation_seed"] = seed
    row["kernel_backend_used"] = kernel_backend
    row["union_segments_set"] = sorted([list(seg) for seg in row.pop("union_segments_set")])
    row["candidate_complement_set"] = sorted([list(seg) for seg in row.pop("candidate_complement_set")])
    return row


def stage_summary_row(name: str, stats: dict | None) -> str:
    if not stats or not stats.get("best"):
        return f"- `{name}`: no evaluated candidates yet"
    best = stats["best"]
    comp = best["comparison"]
    return (
        f"- `{name}`: checked=`{stats['checked_count']}`, exact_complement=`{stats['exact_complement_count']}`, "
        f"exact_union=`{stats['exact_union_count']}`, best=`{best['spec']['key']}` "
        f"(match=`{comp['matched_complement_segments']}/{len(MISSING_SEGMENTS)}`, "
        f"missing=`{comp['missing_after_union_vs_universal']}`, extra=`{comp['extra_after_union_vs_universal']}`)"
    )


def initialize_state(args: argparse.Namespace) -> dict:
    stages = build_base_stages()
    first_stage = stages[0]
    return {
        "version": STATE_VERSION,
        "status": "created",
        "created_at": now_string(),
        "updated_at": now_string(),
        "kernel_backend": str(args.kernel_backend),
        "population_size": int(args.population_size),
        "ant_count": int(args.ant_count),
        "projection_batch": int(args.projection_batch),
        "log_every": int(args.log_every),
        "topology_max_evals_per_signature": int(args.topology_max_evals_per_signature),
        "fixed_leader_key": LEADER_KEY,
        "fixed_leader_spec": LEADER_SPEC_DICT,
        "fixed_leader_segment_ids": sorted([list(seg) for seg in LEADER_SEGMENTS]),
        "universal_segment_ids": sorted([list(seg) for seg in UNIVERSAL_SEGMENTS]),
        "missing_segment_ids": sorted([list(seg) for seg in MISSING_SEGMENTS]),
        "missing_segment_xy": [[list(TARGET_NODE_ORDER[i]), list(TARGET_NODE_ORDER[j])] for i, j in sorted(MISSING_SEGMENTS)],
        "missing_angle_classes_deg": MISSING_ANGLE_CLASSES,
        "stages": stages,
        "current_stage_index": 0,
        "current_stage_generation": 0,
        "current_stage_pending_indices": list(range(stage_total(first_stage))),
        "current_stage_total_candidates": stage_total(first_stage),
        "current_stage_pheromone": initial_stage_pheromone(first_stage),
        "current_stage_population": [],
        "orientation_stages_appended": False,
        "stage_results": {},
        "total_candidates_checked": 0,
        "total_candidates_evaluated": 0,
        "total_projection_evaluations": 0,
        "topology_filtered_batch_equivalent_total": 0,
        "topology_filtered_signature_cap_total": 0,
        "unique_topological_signatures": {},
        "exact_complement_matches": 0,
        "exact_union_matches": 0,
        "elapsed_wall_seconds": 0.0,
        "next_seed": 4400001,
        "best_complement_candidate": None,
        "best_union_candidate": None,
        "best_source_candidates": {"16": None, "T": None},
        "best_candidates": [],
    }


def load_state(path: Path, args: argparse.Namespace) -> dict:
    if path.exists():
        state = json.loads(path.read_text())
        if state.get("version") != STATE_VERSION:
            raise RuntimeError(f"state version mismatch in {path}")
        for stage in state.get("stages", []):
            stage["projection_entries"] = [tuple(x) for x in stage.get("projection_entries", [])]
        state["kernel_backend"] = str(args.kernel_backend)
        state["population_size"] = int(args.population_size)
        state["ant_count"] = int(args.ant_count)
        state["projection_batch"] = int(args.projection_batch)
        state["log_every"] = int(args.log_every)
        state["topology_max_evals_per_signature"] = int(args.topology_max_evals_per_signature)
        return state
    return initialize_state(args)


def current_stage(state: dict) -> dict | None:
    idx = int(state["current_stage_index"])
    stages = state["stages"]
    if 0 <= idx < len(stages):
        return stages[idx]
    return None


def ensure_stage_stats(state: dict, stage_name: str) -> dict:
    return state["stage_results"].setdefault(
        stage_name,
        {
            "checked_count": 0,
            "evaluated_count": 0,
            "exact_complement_count": 0,
            "exact_union_count": 0,
            "best": None,
        },
    )


def maybe_update_bests(state: dict, row: dict) -> None:
    comp = row["comparison"]
    if state["best_complement_candidate"] is None:
        state["best_complement_candidate"] = row
    else:
        cur = state["best_complement_candidate"]["comparison"]
        if (
            comp["matched_complement_segments"],
            -comp["missing_complement_segments"],
            -comp["extra_complement_segments"],
            -comp["missing_after_union_vs_universal"],
            -comp["extra_after_union_vs_universal"],
            row["score"],
        ) > (
            cur["matched_complement_segments"],
            -cur["missing_complement_segments"],
            -cur["extra_complement_segments"],
            -cur["missing_after_union_vs_universal"],
            -cur["extra_after_union_vs_universal"],
            state["best_complement_candidate"]["score"],
        ):
            state["best_complement_candidate"] = row

    if state["best_union_candidate"] is None:
        state["best_union_candidate"] = row
    else:
        cur = state["best_union_candidate"]["comparison"]
        if (
            -comp["missing_after_union_vs_universal"],
            -comp["extra_after_union_vs_universal"],
            comp["matched_complement_segments"],
            -comp["extra_complement_segments"],
            row["score"],
        ) > (
            -cur["missing_after_union_vs_universal"],
            -cur["extra_after_union_vs_universal"],
            cur["matched_complement_segments"],
            -cur["extra_complement_segments"],
            state["best_union_candidate"]["score"],
        ):
            state["best_union_candidate"] = row

    source_name = row["source_name"]
    current = state["best_source_candidates"].get(source_name)
    if current is None or row["score"] > current["score"]:
        state["best_source_candidates"][source_name] = row

    state["best_candidates"].append(row)
    state["best_candidates"].sort(
        key=lambda item: (
            -int(item["comparison"]["exact_union"]),
            -int(item["comparison"]["exact_complement"]),
            item["comparison"]["missing_after_union_vs_universal"],
            item["comparison"]["extra_after_union_vs_universal"],
            item["comparison"]["missing_complement_segments"],
            item["comparison"]["extra_complement_segments"],
            -item["score"],
        )
    )
    state["best_candidates"] = state["best_candidates"][:30]


def batch_selection(state: dict, rng: np.random.Generator, stage: dict, batch_size: int) -> list[int]:
    pending = state["current_stage_pending_indices"]
    if not pending:
        return []
    pending_set = set(pending)
    chosen: list[int] = []
    for row in state.get("current_stage_population", [])[: max(1, state["population_size"] // 2)]:
        spec = ComplementSpec(
            stage_name=row["spec"]["stage_name"],
            source_name=row["spec"]["source_name"],
            ratio=tuple(row["spec"]["ratio"]),
            base_angle_deg=float(row["spec"]["base_angle_deg"]),
            plane_idx=int(row["spec"]["plane_idx"]),
            readout_mode=row["spec"]["readout_mode"],
            projection_family=row["spec"]["projection_family"],
            projection_idx=int(row["spec"]["projection_idx"]),
            orientation_seed_idx=int(row["spec"]["orientation_seed_idx"]),
        )
        for idx in neighbor_indices(stage, spec):
            if idx in pending_set and idx not in chosen:
                chosen.append(idx)
                if len(chosen) >= batch_size:
                    return chosen
    remaining_candidates = [idx for idx in pending if idx not in set(chosen)]
    if not remaining_candidates:
        return chosen
    weights = np.array(
        [candidate_weight(stage_spec_from_index(stage, idx), state["current_stage_pheromone"]) for idx in remaining_candidates],
        dtype=float,
    )
    if np.all(weights <= 0):
        weights = np.ones_like(weights)
    weights /= weights.sum()
    pick_count = min(batch_size - len(chosen), len(remaining_candidates))
    if pick_count > 0:
        picks = rng.choice(len(remaining_candidates), size=pick_count, replace=False, p=weights)
        chosen.extend(remaining_candidates[int(i)] for i in picks)
    return chosen


def progress(state: dict) -> dict:
    elapsed = float(state["elapsed_wall_seconds"])
    rate = state["total_candidates_checked"] / elapsed if elapsed > 0 else 0.0
    remaining = max(0, state["current_stage_total_candidates"] - (state["current_stage_total_candidates"] - len(state["current_stage_pending_indices"])))
    eta = remaining / rate if rate > 0 else None
    total_planned = sum(stage_total(stage) for stage in state["stages"])
    completed = sum(stage_total(stage) for stage in state["stages"][: state["current_stage_index"]]) + (
        state["current_stage_total_candidates"] - len(state["current_stage_pending_indices"])
    )
    return {
        "stage_candidate_progress": 100.0
        * (state["current_stage_total_candidates"] - len(state["current_stage_pending_indices"]))
        / max(1, state["current_stage_total_candidates"]),
        "overall_candidate_progress": 100.0 * completed / max(1, total_planned),
        "eta": eta,
        "eta_human": humanize_duration_hm(eta),
        "rate": rate,
        "completed_candidates": completed,
        "planned_candidates": total_planned,
    }


def write_summary(state: dict, path: Path) -> None:
    stage = current_stage(state)
    prog = progress(state)
    lines = [
        "# H12 Complement Search Summary",
        "",
        f"- updated: `{state['updated_at']}`",
        f"- status: `{state['status']}`",
        f"- kernel backend: `{state['kernel_backend']}`",
        f"- fixed leader: `{state['fixed_leader_key']}`",
        f"- current stage: `{stage['name'] if stage else 'completed'}`",
        f"- stage generation: `{state['current_stage_generation']}`",
        f"- stage candidate progress: `{prog['stage_candidate_progress']:.4f}%`",
        f"- overall candidate progress: `{prog['overall_candidate_progress']:.4f}%`",
        f"- candidates checked: `{state['total_candidates_checked']}`",
        f"- candidates fully evaluated: `{state['total_candidates_evaluated']}`",
        f"- projection evaluations: `{state['total_projection_evaluations']}`",
        f"- unique topological signatures: `{len(state['unique_topological_signatures'])}`",
        f"- exact complement matches: `{state['exact_complement_matches']}`",
        f"- exact union matches: `{state['exact_union_matches']}`",
        f"- topology-filtered in-batch duplicates: `{state['topology_filtered_batch_equivalent_total']}`",
        f"- topology-filtered by signature cap: `{state['topology_filtered_signature_cap_total']}`",
        f"- elapsed: `{humanize_duration_hm(state['elapsed_wall_seconds'])}`",
        f"- ETA: `{prog['eta_human']}`",
        "",
        "## Fixed Target",
        "",
        f"- missing complement segments: `{len(MISSING_SEGMENTS)}`",
        f"- missing complement angle classes: `{MISSING_ANGLE_CLASSES}`",
        "",
        "## Best 16-cell Candidate",
    ]
    best_16 = state["best_source_candidates"].get("16")
    if best_16 is None:
        lines.append("- no evaluated 16-cell candidate yet")
    else:
        c = best_16["comparison"]
        lines.append(
            f"- `{best_16['spec']['key']}`: complement match=`{c['matched_complement_segments']}/{len(MISSING_SEGMENTS)}`, missing=`{c['missing_after_union_vs_universal']}`, extra=`{c['extra_after_union_vs_universal']}`"
        )
    lines.extend(["", "## Best Tesseract Candidate"])
    best_t = state["best_source_candidates"].get("T")
    if best_t is None:
        lines.append("- no evaluated tesseract candidate yet")
    else:
        c = best_t["comparison"]
        lines.append(
            f"- `{best_t['spec']['key']}`: complement match=`{c['matched_complement_segments']}/{len(MISSING_SEGMENTS)}`, missing=`{c['missing_after_union_vs_universal']}`, extra=`{c['extra_after_union_vs_universal']}`"
        )
    lines.extend(["", "## Best Union Candidate"])
    best_union = state["best_union_candidate"]
    if best_union is None:
        lines.append("- no evaluated union candidate yet")
    else:
        c = best_union["comparison"]
        lines.extend(
            [
                f"- candidate: `{best_union['spec']['key']}`",
                f"- exact complement: `{c['exact_complement']}`",
                f"- exact union: `{c['exact_union']}`",
                f"- matched complement: `{c['matched_complement_segments']}` / `{len(MISSING_SEGMENTS)}`",
                f"- missing vs universal after union: `{c['missing_after_union_vs_universal']}`",
                f"- extra vs universal after union: `{c['extra_after_union_vs_universal']}`",
                f"- node coverage: `{c['node_coverage']}` / `{len(TARGET_NODE_ORDER)}`",
            ]
        )
    lines.extend(["", "## Stage Results"])
    for stage_cfg in state["stages"]:
        lines.append(stage_summary_row(stage_cfg["name"], state["stage_results"].get(stage_cfg["name"])))
    path.write_text("\n".join(lines) + "\n")


def append_log(path: Path, state: dict, note: str) -> None:
    stage = current_stage(state)
    best_16 = state["best_source_candidates"].get("16")
    best_t = state["best_source_candidates"].get("T")
    best_union = state["best_union_candidate"]
    prog = progress(state)
    if best_16 is None:
        best_16_text = "none"
    else:
        c = best_16["comparison"]
        best_16_text = (
            f"{best_16['spec']['key']} | match {c['matched_complement_segments']}/{len(MISSING_SEGMENTS)}, "
            f"missing {c['missing_after_union_vs_universal']}, extra {c['extra_after_union_vs_universal']}"
        )
    if best_t is None:
        best_t_text = "none"
    else:
        c = best_t["comparison"]
        best_t_text = (
            f"{best_t['spec']['key']} | match {c['matched_complement_segments']}/{len(MISSING_SEGMENTS)}, "
            f"missing {c['missing_after_union_vs_universal']}, extra {c['extra_after_union_vs_universal']}"
        )
    if best_union is None:
        union_text = "none"
    else:
        c = best_union["comparison"]
        union_text = (
            f"{best_union['spec']['key']} | exact_complement={c['exact_complement']} exact_union={c['exact_union']} "
            f"| match {c['matched_complement_segments']}/{len(MISSING_SEGMENTS)}, "
            f"missing {c['missing_after_union_vs_universal']}, extra {c['extra_after_union_vs_universal']}"
        )
    entry = f"""
## {now_string()} — {stage['name'] if stage else 'completed'}
Что посчитано:
- current stage: `{stage['name'] if stage else 'completed'}`
- stage generation: `{state['current_stage_generation']}`
- stage candidate progress: `{prog['stage_candidate_progress']:.4f}%`
- overall candidate progress: `{prog['overall_candidate_progress']:.4f}%`
- candidates checked: `{state['total_candidates_checked']}`
- candidates fully evaluated: `{state['total_candidates_evaluated']}`
- unique topological signatures: `{len(state['unique_topological_signatures'])}`
- exact complement matches: `{state['exact_complement_matches']}`
- exact union matches: `{state['exact_union_matches']}`
- ETA: `{prog['eta_human']}`
Лучший 16-cell:
- {best_16_text}
Лучший tesseract:
- {best_t_text}
Лучший union:
- {union_text}
Что это значит:
- мы ищем не всю сетку заново, а ровно дополнение к фиксированному лидеру до `universal-lattice.py`.
Примечание:
- {note}
"""
    with path.open("a") as fh:
        fh.write(entry)


def maybe_activate_orientation_stages(state: dict) -> None:
    if state.get("orientation_stages_appended", False):
        return
    eligible = []
    for source_name in ("16", "T"):
        row = state["best_source_candidates"].get(source_name)
        if row is None:
            continue
        comp = row["comparison"]
        if comp["matched_complement_segments"] >= 12 or comp["missing_after_union_vs_universal"] <= 4:
            eligible.append(source_name)
    if not eligible:
        state["orientation_stages_appended"] = True
        return
    for source_name in eligible:
        for limit in (24, 48, 96):
            state["stages"].append(build_orientation_stage(source_name, limit))
    state["orientation_stages_appended"] = True


def activate_next_stage(state: dict) -> None:
    stage = current_stage(state)
    if stage is not None and stage["name"].startswith("BT_"):
        maybe_activate_orientation_stages(state)
    state["current_stage_index"] += 1
    next_stage = current_stage(state)
    if next_stage is None:
        return
    state["current_stage_generation"] = 0
    state["current_stage_pending_indices"] = list(range(stage_total(next_stage)))
    state["current_stage_total_candidates"] = stage_total(next_stage)
    state["current_stage_pheromone"] = initial_stage_pheromone(next_stage)
    state["current_stage_population"] = []


def run_loop(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    summary_path = state_dir / "summary.md"
    log_path = state_dir / "log.md"
    best_path = state_dir / "best_candidates.json"

    if not log_path.exists():
        log_path.write_text("# H12 Complement Log\n")

    state = load_state(state_path, args)
    state["status"] = "running"
    if args.kernel_backend == "rust_persistent":
        init_rust_kernel_server()
    rng = np.random.default_rng(int(state["next_seed"]) + int(state["total_candidates_checked"]))
    start = time.time()

    while True:
        stage = current_stage(state)
        if stage is None:
            state["status"] = "completed"
            break
        if not state["current_stage_pending_indices"]:
            activate_next_stage(state)
            continue

        batch_size = state["population_size"] + state["ant_count"]
        batch = batch_selection(state, rng, stage, batch_size)
        if not batch:
            activate_next_stage(state)
            continue

        pending_set = set(state["current_stage_pending_indices"])
        for idx in batch:
            pending_set.discard(idx)
        state["current_stage_pending_indices"] = sorted(pending_set)

        batch_seen_signatures: set[str] = set()
        notes: list[str] = []
        stage_stats = ensure_stage_stats(state, stage["name"])
        evaluated_rows: list[dict] = []

        for idx in batch:
            spec = stage_spec_from_index(stage, idx)
            geometry = evaluate_candidate_geometry(spec, stage)
            signature = geometry["topological_signature"]
            state["total_candidates_checked"] += 1
            stage_stats["checked_count"] += 1

            if signature in batch_seen_signatures:
                state["topology_filtered_batch_equivalent_total"] += 1
                continue
            batch_seen_signatures.add(signature)
            sig_stats = state["unique_topological_signatures"].setdefault(signature, {"eval_count": 0, "best_score": -1e18})
            if sig_stats["eval_count"] >= state["topology_max_evals_per_signature"]:
                state["topology_filtered_signature_cap_total"] += 1
                continue

            seed = int(state["next_seed"])
            state["next_seed"] += 1
            row = complete_candidate(geometry, state["projection_batch"], seed, state["kernel_backend"])
            sig_stats["eval_count"] += 1
            sig_stats["best_score"] = max(float(sig_stats["best_score"]), float(row["score"]))
            stage_stats["evaluated_count"] += 1
            state["total_candidates_evaluated"] += 1
            state["total_projection_evaluations"] += state["projection_batch"]
            if row["comparison"]["exact_complement"]:
                stage_stats["exact_complement_count"] += 1
                state["exact_complement_matches"] += 1
            if row["comparison"]["exact_union"]:
                stage_stats["exact_union_count"] += 1
                state["exact_union_matches"] += 1
            if stage_stats["best"] is None or row["score"] > stage_stats["best"]["score"]:
                stage_stats["best"] = row
            evaluated_rows.append(row)
            update_stage_pheromone(state["current_stage_pheromone"], spec, row["score"])
            maybe_update_bests(state, row)
            if row["comparison"]["exact_complement"] or row["comparison"]["exact_union"]:
                notes.append(f"exact target found by {row['spec']['key']}")

        evaluated_rows.sort(
            key=lambda item: (
                -int(item["comparison"]["exact_union"]),
                -int(item["comparison"]["exact_complement"]),
                item["comparison"]["missing_after_union_vs_universal"],
                item["comparison"]["extra_after_union_vs_universal"],
                -item["score"],
            )
        )
        state["current_stage_population"] = evaluated_rows[: state["population_size"]]
        state["current_stage_generation"] += 1
        state["elapsed_wall_seconds"] += time.time() - start
        start = time.time()
        state["updated_at"] = now_string()

        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
        best_path.write_text(json.dumps(state["best_candidates"], indent=2, ensure_ascii=True))
        write_summary(state, summary_path)
        if state["current_stage_generation"] % state["log_every"] == 0 or notes:
            append_log(log_path, state, "; ".join(notes) if notes else "regular checkpoint")

        if state["exact_complement_matches"] > 0 or state["exact_union_matches"] > 0:
            state["status"] = "completed"
            break
        if args.max_generations is not None and state["current_stage_generation"] >= args.max_generations:
            state["status"] = "paused"
            break
        if args.max_candidates is not None and state["total_candidates_checked"] >= args.max_candidates:
            state["status"] = "paused"
            break

    state["updated_at"] = now_string()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
    best_path.write_text(json.dumps(state["best_candidates"], indent=2, ensure_ascii=True))
    write_summary(state, summary_path)
    append_log(log_path, state, "final checkpoint for this process run")
    if args.idle_when_complete and state["status"] == "completed":
        append_log(log_path, state, "search completed; service stays alive because Restart=always is used")
        while True:
            time.sleep(3600)
    return 0


def run_truth() -> int:
    payload = {
        "leader_key": LEADER_KEY,
        "leader_segment_count": len(LEADER_SEGMENTS),
        "universal_segment_count": len(UNIVERSAL_SEGMENTS),
        "missing_segment_count": len(MISSING_SEGMENTS),
        "missing_angle_classes_deg": MISSING_ANGLE_CLASSES,
        "missing_segments_idx": [list(seg) for seg in sorted(MISSING_SEGMENTS)],
        "missing_segments_xy": [[list(TARGET_NODE_ORDER[i]), list(TARGET_NODE_ORDER[j])] for i, j in sorted(MISSING_SEGMENTS)],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


def run_stage_counts() -> int:
    payload = {stage["name"]: stage_total(stage) for stage in build_base_stages()}
    for source_name in ("16", "T"):
        for limit in (24, 48, 96):
            stage = build_orientation_stage(source_name, limit)
            payload[stage["name"]] = stage_total(stage)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--population-size", type=int, default=DEFAULT_POPULATION)
    parser.add_argument("--ant-count", type=int, default=DEFAULT_ANTS)
    parser.add_argument("--projection-batch", type=int, default=DEFAULT_PROJECTION_BATCH)
    parser.add_argument("--log-every", type=int, default=DEFAULT_LOG_EVERY)
    parser.add_argument("--topology-max-evals-per-signature", type=int, default=DEFAULT_TOPOLOGY_MAX_EVALS)
    parser.add_argument("--kernel-backend", choices=["python", "rust_persistent"], default=DEFAULT_KERNEL_BACKEND)
    parser.add_argument("--max-generations", type=int, default=None)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--idle-when-complete", action="store_true")
    parser.add_argument("--truth", action="store_true")
    parser.add_argument("--stage-counts", action="store_true")
    args = parser.parse_args()
    if args.truth:
        return run_truth()
    if args.stage_counts:
        return run_stage_counts()
    return run_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
