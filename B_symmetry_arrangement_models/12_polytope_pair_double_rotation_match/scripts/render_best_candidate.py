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

from research.async_jobs.h12_polytope_pair_search import TARGET_NODE_ORDER, TARGET_SEGMENTS

BRANCH_DIR = ROOT / "research" / "B_symmetry_arrangement_models" / "12_polytope_pair_double_rotation_match"
DEFAULT_STATE_DIR = ROOT / "research" / "async_state" / "h12_polytope_pair"


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
    draw_segments(ax, segments, color=color, linewidth=2.6)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def render_overlay(path: Path, candidate: set[tuple[int, int]]) -> dict:
    matched = candidate & TARGET_SEGMENTS
    missing = TARGET_SEGMENTS - candidate
    extra = candidate - TARGET_SEGMENTS
    fig, ax = plt.subplots(figsize=(5, 6))
    setup_ax(ax, "H12 overlay / difference map")
    draw_segments(ax, matched, color="#178f45", linewidth=3.0, label="matched")
    draw_segments(ax, missing, color="#c62828", linewidth=2.5, linestyle="--", label="missing target")
    draw_segments(ax, extra, color="#1565c0", linewidth=1.8, linestyle=":", label="extra candidate")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {"matched": matched, "missing": missing, "extra": extra}


def segment_text(segments: set[tuple[int, int]]) -> str:
    if not segments:
        return "`none`"
    chunks = []
    for a, b in sorted(segments):
        chunks.append(f"`{TARGET_NODE_ORDER[a]} -> {TARGET_NODE_ORDER[b]}`")
    return ", ".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--out-dir", default=str(BRANCH_DIR / "figures"))
    args = parser.parse_args()

    state_dir = Path(args.state_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best_path = state_dir / "best_candidates.json"
    if not best_path.exists():
        raise SystemExit(f"best candidates file is missing: {best_path}")
    candidates = json.loads(best_path.read_text())
    if not candidates:
        raise SystemExit("best candidates list is empty")
    best = candidates[0]
    candidate = as_segments(best["segment_ids"])

    target_png = out_dir / "h12_target_simplified_lattice.png"
    candidate_png = out_dir / "h12_best_candidate_lattice.png"
    overlay_png = out_dir / "h12_overlay_difference.png"
    report_md = out_dir / "h12_best_candidate_report.md"

    render_single(target_png, "Target simplified lattice", TARGET_SEGMENTS, "#333333")
    render_single(candidate_png, "Best H12 candidate lattice", candidate, "#1565c0")
    diff = render_overlay(overlay_png, candidate)

    c = best["comparison"]
    found = "да" if c["topology_match"] else "нет"
    report_md.write_text(
        "# H12 Best Candidate Report\n\n"
        f"- source / rotation / projection: `{best['spec']['key']}`\n"
        f"- сетку нашли: `{found}`\n"
        f"- score: `{best['score']:.6f}`\n"
        f"- target segments matched: `{c['matched_segments']}` / `{c['target_segment_count']}`\n"
        f"- missing target segments: `{c['missing_segments']}`\n"
        f"- extra candidate segments: `{c['extra_segments']}`\n"
        f"- vertical masts: `{c['vertical_masts_matched']}` / `{c['vertical_masts_total']}`\n"
        f"- central rays: `{c['central_rays_matched']}` / `{c['central_rays_total']}`\n"
        f"- angle-class jaccard: `{c['angle_class_jaccard']:.6f}`\n\n"
        "## Что совпало\n\n"
        f"{segment_text(diff['matched'])}\n\n"
        "## Чего не хватает от целевой сетки\n\n"
        f"{segment_text(diff['missing'])}\n\n"
        "## Что лишнее у кандидата\n\n"
        f"{segment_text(diff['extra'])}\n\n"
        "## Images\n\n"
        f"- target: `{target_png}`\n"
        f"- candidate: `{candidate_png}`\n"
        f"- overlay / difference map: `{overlay_png}`\n"
    )
    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
