#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
READOUT_PATH = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'readout_rule_a2_trunks.json'
TRANSFER_PATH = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'readout_rule_a2_orbit_transfer.json'
OUT_JSON = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'deterministic_a2_subweb_rule.json'
OUT_MD = ROOT / 'research' / 'A_geometric_models' / '05_24cell_tesseract_interaction' / 'data' / 'deterministic_a2_subweb_rule.md'

PRIMARY_TEMPLATES = [
    'A2_B2-0_B1-3_B0-1',
    'A2_B2-0_B1-4_B0-0',
    'A2_B2-0_B1-2_B0-2',
]


def main() -> int:
    readout = json.loads(READOUT_PATH.read_text())
    transfer = json.loads(TRANSFER_PATH.read_text())

    line_map = {int(k): v for k, v in readout['line_map'].items()}
    bucket1_ranked = [int(k) for k, _v in sorted(readout['bucket1_weighted_support'].items(), key=lambda kv: (-kv[1], int(kv[0])))]
    bucket0_ranked = [int(k) for k, _v in sorted(readout['bucket0_weighted_support'].items(), key=lambda kv: (-kv[1], int(kv[0])))]
    bucket2_ranked = [int(k) for k, _v in sorted(readout['bucket2_weighted_support'].items(), key=lambda kv: (-kv[1], int(kv[0])))]

    top_branch_map = {}
    for row in readout['top_branches']:
        best = row['best']
        top_branch_map[best['template_key']] = {
            'template_key': best['template_key'],
            'bucket_counts': best['bucket_counts'],
            'selections': best['selections'],
            'family5_rate': best['family5_rate'],
            'best_counts': best['best_counts'],
        }

    orbit_transfers = {}
    for subset_key, record in transfer['targets'].items():
        orbit_transfers[subset_key] = {
            'classification': record['classification'],
            'best_overlap_score': record['best_overlap_score'],
            'permutation': record['permutation'],
            'signs': record['signs'],
            'templates': {
                row['template_key']: {
                    'mapped_selections': row['mapped_selections'],
                    'transfer_eval_family5_rate': row['transfer_eval_family5_rate'],
                    'mean_bucketwise_jaccard': row['mean_bucketwise_jaccard'],
                }
                for row in record['template_records']
            },
        }

    result = {
        'base_subset_key': readout['axis_subset_key'],
        'base_subset_dims': readout['axis_subset_dims'],
        'template_priority': PRIMARY_TEMPLATES,
        'deterministic_core': {
            'bucket1_core': bucket1_ranked[:3],
            'bucket0_core': bucket0_ranked[:1],
            'best_core_template': 'A2_B2-0_B1-3_B0-1',
        },
        'deterministic_extensions': {
            'bucket1_extension_order': bucket1_ranked[3:5],
            'bucket0_extension_order': bucket0_ranked[1:2],
            'bucket2_refinement_order': bucket2_ranked,
        },
        'canonical_templates': {key: top_branch_map[key] for key in PRIMARY_TEMPLATES if key in top_branch_map},
        'line_vectors': {str(k): line_map[k] for k in sorted(set(bucket1_ranked + bucket0_ranked + bucket2_ranked))},
        'orbit_transfers': orbit_transfers,
    }

    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=True))

    md_lines = [
        '# Deterministic A2 Subweb Rule',
        '',
        f"- base subset: `{result['base_subset_key']}`",
        f"- base dims: `{result['base_subset_dims']}`",
        f"- template priority: `{PRIMARY_TEMPLATES}`",
        '',
        '## Canonical Core',
        '',
        f"- best core template: `{result['deterministic_core']['best_core_template']}`",
        f"- bucket-1 core lines: `{result['deterministic_core']['bucket1_core']}`",
        f"- bucket-0 core line: `{result['deterministic_core']['bucket0_core']}`",
        '',
        'Interpretation:',
        '- start from the `A2_B2-0_B1-3_B0-1` core, not from the more diffuse second-tier templates;',
        '- treat bucket-1 lines as the main diagonal spine and bucket-0 as the primary anchor correction;',
        '',
        '## Ordered Extensions',
        '',
        f"- bucket-1 extension order: `{result['deterministic_extensions']['bucket1_extension_order']}`",
        f"- bucket-0 extension order: `{result['deterministic_extensions']['bucket0_extension_order']}`",
        f"- bucket-2 refinement order: `{result['deterministic_extensions']['bucket2_refinement_order']}`",
        '',
        '## Canonical Templates',
        '',
    ]
    for key in PRIMARY_TEMPLATES:
        row = result['canonical_templates'][key]
        md_lines.extend([
            f"### `{key}`",
            '',
            f"- bucket counts: `{row['bucket_counts']}`",
            f"- selections: `{row['selections']}`",
            f"- best single family5 rate: `{row['family5_rate']:.6f}`",
            f"- best counts: `{row['best_counts']}`",
            '',
        ])
    md_lines.extend(['## Orbit-Stable Transfer', ''])
    for subset_key, row in orbit_transfers.items():
        md_lines.extend([
            f"### `{subset_key}`",
            '',
            f"- classification: `{row['classification']}`",
            f"- overlap score: `{row['best_overlap_score']:.6f}`",
            f"- permutation: `{row['permutation']}`",
            f"- signs: `{row['signs']}`",
            '',
        ])
        for template_key in PRIMARY_TEMPLATES:
            t = row['templates'][template_key]
            md_lines.extend([
                f"- `{template_key}` -> mapped `{t['mapped_selections']}`, transfer family5=`{t['transfer_eval_family5_rate']:.6f}`, overlap=`{t['mean_bucketwise_jaccard']:.6f}`",
            ])
        md_lines.append('')
    md_lines.extend(['## Line Vectors', ''])
    for line_id, vec in result['line_vectors'].items():
        md_lines.append(f"- line `{line_id}`: `{vec}`")
    OUT_MD.write_text('\n'.join(md_lines) + '\n')
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
