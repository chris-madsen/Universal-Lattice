#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.common.grid_generativity import derive_generativity_grammar
from research.common.lattice_signature import build_signature, write_svg
from research.common.polytopes import canonical_24cell_edges, canonical_24cell_vertices
from research.common.projection import projected_edge_signature, random_projection


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def run_baseline(variant_dir: Path) -> int:
    data_dir = variant_dir / "data"
    figures_dir = variant_dir / "figures"
    data_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    signature = build_signature()
    grammar = derive_generativity_grammar(signature)

    signature_path = data_dir / "baseline_lattice_signature.json"
    grammar_path = data_dir / "baseline_grid_generativity.json"
    summary_path = data_dir / "baseline_summary.md"
    figure_path = figures_dir / "baseline_lattice_signature.svg"

    signature_path.write_text(json.dumps(signature, indent=2, ensure_ascii=True))
    grammar_path.write_text(json.dumps(grammar, indent=2, ensure_ascii=True))
    write_svg(signature, figure_path)

    summary = f"""# Baseline Summary

- source: `universal-lattice.py`
- raw segments: `{signature['raw_segment_count']}`
- maximal lines: `{signature['maximal_line_count']}`
- anchor nodes: `{signature['anchor_node_count']}`
- arrangement intersections: `{signature['arrangement_intersection_count']}`
- false intersections: `{signature['false_intersection_count']}`
- absolute families: `{', '.join(sorted(signature['family_counts'].keys()))}`
- center degree: `{grammar['center_degree']}`
- top center degree: `{grammar['top_center_degree']}`
- bottom center degree: `{grammar['bottom_center_degree']}`
- vertical mast count: `{grammar['vertical_mast_count']}`
- mast attachment levels: `{grammar['mast_attachment_levels']}`
"""
    summary_path.write_text(summary)

    log_path = variant_dir / "log.md"
    old_log = log_path.read_text().rstrip() + "\n"
    correction_entry = f"""
## {now_string()} — baseline-correction
Цель: уточнить baseline, отделив реальные опорные узлы решётки от ложных пересечений, которые возникают при полном продолжении прямых.
Гипотеза: `01_raw_24cell_web`
Скрипт: `research/A_geometric_models/01_raw_24cell_web/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_lattice_signature.json`
- `data/baseline_grid_generativity.json`
- `data/baseline_summary.md`
- `figures/baseline_lattice_signature.svg`
Что считаю:
- anchor nodes как явные узлы самой решётки;
- arrangement intersections как все пересечения maximal lines;
- false intersections как разность между этими двумя уровнями.
Формулы / reasoning:
- baseline решётки нельзя сводить только к полному line arrangement, иначе появляется много ложных узлов;
- для generative grammar важнее anchor-узлы и их сигнатуры, а false intersections надо хранить отдельно как диагностический слой.
Промежуточные результаты:
- anchor nodes: `{signature['anchor_node_count']}`
- arrangement intersections: `{signature['arrangement_intersection_count']}`
- false intersections: `{signature['false_intersection_count']}`
- family counts: `{signature['family_counts']}`
- center/top/bottom degrees: `{grammar['center_degree']}` / `{grammar['top_center_degree']}` / `{grammar['bottom_center_degree']}`
Что это значит:
- baseline теперь отражает именно решётку как порождающий объект, а не только её полное arrangement-продолжение;
- отдельный слой false intersections пригодится позже для веток, где `F4` или другие arrangements начнут создавать ложные узлы.
Сложность:
- низкая; это структурное уточнение baseline, а не тяжёлый расчёт.
Следующий шаг:
- перейти к `prune` и проверить, насколько сырая projected web 24-cell вообще совместима с target family-count и базовой узловой грамматикой.
"""
    log_path.write_text(old_log + correction_entry)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        "Baseline completed. The lattice signature now distinguishes anchor nodes from arrangement-induced false intersections.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_lattice_signature.json`\n"
        "- `data/baseline_grid_generativity.json`\n"
        "- `figures/baseline_lattice_signature.svg`\n\n"
        "## Blocking Issues\n\n"
        "None at baseline stage.\n"
    )

    index_path = ROOT / "research" / "index.md"
    index_text = index_path.read_text()
    index_text = index_text.replace("| 01 | A | raw_24cell_web | planned | baseline |", "| 01 | A | raw_24cell_web | active | prune |")
    index_text = index_text.replace("| 01 | A | raw_24cell_web | active | baseline |", "| 01 | A | raw_24cell_web | active | prune |")
    index_path.write_text(index_text)

    print(f"variant={variant_dir.name}")
    print("stage=baseline")
    print(f"signature={signature_path}")
    print(f"grammar={grammar_path}")
    print(f"figure={figure_path}")
    return 0


def run_prune(variant_dir: Path) -> int:
    data_dir = variant_dir / "data"
    signature = build_signature()
    target_family_count = len(signature["family_counts"])

    vertices = canonical_24cell_vertices()
    edges = canonical_24cell_edges(vertices)
    rng = np.random.default_rng(42)

    samples = 1200
    records = []
    histogram = {}
    exact_family_match = 0
    for _ in range(samples):
        projection = random_projection(rng)
        record = projected_edge_signature(vertices, edges, projection)
        records.append(record)
        count = record["absolute_family_count"]
        histogram[count] = histogram.get(count, 0) + 1
        if count == target_family_count:
            exact_family_match += 1

    records.sort(key=lambda r: (abs(r["absolute_family_count"] - target_family_count), r["zero_edges"], abs(r["projected_edge_count"] - signature["maximal_line_count"])))
    best = records[0]
    prune_report = {
        "samples": samples,
        "target_family_count": target_family_count,
        "family_count_histogram": histogram,
        "exact_family_match_count": exact_family_match,
        "best_candidate": best,
        "interpretation": {
            "raw_model_family_match_is_common": exact_family_match > samples * 0.05,
            "raw_model_family_match_exists": exact_family_match > 0,
        },
    }

    report_path = data_dir / "prune_raw_24cell_family_scan.json"
    summary_path = data_dir / "prune_summary.md"
    report_path.write_text(json.dumps(prune_report, indent=2, ensure_ascii=True))

    summary = f"""# Prune Summary

- samples: `{samples}`
- target absolute family count: `{target_family_count}`
- exact family-count matches in raw projected 24-cell samples: `{exact_family_match}`
- histogram: `{histogram}`
- best candidate family count: `{best['absolute_family_count']}`
- best candidate projected vertex count: `{best['projected_vertex_count']}`
- best candidate projected edge count: `{best['projected_edge_count']}`
- best candidate zero edges: `{best['zero_edges']}`
"""
    summary_path.write_text(summary)

    log_path = variant_dir / "log.md"
    old_log = log_path.read_text().rstrip() + "\n"
    prune_entry = f"""
## {now_string()} — prune
Цель: проверить, насколько сырая projected edge-web 24-cell вообще совместима с целевым числом семейств направлений нашей решётки.
Гипотеза: `01_raw_24cell_web`
Скрипт: `research/A_geometric_models/01_raw_24cell_web/scripts/run.py --stage prune`
Артефакты:
- `data/prune_raw_24cell_family_scan.json`
- `data/prune_summary.md`
Что считаю:
- у canonical 24-cell берутся вершины и 96 рёбер;
- затем для `samples={samples}`` случайных ортонормальных 2D-проекций считается число абсолютных семейств направлений на raw projected edge-web;
- сравнивается с target family-count решётки `{target_family_count}`.
Формулы / reasoning:
- это ещё не доказательство и не полный search;
- это быстрый prune: если raw 24-cell почти никогда не попадает даже в target family-count, ветка уже выглядит напряжённой;
- если попадания есть, ветка сохраняет правдоподобие и идёт дальше.
Промежуточные результаты:
- exact family-count matches: `{exact_family_match}` из `{samples}`
- histogram: `{histogram}`
- best candidate family count / projected vertices / projected edges / zero edges: `{best['absolute_family_count']}` / `{best['projected_vertex_count']}` / `{best['projected_edge_count']}` / `{best['zero_edges']}`
Что это значит:
- prune даёт первую необходимую sanity-проверку для `01_raw_24cell_web`;
- следующий шаг зависит от того, выглядит ли совпадение по числу семейств редким исключением или устойчивым режимом.
Сложность:
- низкая-средняя; перебор лёгкий и не блокирует исследование.
Следующий шаг:
- перейти к `search` только если prune не даёт явного structural red flag;
- иначе зафиксировать ослабление гипотезы и двигаться к `02_local_vertex_web`.
"""
    log_path.write_text(old_log + prune_entry)

    result_path = variant_dir / "result.md"
    result_path.write_text(
        "# Result\n\n"
        "Status: active\n\n"
        "## Summary\n\n"
        f"Baseline and prune completed. Raw 24-cell projections were sampled (`samples={samples}`) to test family-count compatibility.\n\n"
        "## Best Witness\n\n"
        "- `data/baseline_lattice_signature.json`\n"
        "- `data/baseline_grid_generativity.json`\n"
        "- `data/prune_raw_24cell_family_scan.json`\n"
        "- `figures/baseline_lattice_signature.svg`\n\n"
        "## Blocking Issues\n\n"
        "None yet. Need to judge whether prune results justify deeper search or moving to the next hypothesis.\n"
    )

    index_path = ROOT / "research" / "index.md"
    index_text = index_path.read_text().replace("| 01 | A | raw_24cell_web | active | prune |", "| 01 | A | raw_24cell_web | active | analyze prune |")
    index_path.write_text(index_text)

    print(f"variant={variant_dir.name}")
    print("stage=prune")
    print(f"report={report_path}")
    print(f"summary={summary_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["baseline", "prune", "search", "analyze", "finalize"], default="baseline")
    args = parser.parse_args()

    variant_dir = Path(__file__).resolve().parent.parent
    if args.stage == "baseline":
        return run_baseline(variant_dir)
    if args.stage == "prune":
        return run_prune(variant_dir)

    print(f"variant={variant_dir.name}")
    print(f"stage={args.stage}")
    print("TODO: implement hypothesis-specific workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
