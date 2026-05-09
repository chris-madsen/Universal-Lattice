from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class SignedPermutationAction:
    perm: tuple[int, ...]
    signs: tuple[int, ...]


def root_line_key_signature(vec: np.ndarray, tol: float = 1e-9) -> tuple[float, ...]:
    idx = next(i for i, x in enumerate(vec) if abs(float(x)) > tol)
    if vec[idx] < 0:
        vec = -vec
    scale = float(vec[idx])
    normalized = vec / scale
    return tuple(round(float(x), 8) for x in normalized.tolist())


def signed_permutation_actions(dim: int = 4) -> list[SignedPermutationAction]:
    actions: list[SignedPermutationAction] = []
    for perm in itertools.permutations(range(dim)):
        for signs in itertools.product((-1, 1), repeat=dim):
            actions.append(SignedPermutationAction(perm=tuple(int(x) for x in perm), signs=tuple(int(x) for x in signs)))
    return actions


def transform_vector(vec: np.ndarray, action: SignedPermutationAction) -> np.ndarray:
    return np.array(
        [float(action.signs[i]) * float(vec[action.perm[i]]) for i in range(len(action.perm))],
        dtype=float,
    )


def canonical_grouped_line_signature(
    vectors_by_group: dict[str, Sequence[np.ndarray]],
    *,
    dim: int = 4,
    tol: float = 1e-9,
    actions: Iterable[SignedPermutationAction] | None = None,
) -> str:
    action_list = list(actions) if actions is not None else signed_permutation_actions(dim=dim)
    group_order = sorted(vectors_by_group.keys())
    best: tuple | None = None

    for action in action_list:
        rep = []
        for group in group_order:
            keys = sorted(
                root_line_key_signature(transform_vector(np.asarray(vec, dtype=float), action), tol=tol)
                for vec in vectors_by_group[group]
            )
            rep.append((group, tuple(keys)))
        rep_tuple = tuple(rep)
        if best is None or rep_tuple < best:
            best = rep_tuple

    return repr(best)
