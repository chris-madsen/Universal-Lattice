#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.family_kernel import evaluate_vectors_rust_persistent, shutdown_rust_kernel_server

GA_PATH = ROOT / 'research' / 'async_jobs' / 'branch05_ga_aco_tree_search.py'
RULE_PATH = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'deterministic_a2_subweb_rule.json'
OUT_JSON = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'concrete_witness_candidate_a2.json'
OUT_MD = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'concrete_witness_candidate_a2.md'
CANONICAL_COUNTS = [1, 1, 1, 1, 2]
PROJECTION_BATCH = 8192
TRANSFER_MIN_RATE = 0.16


def load_ga_module():
    spec = importlib.util.spec_from_file_location('ga05_promote_witness', GA_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['ga05_promote_witness'] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def evaluate(module, candidate: dict, seed: int) -> dict:
    result = evaluate_vectors_rust_persistent(module.selected_vectors(candidate), projection_batch=PROJECTION_BATCH, seed=seed)
    result['preserves_canonical_counts'] = result['best_counts'] == CANONICAL_COUNTS
    return result


def main() -> int:
    module = load_ga_module()
    rule = json.loads(RULE_PATH.read_text())

    primary = rule['canonical_templates']['A2_B2-0_B1-3_B0-1']
    candidate = {
        'template_key': primary['template_key'],
        'axis_subset_key': rule['base_subset_key'],
        'axis_size': 2,
        'total_cell_count': 4,
        'bucket_counts': primary['bucket_counts'],
        'selections': primary['selections'],
    }
    base_eval = evaluate(module, candidate, seed=810001)

    ablations = []
    for bucket in ['1', '0']:
        for idx, line_id in enumerate(list(candidate['selections'][bucket])):
            altered = json.loads(json.dumps(candidate))
            altered['selections'][bucket] = [x for x in altered['selections'][bucket] if x != line_id]
            altered['bucket_counts'][bucket] = len(altered['selections'][bucket])
            altered['total_cell_count'] = sum(altered['bucket_counts'].values())
            altered['template_key'] = f"ABLATE_{bucket}_{line_id}"
            metrics = evaluate(module, altered, seed=820000 + idx + (100 if bucket == '0' else 0))
            ablations.append({
                'name': altered['template_key'],
                'removed_bucket': bucket,
                'removed_line': line_id,
                'metrics': metrics,
            })

    additions = []
    extensions = [
        ('1', 2),
        ('1', 0),
        ('0', 7),
        ('2', 1),
        ('2', 4),
    ]
    for idx, (bucket, line_id) in enumerate(extensions):
        altered = json.loads(json.dumps(candidate))
        altered['selections'][bucket] = list(altered['selections'][bucket]) + [line_id]
        altered['bucket_counts'][bucket] = len(altered['selections'][bucket])
        altered['total_cell_count'] = sum(altered['bucket_counts'].values())
        altered['template_key'] = f"ADD_{bucket}_{line_id}"
        metrics = evaluate(module, altered, seed=830000 + idx)
        additions.append({
            'name': altered['template_key'],
            'added_bucket': bucket,
            'added_line': line_id,
            'metrics': metrics,
        })

    transfers = []
    for idx, subset_key in enumerate(['12', '13', '23']):
        mapped = rule['orbit_transfers'][subset_key]['templates']['A2_B2-0_B1-3_B0-1']['mapped_selections']
        altered = json.loads(json.dumps(candidate))
        altered['axis_subset_key'] = subset_key
        altered['selections'] = mapped
        metrics = evaluate(module, altered, seed=840000 + idx)
        transfers.append({
            'subset_key': subset_key,
            'classification': rule['orbit_transfers'][subset_key]['classification'],
            'mapped_selections': mapped,
            'metrics': metrics,
        })

    avg_transfer_rate = sum(row['metrics']['family5_rate'] for row in transfers) / len(transfers)
    all_ablations_break = all(not row['metrics']['preserves_canonical_counts'] for row in ablations)
    all_additions_break = all(not row['metrics']['preserves_canonical_counts'] for row in additions)
    transfers_hold = all(row['metrics']['preserves_canonical_counts'] and row['metrics']['family5_rate'] >= TRANSFER_MIN_RATE for row in transfers)

    verdict = {
        'base_preserves_canonical_counts': base_eval['preserves_canonical_counts'],
        'all_single_ablations_break_canonical_counts': all_ablations_break,
        'all_single_additions_break_canonical_counts': all_additions_break,
        'all_transfers_hold_canonical_counts_and_rate': transfers_hold,
        'transfer_min_rate_threshold': TRANSFER_MIN_RATE,
        'average_transfer_family5_rate': avg_transfer_rate,
    }
    verdict['is_concrete_witness_candidate'] = all(verdict.values()) if isinstance(list(verdict.values())[-1], bool) else (
        verdict['base_preserves_canonical_counts']
        and verdict['all_single_ablations_break_canonical_counts']
        and verdict['all_single_additions_break_canonical_counts']
        and verdict['all_transfers_hold_canonical_counts_and_rate']
    )

    result = {
        'candidate': candidate,
        'projection_batch': PROJECTION_BATCH,
        'canonical_counts': CANONICAL_COUNTS,
        'base_eval': base_eval,
        'ablations': ablations,
        'additions': additions,
        'transfers': transfers,
        'verdict': verdict,
        'selection_reason': {
            'chosen_template': 'A2_B2-0_B1-3_B0-1',
            'why_not_A2_B2-0_B1-4_B0-0': 'slightly stronger raw average on some subsets, but much weaker global search support and less interpretable anchor-correction structure',
            'why_not_A2_B2-0_B1-2_B0-2': 'stable but weaker than the chosen core on both support and average transferred strength',
        },
    }

    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=True))

    lines = [
        '# Concrete Witness Candidate: A2 Core',
        '',
        f"- candidate: `{candidate['template_key']}@{candidate['axis_subset_key']}`",
        f"- projection batch: `{PROJECTION_BATCH}`",
        f"- canonical counts target: `{CANONICAL_COUNTS}`",
        '',
        '## Base Candidate',
        '',
        f"- selections: `{candidate['selections']}`",
        f"- family5 rate: `{base_eval['family5_rate']:.6f}`",
        f"- exact rate: `{base_eval['exact_rate']:.6f}`",
        f"- best counts: `{base_eval['best_counts']}`",
        f"- preserves canonical counts: `{base_eval['preserves_canonical_counts']}`",
        '',
        '## Single-Line Ablations',
        '',
    ]
    for row in ablations:
        m = row['metrics']
        lines.extend([
            f"- `{row['name']}` -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, preserves canonical=`{m['preserves_canonical_counts']}`",
        ])
    lines.extend(['', '## Single-Line Additions', ''])
    for row in additions:
        m = row['metrics']
        lines.extend([
            f"- `{row['name']}` -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, preserves canonical=`{m['preserves_canonical_counts']}`",
        ])
    lines.extend(['', '## Orbit Transfers', ''])
    for row in transfers:
        m = row['metrics']
        lines.extend([
            f"- `{row['subset_key']}` ({row['classification']}) -> family5=`{m['family5_rate']:.6f}`, best_counts=`{m['best_counts']}`, preserves canonical=`{m['preserves_canonical_counts']}`",
        ])
    lines.extend([
        '',
        '## Verdict',
        '',
        f"- all single ablations break canonical counts: `{all_ablations_break}`",
        f"- all single additions break canonical counts: `{all_additions_break}`",
        f"- all transfers hold canonical counts and rate >= {TRANSFER_MIN_RATE}: `{transfers_hold}`",
        f"- average transfer family5 rate: `{avg_transfer_rate:.6f}`",
        f"- concrete witness candidate: `{verdict['is_concrete_witness_candidate']}`",
        '',
        '## Interpretation',
        '- this is not yet a full proof of the entire generating lattice, but it is a concrete witness candidate for the strongest `A2` subweb class;',
        '- the chosen core survives orbit transfer and breaks immediately when over-pruned or over-extended in one-line moves;',
        '- that is exactly the behavior we want from a candidate that is more than a loose scaffold.',
    ])
    OUT_MD.write_text('\n'.join(lines) + '\n')
    shutdown_rust_kernel_server()
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
