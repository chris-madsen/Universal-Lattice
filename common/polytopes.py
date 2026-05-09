#!/usr/bin/env python3
from __future__ import annotations

import itertools
import math
from typing import List, Tuple

import numpy as np


def canonical_24cell_vertices() -> np.ndarray:
    verts = set()
    for perm in set(itertools.permutations([1, 1, 0, 0], 4)):
        nz = [i for i, v in enumerate(perm) if v != 0]
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                p = list(perm)
                p[nz[0]] *= s1
                p[nz[1]] *= s2
                verts.add(tuple(p))
    V = np.array(sorted(verts), dtype=float)
    if V.shape != (24, 4):
        raise ValueError(f"unexpected 24-cell vertex shape: {V.shape}")
    return V


def canonical_24cell_edges(vertices: np.ndarray, tol: float = 1e-9) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    target = math.sqrt(2.0)
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            d = float(np.linalg.norm(vertices[i] - vertices[j]))
            if abs(d - target) < tol:
                edges.append((i, j))
    if len(edges) != 96:
        raise ValueError(f"unexpected 24-cell edge count: {len(edges)}")
    return edges



def canonical_f4_roots() -> np.ndarray:
    short = set()
    long = set()

    # short roots: coordinate axes
    for i in range(4):
        for s in (-1, 1):
            vec = [0.0, 0.0, 0.0, 0.0]
            vec[i] = float(s)
            short.add(tuple(vec))

    # short roots: half-integer shell
    for signs in itertools.product((-0.5, 0.5), repeat=4):
        short.add(tuple(signs))

    # long roots: permutations of (+/-1, +/-1, 0, 0)
    for perm in set(itertools.permutations([1.0, 1.0, 0.0, 0.0], 4)):
        nz = [i for i, v in enumerate(perm) if v != 0.0]
        for s1 in (-1.0, 1.0):
            for s2 in (-1.0, 1.0):
                p = list(perm)
                p[nz[0]] *= s1
                p[nz[1]] *= s2
                long.add(tuple(p))

    roots = np.array(sorted(short | long), dtype=float)
    if roots.shape != (48, 4):
        raise ValueError(f"unexpected F4 root count: {roots.shape}")
    return roots
