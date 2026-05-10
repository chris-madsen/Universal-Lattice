#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TARGET_FAMILY_COUNT = 5
TARGET_PROFILE = (3, 4, 6, 6, 8)
FOCUSED_PROFILE = [1, 1, 1, 1, 6]
CLASS_GRID = [(t, c) for t in (2, 3, 4) for c in (4, 5, 6, 7, 8)]
DEFAULT_TARGET_SAMPLES_PER_CLASS = 2_000_000
DEFAULT_BATCH_SIZE = 20_000
DEFAULT_WORKERS = 2
STATE_VERSION = 1


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def class_key(t_count: int, c_count: int) -> str:
    return f"T{t_count}_C{c_count}"


def root_line_key(vec: np.ndarray, tol: float = 1e-9):
    idx = next(i for i, x in enumerate(vec) if abs(float(x)) > tol)
    if vec[idx] < 0:
        vec = -vec
    scale = float(vec[idx])
    normalized = vec / scale
    return tuple(round(float(x), 8) for x in normalized.tolist())


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def unique_line_representatives(vectors: np.ndarray) -> list[np.ndarray]:
    reps = []
    seen = set()
    for vec in vectors:
        key = root_line_key(vec.copy())
        if key not in seen:
            seen.add(key)
            reps.append(vec)
    return reps


def canonical_24cell_vertices() -> np.ndarray:
    import itertools
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
        for s in (-1.0, 1.0):
            vec = np.zeros(4, dtype=float)
            vec[i] = s
            vectors.append(vec)
    return np.array(vectors, dtype=float)


def random_projection(rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(4, 4))
    q, _ = np.linalg.qr(matrix)
    return np.vstack([q[0], q[1]])


def clustered_family_counts(vectors: list[np.ndarray], projection: np.ndarray, tol: float = 1.5) -> list[int]:
    projected = [(projection @ vec.reshape(-1, 1)).reshape(-1) for vec in vectors]
    usable = [vec for vec in projected if np.linalg.norm(vec) > 1e-9]
    if not usable:
        return []
    decorated = sorted((angle_mod_180(vec), vec) for vec in usable)
    groups = [[decorated[0]]]
    for angle, vec in decorated[1:]:
        if abs(angle - groups[-1][-1][0]) <= tol:
            groups[-1].append((angle, vec))
        else:
            groups.append([(angle, vec)])
    return [len(group) for group in groups]


def profile_score(counts: list[int], target_total: int = 27, target_profile: tuple[int, ...] = TARGET_PROFILE) -> float:
    families = len(counts)
    if families == 0:
        return 1e9
    total = sum(counts)
    counts_sorted = sorted(counts)
    target_scaled = sorted(total * value / target_total for value in target_profile)
    usable_target = target_scaled[:families] if families < len(target_scaled) else target_scaled + [0.0] * (families - len(target_scaled))
    l1 = sum(abs(float(a) - float(b)) for a, b in zip(counts_sorted, usable_target))
    return 100.0 * abs(families - TARGET_FAMILY_COUNT) + l1


_AXIS_LINES = None
_CELL_LINES = None


def get_lines() -> tuple[list[np.ndarray], list[np.ndarray]]:
    global _AXIS_LINES, _CELL_LINES
    if _AXIS_LINES is None or _CELL_LINES is None:
        _AXIS_LINES = unique_line_representatives(tesseract_axis_vectors())
        _CELL_LINES = unique_line_representatives(canonical_24cell_vertices())
    return _AXIS_LINES, _CELL_LINES


def sample_chunk(t_count: int, c_count: int, sample_count: int, seed: int) -> dict:
    axis_lines, cell_lines = get_lines()
    rng = np.random.default_rng(seed)
    family5_hits = 0
    exact_hits = 0
    family_hist: Dict[int, int] = {}
    best = None
    for _ in range(sample_count):
        chosen_axes = [axis_lines[i] for i in rng.choice(len(axis_lines), size=t_count, replace=False)]
        chosen_cell = [cell_lines[i] for i in rng.choice(len(cell_lines), size=c_count, replace=False)]
        projection = random_projection(rng)
        counts = clustered_family_counts(chosen_axes + chosen_cell, projection, tol=1.5)
        sorted_counts = sorted(counts)
        fam_count = len(counts)
        family_hist[fam_count] = family_hist.get(fam_count, 0) + 1
        exact = sorted_counts == FOCUSED_PROFILE
        if fam_count == TARGET_FAMILY_COUNT:
            family5_hits += 1
        if exact:
            exact_hits += 1
        rec = {
            "class": class_key(t_count, c_count),
            "tesseract_count": t_count,
            "cell_count": c_count,
            "family_count": fam_count,
            "family_multiplicities": sorted_counts,
            "profile_score": profile_score(counts),
            "exact_profile_hit": exact,
        }
        if best is None or (rec["profile_score"], abs(rec["family_count"] - TARGET_FAMILY_COUNT)) < (
            best["profile_score"],
            abs(best["family_count"] - TARGET_FAMILY_COUNT),
        ):
            best = rec
    return {
        "class": class_key(t_count, c_count),
        "sample_count": sample_count,
        "family5_hits": family5_hits,
        "exact_hits": exact_hits,
        "family_hist": family_hist,
        "best": best,
    }


def default_state(target_samples_per_class: int, batch_size: int) -> dict:
    classes = {}
    for t_count, c_count in CLASS_GRID:
        classes[class_key(t_count, c_count)] = {
            "t_count": t_count,
            "c_count": c_count,
            "completed_samples": 0,
            "family5_hits": 0,
            "exact_hits": 0,
            "family_hist": {},
            "best": None,
        }
    return {
        "state_version": STATE_VERSION,
        "created_at": now_string(),
        "updated_at": now_string(),
        "target_samples_per_class": target_samples_per_class,
        "batch_size": batch_size,
        "classes": classes,
        "total_samples": 0,
        "next_seed": 1000,
        "checkpoint_count": 0,
        "elapsed_wall_seconds": 0.0,
        "status": "initialized",
    }


def load_state(state_path: Path, target_samples_per_class: int, batch_size: int) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text())
    return default_state(target_samples_per_class, batch_size)


def merge_result(state: dict, result: dict) -> tuple[bool, bool]:
    entry = state["classes"][result["class"]]
    entry["completed_samples"] += result["sample_count"]
    entry["family5_hits"] += result["family5_hits"]
    entry["exact_hits"] += result["exact_hits"]
    for k, v in result["family_hist"].items():
        entry["family_hist"][k] = entry["family_hist"].get(k, 0) + v
    improved = False
    exact_improved = False
    if entry["best"] is None or (
        result["best"]["profile_score"],
        abs(result["best"]["family_count"] - TARGET_FAMILY_COUNT),
    ) < (
        entry["best"]["profile_score"],
        abs(entry["best"]["family_count"] - TARGET_FAMILY_COUNT),
    ):
        improved = True
        entry["best"] = result["best"]
    if result["best"]["family_multiplicities"] == FOCUSED_PROFILE:
        current_exact = entry.get("best_exact")
        if current_exact is None or result["best"]["profile_score"] < current_exact["profile_score"]:
            entry["best_exact"] = result["best"]
            exact_improved = True
    state["total_samples"] += result["sample_count"]
    return improved, exact_improved


def compute_progress(state: dict) -> dict:
    target = state["target_samples_per_class"]
    class_rows = []
    variants_started = 0
    variants_completed = 0
    for key, entry in state["classes"].items():
        completed = entry["completed_samples"]
        remaining = max(0, target - completed)
        family_rate = entry["family5_hits"] / completed if completed else 0.0
        exact_rate = entry["exact_hits"] / completed if completed else 0.0
        progress_percent = 100.0 * completed / target if target else 0.0
        if completed > 0:
            variants_started += 1
        if completed >= target:
            variants_completed += 1
        class_rows.append({
            "class": key,
            "completed": completed,
            "remaining": remaining,
            "progress_percent": progress_percent,
            "family5_rate": family_rate,
            "exact_rate": exact_rate,
            "best": entry["best"],
        })
    by_family = sorted(class_rows, key=lambda r: (-r["family5_rate"], -r["exact_rate"], r["class"]))
    by_exact = sorted(class_rows, key=lambda r: (-r["exact_rate"], -r["family5_rate"], r["class"]))
    total_target = target * len(state["classes"])
    overall_progress_percent = 100.0 * state["total_samples"] / total_target if total_target else 0.0
    return {
        "rows": class_rows,
        "best_family": by_family[0],
        "best_exact": by_exact[0],
        "variants_total": len(state["classes"]),
        "variants_started": variants_started,
        "variants_completed": variants_completed,
        "overall_progress_percent": overall_progress_percent,
    }


def write_summary(state: dict, summary_path: Path) -> None:
    prog = compute_progress(state)
    target = state["target_samples_per_class"]
    total_target = target * len(state["classes"])
    remaining = total_target - state["total_samples"]
    elapsed = state["elapsed_wall_seconds"]
    rate = state["total_samples"] / elapsed if elapsed > 0 else 0.0
    eta = remaining / rate if rate > 0 else None
    lines = [
        "# Branch 05 Async Ridge Search Summary",
        "",
        f"- updated: `{state['updated_at']}`",
        f"- status: `{state['status']}`",
        f"- total samples: `{state['total_samples']}` / `{total_target}`",
        f"- overall progress: `{prog['overall_progress_percent']:.4f}%`",
        f"- variants started: `{prog['variants_started']}` / `{prog['variants_total']}`",
        f"- variants completed: `{prog['variants_completed']}` / `{prog['variants_total']}`",
        f"- elapsed wall seconds: `{elapsed:.1f}`",
        f"- effective samples/sec: `{rate:.1f}`",
        f"- ETA seconds: `{eta:.1f}`" if eta is not None else "- ETA seconds: `n/a`",
        f"- best family5 class: `{prog['best_family']['class']}` rate=`{prog['best_family']['family5_rate']:.6f}`",
        f"- best exact class: `{prog['best_exact']['class']}` rate=`{prog['best_exact']['exact_rate']:.6f}`",
        "",
        "## Per-Class Progress",
    ]
    for row in sorted(prog["rows"], key=lambda r: r["class"]):
        lines.append(
            f"- `{row['class']}`: completed=`{row['completed']}`, remaining=`{row['remaining']}`, progress=`{row['progress_percent']:.4f}%`, family5=`{row['family5_rate']:.6f}`, exact=`{row['exact_rate']:.6f}`, best=`{row['best']}`"
        )
    summary_path.write_text("\n".join(lines) + "\n")


def append_log(log_path: Path, state: dict, note: str) -> None:
    prog = compute_progress(state)
    target = state["target_samples_per_class"]
    total_target = target * len(state["classes"])
    remaining = total_target - state["total_samples"]
    elapsed = state["elapsed_wall_seconds"]
    rate = state["total_samples"] / elapsed if elapsed > 0 else 0.0
    eta = remaining / rate if rate > 0 else None
    entry = f"""
## {now_string()} — checkpoint {state['checkpoint_count']}
Target:
- in-depth async search for ridge classes of the `05_24cell_tesseract_interaction` branch.
What is counted:
- total samples: `{state['total_samples']}` / `{total_target}`
- overall progress: `{prog['overall_progress_percent']:.4f}%`
- variants started/completed: `{prog['variants_started']}` / `{prog['variants_completed']}` / `{prog['variants_total']}`
- remaining samples: `{remaining}`
- effective samples/sec: `{rate:.1f}`
- ETA sec: `{eta:.1f}`
Best family5-class:
- `{prog['best_family']['class']}` rate=`{prog['best_family']['family5_rate']:.6f}`
Best exact-profile class:
- `{prog['best_exact']['class']}` rate=`{prog['best_exact']['exact_rate']:.6f}`
Note:
- {note}
"""
    with log_path.open("a") as fh:
        fh.write(entry)


def choose_tasks(state: dict, workers: int) -> list[tuple[int, int, int, int]]:
    target = state["target_samples_per_class"]
    batch = state["batch_size"]
    pending = []
    for key, entry in state["classes"].items():
        remaining = target - entry["completed_samples"]
        if remaining > 0:
            pending.append((remaining, key, entry))
    pending.sort(key=lambda item: (-item[0], item[1]))
    chosen = []
    for _, key, entry in pending[:workers]:
        seed = state["next_seed"]
        state["next_seed"] += 1
        chosen.append((entry["t_count"], entry["c_count"], min(batch, target - entry["completed_samples"]), seed))
    return chosen


def run_loop(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    summary_path = state_dir / "summary.md"
    log_path = state_dir / "log.md"
    state = load_state(state_path, args.target_samples_per_class, args.batch_size)
    start = time.time()
    if not log_path.exists():
        log_path.write_text("# Async Log\n")
    state["status"] = "running"
    max_checkpoints = args.max_checkpoints
    made_progress = False

    while True:
        tasks = choose_tasks(state, args.workers)
        if not tasks:
            state["status"] = "completed"
            break
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(sample_chunk, t, c, n, seed) for t, c, n, seed in tasks]
            notes = []
            for future in as_completed(futures):
                result = future.result()
                improved, exact_improved = merge_result(state, result)
                note = f"merged {result['sample_count']} for {result['class']}"
                if improved:
                    note += "; new best profile"
                if exact_improved:
                    note += "; new best exact-profile"
                notes.append(note)
                made_progress = True
        state["checkpoint_count"] += 1
        state["elapsed_wall_seconds"] += time.time() - start
        start = time.time()
        state["updated_at"] = now_string()
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
        write_summary(state, summary_path)
        if state["checkpoint_count"] % args.log_every == 0 or any("new best" in note for note in notes):
            append_log(log_path, state, "; ".join(notes))
        if max_checkpoints is not None and state["checkpoint_count"] >= max_checkpoints:
            state["status"] = "paused"
            break
    state["updated_at"] = now_string()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=True))
    write_summary(state, summary_path)
    if made_progress:
        append_log(log_path, state, f"loop exit with status={state['status']}")
    return 0


def benchmark(args: argparse.Namespace) -> int:
    t0 = time.time()
    bench_args = argparse.Namespace(**vars(args))
    bench_args.max_checkpoints = 2
    run_loop(bench_args)
    elapsed = time.time() - t0
    state_path = Path(args.state_dir) / "state.json"
    state = json.loads(state_path.read_text())
    samples = state["total_samples"]
    rate = samples / elapsed if elapsed > 0 else 0.0
    print(json.dumps({
        "elapsed_sec": elapsed,
        "samples": samples,
        "samples_per_sec": rate,
        "workers": args.workers,
        "batch_size": args.batch_size,
        "classes_in_round": min(args.workers, len(CLASS_GRID)),
    }, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(ROOT / "research" / "async_state" / "branch05_ridge"))
    parser.add_argument("--target-samples-per-class", type=int, default=DEFAULT_TARGET_SAMPLES_PER_CLASS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--log-every", type=int, default=5)
    parser.add_argument("--max-checkpoints", type=int, default=None)
    parser.add_argument("--benchmark", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    if args.benchmark:
        return benchmark(args)
    return run_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
