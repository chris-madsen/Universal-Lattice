#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = ROOT / "research" / "async_state" / "branch05_ab" / "no_filter" / "ga_aco_state.json"
OUT_DIR = ROOT / "research" / "B_symmetry_arrangement_models" / "12_topology_signature_filter" / "figures"
SIMPLIFIED_OUT = OUT_DIR / "h12_simplified_lattice.png"
BEST_OUT = OUT_DIR / "h12_best_candidate_grid.png"
REPORT_OUT = OUT_DIR / "h12_best_candidate_grid_report.md"


def load_best_candidate() -> dict:
    state = json.loads(STATE_PATH.read_text())
    best = state.get("best_overall")
    if not best:
        raise RuntimeError(f"best_overall missing in {STATE_PATH}")
    return best


def circular_distance_deg(a: float, b: float) -> float:
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def orientation_deg(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    if abs(angle - 180.0) < 1e-9:
        return 0.0
    return angle


def has_intermediate_collinear_point(
    p1: tuple[float, float],
    p2: tuple[float, float],
    points: list[tuple[float, float]],
    eps: float = 1e-9,
) -> bool:
    x1, y1 = p1
    x2, y2 = p2
    for x, y in points:
        if (x, y) == p1 or (x, y) == p2:
            continue
        area2 = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if abs(area2) > eps:
            continue
        if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
            return True
    return False


def normalize_segment(seg: tuple[tuple[float, float], tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    a, b = seg
    return (a, b) if a <= b else (b, a)


def cluster_angles(angles: Iterable[float], tol_deg: float = 1.5) -> list[float]:
    ordered = sorted(float(a) % 180.0 for a in angles)
    if not ordered:
        return []
    groups: list[list[float]] = [[ordered[0]]]
    for angle in ordered[1:]:
        if abs(angle - groups[-1][-1]) <= tol_deg:
            groups[-1].append(angle)
        else:
            groups.append([angle])
    centers = [sum(g) / len(g) for g in groups]
    return centers


def simplified_nodes() -> list[tuple[float, float]]:
    xs = [0.0, 1.0, 2.0]
    ys = [0.0, 1.0, 1.5, 2.0, 3.0]
    return [(x, y) for x in xs for y in ys]


def simplified_segments() -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for x in [0.0, 1.0, 2.0]:
        segs.append(((x, 0.0), (x, 3.0)))
    center = (1.0, 1.5)
    for target in [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0), (0.0, 3.0), (2.0, 0.0), (2.0, 1.0), (2.0, 2.0), (2.0, 3.0)]:
        segs.append((center, target))
    return [normalize_segment(s) for s in segs]


def render_grid(
    out_path: Path,
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    title: str,
    line_color: str,
) -> None:
    fig, ax = plt.subplots(figsize=(6, 9))
    for (x1, y1), (x2, y2) in segments:
        ax.plot([x1, x2], [y1, y2], color=line_color, lw=1.8, zorder=2)

    for x, y in simplified_nodes():
        ax.scatter(x, y, color="#d33", s=35, zorder=3)

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=12)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def best_projection_for_candidate(module, candidate: dict, projection_batch: int = 96) -> tuple[np.ndarray, list[int]]:
    vectors = module.selected_vectors(candidate)
    seed = int(candidate.get("evaluation_seed", 0))
    rng = np.random.default_rng(seed)
    best_projection = None
    best_counts = None
    best_key = None
    for _ in range(projection_batch):
        projection = module.random_projection(rng)
        counts = module.clustered_family_counts(vectors, projection, tol=1.5)
        score = float(module.profile_score(counts))
        fam_gap = abs(len(counts) - 5)
        key = (score, fam_gap)
        if best_key is None or key < best_key:
            best_key = key
            best_projection = projection
            best_counts = sorted(counts)
    if best_projection is None or best_counts is None:
        raise RuntimeError("failed to derive best projection")
    return best_projection, best_counts


def candidate_family_angles(module, candidate: dict) -> list[float]:
    projection, _ = best_projection_for_candidate(module, candidate, projection_batch=96)
    vectors = module.selected_vectors(candidate)
    projected = [(projection @ np.asarray(v, dtype=float).reshape(-1, 1)).reshape(-1) for v in vectors]
    usable = [v for v in projected if np.linalg.norm(v) > 1e-9]
    angles = [float((math.degrees(math.atan2(float(v[1]), float(v[0]))) + 180.0) % 180.0) for v in usable]
    return cluster_angles(angles, tol_deg=1.5)


def candidate_grid_segments(
    family_angles: list[float],
    angle_tol_deg: float = 2.0,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    pts = simplified_nodes()
    segs: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for p1, p2 in itertools.combinations(pts, 2):
        angle = orientation_deg(p1, p2)
        if min(circular_distance_deg(angle, fam) for fam in family_angles) > angle_tol_deg:
            continue
        if has_intermediate_collinear_point(p1, p2, pts):
            continue
        segs.append(normalize_segment((p1, p2)))
    return sorted(set(segs))


def main() -> int:
    import importlib.util
    import sys

    module_path = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
    spec = importlib.util.spec_from_file_location("branch05_ga_aco_tree_search", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to import module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    best = load_best_candidate()
    family_angles = candidate_family_angles(module, best)

    simplified = simplified_segments()
    candidate_segments = candidate_grid_segments(family_angles, angle_tol_deg=2.0)

    render_grid(
        SIMPLIFIED_OUT,
        simplified,
"Our simplified grid (central bundle)",
        "#7f7f7f",
    )
    render_grid(
        BEST_OUT,
        candidate_segments,
"Best grid for hypothesis 12 (A2 candidate)",
        "#2255cc",
    )

    simp_angles = sorted({round(orientation_deg(a, b), 6) for a, b in simplified})
    cand_angles = sorted({round(orientation_deg(a, b), 6) for a, b in candidate_segments})
    overlap = set(simp_angles) & set(cand_angles)
    jaccard = (len(overlap) / len(set(simp_angles) | set(cand_angles))) if (set(simp_angles) | set(cand_angles)) else 0.0

    report = [
        "# H12 Grid Render Report",
        "",
        f"- best candidate: `{best.get('template_key')}@{best.get('axis_subset_key')}`",
        f"- best single family5: `{best.get('family5_rate')}`",
        f"- best counts: `{best.get('best_counts')}`",
        f"- derived family angles (deg): `{[round(x, 6) for x in family_angles]}`",
        f"- simplified segments: `{len(simplified)}`",
        f"- candidate segments: `{len(candidate_segments)}`",
        f"- simplified angle classes: `{simp_angles}`",
        f"- candidate angle classes: `{cand_angles}`",
        f"- angle-class overlap: `{sorted(overlap)}`",
        f"- angle-class jaccard: `{jaccard:.6f}`",
        f"- image simplified: `{SIMPLIFIED_OUT}`",
        f"- image candidate: `{BEST_OUT}`",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(report) + "\n")
    print(SIMPLIFIED_OUT)
    print(BEST_OUT)
    print(REPORT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
