#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import argparse
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


Frac = Fraction
Point = Tuple[Frac, Frac]
Segment = Tuple[Point, Point]


@dataclass(frozen=True)
class CanonicalLine:
    a: Frac
    b: Frac
    c: Frac


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def frac(value: float | int) -> Frac:
    return Frac(str(value)) if isinstance(value, float) else Frac(value)


def point(x: float | int, y: float | int) -> Point:
    return (frac(x), frac(y))


def build_reference_segments() -> List[Segment]:
    segments: List[Segment] = []
    for x in [0, 1, 2]:
        segments.append((point(x, 0), point(x, 3)))
    for ty in [0, 1, 1.5, 2]:
        segments.append((point(0, 3), point(2, ty)))
        segments.append((point(2, 3), point(0, ty)))
    for ty in [1, 1.5, 2, 3]:
        segments.append((point(0, 0), point(2, ty)))
        segments.append((point(2, 0), point(0, ty)))
    for tx, ty in [(0, 2), (2, 2), (0, 1.5), (2, 1.5)]:
        segments.append((point(1, 3), point(tx, ty)))
    for tx, ty in [(0, 1), (2, 1), (0, 1.5), (2, 1.5)]:
        segments.append((point(1, 0), point(tx, ty)))
    segments.append((point(0, 1), point(2, 2)))
    segments.append((point(2, 1), point(0, 2)))
    return segments


def build_anchor_nodes() -> List[Point]:
    return [point(x, y) for x in [0, 1, 2] for y in [0, 1, 1.5, 2, 3]]


def canonicalize_segment(segment: Segment) -> Segment:
    p1, p2 = segment
    return (p1, p2) if p1 <= p2 else (p2, p1)


def canonical_line_from_segment(segment: Segment) -> CanonicalLine:
    (x1, y1), (x2, y2) = segment
    a = y1 - y2
    b = x2 - x1
    c = x1 * y2 - x2 * y1
    denoms = [v.denominator for v in (a, b, c)]
    lcm = 1
    for d in denoms:
        lcm = lcm * d // gcd(lcm, d)
    ai = int(a * lcm)
    bi = int(b * lcm)
    ci = int(c * lcm)
    g = gcd(gcd(abs(ai), abs(bi)), abs(ci)) or 1
    ai //= g
    bi //= g
    ci //= g
    if ai < 0 or (ai == 0 and bi < 0) or (ai == 0 and bi == 0 and ci < 0):
        ai, bi, ci = -ai, -bi, -ci
    return CanonicalLine(Frac(ai), Frac(bi), Frac(ci))


def project_param(point_: Point, segment: Segment) -> Frac:
    (x, y) = point_
    (x1, y1), (x2, y2) = segment
    dx = x2 - x1
    dy = y2 - y1
    denom = dx * dx + dy * dy
    return Frac(0) if denom == 0 else ((x - x1) * dx + (y - y1) * dy) / denom


def signed_slope(segment: Segment) -> Frac | None:
    (x1, y1), (x2, y2) = segment
    dx = x2 - x1
    dy = y2 - y1
    return None if dx == 0 else dy / dx


def family_name(segment: Segment) -> str:
    slope = signed_slope(segment)
    if slope is None:
        return "vertical"
    abs_slope = abs(slope)
    mapping = {
        Frac(1, 2): "slope_abs_1_2",
        Frac(3, 4): "slope_abs_3_4",
        Frac(1, 1): "slope_abs_1_1",
        Frac(3, 2): "slope_abs_3_2",
    }
    return mapping.get(abs_slope, f"slope_abs_{abs_slope.numerator}_{abs_slope.denominator}")


def oriented_family_name(segment: Segment) -> str:
    slope = signed_slope(segment)
    if slope is None:
        return "vertical"
    sign = "pos" if slope > 0 else "neg"
    abs_slope = abs(slope)
    return f"{sign}_{abs_slope.numerator}_{abs_slope.denominator}"


def family_sort_key(segment: Segment) -> Tuple[int, float, float]:
    fam = family_name(segment)
    order = {"vertical": 0, "slope_abs_1_2": 1, "slope_abs_3_4": 2, "slope_abs_1_1": 3, "slope_abs_3_2": 4}
    slope = signed_slope(segment)
    slope_value = 999.0 if slope is None else float(slope)
    return (order.get(fam, 99), float(length_squared(segment)), slope_value)


def segment_sort_key(segment: Segment) -> Tuple[float, float, float, float]:
    (x1, y1), (x2, y2) = segment
    return (float(x1), float(y1), float(x2), float(y2))


def merge_into_maximal_segments(segments: Sequence[Segment]) -> List[Dict[str, object]]:
    groups: Dict[CanonicalLine, List[Segment]] = {}
    for seg in segments:
        groups.setdefault(canonical_line_from_segment(seg), []).append(canonicalize_segment(seg))
    maximal: List[Dict[str, object]] = []
    for line, segs in groups.items():
        endpoints: List[Point] = []
        for seg in segs:
            endpoints.extend(seg)
        ref = segs[0]
        unique_points = sorted(set(endpoints), key=lambda p: project_param(p, ref))
        maximal.append({
            "line": line,
            "segment": (unique_points[0], unique_points[-1]),
            "support_points": unique_points,
            "source_segment_count": len(segs),
        })
    maximal.sort(key=lambda item: (family_sort_key(item["segment"]), segment_sort_key(item["segment"])))
    return maximal


def segment_contains_point(segment: Segment, p: Point) -> bool:
    (x, y) = p
    (x1, y1), (x2, y2) = segment
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if cross != 0:
        return False
    return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)


def line_intersection(seg1: Segment, seg2: Segment) -> Point | None:
    (x1, y1), (x2, y2) = seg1
    (x3, y3), (x4, y4) = seg2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None
    det1 = x1 * y2 - y1 * x2
    det2 = x3 * y4 - y3 * x4
    px = (det1 * (x3 - x4) - (x1 - x2) * det2) / den
    py = (det1 * (y3 - y4) - (y1 - y2) * det2) / den
    return (px, py)


def infer_arrangement_intersections(maximal_segments: Sequence[Dict[str, object]]) -> List[Point]:
    nodes = set(build_anchor_nodes())
    segments = [item["segment"] for item in maximal_segments]
    for idx, seg1 in enumerate(segments):
        for seg2 in segments[idx + 1 :]:
            p = line_intersection(seg1, seg2)
            if p is None:
                continue
            if segment_contains_point(seg1, p) and segment_contains_point(seg2, p):
                nodes.add(p)
    return sorted(nodes)


def length_squared(segment: Segment) -> Frac:
    (x1, y1), (x2, y2) = segment
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy


def point_label(p: Point) -> str:
    x, y = p
    return f"({format_fraction(x)},{format_fraction(y)})"


def format_fraction(value: Frac) -> str:
    return str(int(value)) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def to_json_value(value):
    if isinstance(value, Fraction):
        return {"fraction": format_fraction(value), "float": float(value)}
    if isinstance(value, CanonicalLine):
        return {"a": format_fraction(value.a), "b": format_fraction(value.b), "c": format_fraction(value.c)}
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and all(isinstance(v, tuple) and len(v) == 2 and all(isinstance(c, Fraction) for c in v) for v in value)
    ):
        p1, p2 = value
        return [to_json_value(p1), to_json_value(p2)]
    if isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, Fraction) for v in value):
        x, y = value
        return {
            "x": float(x),
            "y": float(y),
            "x_fraction": format_fraction(x),
            "y_fraction": format_fraction(y),
            "label": point_label(value),
        }
    return value


def from_json_point(payload: Dict[str, object]) -> Point:
    return (Frac(str(payload["x_fraction"])), Frac(str(payload["y_fraction"])))


def from_json_segment(payload) -> Segment:
    return (from_json_point(payload[0]), from_json_point(payload[1]))


def fraction_key(text: str) -> Tuple[int, int]:
    value = Frac(text)
    return (value.numerator, value.denominator)


def build_signature() -> Dict[str, object]:
    raw_segments = [canonicalize_segment(seg) for seg in build_reference_segments()]
    maximal_segments = merge_into_maximal_segments(raw_segments)
    anchor_nodes = sorted(build_anchor_nodes())
    arrangement_nodes = infer_arrangement_intersections(maximal_segments)
    false_intersections = sorted(set(arrangement_nodes) - set(anchor_nodes))

    line_records = []
    for idx, item in enumerate(maximal_segments, start=1):
        segment = item["segment"]
        line_records.append({
            "id": f"L{idx:02d}",
            "family": family_name(segment),
            "oriented_family": oriented_family_name(segment),
            "segment": to_json_value(segment),
            "line": to_json_value(item["line"]),
            "support_points": [to_json_value(p) for p in item["support_points"]],
            "support_point_labels": [point_label(p) for p in item["support_points"]],
            "source_segment_count": item["source_segment_count"],
        })

    anchor_records = []
    for idx, node in enumerate(anchor_nodes, start=1):
        incident = []
        family_counts: Dict[str, int] = {}
        for line in line_records:
            seg = from_json_segment(line["segment"])
            if segment_contains_point(seg, node):
                incident.append(line["id"])
                family_counts[line["family"]] = family_counts.get(line["family"], 0) + 1
        anchor_records.append({
            "id": f"N{idx:02d}",
            "point": to_json_value(node),
            "incident_lines": incident,
            "degree": len(incident),
            "family_counts": family_counts,
        })

    family_counts: Dict[str, int] = {}
    oriented_family_counts: Dict[str, int] = {}
    for line in line_records:
        family_counts[line["family"]] = family_counts.get(line["family"], 0) + 1
        oriented_family_counts[line["oriented_family"]] = oriented_family_counts.get(line["oriented_family"], 0) + 1

    mast_attachment_levels = {}
    for x in [Frac(0), Frac(1), Frac(2)]:
        labels = sorted({node["point"]["y_fraction"] for node in anchor_records if Frac(node["point"]["x_fraction"]) == x}, key=fraction_key)
        mast_attachment_levels[str(int(x))] = labels

    return {
        "source": "universal-lattice.py",
        "raw_segment_count": len(raw_segments),
        "maximal_line_count": len(line_records),
        "anchor_node_count": len(anchor_records),
        "arrangement_intersection_count": len(arrangement_nodes),
        "false_intersection_count": len(false_intersections),
        "family_counts": family_counts,
        "oriented_family_counts": oriented_family_counts,
        "mast_attachment_levels": mast_attachment_levels,
        "key_nodes": {
            "center": point_label(point(1, 1.5)),
            "top_center": point_label(point(1, 3)),
            "bottom_center": point_label(point(1, 0)),
            "corners": [point_label(point(0, 0)), point_label(point(0, 3)), point_label(point(2, 0)), point_label(point(2, 3))],
        },
        "raw_segments": [to_json_value(seg) for seg in raw_segments],
        "maximal_lines": line_records,
        "anchor_nodes": anchor_records,
        "arrangement_intersections": [to_json_value(p) for p in arrangement_nodes],
        "false_intersections": [to_json_value(p) for p in false_intersections],
    }


def write_svg(signature: Dict[str, object], output_path: Path) -> None:
    width = 900
    height = 1200
    margin_x = 120
    margin_y = 120
    scale_x = 300
    scale_y = 280

    def map_point(p: Point) -> Tuple[float, float]:
        x, y = p
        return (margin_x + float(x) * scale_x, height - margin_y - float(y) * scale_y)

    lines_svg: List[str] = []
    for line in signature["maximal_lines"]:
        seg = from_json_segment(line["segment"])
        (x1, y1), (x2, y2) = map_point(seg[0]), map_point(seg[1])
        lines_svg.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#9aa0a6" stroke-width="3" />')
        lines_svg.append(f'<text x="{(x1+x2)/2:.2f}" y="{(y1+y2)/2-8:.2f}" font-size="18" text-anchor="middle" fill="#2f4f4f">{line["id"]}</text>')

    nodes_svg: List[str] = []
    for node in signature["anchor_nodes"]:
        p = from_json_point(node["point"])
        x, y = map_point(p)
        nodes_svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="#d62728" />')
        nodes_svg.append(f'<text x="{x + 10:.2f}" y="{y - 10:.2f}" font-size="16" fill="#111">{node["id"]}</text>')

    family_text = ', '.join(f'{k}:{v}' for k, v in signature['family_counts'].items())
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white" />
  <text x="40" y="45" font-size="28" fill="#111">Universal lattice baseline signature</text>
  <text x="40" y="80" font-size="18" fill="#444">maximal lines={signature['maximal_line_count']} | anchor nodes={signature['anchor_node_count']} | false intersections={signature['false_intersection_count']} | families={family_text}</text>
  {' '.join(lines_svg + nodes_svg)}
</svg>
'''
    output_path.write_text(svg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args()
    signature = build_signature()
    args.output.write_text(json.dumps(signature, indent=2, ensure_ascii=True))
    if args.figure:
        write_svg(signature, args.figure)
    print(f"wrote_signature={args.output}")
    if args.figure:
        print(f"wrote_figure={args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
