#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.lattice_signature import build_signature


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def run_baseline(variant_dir: Path) -> int:
    signature = build_signature()
    data = {
        "target_absolute_family_count": len(signature["family_counts"]),
        "target_family_counts": signature["family_counts"],
        "target_anchor_node_count": signature["anchor_node_count"],
        "target_false_intersection_count": signature["false_intersection_count"],
        "affine_invariants": [
            "collinearity",
            "line incidence",
            "intersection graph",
            "projective direction distinctness under invertible linear map",
        ],
    }
    data_dir = variant_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / 'baseline_affine_constraints.json'
    md_path = data_dir / 'baseline_affine_constraints.md'
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=True))
    md_path.write_text(f'''# Affine Baseline Constraints\n\n- target absolute family count: `{data['target_absolute_family_count']}`\n- target family counts: `{data['target_family_counts']}`\n- affine invariants: `{data['affine_invariants']}`\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text () `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage baseline`\nArtifacts:\n- `data/baseline_affine_constraints.json`\n- `data/baseline_affine_constraints.md`\nWhat I think:\n- target family-count lattice;\n- list of structural properties that are invertible affine map saves.\nFormulas/reasoning:\n- affine-normalization can change angles and length ratios;\n- but it does not glue different directions together like projective classes and does not break incidence by itself.\nIntermediate results:\n- target absolute family count: `{data['target_absolute_family_count']}`\n- affine invariants: `{data['affine_invariants']}`\nWhat does this mean:\n- branch `03` should explain the lattice without hope of a miraculous collapse of different directions only by affine transformation.\nDifficulty:\n- low.\nNext step:\n- go to prune and check what this limitation means against the background of the results of `01_raw_24cell_web`.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: active

## Summary

Baseline affine constraints recorded.

## Best Witness

- `data/baseline_affine_constraints.json`
- `data/baseline_affine_constraints.md`

## Blocking Issues

None at baseline stage.
''')

    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"constraints={json_path}")
    return 0


def run_prune(variant_dir: Path) -> int:
    raw_prune_path = ROOT / 'research' / 'A_geometric_models' / '01_raw_24cell_web' / 'data' / 'prune_raw_24cell_family_scan.json'
    raw_prune = json.loads(raw_prune_path.read_text())
    target_family_count = raw_prune['target_family_count']
    exact_matches = raw_prune['exact_family_match_count']
    best_family_count = raw_prune['best_candidate']['absolute_family_count']
    histogram = raw_prune['family_count_histogram']

    report = {
        'target_absolute_family_count': target_family_count,
        'raw_projection_exact_match_count': exact_matches,
        'raw_projection_best_family_count': best_family_count,
        'raw_projection_histogram': histogram,
        'affine_statement': 'An invertible affine map in 2D preserves distinct direction classes in projective space, so it cannot by itself merge 7 observed raw families into 5 target families.',
        'implication': 'Pure raw+affine is weakened; any rescue would require additional selection/pruning beyond affine normalization itself.',
    }

    data_dir = variant_dir / 'data'
    report_path = data_dir / 'prune_affine_direction_invariance.json'
    summary_path = data_dir / 'prune_affine_direction_invariance.md'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    summary_path.write_text(f'''# Affine Prune Summary\n\n- target absolute family count: `{target_family_count}`\n- raw exact family-count matches from branch 01: `{exact_matches}`\n- best raw family count observed: `{best_family_count}`\n- raw histogram: `{histogram}`\n- affine statement: `{report['affine_statement']}`\n- implication: `{report['implication']}`\n''')

    log_path = variant_dir / 'log.md'
log = log_path.read_text () `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage prune`\nArtifacts:\n- `data/prune_affine_direction_invariance.json`\n- `data/prune_affine_direction_invariance.md`\nWhat I think:\n- prune results from `01_raw_24cell_web`;\n- projective invariant: invertible affine map does not glue different direction classes into one.\nFormulas / reasoning:\n- if raw branch `01` does not give a target family-count `5`, and the best level found is `7`, then pure affine normalization by itself will not turn `7` distinct direction classes into `5`;\n- it means branch `03` in its pure form is weakened logically, and not just numerically.\nIntermediate results:\n- raw exact matches from `01`: `{exact_matches}`\n- best raw family count: `{best_family_count}`\n- implication: `{report['implication']}`\nWhat does this mean:\n- branch `03_affine_normalized_24cell` is now receiving fast logical red flag;\n- if it is ever saved, then not as “raw + affine only”, but through an additional selection mechanism, which is closer to other branches of the plan.\nDifficulty:\n- low; this is a logical prune without heavy searching.\nNext step:\n- commit the weakening branch and go to `06_double_rotation_overlay`.\n'''
    log_path.write_text(log)

    result_path = variant_dir / 'result.md'
    result_path.write_text('''# Result

Status: prune_red_flag

## Summary

Baseline and logical prune completed. Since branch `01_raw_24cell_web` did not reach the target family-count, pure affine normalization is weakened: an invertible affine map cannot by itself merge distinct raw direction classes into the target 5-family lattice.

## Best Witness

- `data/baseline_affine_constraints.json`
- `data/prune_affine_direction_invariance.json`

## Blocking Issues

This branch is weakened unless an additional selection mechanism is introduced; that would move it closer to later branches rather than keep it as pure affine normalization.
''')

    print(f"variant={variant_dir.name}")
    print("stage=prune")
    print(f"report={report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['baseline', 'prune', 'search', 'analyze', 'finalize'], default='baseline')
    args = parser.parse_args()
    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == 'baseline':
        return run_baseline(variant_dir)
    if args.stage == 'prune':
        return run_prune(variant_dir)
    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print('TODO: implement hypothesis-specific workflow')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
