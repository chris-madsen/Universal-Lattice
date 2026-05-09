#!/usr/bin/env python3
from __future__ import annotations

from typing import Dict, List

KEY_FAMILIES = {"vertical", "slope_abs_1_2", "slope_abs_3_4", "slope_abs_1_1", "slope_abs_3_2"}


def derive_generativity_grammar(signature: Dict[str, object]) -> Dict[str, object]:
    nodes: List[Dict[str, object]] = signature["anchor_nodes"]
    family_counts: Dict[str, int] = signature["family_counts"]

    center = next(node for node in nodes if node["point"]["label"] == "(1,3/2)")
    top_center = next(node for node in nodes if node["point"]["label"] == "(1,3)")
    bottom_center = next(node for node in nodes if node["point"]["label"] == "(1,0)")
    corners = [node for node in nodes if node["point"]["label"] in {"(0,0)", "(0,3)", "(2,0)", "(2,3)"}]

    return {
        "vertical_mast_count": family_counts.get("vertical", 0),
        "absolute_family_count": len(family_counts),
        "family_set_matches_expected": set(family_counts) == KEY_FAMILIES,
        "anchor_node_count": signature["anchor_node_count"],
        "false_intersection_count": signature["false_intersection_count"],
        "center_degree": center["degree"],
        "top_center_degree": top_center["degree"],
        "bottom_center_degree": bottom_center["degree"],
        "corner_degrees": {node["point"]["label"]: node["degree"] for node in corners},
        "mast_attachment_levels": signature["mast_attachment_levels"],
        "central_core_labels": [center["point"]["label"], top_center["point"]["label"], bottom_center["point"]["label"]],
    }
