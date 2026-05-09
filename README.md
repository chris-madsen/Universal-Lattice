# Research Workspace

This directory stores the working artifacts of the generative lattice origin research from `universal-lattice.py`.

Rules:
- all the research noise lives only here;
- each hypothesis is kept in its own folder;
- scripts, logs, results and visual artifacts do not mix;
- if a branch runs into computational complexity, this is recorded in the log, and the research moves on.

Quick entry documents:
- general index of branches: `/home/ilja/Desktop/runes/docs/research/index.md`
- glossary/faq on terminology branch `05`: `/home/ilja/Desktop/runes/docs/research/branch05_glossary_faq.md`
- active H12 branch source-pair double-rotation search: `/home/ilja/Desktop/runes/docs/research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/result.md`
- historical H12-filter entry: `/home/ilja/Desktop/runes/docs/research/B_symmetry_arrangement_models/12_topology_signature_filter/result.md`

## Git Publication Profile

To publish to git, we store in this directory:
- code (`scripts/`, `common/`, `async_jobs/`, `rust/*/src/`);
- text artifacts (`README.md`, `log.md`, `result.md`, `*.md`, `*.json` in branches).

Exclude via `.gitignore`:
- runtime states (`async_state/`);
- cache/compiled noise (`__pycache__/`, `*.pyc`);
- Rust build artifacts (`rust/**/target/`);
- visual artifacts (`*.png`, `*.jpg`, `*.svg`, `*.webp`, `*.pdf`).
