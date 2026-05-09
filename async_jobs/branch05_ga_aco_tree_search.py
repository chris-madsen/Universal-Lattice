#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import (
    clustered_family_counts as core_clustered_family_counts,
    configured_kernel_backend,
    evaluate_vectors_python,
    evaluate_vectors_rust_persistent,
    init_rust_kernel_server,
    profile_score as core_profile_score,
    random_projection as core_random_projection,
    root_line_key as core_root_line_key,
    unique_line_representatives as core_unique_line_representatives,
)
from research.common.meta_search import (
    humanize_duration_hm,
    low_pass_harmonic_prior_from_matrix,
    now_string as core_now_string,
    top_rate_entries,
    weighted_choice as core_weighted_choice,
    weighted_sample_without_replacement as core_weighted_sample_without_replacement,
)
from research.common.topological_signature import (
    root_line_key_signature,
    signed_permutation_actions,
    transform_vector,
)

STATE_VERSION = 3
TARGET_FAMILY_COUNT = 5
TARGET_PROFILE = (3, 4, 6, 6, 8)
FOCUSED_PROFILE = [1, 1, 1, 1, 6]
DEFAULT_WORKERS = 2
DEFAULT_POPULATION = 28
DEFAULT_ANTS = 44
DEFAULT_ELITES = 8
DEFAULT_PROJECTION_BATCH = 96
DEFAULT_TARGET_GENERATIONS = 12000
DEFAULT_LOG_EVERY = 5
DEFAULT_TOPOLOGY_FILTER = True
DEFAULT_TOPOLOGY_MAX_EVALS_PER_SIGNATURE = 1
DEFAULT_STATE_DIR = ROOT / "research" / "async_state" / "branch05_ridge"
OLD_BRUTE_STATE = DEFAULT_STATE_DIR / "state.json"
BRANCH10_SEARCH = ROOT / "research" / "B_symmetry_arrangement_models" / "10_orbit_selected_subweb" / "data" / "search_orbit_templates.json"
DEFAULT_KERNEL_BACKEND = configured_kernel_backend()
WORKER_KERNEL_BACKEND = DEFAULT_KERNEL_BACKEND
PRIORITY_CLASS_TEMPLATE_KEYS = ("A2_B2-0_B1-4_B0-0", "A2_B2-0_B1-3_B0-1")
PRIORITY_CLASS_SUBSET_KEYS = ("02", "12", "13", "23")
PRIORITY_TEMPLATE_HEURISTIC_MULT = 8.0
PRIORITY_TEMPLATE_PHEROMONE_MULT = 3.0
PRIORITY_SUBSET_PHEROMONE_MULT = 2.0
PRIORITY_OVERLAY_VERSION = 1
PRIORITY_FOCUS_TEMPLATE_KEY = "A2_B2-0_B1-4_B0-0"
PRIORITY_FOCUS_SUBSET_KEYS = ("02", "12", "13", "23")
DEFAULT_PRIORITY_FOCUS_EVALS = 280


@dataclass(frozen=True)
class Template:
    axis_size: int
    total_cell_count: int
    bucket_counts: Dict[str, int]

    @property
    def key(self) -> str:
        bc = self.bucket_counts
        return f"A{self.axis_size}_B2-{bc['2']}_B1-{bc['1']}_B0-{bc['0']}"


def now_string() -> str:
    return core_now_string()


def root_line_key(vec: np.ndarray, tol: float = 1e-9):
    return core_root_line_key(vec, tol=tol)


def angle_mod_180(vec: np.ndarray) -> float:
    return float((np.degrees(np.arctan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0)


def unique_line_representatives(vectors: np.ndarray) -> list[np.ndarray]:
    return core_unique_line_representatives(vectors)


def canonical_24cell_vertices() -> np.ndarray:
    verts = set()
    for perm in set(itertools.permutations([1, 1, 0, 0], 4)):
        nz = [i for i, v in enumerate(perm) if v != 0]
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                p = list(perm)
                p[nz[0]] *= s1
                p[nz[1]] *= s2
                verts.add(tuple(float(x) for x in p))
    return np.array(sorted(verts), dtype=float)


def tesseract_axis_vectors() -> np.ndarray:
    vectors = []
    for i in range(4):
        vec = np.zeros(4, dtype=float)
        vec[i] = 1.0
        vectors.append(vec)
    return np.array(vectors, dtype=float)


def random_projection(rng: np.random.Generator) -> np.ndarray:
    return core_random_projection(rng)


def clustered_family_counts(vectors: list[np.ndarray], projection: np.ndarray, tol: float = 1.5) -> list[int]:
    return core_clustered_family_counts(vectors, projection, tol=tol)


def profile_score(counts: list[int], target_total: int = 27, target_profile: tuple[int, ...] = TARGET_PROFILE) -> float:
    return core_profile_score(
        counts,
        target_family_count=TARGET_FAMILY_COUNT,
        target_total=target_total,
        target_profile=target_profile,
    )


def candidate_quality(family5_rate: float, exact_rate: float, mean_profile_score: float) -> float:
    return 10000.0 * exact_rate + 1000.0 * family5_rate + 10.0 / (1.0 + mean_profile_score)


AXIS_VECS = unique_line_representatives(tesseract_axis_vectors())
CELL_VECS = unique_line_representatives(canonical_24cell_vertices())
AXIS_SUBSETS = [tuple(combo) for size in (2, 3, 4) for combo in itertools.combinations(range(4), size)]
AXIS_SUBSET_KEYS = ["".join(map(str, subset)) for subset in AXIS_SUBSETS]
AXIS_SUBSET_MAP = {"".join(map(str, subset)): subset for subset in AXIS_SUBSETS}
TOPOLOGY_ACTIONS = signed_permutation_actions(dim=4)


def bucket_lines_for_subset(subset: tuple[int, ...]) -> dict[str, list[int]]:
    selected_dims = set(subset)
    buckets = {"0": [], "1": [], "2": []}
    for idx, vec in enumerate(CELL_VECS):
        support = {i for i, x in enumerate(vec) if abs(float(x)) > 1e-9}
        overlap = len(support & selected_dims)
        buckets[str(overlap)].append(idx)
    return buckets


SUBSET_BUCKETS = {"".join(map(str, subset)): bucket_lines_for_subset(subset) for subset in AXIS_SUBSETS}
CAPS_BY_AXIS_SIZE = {
    2: {"2": 2, "1": 8, "0": 2},
    3: {"2": 6, "1": 6, "0": 0},
    4: {"2": 12, "1": 0, "0": 0},
}


def candidate_space_count(template: Template, axis_subset_key: str) -> int:
    buckets = SUBSET_BUCKETS[axis_subset_key]
    ways = 1
    for bucket in ("2", "1", "0"):
        ways *= math.comb(len(buckets[bucket]), template.bucket_counts[bucket])
    return ways


class Branch05TopologySignatureEngine:
    def __init__(self) -> None:
        self._actions = TOPOLOGY_ACTIONS
        self._subset_map = AXIS_SUBSET_MAP
        self._axis_keys_by_action: list[list[tuple[float, ...]]] = []
        self._cell_keys_by_action: list[list[tuple[float, ...]]] = []
        for action in self._actions:
            self._axis_keys_by_action.append(
                [root_line_key_signature(transform_vector(vec, action)) for vec in AXIS_VECS]
            )
            self._cell_keys_by_action.append(
                [root_line_key_signature(transform_vector(vec, action)) for vec in CELL_VECS]
            )

    def signature(self, candidate: dict) -> str:
        axis_ids = self._subset_map[candidate["axis_subset_key"]]
        b2 = candidate["selections"]["2"]
        b1 = candidate["selections"]["1"]
        b0 = candidate["selections"]["0"]
        best: tuple | None = None
        for action_idx in range(len(self._actions)):
            rep = (
                tuple(sorted(self._axis_keys_by_action[action_idx][int(i)] for i in axis_ids)),
                tuple(sorted(self._cell_keys_by_action[action_idx][int(i)] for i in b2)),
                tuple(sorted(self._cell_keys_by_action[action_idx][int(i)] for i in b1)),
                tuple(sorted(self._cell_keys_by_action[action_idx][int(i)] for i in b0)),
            )
            if best is None or rep < best:
                best = rep
        return repr(best)


TOPOLOGY_ENGINE = Branch05TopologySignatureEngine()


def generate_templates() -> list[Template]:
    templates: list[Template] = []
    for axis_size in (2, 3, 4):
        caps = CAPS_BY_AXIS_SIZE[axis_size]
        for total in range(4, 9):
            for c2 in range(caps["2"] + 1):
                for c1 in range(caps["1"] + 1):
                    c0 = total - c2 - c1
                    if 0 <= c0 <= caps["0"]:
                        templates.append(Template(axis_size=axis_size, total_cell_count=total, bucket_counts={"2": c2, "1": c1, "0": c0}))
    unique = {}
    for tmpl in templates:
        unique[tmpl.key] = tmpl
    return [unique[key] for key in sorted(unique)]


TEMPLATES = generate_templates()
TEMPLATE_MAP = {tmpl.key: tmpl for tmpl in TEMPLATES}
ROOT_BRANCHES = [
    {
        "template_key": tmpl.key,
        "axis_subset_key": subset_key,
        "key": f"{tmpl.key}@{subset_key}",
    }
    for tmpl in TEMPLATES
    for subset_key in AXIS_SUBSET_KEYS
    if len(subset_key) == tmpl.axis_size
]
TOTAL_CANDIDATE_SPACE = sum(
    candidate_space_count(TEMPLATE_MAP[root["template_key"]], root["axis_subset_key"]) for root in ROOT_BRANCHES
)


def normalize_candidate(candidate: dict) -> dict:
    candidate = dict(candidate)
    candidate["bucket_counts"] = {str(k): int(v) for k, v in candidate["bucket_counts"].items()}
    candidate["selections"] = {str(k): [int(x) for x in v] for k, v in candidate["selections"].items()}
    return candidate


def weighted_choice(items: list, weights: list[float], rng: np.random.Generator):
    return core_weighted_choice(items, weights, rng)


def weighted_sample_without_replacement(items: list[int], weights: list[float], k: int, rng: np.random.Generator) -> list[int]:
    return core_weighted_sample_without_replacement(items, weights, k, rng)


def candidate_key(candidate: dict) -> str:
    parts = [candidate["template_key"], candidate["axis_subset_key"]]
    for bucket in ("2", "1", "0"):
        parts.append(f"{bucket}:{','.join(map(str, sorted(candidate['selections'][bucket])))}")
    return "|".join(parts)


def root_branch_key(candidate: dict) -> str:
    return f"{candidate['template_key']}@{candidate['axis_subset_key']}"


def topological_signature(candidate: dict) -> str:
    return TOPOLOGY_ENGINE.signature(candidate)


def low_pass_harmonic_prior_from_brute_state(path: Path) -> tuple[dict[str, dict[str, float]], list[list[float]], list[list[float]]]:
    raw = np.full((3, 5), 1e-6, dtype=float)
    if path.exists():
        state = json.loads(path.read_text())
        for key, entry in state["classes"].items():
            t = int(entry["t_count"])
            c = int(entry["c_count"])
            completed = max(1, int(entry["completed_samples"]))
            family_rate = entry["family5_hits"] / completed
            exact_rate = entry["exact_hits"] / completed
            raw[t - 2, c - 4] = family_rate + 5.0 * exact_rate
    smooth = low_pass_harmonic_prior_from_matrix(raw, keep_rows=2, keep_cols=3, floor=0.05)
    prior = {}
    for t in range(2, 5):
        prior[str(t)] = {}
        for c in range(4, 9):
            prior[str(t)][str(c)] = float(smooth[t - 2, c - 4])
    return prior, raw.tolist(), smooth.tolist()


def branch10_template_prior(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    result = {}
    for row in data.get("results", []):
        result[row["template"]] = float(row.get("family5_hit_rate", 0.0) + 5.0 * row.get("exact_profile_hit_rate", 0.0))
    return result


def bootstrap_priors() -> dict:
    harmonic_prior, raw_matrix, smooth_matrix = low_pass_harmonic_prior_from_brute_state(OLD_BRUTE_STATE)
    template_prior = branch10_template_prior(BRANCH10_SEARCH)
    heuristic = {}
    for tmpl in TEMPLATES:
        root_score = harmonic_prior[str(tmpl.axis_size)][str(tmpl.total_cell_count)]
        orbit_score = template_prior.get(tmpl.key, 0.0)
        heuristic[tmpl.key] = float(0.7 * root_score + 0.3 * orbit_score + 1e-6)
    for key in PRIORITY_CLASS_TEMPLATE_KEYS:
        if key in heuristic:
            heuristic[key] *= PRIORITY_TEMPLATE_HEURISTIC_MULT
    return {
        "harmonic_prior": harmonic_prior,
        "raw_matrix": raw_matrix,
        "smooth_matrix": smooth_matrix,
        "branch10_template_prior": template_prior,
        "template_heuristic": heuristic,
    }


def initial_pheromones(priors: dict) -> dict:
    template_pheromone = {tmpl.key: 1.0 + 5.0 * priors["template_heuristic"].get(tmpl.key, 0.0) for tmpl in TEMPLATES}
    subset_pheromone = {key: 1.0 for key in AXIS_SUBSET_KEYS}
    line_pheromone = {}
    for subset_key, buckets in SUBSET_BUCKETS.items():
        line_pheromone[subset_key] = {}
        for bucket, line_ids in buckets.items():
            line_pheromone[subset_key][bucket] = {str(line_id): 1.0 for line_id in line_ids}
    for key in PRIORITY_CLASS_TEMPLATE_KEYS:
        if key in template_pheromone:
            template_pheromone[key] *= PRIORITY_TEMPLATE_PHEROMONE_MULT
    for subset_key in PRIORITY_CLASS_SUBSET_KEYS:
        if subset_key in subset_pheromone:
            subset_pheromone[subset_key] *= PRIORITY_SUBSET_PHEROMONE_MULT
    return {
        "template": template_pheromone,
        "subset": subset_pheromone,
        "line": line_pheromone,
    }


def apply_priority_overlay(state: dict) -> None:
    for key in PRIORITY_CLASS_TEMPLATE_KEYS:
        heuristic = state["priors"]["template_heuristic"].get(key)
        if heuristic is not None:
            state["priors"]["template_heuristic"][key] = float(heuristic) * PRIORITY_TEMPLATE_HEURISTIC_MULT
        if key in state["pheromones"]["template"]:
            state["pheromones"]["template"][key] *= PRIORITY_TEMPLATE_PHEROMONE_MULT
    for subset_key in PRIORITY_CLASS_SUBSET_KEYS:
        if subset_key in state["pheromones"]["subset"]:
            state["pheromones"]["subset"][subset_key] *= PRIORITY_SUBSET_PHEROMONE_MULT


def default_state(args: argparse.Namespace) -> dict:
    priors = bootstrap_priors()
    pheromones = initial_pheromones(priors)
    return {
        "state_version": STATE_VERSION,
        "algorithm": "ga_aco_tree_v1",
        "created_at": now_string(),
        "updated_at": now_string(),
        "status": "initialized",
        "target_generations": args.target_generations,
        "generation": 0,
        "population_size": args.population_size,
        "ant_count": args.ant_count,
        "elite_count": args.elite_count,
        "projection_batch": args.projection_batch,
        "workers": args.workers,
        "kernel_backend": args.kernel_backend,
        "topology_filter_enabled": bool(args.topology_filter),
        "topology_max_evals_per_signature": int(args.topology_max_evals_per_signature),
        "priority_overlay_version": PRIORITY_OVERLAY_VERSION,
        "priority_class_templates": list(PRIORITY_CLASS_TEMPLATE_KEYS),
        "priority_class_subsets": list(PRIORITY_CLASS_SUBSET_KEYS),
        "priority_focus_template_key": PRIORITY_FOCUS_TEMPLATE_KEY,
        "priority_focus_subset_keys": list(PRIORITY_FOCUS_SUBSET_KEYS),
        "priority_focus_target_evals": DEFAULT_PRIORITY_FOCUS_EVALS,
        "priority_focus_initial_template_evals": 0,
        "priority_focus_remaining_evals": DEFAULT_PRIORITY_FOCUS_EVALS,
        "topology_signature_stats": {},
        "topology_skipped_batch_equivalent_total": 0,
        "topology_skipped_cap_total": 0,
        "checkpoint_count": 0,
        "elapsed_wall_seconds": 0.0,
        "total_candidate_evaluations": 0,
        "total_projection_evaluations": 0,
        "next_seed": 5000,
        "priors": priors,
        "pheromones": pheromones,
        "population": [],
        "template_stats": {},
        "root_branch_stats": {},
        "best_overall": None,
        "best_exact": None,
        "bootstrap_sources": {
            "old_brute_state": str(OLD_BRUTE_STATE),
            "branch10_search": str(BRANCH10_SEARCH),
        },
    }


def load_state(state_path: Path, args: argparse.Namespace) -> dict:
    if state_path.exists():
        state = json.loads(state_path.read_text())
        state["population"] = [normalize_candidate(c) for c in state.get("population", [])]
        state.setdefault("algorithm", "ga_aco_tree_v1")
        state.setdefault("priors", bootstrap_priors())
        state.setdefault("pheromones", initial_pheromones(state["priors"]))
        state.setdefault("template_stats", {})
        state.setdefault("root_branch_stats", {})
        state.setdefault("best_overall", None)
        state.setdefault("best_exact", None)
        state.setdefault("total_candidate_evaluations", 0)
        state.setdefault("total_projection_evaluations", 0)
        state.setdefault("elapsed_wall_seconds", 0.0)
        state.setdefault("checkpoint_count", 0)
        state.setdefault("status", "initialized")
        state.setdefault("priority_overlay_version", 0)
        state.setdefault("priority_class_templates", list(PRIORITY_CLASS_TEMPLATE_KEYS))
        state.setdefault("priority_class_subsets", list(PRIORITY_CLASS_SUBSET_KEYS))
        state.setdefault("priority_focus_template_key", PRIORITY_FOCUS_TEMPLATE_KEY)
        state.setdefault("priority_focus_subset_keys", list(PRIORITY_FOCUS_SUBSET_KEYS))
        state.setdefault("priority_focus_target_evals", DEFAULT_PRIORITY_FOCUS_EVALS)
        focus_key = str(state.get("priority_focus_template_key", PRIORITY_FOCUS_TEMPLATE_KEY))
        current_focus_eval_count = int(state.get("template_stats", {}).get(focus_key, {}).get("eval_count", 0))
        state.setdefault("priority_focus_initial_template_evals", current_focus_eval_count)
        if "priority_focus_remaining_evals" not in state:
            state["priority_focus_remaining_evals"] = int(state.get("priority_focus_target_evals", DEFAULT_PRIORITY_FOCUS_EVALS))
        state["kernel_backend"] = args.kernel_backend
        state.setdefault("topology_signature_stats", {})
        state.setdefault("topology_skipped_batch_equivalent_total", 0)
        state.setdefault("topology_skipped_cap_total", 0)
        state["topology_filter_enabled"] = bool(args.topology_filter)
        state["topology_max_evals_per_signature"] = int(args.topology_max_evals_per_signature)
        state.setdefault(
            "bootstrap_sources",
            {
                "old_brute_state": str(OLD_BRUTE_STATE),
                "branch10_search": str(BRANCH10_SEARCH),
            },
        )
        state["state_version"] = STATE_VERSION
        if int(state.get("priority_overlay_version", 0)) < PRIORITY_OVERLAY_VERSION:
            apply_priority_overlay(state)
            state["priority_overlay_version"] = PRIORITY_OVERLAY_VERSION
        return state
    state = default_state(args)
    apply_priority_overlay(state)
    state["priority_overlay_version"] = PRIORITY_OVERLAY_VERSION
    return state


def heuristic_for_template(state: dict, template_key: str) -> float:
    return float(state["priors"]["template_heuristic"].get(template_key, 1e-6))


def seed_population_from_priors(state: dict, rng: np.random.Generator) -> list[dict]:
    ranked_templates = sorted(TEMPLATES, key=lambda t: (-heuristic_for_template(state, t.key), t.key))
    population = []
    for tmpl in ranked_templates[: state["population_size"]]:
        subset_candidates = [key for key in AXIS_SUBSET_KEYS if len(key) == tmpl.axis_size]
        subset_key = weighted_choice(subset_candidates, [state["pheromones"]["subset"][key] for key in subset_candidates], rng)
        population.append(build_candidate_from_template(state, tmpl.key, subset_key, rng, source="bootstrap"))
    return population


def build_candidate_from_template(state: dict, template_key: str, axis_subset_key: str, rng: np.random.Generator, source: str) -> dict:
    tmpl = TEMPLATE_MAP[template_key]
    buckets = SUBSET_BUCKETS[axis_subset_key]
    selections = {"2": [], "1": [], "0": []}
    for bucket in ("2", "1", "0"):
        count = tmpl.bucket_counts[bucket]
        items = buckets[bucket]
        weights = [state["pheromones"]["line"][axis_subset_key][bucket][str(line_id)] for line_id in items]
        selections[bucket] = weighted_sample_without_replacement(items, weights, count, rng)
    return {
        "template_key": template_key,
        "axis_subset_key": axis_subset_key,
        "axis_size": tmpl.axis_size,
        "total_cell_count": tmpl.total_cell_count,
        "bucket_counts": dict(tmpl.bucket_counts),
        "selections": selections,
        "source": source,
    }


def propose_ant_candidate(state: dict, rng: np.random.Generator) -> dict:
    template_keys = [tmpl.key for tmpl in TEMPLATES]
    weights = []
    for key in template_keys:
        pher = state["pheromones"]["template"][key]
        heur = heuristic_for_template(state, key)
        weights.append((pher ** 1.0) * (heur ** 2.0))
    template_key = weighted_choice(template_keys, weights, rng)
    axis_size = TEMPLATE_MAP[template_key].axis_size
    subset_candidates = [key for key in AXIS_SUBSET_KEYS if len(key) == axis_size]
    subset_weights = [state["pheromones"]["subset"][key] for key in subset_candidates]
    subset_key = weighted_choice(subset_candidates, subset_weights, rng)
    return build_candidate_from_template(state, template_key, subset_key, rng, source="aco")


def priority_focus_active(state: dict) -> bool:
    return int(state.get("priority_focus_remaining_evals", 0)) > 0


def priority_focus_subset_candidates(state: dict) -> list[str]:
    template_key = str(state.get("priority_focus_template_key", PRIORITY_FOCUS_TEMPLATE_KEY))
    tmpl = TEMPLATE_MAP.get(template_key)
    if tmpl is None:
        return []
    requested = [str(x) for x in state.get("priority_focus_subset_keys", list(PRIORITY_FOCUS_SUBSET_KEYS))]
    requested = [x for x in requested if x in AXIS_SUBSET_MAP and len(x) == tmpl.axis_size]
    if requested:
        return requested
    return [key for key in AXIS_SUBSET_KEYS if len(key) == tmpl.axis_size]


def propose_priority_focus_candidate(state: dict, rng: np.random.Generator, source: str) -> dict:
    template_key = str(state.get("priority_focus_template_key", PRIORITY_FOCUS_TEMPLATE_KEY))
    if template_key not in TEMPLATE_MAP:
        return propose_ant_candidate(state, rng)
    subset_candidates = priority_focus_subset_candidates(state)
    if not subset_candidates:
        return propose_ant_candidate(state, rng)
    subset_weights = [state["pheromones"]["subset"][key] for key in subset_candidates]
    subset_key = weighted_choice(subset_candidates, subset_weights, rng)
    return build_candidate_from_template(state, template_key, subset_key, rng, source=source)


def mutate_bucket_counts(bucket_counts: dict[str, int], axis_size: int, rng: np.random.Generator) -> dict[str, int]:
    caps = CAPS_BY_AXIS_SIZE[axis_size]
    result = dict(bucket_counts)
    src, dst = rng.choice(["2", "1", "0"], size=2, replace=False)
    if result[src] > 0 and result[dst] < caps[dst]:
        result[src] -= 1
        result[dst] += 1
    return result


def nearest_template(axis_size: int, bucket_counts: dict[str, int]) -> str:
    total = sum(bucket_counts.values())
    candidates = [tmpl for tmpl in TEMPLATES if tmpl.axis_size == axis_size and tmpl.total_cell_count == total]
    if not candidates:
        candidates = [tmpl for tmpl in TEMPLATES if tmpl.axis_size == axis_size]
    def dist(tmpl: Template):
        return (
            sum(abs(tmpl.bucket_counts[b] - bucket_counts[b]) for b in ("2", "1", "0")),
            abs(tmpl.total_cell_count - total),
        )
    best = min(candidates, key=lambda tmpl: (dist(tmpl), tmpl.key))
    return best.key


def propose_ga_child(state: dict, parents: list[dict], rng: np.random.Generator) -> dict:
    p1, p2 = parents
    if rng.random() < 0.6:
        axis_size = p1["axis_size"]
    else:
        axis_size = p2["axis_size"]
    if rng.random() < 0.2:
        axis_size = int(np.clip(axis_size + rng.choice([-1, 1]), 2, 4))
    subset_candidates = [key for key in AXIS_SUBSET_KEYS if len(key) == axis_size]
    if len(p1["axis_subset_key"]) == axis_size and rng.random() < 0.5:
        subset_key = p1["axis_subset_key"]
    elif len(p2["axis_subset_key"]) == axis_size and rng.random() < 0.5:
        subset_key = p2["axis_subset_key"]
    else:
        subset_key = weighted_choice(subset_candidates, [state["pheromones"]["subset"][k] for k in subset_candidates], rng)
    bucket_counts = {}
    for bucket in ("2", "1", "0"):
        bucket_counts[bucket] = p1["bucket_counts"][bucket] if rng.random() < 0.5 else p2["bucket_counts"][bucket]
    if rng.random() < 0.4:
        bucket_counts = mutate_bucket_counts(bucket_counts, axis_size, rng)
    template_key = nearest_template(axis_size, bucket_counts)
    return build_candidate_from_template(state, template_key, subset_key, rng, source="ga")


def selected_vectors(candidate: dict) -> list[np.ndarray]:
    vectors = [AXIS_VECS[i] for i in AXIS_SUBSET_MAP[candidate["axis_subset_key"]]]
    for bucket in ("2", "1", "0"):
        vectors.extend(CELL_VECS[idx] for idx in candidate["selections"][bucket])
    return vectors


def evaluate_candidate(candidate: dict, projection_batch: int, seed: int) -> dict:
    candidate = normalize_candidate(candidate)
    vectors = selected_vectors(candidate)
    backend_used = WORKER_KERNEL_BACKEND
    try:
        if backend_used == "rust_persistent":
            metrics = evaluate_vectors_rust_persistent(vectors, projection_batch=projection_batch, seed=seed)
            metrics["fitness"] = candidate_quality(
                metrics["family5_rate"],
                metrics["exact_rate"],
                metrics["mean_profile_score"],
            )
        else:
            metrics = evaluate_vectors_python(
                vectors,
                projection_batch=projection_batch,
                seed=seed,
                target_family_count=TARGET_FAMILY_COUNT,
                target_profile=TARGET_PROFILE,
                focused_profile=tuple(FOCUSED_PROFILE),
            )
            backend_used = "python"
    except Exception:
        metrics = evaluate_vectors_python(
            vectors,
            projection_batch=projection_batch,
            seed=seed,
            target_family_count=TARGET_FAMILY_COUNT,
            target_profile=TARGET_PROFILE,
            focused_profile=tuple(FOCUSED_PROFILE),
        )
        backend_used = "python_fallback"
    evaluated = dict(candidate)
    evaluated.update(
        {
            "family5_hits": metrics["family5_hits"],
            "exact_hits": metrics["exact_hits"],
            "family5_rate": metrics["family5_rate"],
            "exact_rate": metrics["exact_rate"],
            "mean_profile_score": metrics["mean_profile_score"],
            "fitness": metrics["fitness"],
            "family_histogram": metrics["family_histogram"],
            "best_counts": metrics["best_counts"],
            "evaluation_seed": seed,
            "root_branch_key": root_branch_key(candidate),
            "kernel_backend_used": backend_used,
        }
    )
    return evaluated


def worker_initializer(kernel_backend: str) -> None:
    global WORKER_KERNEL_BACKEND
    WORKER_KERNEL_BACKEND = kernel_backend
    if kernel_backend == "rust_persistent":
        init_rust_kernel_server()


def update_template_stats(state: dict, candidate: dict) -> None:
    key = candidate["template_key"]
    stats = state["template_stats"].setdefault(key, {"eval_count": 0, "family5_sum": 0.0, "exact_sum": 0.0, "fitness_sum": 0.0, "best": None})
    stats["eval_count"] += 1
    stats["family5_sum"] += candidate["family5_rate"]
    stats["exact_sum"] += candidate["exact_rate"]
    stats["fitness_sum"] += candidate["fitness"]
    if stats["best"] is None or candidate["fitness"] > stats["best"]["fitness"]:
        stats["best"] = candidate


def update_root_branch_stats(state: dict, candidate: dict) -> None:
    key = candidate["root_branch_key"]
    stats = state["root_branch_stats"].setdefault(
        key,
        {
            "template_key": candidate["template_key"],
            "axis_subset_key": candidate["axis_subset_key"],
            "eval_count": 0,
            "family5_sum": 0.0,
            "exact_sum": 0.0,
            "fitness_sum": 0.0,
            "best": None,
        },
    )
    stats["eval_count"] += 1
    stats["family5_sum"] += candidate["family5_rate"]
    stats["exact_sum"] += candidate["exact_rate"]
    stats["fitness_sum"] += candidate["fitness"]
    if stats["best"] is None or candidate["fitness"] > stats["best"]["fitness"]:
        stats["best"] = candidate


def maybe_update_bests(state: dict, candidate: dict) -> list[str]:
    notes = []
    if state["best_overall"] is None or candidate["fitness"] > state["best_overall"]["fitness"]:
        state["best_overall"] = candidate
        notes.append(f"new overall best {candidate['template_key']} @ {candidate['axis_subset_key']}")
    if candidate["exact_rate"] > 0:
        if state["best_exact"] is None or (candidate["exact_rate"], candidate["family5_rate"], -candidate["mean_profile_score"]) > (
            state["best_exact"]["exact_rate"], state["best_exact"]["family5_rate"], -state["best_exact"]["mean_profile_score"]
        ):
            state["best_exact"] = candidate
            notes.append(f"new exact best {candidate['template_key']} @ {candidate['axis_subset_key']}")
    return notes


def evaporate_and_deposit(state: dict, elites: list[dict]) -> None:
    rho = 0.08
    for key in state["pheromones"]["template"]:
        state["pheromones"]["template"][key] *= (1.0 - rho)
    for key in state["pheromones"]["subset"]:
        state["pheromones"]["subset"][key] *= (1.0 - rho)
    for subset_key, buckets in state["pheromones"]["line"].items():
        for bucket, line_map in buckets.items():
            for line_id in line_map:
                line_map[line_id] *= (1.0 - rho)

    for idx, cand in enumerate(elites):
        deposit = max(0.01, cand["fitness"]) * (1.0 / (1 + idx)) * 0.001
        state["pheromones"]["template"][cand["template_key"]] += deposit
        state["pheromones"]["subset"][cand["axis_subset_key"]] += deposit
        for bucket in ("2", "1", "0"):
            for line_id in cand["selections"][bucket]:
                state["pheromones"]["line"][cand["axis_subset_key"]][bucket][str(line_id)] += deposit


def choose_parents(population: list[dict], rng: np.random.Generator) -> list[dict]:
    ranked = sorted(population, key=lambda c: (-c.get("fitness", 0.0), -c.get("exact_rate", 0.0), -c.get("family5_rate", 0.0)))
    weights = np.linspace(len(ranked), 1, len(ranked))
    idx1 = int(rng.choice(len(ranked), p=weights / weights.sum()))
    idx2 = int(rng.choice(len(ranked), p=weights / weights.sum()))
    return [ranked[idx1], ranked[idx2]]


def compute_progress(state: dict) -> dict:
    generations = state["generation"]
    target = state["target_generations"]
    progress_percent = 100.0 * generations / target if target else 0.0
    touched_templates = sum(1 for stats in state["template_stats"].values() if stats["eval_count"] > 0)
    total_templates = len(TEMPLATES)
    total_planned_candidates = target * (state["population_size"] + state["ant_count"])
    candidate_progress = 100.0 * state["total_candidate_evaluations"] / total_planned_candidates if total_planned_candidates else 0.0
    touched_root_branches = sum(1 for stats in state["root_branch_stats"].values() if stats["eval_count"] > 0)
    total_root_branches = len(ROOT_BRANCHES)
    root_branch_progress = 100.0 * touched_root_branches / total_root_branches if total_root_branches else 0.0
    unique_topology_signatures = len(state.get("topology_signature_stats", {}))
    topology_space_progress = 100.0 * unique_topology_signatures / TOTAL_CANDIDATE_SPACE if TOTAL_CANDIDATE_SPACE else 0.0
    return {
        "generation": generations,
        "progress_percent": progress_percent,
        "touched_templates": touched_templates,
        "total_templates": total_templates,
        "candidate_progress_percent": candidate_progress,
        "touched_root_branches": touched_root_branches,
        "total_root_branches": total_root_branches,
        "root_branch_progress_percent": root_branch_progress,
        "unique_topology_signatures": unique_topology_signatures,
        "total_candidate_space": TOTAL_CANDIDATE_SPACE,
        "topology_space_progress_percent": topology_space_progress,
    }


def top_root_branches(state: dict, limit: int = 8) -> list[tuple[str, dict]]:
    return top_rate_entries(state["root_branch_stats"], limit=limit)


def write_summary(state: dict, summary_path: Path) -> None:
    prog = compute_progress(state)
    elapsed = state["elapsed_wall_seconds"]
    gen_rate = state["generation"] / elapsed if elapsed > 0 else 0.0
    remaining_gens = max(0, state["target_generations"] - state["generation"])
    eta = remaining_gens / gen_rate if gen_rate > 0 else None
    top_templates = top_rate_entries(state["template_stats"], limit=10)
    top_branches = top_root_branches(state, limit=10)
    lines = [
        "# Branch 05 GA+ACO Tree Search Summary",
        "",
        f"- updated: `{state['updated_at']}`",
        f"- status: `{state['status']}`",
        f"- kernel backend: `{state.get('kernel_backend', DEFAULT_KERNEL_BACKEND)}`",
        f"- topology filter: `{state.get('topology_filter_enabled', False)}`",
        f"- topology max evals/signature: `{state.get('topology_max_evals_per_signature', 1)}`",
        f"- priority class templates: `{state.get('priority_class_templates', list(PRIORITY_CLASS_TEMPLATE_KEYS))}`",
        f"- priority class subsets: `{state.get('priority_class_subsets', list(PRIORITY_CLASS_SUBSET_KEYS))}`",
        f"- priority overlay version: `{state.get('priority_overlay_version', 0)}`",
        f"- priority focus template: `{state.get('priority_focus_template_key', PRIORITY_FOCUS_TEMPLATE_KEY)}`",
        f"- priority focus subsets: `{state.get('priority_focus_subset_keys', list(PRIORITY_FOCUS_SUBSET_KEYS))}`",
        f"- priority focus remaining evals: `{state.get('priority_focus_remaining_evals', 0)}` / `{state.get('priority_focus_target_evals', DEFAULT_PRIORITY_FOCUS_EVALS)}`",
        f"- generation: `{state['generation']}` / `{state['target_generations']}`",
        f"- generation progress: `{prog['progress_percent']:.4f}%`",
        f"- candidate evaluations: `{state['total_candidate_evaluations']}`",
        f"- candidate progress: `{prog['candidate_progress_percent']:.4f}%`",
        f"- projection evaluations: `{state['total_projection_evaluations']}`",
        f"- unique topological signatures: `{prog['unique_topology_signatures']}` / `{prog['total_candidate_space']}`",
        f"- topological-space coverage: `{prog['topology_space_progress_percent']:.4f}%`",
        f"- skipped equivalent in-batch (total): `{state.get('topology_skipped_batch_equivalent_total', 0)}`",
        f"- skipped by signature cap (total): `{state.get('topology_skipped_cap_total', 0)}`",
        f"- templates touched: `{prog['touched_templates']}` / `{prog['total_templates']}`",
        f"- root branches touched: `{prog['touched_root_branches']}` / `{prog['total_root_branches']}`",
        f"- root-branch coverage: `{prog['root_branch_progress_percent']:.4f}%`",
        f"- elapsed wall seconds: `{elapsed:.1f}`",
        f"- generations/sec: `{gen_rate:.4f}`",
        f"- ETA: `{humanize_duration_hm(eta)}`",
        f"- best overall: `{state['best_overall']}`",
        f"- best exact: `{state['best_exact']}`",
        "",
        "## Top Templates By Running Family-5 Rate",
    ]
    for key, stats in top_templates:
        eval_count = max(1, stats["eval_count"])
        lines.append(
            f"- `{key}`: evals=`{stats['eval_count']}`, family5=`{stats['family5_sum']/eval_count:.6f}`, exact=`{stats['exact_sum']/eval_count:.6f}`, best=`{stats['best']}`"
        )
    lines.extend(["", "## Top Root Branches By Running Family-5 Rate"])
    for key, stats in top_branches:
        eval_count = max(1, stats["eval_count"])
        lines.append(
            f"- `{key}`: evals=`{stats['eval_count']}`, family5=`{stats['family5_sum']/eval_count:.6f}`, exact=`{stats['exact_sum']/eval_count:.6f}`, best=`{stats['best']}`"
        )
    summary_path.write_text("\n".join(lines) + "\n")


def append_log(log_path: Path, state: dict, note: str) -> None:
    prog = compute_progress(state)
    elapsed = state["elapsed_wall_seconds"]
    gen_rate = state["generation"] / elapsed if elapsed > 0 else 0.0
    remaining_gens = max(0, state["target_generations"] - state["generation"])
    eta = remaining_gens / gen_rate if gen_rate > 0 else None
    entry = f"""
## {now_string()} — generation {state['generation']}
Что посчитано:
- kernel backend: `{state.get('kernel_backend', DEFAULT_KERNEL_BACKEND)}`
- topology filter: `{state.get('topology_filter_enabled', False)}`
- topology max evals/signature: `{state.get('topology_max_evals_per_signature', 1)}`
- priority class templates: `{state.get('priority_class_templates', list(PRIORITY_CLASS_TEMPLATE_KEYS))}`
- priority class subsets: `{state.get('priority_class_subsets', list(PRIORITY_CLASS_SUBSET_KEYS))}`
- priority overlay version: `{state.get('priority_overlay_version', 0)}`
- priority focus template: `{state.get('priority_focus_template_key', PRIORITY_FOCUS_TEMPLATE_KEY)}`
- priority focus subsets: `{state.get('priority_focus_subset_keys', list(PRIORITY_FOCUS_SUBSET_KEYS))}`
- priority focus remaining evals: `{state.get('priority_focus_remaining_evals', 0)}` / `{state.get('priority_focus_target_evals', DEFAULT_PRIORITY_FOCUS_EVALS)}`
- generations: `{state['generation']}` / `{state['target_generations']}`
- generation progress: `{prog['progress_percent']:.4f}%`
- candidate evaluations: `{state['total_candidate_evaluations']}`
- candidate progress: `{prog['candidate_progress_percent']:.4f}%`
- projection evaluations: `{state['total_projection_evaluations']}`
- unique topological signatures: `{prog['unique_topology_signatures']}` / `{prog['total_candidate_space']}`
- topological-space coverage: `{prog['topology_space_progress_percent']:.4f}%`
- skipped equivalent in-batch total: `{state.get('topology_skipped_batch_equivalent_total', 0)}`
- skipped by signature cap total: `{state.get('topology_skipped_cap_total', 0)}`
- templates touched: `{prog['touched_templates']}` / `{prog['total_templates']}`
- root branches touched: `{prog['touched_root_branches']}` / `{prog['total_root_branches']}`
- root-branch coverage: `{prog['root_branch_progress_percent']:.4f}%`
- ETA: `{humanize_duration_hm(eta)}`
Лучший overall:
- `{state['best_overall']}`
Лучший exact:
- `{state['best_exact']}`
Примечание:
- {note}
"""
    with log_path.open("a") as fh:
        fh.write(entry)


def dedup_population(candidates: list[dict]) -> list[dict]:
    best_by_key = {}
    for cand in candidates:
        key = candidate_key(cand)
        if key not in best_by_key or cand["fitness"] > best_by_key[key]["fitness"]:
            best_by_key[key] = cand
    return list(best_by_key.values())


def run_generation(state: dict, rng: np.random.Generator, pool: ProcessPoolExecutor) -> list[str]:
    notes = []
    if not state["population"]:
        seeds = seed_population_from_priors(state, rng)
        state["population"] = seeds
    current_population = state["population"]
    evaluated_population = [cand for cand in current_population if "fitness" in cand]
    elites = sorted(evaluated_population, key=lambda c: (-c.get("fitness", -1e9), -c.get("exact_rate", 0.0), -c.get("family5_rate", 0.0)))[: state["elite_count"]]

    focus_mode = priority_focus_active(state)
    if focus_mode:
        ga_children = [propose_priority_focus_candidate(state, rng, source="priority_ga") for _ in range(state["population_size"])]
        ants = [propose_priority_focus_candidate(state, rng, source="priority_aco") for _ in range(state["ant_count"])]
        notes.append(
            f"priority focus active template={state.get('priority_focus_template_key', PRIORITY_FOCUS_TEMPLATE_KEY)} remaining={state.get('priority_focus_remaining_evals', 0)}"
        )
    else:
        ga_children = []
        while len(ga_children) < state["population_size"]:
            parent_pool = evaluated_population if evaluated_population else current_population
            parents = choose_parents(parent_pool, rng)
            ga_children.append(propose_ga_child(state, parents, rng))
        ants = [propose_ant_candidate(state, rng) for _ in range(state["ant_count"])]
    batch = ga_children + ants

    skipped_batch_equivalent = 0
    skipped_signature_cap = 0
    if state.get("topology_filter_enabled", False):
        filtered_batch = []
        seen_in_batch: set[str] = set()
        max_evals_per_signature = max(1, int(state.get("topology_max_evals_per_signature", 1)))
        over_cap_candidates: list[tuple[int, dict, str]] = []
        for cand in batch:
            sig = topological_signature(cand)
            if sig in seen_in_batch:
                skipped_batch_equivalent += 1
                continue
            seen_in_batch.add(sig)
            sig_stats = state["topology_signature_stats"].get(sig)
            sig_eval_count = int(sig_stats.get("eval_count", 0)) if sig_stats is not None else 0
            if sig_eval_count >= max_evals_per_signature:
                skipped_signature_cap += 1
                over_cap_candidates.append((sig_eval_count, cand, sig))
                continue
            stamped = dict(cand)
            stamped["_topological_signature"] = sig
            filtered_batch.append(stamped)
        if not filtered_batch and over_cap_candidates:
            # Anti-stall fallback: keep the loop productive when all proposals hit cap.
            # We allow a tiny amount of least-seen signatures to pass in this generation.
            over_cap_candidates.sort(key=lambda item: item[0])
            rescue_count = min(max(1, state["population_size"] // 6), len(over_cap_candidates))
            for _, cand, sig in over_cap_candidates[:rescue_count]:
                stamped = dict(cand)
                stamped["_topological_signature"] = sig
                filtered_batch.append(stamped)
            notes.append(
                f"topology anti-stall backfill={rescue_count} (all candidates exceeded signature cap)"
            )
        batch = filtered_batch
        state["topology_skipped_batch_equivalent_total"] += skipped_batch_equivalent
        state["topology_skipped_cap_total"] += skipped_signature_cap
        if skipped_batch_equivalent or skipped_signature_cap:
            notes.append(
                f"topology filter skipped batch_equivalent={skipped_batch_equivalent}, signature_cap={skipped_signature_cap}"
            )

    if not batch:
        state["generation"] += 1
        state["checkpoint_count"] += 1
        notes.append("no fresh candidates after topology filter")
        return notes

    seeds = []
    for _ in batch:
        seeds.append(state["next_seed"])
        state["next_seed"] += 1

    evaluated = []
    future_to_signature: dict = {}
    futures = []
    for cand, seed in zip(batch, seeds):
        sig = cand.pop("_topological_signature", None)
        future = pool.submit(evaluate_candidate, cand, state["projection_batch"], seed)
        futures.append(future)
        future_to_signature[future] = sig

    for future in as_completed(futures):
        cand = future.result()
        signature = future_to_signature.get(future)
        if signature is not None:
            sig_stats = state["topology_signature_stats"].setdefault(
                signature,
                {
                    "eval_count": 0,
                    "first_generation": state["generation"],
                    "best_fitness": -1e18,
                    "best_template_key": None,
                    "best_axis_subset_key": None,
                    "best_candidate_key": None,
                },
            )
            sig_stats["eval_count"] += 1
            if cand["fitness"] > sig_stats["best_fitness"]:
                sig_stats["best_fitness"] = cand["fitness"]
                sig_stats["best_template_key"] = cand["template_key"]
                sig_stats["best_axis_subset_key"] = cand["axis_subset_key"]
                sig_stats["best_candidate_key"] = candidate_key(cand)
        evaluated.append(cand)
        update_template_stats(state, cand)
        update_root_branch_stats(state, cand)
        notes.extend(maybe_update_bests(state, cand))

    state["total_candidate_evaluations"] += len(evaluated)
    state["total_projection_evaluations"] += len(evaluated) * state["projection_batch"]
    if focus_mode:
        remaining = int(state.get("priority_focus_remaining_evals", 0))
        remaining = max(0, remaining - len(evaluated))
        state["priority_focus_remaining_evals"] = remaining
        if remaining == 0:
            focus_key = str(state.get("priority_focus_template_key", PRIORITY_FOCUS_TEMPLATE_KEY))
            focus_stats = state.get("template_stats", {}).get(focus_key, {})
            notes.append(
                f"priority focus completed template={focus_key} evals={int(focus_stats.get('eval_count', 0))}"
            )
    combined = dedup_population(elites + evaluated)
    combined.sort(key=lambda c: (-c["fitness"], -c["exact_rate"], -c["family5_rate"], c["mean_profile_score"]))
    state["population"] = combined[: state["population_size"]]
    evaporate_and_deposit(state, state["population"][: max(1, state["elite_count"] * 2)])
    state["generation"] += 1
    state["checkpoint_count"] += 1
    return notes


def run_loop(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "ga_aco_state.json"
    summary_path = state_dir / "ga_aco_summary.md"
    log_path = state_dir / "ga_aco_log.md"
    bootstrap_path = state_dir / "ga_aco_bootstrap.md"
    state = load_state(state_path, args)
    if not log_path.exists():
        log_path.write_text("# GA+ACO Async Log\n")
    if not bootstrap_path.exists():
        priors = state["priors"]
        strongest_templates = sorted(priors["template_heuristic"].items(), key=lambda kv: (-kv[1], kv[0]))[:12]
        bootstrap_path.write_text(
            "# GA+ACO Bootstrap\n\n"
            f"- old brute source: `{state['bootstrap_sources']['old_brute_state']}`\n"
            f"- branch10 source: `{state['bootstrap_sources']['branch10_search']}`\n"
            f"- harmonic raw matrix: `{priors['raw_matrix']}`\n"
            f"- harmonic smoothed matrix: `{priors['smooth_matrix']}`\n"
            f"- strongest template heuristics: `{strongest_templates}`\n"
        )
    state["status"] = "running"
    rng = np.random.default_rng(state["next_seed"])
    start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=worker_initializer, initargs=(args.kernel_backend,)) as pool:
        while state["generation"] < state["target_generations"]:
            notes = run_generation(state, rng, pool)
            state["elapsed_wall_seconds"] += time.time() - start
            start = time.time()
            state["updated_at"] = now_string()
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
            write_summary(state, summary_path)
            if state["checkpoint_count"] % args.log_every == 0 or notes:
                append_log(log_path, state, "; ".join(notes) if notes else "regular checkpoint")
            if args.max_generations is not None and state["generation"] >= args.max_generations:
                state["status"] = "paused"
                break
    if state["generation"] >= state["target_generations"]:
        state["status"] = "completed"
    state["updated_at"] = now_string()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
    write_summary(state, summary_path)
    append_log(log_path, state, f"loop exit status={state['status']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--population-size", type=int, default=DEFAULT_POPULATION)
    parser.add_argument("--ant-count", type=int, default=DEFAULT_ANTS)
    parser.add_argument("--elite-count", type=int, default=DEFAULT_ELITES)
    parser.add_argument("--projection-batch", type=int, default=DEFAULT_PROJECTION_BATCH)
    parser.add_argument("--target-generations", type=int, default=DEFAULT_TARGET_GENERATIONS)
    parser.add_argument("--log-every", type=int, default=DEFAULT_LOG_EVERY)
    parser.add_argument("--max-generations", type=int, default=None)
    parser.add_argument("--kernel-backend", default=DEFAULT_KERNEL_BACKEND, choices=["rust_persistent", "python"])
    parser.add_argument("--topology-max-evals-per-signature", type=int, default=DEFAULT_TOPOLOGY_MAX_EVALS_PER_SIGNATURE)
    parser.add_argument("--topology-filter", dest="topology_filter", action="store_true")
    parser.add_argument("--no-topology-filter", dest="topology_filter", action="store_false")
    parser.set_defaults(topology_filter=DEFAULT_TOPOLOGY_FILTER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    return run_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
