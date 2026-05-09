# Research Workspace

Этот каталог хранит рабочие артефакты исследования происхождения порождающей решётки из `universal-lattice.py`.

Правила:
- весь исследовательский шум живёт только здесь;
- каждая гипотеза ведётся в своей папке;
- скрипты, логи, результаты и визуальные артефакты не смешиваются;
- если ветка упирается в вычислительную сложность, это фиксируется в логе, и исследование идёт дальше.

Быстрые входные документы:
- общий индекс веток: `/home/ilja/Desktop/runes/docs/research/index.md`
- glossary/faq по терминологии branch `05`: `/home/ilja/Desktop/runes/docs/research/branch05_glossary_faq.md`
- активная H12-ветка source-pair double-rotation search: `/home/ilja/Desktop/runes/docs/research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/result.md`
- исторический H12-filter заход: `/home/ilja/Desktop/runes/docs/research/B_symmetry_arrangement_models/12_topology_signature_filter/result.md`

## Git Publication Profile

Для публикации в git в этом каталоге храним:
- код (`scripts/`, `common/`, `async_jobs/`, `rust/*/src/`);
- текстовые артефакты (`README.md`, `log.md`, `result.md`, `*.md`, `*.json` в ветках).

Исключаем через `.gitignore`:
- runtime-состояния (`async_state/`);
- cache/compiled шум (`__pycache__/`, `*.pyc`);
- Rust build artifacts (`rust/**/target/`);
- визуальные артефакты (`*.png`, `*.jpg`, `*.svg`, `*.webp`, `*.pdf`).
