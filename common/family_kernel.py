from __future__ import annotations

import atexit
import json
import math
import os
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

DEFAULT_TARGET_FAMILY_COUNT = 5
DEFAULT_TARGET_PROFILE = (3, 4, 6, 6, 8)
DEFAULT_FOCUSED_PROFILE = (1, 1, 1, 1, 6)
DEFAULT_ANGLE_TOL_DEG = 1.5
ROOT = Path(__file__).resolve().parents[2]
_RUST_SERVER_PROC: subprocess.Popen[str] | None = None
_RUST_SERVER_LOCK = threading.Lock()
_RUST_SERVER_BINARY: Path | None = None


def root_line_key(vec: np.ndarray, tol: float = 1e-9):
    idx = next(i for i, x in enumerate(vec) if abs(float(x)) > tol)
    if vec[idx] < 0:
        vec = -vec
    scale = float(vec[idx])
    normalized = vec / scale
    return tuple(round(float(x), 8) for x in normalized.tolist())


def unique_line_representatives(vectors: np.ndarray) -> list[np.ndarray]:
    reps = []
    seen = set()
    for vec in vectors:
        key = root_line_key(vec.copy())
        if key not in seen:
            seen.add(key)
            reps.append(vec)
    return reps


def random_projection(rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(4, 4))
    q, _ = np.linalg.qr(matrix)
    return np.vstack([q[0], q[1]])


def angle_mod_180(vec: np.ndarray) -> float:
    return (math.degrees(math.atan2(float(vec[1]), float(vec[0]))) + 180.0) % 180.0


def clustered_family_counts(vectors: list[np.ndarray], projection: np.ndarray, tol: float = DEFAULT_ANGLE_TOL_DEG) -> list[int]:
    projected = [(projection @ np.asarray(vec, dtype=float).reshape(-1, 1)).reshape(-1) for vec in vectors]
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


def profile_score(
    counts: list[int],
    *,
    target_family_count: int = DEFAULT_TARGET_FAMILY_COUNT,
    target_total: int = 27,
    target_profile: tuple[int, ...] = DEFAULT_TARGET_PROFILE,
) -> float:
    families = len(counts)
    if families == 0:
        return 1e9
    total = sum(counts)
    counts_sorted = sorted(counts)
    target_scaled = sorted(total * value / target_total for value in target_profile)
    usable_target = target_scaled[:families] if families < len(target_scaled) else target_scaled + [0.0] * (families - len(target_scaled))
    l1 = sum(abs(float(a) - float(b)) for a, b in zip(counts_sorted, usable_target))
    return 100.0 * abs(families - target_family_count) + l1


def candidate_quality(family5_rate: float, exact_rate: float, mean_profile_score: float) -> float:
    return 10000.0 * exact_rate + 1000.0 * family5_rate + 10.0 / (1.0 + mean_profile_score)


def evaluate_vectors_python(
    vectors: list[np.ndarray],
    *,
    projection_batch: int,
    seed: int,
    target_family_count: int = DEFAULT_TARGET_FAMILY_COUNT,
    target_profile: tuple[int, ...] = DEFAULT_TARGET_PROFILE,
    focused_profile: tuple[int, ...] = DEFAULT_FOCUSED_PROFILE,
    tol: float = DEFAULT_ANGLE_TOL_DEG,
) -> dict:
    rng = np.random.default_rng(seed)
    family5_hits = 0
    exact_hits = 0
    mean_profile = 0.0
    family_hist: dict[int, int] = {}
    best_counts: list[int] | None = None
    best_score: float | None = None
    best_family_gap = 999
    for _ in range(projection_batch):
        projection = random_projection(rng)
        counts = clustered_family_counts(vectors, projection, tol=tol)
        sorted_counts = sorted(counts)
        fam_count = len(counts)
        score = profile_score(counts, target_family_count=target_family_count, target_profile=target_profile)
        mean_profile += score
        family_hist[fam_count] = family_hist.get(fam_count, 0) + 1
        if fam_count == target_family_count:
            family5_hits += 1
        if tuple(sorted_counts) == tuple(focused_profile):
            exact_hits += 1
        family_gap = abs(fam_count - target_family_count)
        if best_score is None or (score, family_gap) < (best_score, best_family_gap):
            best_score = score
            best_family_gap = family_gap
            best_counts = sorted_counts
    mean_profile /= projection_batch
    family5_rate = family5_hits / projection_batch
    exact_rate = exact_hits / projection_batch
    return {
        "family5_hits": family5_hits,
        "exact_hits": exact_hits,
        "family5_rate": family5_rate,
        "exact_rate": exact_rate,
        "mean_profile_score": mean_profile,
        "fitness": candidate_quality(family5_rate, exact_rate, mean_profile),
        "family_histogram": family_hist,
        "best_counts": best_counts,
        "best_profile_score": best_score,
    }


def shared_rust_kernel_dir() -> Path:
    return ROOT / "research" / "rust" / "projection_family_kernel"


def ensure_rust_kernel_built(kernel_dir: Path | None = None) -> Path:
    kernel_dir = kernel_dir or shared_rust_kernel_dir()
    subprocess.run(["cargo", "build", "--release"], cwd=kernel_dir, check=True)
    binary_name = kernel_dir.name.replace("-", "_")
    return kernel_dir / "target" / "release" / binary_name


def init_rust_kernel_server(kernel_dir: Path | None = None) -> Path:
    global _RUST_SERVER_PROC, _RUST_SERVER_BINARY
    with _RUST_SERVER_LOCK:
        if _RUST_SERVER_PROC is not None and _RUST_SERVER_PROC.poll() is None:
            assert _RUST_SERVER_BINARY is not None
            return _RUST_SERVER_BINARY
        kernel_dir = kernel_dir or shared_rust_kernel_dir()
        binary = ensure_rust_kernel_built(kernel_dir)
        _RUST_SERVER_PROC = subprocess.Popen(
            [str(binary), "--server"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        _RUST_SERVER_BINARY = binary
        return binary


def shutdown_rust_kernel_server() -> None:
    global _RUST_SERVER_PROC
    with _RUST_SERVER_LOCK:
        if _RUST_SERVER_PROC is None:
            return
        proc = _RUST_SERVER_PROC
        _RUST_SERVER_PROC = None
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


atexit.register(shutdown_rust_kernel_server)


def evaluate_vectors_rust(
    vectors: list[np.ndarray] | list[list[float]],
    *,
    projection_batch: int,
    seed: int,
    kernel_dir: Path | None = None,
) -> dict:
    kernel_dir = kernel_dir or shared_rust_kernel_dir()
    binary = ensure_rust_kernel_built(kernel_dir)
    payload = {
        "vectors": [[float(x) for x in vec] for vec in vectors],
        "projection_batch": projection_batch,
        "seed": seed,
    }
    with tempfile.TemporaryDirectory(prefix="projection-family-kernel-") as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=True))
        raw = subprocess.check_output([str(binary), str(input_path)], cwd=ROOT, text=True)
    return json.loads(raw)


def evaluate_vectors_rust_persistent(
    vectors: list[np.ndarray] | list[list[float]],
    *,
    projection_batch: int,
    seed: int,
    kernel_dir: Path | None = None,
) -> dict:
    init_rust_kernel_server(kernel_dir)
    payload = {
        "vectors": [[float(x) for x in vec] for vec in vectors],
        "projection_batch": projection_batch,
        "seed": seed,
    }
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    with _RUST_SERVER_LOCK:
        proc = _RUST_SERVER_PROC
        if proc is None or proc.poll() is not None or proc.stdin is None or proc.stdout is None:
            raise RuntimeError("rust kernel server is not available")
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        raw = proc.stdout.readline()
    if not raw:
        raise RuntimeError("rust kernel server returned empty response")
    data = json.loads(raw)
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"rust kernel server error: {data['error']}")
    return data


def configured_kernel_backend(default: str = "rust_persistent") -> str:
    return os.environ.get("RUNES_FAMILY_KERNEL_BACKEND", default).strip().lower()
