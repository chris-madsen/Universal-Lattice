from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import numpy as np


def now_string(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(fmt)


def humanize_duration_hm(seconds: float | None) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "n/a"
    total_minutes = max(0, int(round(seconds / 60.0)))
    days, rem_minutes = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(rem_minutes, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def weighted_choice(items: list[Any], weights: list[float], rng: np.random.Generator):
    arr = np.array(weights, dtype=float)
    if np.all(arr <= 0):
        arr = np.ones_like(arr)
    arr = arr / arr.sum()
    return items[int(rng.choice(len(items), p=arr))]


def weighted_sample_without_replacement(items: list[int], weights: list[float], k: int, rng: np.random.Generator) -> list[int]:
    if k <= 0:
        return []
    pool_items = list(items)
    pool_weights = list(weights)
    chosen = []
    for _ in range(min(k, len(pool_items))):
        arr = np.array(pool_weights, dtype=float)
        if np.all(arr <= 0):
            arr = np.ones_like(arr)
        arr = arr / arr.sum()
        idx = int(rng.choice(len(pool_items), p=arr))
        chosen.append(pool_items.pop(idx))
        pool_weights.pop(idx)
    return chosen


def low_pass_harmonic_prior_from_matrix(
    raw_matrix: list[list[float]] | np.ndarray,
    keep_rows: int = 2,
    keep_cols: int = 3,
    floor: float = 0.05,
) -> np.ndarray:
    raw = np.array(raw_matrix, dtype=float)
    freq = np.fft.rfft2(raw)
    keep = np.zeros_like(freq)
    keep[: min(keep_rows, keep.shape[0]), : min(keep_cols, keep.shape[1])] = freq[
        : min(keep_rows, freq.shape[0]), : min(keep_cols, freq.shape[1])
    ]
    smooth = np.fft.irfft2(keep, s=raw.shape).real
    smooth -= smooth.min()
    if smooth.max() > 0:
        smooth /= smooth.max()
    smooth += floor
    return smooth


def rate_tuple(stats: dict, key: str) -> tuple[float, float, str]:
    eval_count = max(1, int(stats.get("eval_count", 0)))
    family5_rate = float(stats.get("family5_sum", 0.0)) / eval_count
    exact_rate = float(stats.get("exact_sum", 0.0)) / eval_count
    return family5_rate, exact_rate, key


def top_rate_entries(stats_map: dict[str, dict], limit: int = 10) -> list[tuple[str, dict]]:
    return sorted(
        stats_map.items(),
        key=lambda kv: (-rate_tuple(kv[1], kv[0])[0], -rate_tuple(kv[1], kv[0])[1], kv[0]),
    )[:limit]
