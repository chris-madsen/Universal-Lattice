#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import (
    evaluate_vectors_python,
    evaluate_vectors_rust,
    evaluate_vectors_rust_persistent,
    shutdown_rust_kernel_server,
)

STATE_PATH = ROOT / 'research' / 'async_state' / 'branch05_ridge' / 'ga_aco_state.json'
GA_PATH = ROOT / 'research' / 'async_jobs' / 'branch05_ga_aco_tree_search.py'
OUT_JSON = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'bench_branch05_hot_kernel_persistent.json'
OUT_MD = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'bench_branch05_hot_kernel_persistent.md'


def load_ga_module():
    spec = importlib.util.spec_from_file_location('ga05_bench_persistent', GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['ga05_bench_persistent'] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    state = json.loads(STATE_PATH.read_text())
    candidate = state['best_overall']
    module = load_ga_module()
    vectors = [list(map(float, vec.tolist())) for vec in module.selected_vectors(candidate)]
    projection_batch = 25000
    seed = 424242

    t0 = time.perf_counter()
    py = evaluate_vectors_python(vectors, projection_batch=projection_batch, seed=seed)
    py_elapsed = time.perf_counter() - t0

    t0 = time.perf_counter()
    rs = evaluate_vectors_rust(vectors, projection_batch=projection_batch, seed=seed)
    rs_elapsed = time.perf_counter() - t0

    t0 = time.perf_counter()
    rp = evaluate_vectors_rust_persistent(vectors, projection_batch=projection_batch, seed=seed)
    rp_elapsed = time.perf_counter() - t0
    shutdown_rust_kernel_server()

    report = {
        'candidate': candidate['root_branch_key'],
        'projection_batch': projection_batch,
        'seed': seed,
        'python_elapsed_sec': py_elapsed,
        'rust_subprocess_elapsed_sec': rs_elapsed,
        'rust_persistent_elapsed_sec': rp_elapsed,
        'python_over_rust_subprocess': py_elapsed / rs_elapsed,
        'python_over_rust_persistent': py_elapsed / rp_elapsed,
        'rust_subprocess_over_rust_persistent': rs_elapsed / rp_elapsed,
        'python_family5_rate': py['family5_rate'],
        'rust_subprocess_family5_rate': rs['family5_rate'],
        'rust_persistent_family5_rate': rp['family5_rate'],
        'python_best_counts': py['best_counts'],
        'rust_subprocess_best_counts': rs['best_counts'],
        'rust_persistent_best_counts': rp['best_counts'],
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    OUT_MD.write_text(
        '# Branch 05 Persistent Rust Kernel Benchmark\n\n'
        f"- candidate: `{report['candidate']}`\n"
        f"- projection batch: `{projection_batch}`\n"
        f"- python elapsed: `{py_elapsed:.6f}s`\n"
        f"- rust subprocess elapsed: `{rs_elapsed:.6f}s`\n"
        f"- rust persistent elapsed: `{rp_elapsed:.6f}s`\n"
        f"- python / rust subprocess: `{report['python_over_rust_subprocess']:.4f}x`\n"
        f"- python / rust persistent: `{report['python_over_rust_persistent']:.4f}x`\n"
        f"- rust subprocess / rust persistent: `{report['rust_subprocess_over_rust_persistent']:.4f}x`\n"
        '\n'
        '## Family-5 Rates\n'
        f"- python: `{py['family5_rate']:.6f}`\n"
        f"- rust subprocess: `{rs['family5_rate']:.6f}`\n"
        f"- rust persistent: `{rp['family5_rate']:.6f}`\n"
        '\n'
        '## Best Counts\n'
        f"- python: `{py['best_counts']}`\n"
        f"- rust subprocess: `{rs['best_counts']}`\n"
        f"- rust persistent: `{rp['best_counts']}`\n"
    )
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
