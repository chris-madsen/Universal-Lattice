#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_python

GA_PATH = ROOT / 'research' / 'async_jobs' / 'branch05_ga_aco_tree_search.py'
STATE_PATH = ROOT / 'research' / 'async_state' / 'branch05_ridge' / 'ga_aco_state.json'
BASE_RULE_PATH = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'readout_rule_a2_trunks.json'
OUT_JSON = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'readout_rule_a2_orbit_transfer.json'
OUT_MD = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'readout_rule_a2_orbit_transfer.md'

BASE_TEMPLATES = [
    'A2_B2-0_B1-4_B0-0',
    'A2_B2-0_B1-3_B0-1',
    'A2_B2-0_B1-2_B0-2',
]
TARGET_SUBSETS = ['12', '13', '23']
PROJECTION_BATCH = 1024
BASE_SUBSET = (0, 2)


def load_ga_module():
    spec = importlib.util.spec_from_file_location('ga05_orbit_transfer', GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['ga05_orbit_transfer'] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def transform_vec(vec: np.ndarray, perm: tuple[int, ...], signs: tuple[float, ...]) -> np.ndarray:
    return np.array([signs[i] * vec[perm[i]] for i in range(4)], dtype=float)


def jaccard(a: list[int], b: list[int]) -> float:
    a_set = set(a)
    b_set = set(b)
    if not a_set and not b_set:
        return 1.0
    return len(a_set & b_set) / len(a_set | b_set)


def target_subset_key(module, perm: tuple[int, ...], signs: tuple[float, ...]) -> str:
    dims = []
    for axis_idx in BASE_SUBSET:
        vec = module.AXIS_VECS[axis_idx]
        transformed = transform_vec(vec, perm, signs)
        dims.append(int(np.flatnonzero(np.abs(transformed) > 1e-9)[0]))
    return ''.join(map(str, sorted(dims)))


def map_line_ids(module, line_map: dict, ids: list[int], perm: tuple[int, ...], signs: tuple[float, ...]) -> list[int]:
    mapped = []
    for idx in ids:
        vec = module.CELL_VECS[idx]
        key = module.root_line_key(transform_vec(vec, perm, signs))
        mapped.append(line_map[key])
    return sorted(mapped)


def classify_transfer(score: float) -> str:
    if score >= 0.47:
        return 'strong'
    if score >= 0.44:
        return 'good'
    if score >= 0.40:
        return 'partial'
    return 'weak'


def main() -> int:
    module = load_ga_module()
    state = json.loads(STATE_PATH.read_text())
    _base_rule = json.loads(BASE_RULE_PATH.read_text())
    line_map = {module.root_line_key(vec.copy()): idx for idx, vec in enumerate(module.CELL_VECS)}
    base_best = {tmpl: state['root_branch_stats'][f'{tmpl}@02']['best'] for tmpl in BASE_TEMPLATES}

    result = {
        'base_subset_key': '02',
        'base_templates': BASE_TEMPLATES,
        'projection_batch': PROJECTION_BATCH,
        'targets': {},
    }

    for target_subset in TARGET_SUBSETS:
        best_score = None
        best_record = None
        for perm in itertools.permutations(range(4)):
            for signs in itertools.product([-1.0, 1.0], repeat=4):
                if target_subset_key(module, perm, signs) != target_subset:
                    continue
                score = 0.0
                template_records = []
                for template_key in BASE_TEMPLATES:
                    observed = state['root_branch_stats'].get(f'{template_key}@{target_subset}')
                    if not observed:
                        continue
                    mapped_selections = {
                        bucket: map_line_ids(module, line_map, base_best[template_key]['selections'][bucket], perm, signs)
                        for bucket in ['2', '1', '0']
                    }
                    observed_best = observed['best']['selections']
                    overlap = sum(jaccard(mapped_selections[bucket], observed_best[bucket]) for bucket in ['2', '1', '0']) / 3.0
                    running_family5 = observed['family5_sum'] / max(1, observed['eval_count'])
                    score += overlap * running_family5
                    template_records.append(
                        {
                            'template_key': template_key,
                            'mapped_selections': mapped_selections,
                            'observed_best_selections': observed_best,
                            'bucketwise_jaccard': {
                                bucket: jaccard(mapped_selections[bucket], observed_best[bucket])
                                for bucket in ['2', '1', '0']
                            },
                            'mean_bucketwise_jaccard': overlap,
                            'observed_running_family5_rate': running_family5,
                            'observed_best_single_family5_rate': observed['best']['family5_rate'],
                        }
                    )
                if best_score is None or score > best_score:
                    best_score = score
                    best_record = {
                        'target_subset_key': target_subset,
                        'best_overlap_score': score,
                        'classification': classify_transfer(score),
                        'permutation': list(perm),
                        'signs': [int(x) for x in signs],
                        'template_records': template_records,
                    }
        for idx, template_record in enumerate(best_record['template_records']):
            template_key = template_record['template_key']
            candidate = {
                'template_key': template_key,
                'axis_subset_key': target_subset,
                'axis_size': base_best[template_key]['axis_size'],
                'total_cell_count': base_best[template_key]['total_cell_count'],
                'bucket_counts': base_best[template_key]['bucket_counts'],
                'selections': template_record['mapped_selections'],
            }
            metrics = evaluate_vectors_python(
                module.selected_vectors(candidate),
                projection_batch=PROJECTION_BATCH,
                seed=1000 + idx,
            )
            template_record['transfer_eval_family5_rate'] = metrics['family5_rate']
            template_record['transfer_eval_exact_rate'] = metrics['exact_rate']
            template_record['transfer_eval_best_counts'] = metrics['best_counts']
        result['targets'][target_subset] = best_record

    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=True))

    md_lines = [
        '# A2 Orbit-Transfer Check',
        '',
        '- base subset: `02`',
        f'- templates checked: `{BASE_TEMPLATES}`',
        f'- transfer evaluation batch: `{PROJECTION_BATCH}`',
        '',
    ]
    for target_subset in TARGET_SUBSETS:
        record = result['targets'][target_subset]
        md_lines.extend(
            [
                f'## Target `{target_subset}`',
                '',
                f"- classification: `{record['classification']}`",
                f"- best overlap score: `{record['best_overlap_score']:.6f}`",
                f"- permutation: `{record['permutation']}`",
                f"- signs: `{record['signs']}`",
                '',
            ]
        )
        for template_record in record['template_records']:
            md_lines.extend(
                [
                    f"### `{template_record['template_key']}`",
                    '',
                    f"- mapped selections: `{template_record['mapped_selections']}`",
                    f"- observed best selections: `{template_record['observed_best_selections']}`",
                    f"- bucketwise jaccard: `{template_record['bucketwise_jaccard']}`",
                    f"- mean overlap: `{template_record['mean_bucketwise_jaccard']:.6f}`",
                    f"- observed running family5 rate: `{template_record['observed_running_family5_rate']:.6f}`",
                    f"- observed best single family5 rate: `{template_record['observed_best_single_family5_rate']:.6f}`",
                    f"- transfer-eval family5 rate: `{template_record['transfer_eval_family5_rate']:.6f}`",
                    f"- transfer-eval exact rate: `{template_record['transfer_eval_exact_rate']:.6f}`",
                    f"- transfer-eval best counts: `{template_record['transfer_eval_best_counts']}`",
                    '',
                ]
            )
    OUT_MD.write_text('\n'.join(md_lines) + '\n')
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
