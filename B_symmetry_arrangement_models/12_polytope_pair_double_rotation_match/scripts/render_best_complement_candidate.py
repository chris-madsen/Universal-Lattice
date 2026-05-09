#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.async_jobs.h12_complement_search import (
    BRANCH_DIR,
    DEFAULT_STATE_DIR,
    LEADER_KEY,
    LEADER_SEGMENTS,
    MISSING_SEGMENTS,
    SIMPLIFIED_SEGMENTS,
    TARGET_NODE_ORDER,
    UNIVERSAL_SEGMENTS,
)


def as_segments(raw: list[list[int]]) -> set[tuple[int, int]]:
    return {tuple(sorted((int(a), int(b)))) for a, b in raw}


def draw_segments(ax, segments: set[tuple[int, int]], *, color: str, linewidth: float, linestyle: str = "-", label: str | None = None) -> None:
    first = True
    for a, b in sorted(segments):
        x1, y1 = TARGET_NODE_ORDER[a]
        x2, y2 = TARGET_NODE_ORDER[b]
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, linestyle=linestyle, label=label if first else None)
        first = False


def setup_ax(ax, title: str) -> None:
    xs = [x for x, _ in TARGET_NODE_ORDER]
    ys = [y for _, y in TARGET_NODE_ORDER]
    ax.scatter(xs, ys, s=22, color="#111111", zorder=4)
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-0.2, 2.2)
    ax.set_ylim(-0.2, 3.2)
    ax.grid(True, color="#dddddd", linewidth=0.6)


def render_single(path: Path, title: str, segments: set[tuple[int, int]], color: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 5))
    setup_ax(ax, title)
    draw_segments(ax, segments, color=color, linewidth=2.4)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def render_overlay(path: Path, title: str, base: set[tuple[int, int]], ref: set[tuple[int, int]]) -> dict:
    common = base & ref
    extra = base - ref
    missing = ref - base
    fig, ax = plt.subplots(figsize=(5, 6))
    setup_ax(ax, title)
    draw_segments(ax, common, color="#178f45", linewidth=3.0, label="matched")
    draw_segments(ax, missing, color="#c62828", linewidth=2.2, linestyle="--", label="missing")
    draw_segments(ax, extra, color="#1565c0", linewidth=1.7, linestyle=":", label="extra")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {"matched": common, "missing": missing, "extra": extra}


def render_leader_plus_complement(
    path: Path,
    title: str,
    leader_segments: set[tuple[int, int]],
    complement_segments: set[tuple[int, int]],
) -> None:
    shared = leader_segments & complement_segments
    leader_only = leader_segments - complement_segments
    complement_only = complement_segments - leader_segments
    fig, ax = plt.subplots(figsize=(5, 6))
    setup_ax(ax, title)
    draw_segments(ax, leader_only, color="#6d6d6d", linewidth=2.2, label="leader only")
    draw_segments(ax, complement_only, color="#1565c0", linewidth=2.2, label="complement only")
    draw_segments(ax, shared, color="#7b1fa2", linewidth=2.8, label="overlap")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def segment_text(segments: set[tuple[int, int]]) -> str:
    if not segments:
        return "`none`"
    return ", ".join(f"`{TARGET_NODE_ORDER[a]} -> {TARGET_NODE_ORDER[b]}`" for a, b in sorted(segments))


def best_exact_complement_candidate(rows: list[dict]) -> dict | None:
    exact = [row for row in rows if row.get("comparison", {}).get("exact_complement")]
    if exact:
        exact.sort(
            key=lambda row: (
                row["comparison"]["missing_after_union_vs_universal"],
                row["comparison"]["extra_after_union_vs_universal"],
                -row["comparison"]["matched_complement_segments"],
            )
        )
        return exact[0]
    rows_sorted = sorted(
        rows,
        key=lambda row: (
            -row["comparison"]["matched_complement_segments"],
            row["comparison"]["missing_after_union_vs_universal"],
            row["comparison"]["extra_after_union_vs_universal"],
        ),
    )
    return rows_sorted[0] if rows_sorted else None


def best_union_candidate(rows: list[dict]) -> dict | None:
    rows_sorted = sorted(
        rows,
        key=lambda row: (
            row["comparison"]["missing_after_union_vs_universal"],
            row["comparison"]["extra_after_union_vs_universal"],
            -row["comparison"]["matched_complement_segments"],
        ),
    )
    return rows_sorted[0] if rows_sorted else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--out-dir", default=str(BRANCH_DIR / "figures"))
    args = parser.parse_args()

    state_dir = Path(args.state_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    if not state_path.exists():
        raise SystemExit(f"missing state file: {state_path}")
    state = json.loads(state_path.read_text())
    rows = state.get("best_candidates", [])
    best_complement = best_exact_complement_candidate(rows)
    best_union = best_union_candidate(rows)
    if best_complement is None or best_union is None:
        raise SystemExit("best complement candidate list is empty")

    complement = as_segments(best_complement["candidate_complement_segment_ids"])
    union_complement = as_segments(best_union["candidate_complement_segment_ids"])
    union = as_segments(best_union["union_segment_ids"])

    leader_png = out_dir / "h12_complement_leader_only.png"
    complement_png = out_dir / "h12_complement_only.png"
    leader_plus_complement_png = out_dir / "h12_leader_plus_complement.png"
    union_vs_universal_png = out_dir / "h12_union_vs_universal_overlay.png"
    union_vs_simplified_png = out_dir / "h12_union_vs_simplified_overlay.png"
    complement_diff_png = out_dir / "h12_complement_difference_map.png"
    report_md = out_dir / "h12_complement_report.md"

    render_single(leader_png, f"Fixed leader: {LEADER_KEY}", LEADER_SEGMENTS, "#666666")
    render_single(complement_png, "Best complement candidate only", complement, "#1565c0")
    render_leader_plus_complement(
        leader_plus_complement_png,
        "Leader + complement candidate (best union candidate)",
        LEADER_SEGMENTS,
        union_complement,
    )
    uni_diff = render_overlay(union_vs_universal_png, "Union vs universal", union, UNIVERSAL_SEGMENTS)
    render_overlay(union_vs_simplified_png, "Union vs simplified", union, SIMPLIFIED_SEGMENTS)
    comp_diff = render_overlay(complement_diff_png, "Complement vs missing target", complement, MISSING_SEGMENTS)

    cc = best_complement["comparison"]
    cu = best_union["comparison"]
    report_md.write_text(
        "# H12 Complement Candidate Report\n\n"
        f"- fixed leader: `{LEADER_KEY}`\n"
        f"- best exact-complement candidate: `{best_complement['spec']['key']}`\n"
        f"- complement source: `{best_complement['source_name']}`\n"
        f"- exact complement: `{cc['exact_complement']}`\n"
        f"- matched complement segments: `{cc['matched_complement_segments']}` / `{len(MISSING_SEGMENTS)}`\n"
        f"- missing after union vs universal: `{cc['missing_after_union_vs_universal']}`\n"
        f"- extra after union vs universal: `{cc['extra_after_union_vs_universal']}`\n"
        f"- angle-class match: `{cc['angle_class_match']:.6f}`\n"
        f"- best union candidate: `{best_union['spec']['key']}`\n"
        f"- union source: `{best_union['source_name']}`\n"
        f"- exact union: `{cu['exact_union']}`\n"
        f"- union matched complement segments: `{cu['matched_complement_segments']}` / `{len(MISSING_SEGMENTS)}`\n"
        f"- union missing vs universal: `{cu['missing_after_union_vs_universal']}`\n"
        f"- union extra vs universal: `{cu['extra_after_union_vs_universal']}`\n"
        f"- node coverage: `{cu['node_coverage']}` / `{len(TARGET_NODE_ORDER)}`\n\n"
        "## Complement Difference Map\n\n"
        f"- matched complement lines: {segment_text(comp_diff['matched'])}\n"
        f"- missing complement lines: {segment_text(comp_diff['missing'])}\n"
        f"- extra complement lines: {segment_text(comp_diff['extra'])}\n\n"
        "## Union vs Universal\n\n"
        f"- matched union lines: `{len(uni_diff['matched'])}`\n"
        f"- missing universal lines: {segment_text(uni_diff['missing'])}\n"
        f"- extra union lines: {segment_text(uni_diff['extra'])}\n\n"
        "## Images\n\n"
        f"- leader only: `{leader_png}`\n"
        f"- complement only: `{complement_png}`\n"
        f"- leader + complement: `{leader_plus_complement_png}`\n"
        f"- union vs universal: `{union_vs_universal_png}`\n"
        f"- union vs simplified: `{union_vs_simplified_png}`\n"
        f"- complement difference map: `{complement_diff_png}`\n"
    )
    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
