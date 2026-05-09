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
    log = log_path.read_text().rstrip() + f'''\n\n## {now_string()} — baseline\nЦель: зафиксировать, какие свойства решётки branch `03` вправе менять affine-нормализацией, а какие нет.\nГипотеза: `03_affine_normalized_24cell`\nСкрипт: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage baseline`\nАртефакты:\n- `data/baseline_affine_constraints.json`\n- `data/baseline_affine_constraints.md`\nЧто считаю:\n- target family-count решётки;\n- список структурных свойств, которые invertible affine map сохраняет.\nФормулы / reasoning:\n- affine-нормализация может менять углы и отношения длин;\n- но она не склеивает разные направления как projective classes и не ломает incidence сама по себе.\nПромежуточные результаты:\n- target absolute family count: `{data['target_absolute_family_count']}`\n- affine invariants: `{data['affine_invariants']}`\nЧто это значит:\n- ветка `03` должна объяснять решётку без надежды на чудесное схлопывание разных направлений только affine-преобразованием.\nСложность:\n- низкая.\nСледующий шаг:\n- перейти к prune и проверить, что означает это ограничение на фоне результатов `01_raw_24cell_web`.\n'''
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
    log = log_path.read_text().rstrip() + f'''\n\n## {now_string()} — prune\nЦель: проверить, способна ли чистая affine-нормализация сама по себе спасти branch `03`, если branch `01` уже не попал в target family-count.\nГипотеза: `03_affine_normalized_24cell`\nСкрипт: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage prune`\nАртефакты:\n- `data/prune_affine_direction_invariance.json`\n- `data/prune_affine_direction_invariance.md`\nЧто считаю:\n- результаты prune из `01_raw_24cell_web`;\n- projective invariant: invertible affine map не склеивает разные direction classes в одну.\nФормулы / reasoning:\n- если raw branch `01` не даёт target family-count `5`, а лучший найденный уровень `7`, то pure affine normalization сама по себе не превратит `7` distinct direction classes в `5`;\n- значит ветка `03` в чистом виде ослабляется логически, а не только численно.\nПромежуточные результаты:\n- raw exact matches from `01`: `{exact_matches}`\n- best raw family count: `{best_family_count}`\n- implication: `{report['implication']}`\nЧто это значит:\n- ветка `03_affine_normalized_24cell` сейчас получает быстрый логический red flag;\n- если её когда-то спасать, то уже не как “raw + affine only”, а через дополнительный selection mechanism, что ближе к другим веткам плана.\nСложность:\n- низкая; это логический prune без тяжёлого поиска.\nСледующий шаг:\n- зафиксировать ослабление ветки и перейти к `06_double_rotation_overlay`.\n'''
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
