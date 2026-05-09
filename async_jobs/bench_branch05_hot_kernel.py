#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_python, evaluate_vectors_rust, shared_rust_kernel_dir

GA_PATH = ROOT / 'research' / 'async_jobs' / 'branch05_ga_aco_tree_search.py'
OUT_DIR = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data'
STATE_PATH = ROOT / 'research' / 'async_state' / 'branch05_ridge' / 'ga_aco_state.json'


def load_ga_module():
    spec = importlib.util.spec_from_file_location('ga_branch05', GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['ga_branch05'] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def current_best_candidate(state: dict) -> dict:
    return state['best_overall']


def selected_vectors(module, candidate: dict):
    return [[float(x) for x in vec.tolist()] for vec in module.selected_vectors(candidate)]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE_PATH.read_text())
    candidate = current_best_candidate(state)
    module = load_ga_module()

    projection_batch = 25000
    seed = 424242

    vectors = selected_vectors(module, candidate)

    py_start = time.perf_counter()
    py_result = evaluate_vectors_python(vectors, projection_batch=projection_batch, seed=seed)
    py_elapsed = time.perf_counter() - py_start

    rust_start = time.perf_counter()
    rust_result = evaluate_vectors_rust(vectors, projection_batch=projection_batch, seed=seed)
    rust_elapsed = time.perf_counter() - rust_start

    speedup = py_elapsed / rust_elapsed if rust_elapsed > 0 else None

    report = {
        'projection_batch': projection_batch,
        'seed': seed,
        'candidate': candidate,
        'python': {
            'elapsed_sec': py_elapsed,
            'family5_rate': py_result['family5_rate'],
            'exact_rate': py_result['exact_rate'],
            'mean_profile_score': py_result['mean_profile_score'],
            'best_counts': py_result['best_counts'],
            'sec_per_projection': py_elapsed / projection_batch,
        },
        'rust': {
            'elapsed_sec': rust_elapsed,
            'family5_rate': rust_result['family5_rate'],
            'exact_rate': rust_result['exact_rate'],
            'mean_profile_score': rust_result['mean_profile_score'],
            'best_counts': rust_result['best_counts'],
            'sec_per_projection': rust_elapsed / projection_batch,
        },
        'speedup_python_over_rust': speedup,
        'shared_rust_kernel_dir': str(shared_rust_kernel_dir()),
        'note': 'The benchmark compares the shared projection-family core kernel for one live branch-05 candidate. Rust uses the same high-level scoring logic but an independent QR implementation and RNG stream, so throughput is the main comparison target, not bitwise-identical hit counts.',
    }

    json_path = OUT_DIR / 'bench_branch05_hot_kernel.json'
    md_path = OUT_DIR / 'bench_branch05_hot_kernel.md'
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    md_path.write_text(
        '# Branch 05 Hot Kernel Benchmark\n\n'
        f"- projection batch: `{projection_batch}`\n"
        f"- seed: `{seed}`\n"
        f"- candidate: `{candidate['root_branch_key']}`\n"
        f"- python elapsed: `{py_elapsed:.6f}s`\n"
        f"- rust elapsed: `{rust_elapsed:.6f}s`\n"
        f"- python sec/projection: `{py_elapsed / projection_batch:.9f}`\n"
        f"- rust sec/projection: `{rust_elapsed / projection_batch:.9f}`\n"
        f"- speedup (python/rust): `{speedup:.4f}x`\n"
        '\n'
        '## Python\n'
        f"- family5 rate: `{py_result['family5_rate']:.6f}`\n"
        f"- exact rate: `{py_result['exact_rate']:.6f}`\n"
        f"- mean profile score: `{py_result['mean_profile_score']:.6f}`\n"
        f"- best counts: `{py_result['best_counts']}`\n"
        '\n'
        '## Rust\n'
        f"- family5 rate: `{rust_result['family5_rate']:.6f}`\n"
        f"- exact rate: `{rust_result['exact_rate']:.6f}`\n"
        f"- mean profile score: `{rust_result['mean_profile_score']:.6f}`\n"
        f"- best counts: `{rust_result['best_counts']}`\n"
        '\n'
        '## Note\n'
        f"- {report['note']}\n"
    )

    print(json_path)
    print(md_path)
    print(json.dumps({'python_elapsed_sec': py_elapsed, 'rust_elapsed_sec': rust_elapsed, 'speedup': speedup}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
