# 12_topology_signature_filter

Purpose of the branch: remove orbitally equivalent configurations from branch `05` before heavy evaluation by projections.

Key idea:
- construct a symmetry-invariant `topological_signature` candidate;
- use it as a filter in the `GA + ACO` tree;
- We estimate how much the number of actually different configurations decreases.

Main artifacts:
- `data/topology_signature_space_report.json`
- `data/topology_signature_space_report.md`
