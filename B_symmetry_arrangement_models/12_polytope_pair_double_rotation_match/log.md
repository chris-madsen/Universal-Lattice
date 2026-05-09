# Log

## 2026-05-09 15:20 — branch initialization
Цель:
Запустить настоящую H12-ветку как поиск пар 4D-источников с double rotation и сравнением с упрощённой сеткой.
Гипотеза:
`12_polytope_pair_double_rotation_match`
Скрипт:
`research/async_jobs/h12_polytope_pair_search.py`
Артефакты:
- `PLAN.md`
- `README.md`
- `research/async_state/h12_polytope_pair/`
Что считаю:
- красивые пары политопов;
- double rotations;
- deterministic projection families;
- topology signature against simplified lattice;
- score совпадения сегментов, центральных лучей, вертикальных мачт и угловых классов.
Формулы / reasoning:
- full coarse scan не запускается;
- topology signature убирает affine multiplication;
- Rust kernel используется для projection-family stability внутри общей Python-оболочки.
Промежуточные результаты:
- count calculator: `3,240` structural families, `155,520` deterministic projected candidates.
- target extractor: `11` segments, `15` nodes, `3` vertical masts, `8` central rays.
Что это значит:
- ветка теперь соответствует исходной постановке H12, а не старому заходу `12_topology_signature_filter`.
Сложность:
- контролируемая; запускается resumable async service с checkpoint после каждой пачки.
Следующий шаг:
- запустить systemd service `runes-h12-polytope-pair.service`.

## 2026-05-09 15:19 — service deployed
Цель:
Запустить H12 как resumable background job в существующем research slice.
Гипотеза:
`12_polytope_pair_double_rotation_match`
Скрипт:
`research/async_jobs/h12_polytope_pair_search.py`
Артефакты:
- `/home/ilja/.config/systemd/user/runes-h12-polytope-pair.service`
- `research/async_state/h12_polytope_pair/state.json`
- `research/async_state/h12_polytope_pair/summary.md`
- `research/async_state/h12_polytope_pair/log.md`
- `research/async_state/h12_polytope_pair/best_candidates.json`
- `figures/h12_best_candidate_report.md`
Что считаю:
- source pairs;
- double rotations;
- deterministic projection families;
- readout modes;
- topology signature against simplified lattice;
- Rust-backed projection-family stability.
Формулы / reasoning:
- service uses `CPUWeight=10`, `Nice=19`, batch CPU scheduling and idle I/O;
- no hard CPU quota is used;
- `Restart=always` is safe because the job resumes from `state.json` and idles after completion.
Промежуточные результаты:
- service active in `runes-research.slice`;
- restart/resume smoke test passed;
- live search reached `8/11` target segments and `8/8` central rays in early generations, but not the full simplified grid.
Что это значит:
- H12 now runs as the intended beautiful-first pair-of-polytopes search, not as the old standalone topology filter.
Сложность:
- controlled async search; current live ETA is reported in hours/minutes in `summary.md`.
Следующий шаг:
- monitor `summary.md` and render updated best candidates when the live best changes materially.

## 2026-05-09 15:59 — target-segmentation correction and rerun
Цель:
Проверить, не является ли `vertical_masts=0` артефактом сегментации, а не реальным провалом геометрии.
Гипотеза:
`12_polytope_pair_double_rotation_match`
Скрипт:
`research/async_jobs/h12_polytope_pair_search.py`
Артефакты:
- `research/async_jobs/h12_polytope_pair_search.py` (patched `segments_from_family_angles`)
- `research/async_state/h12_polytope_pair_pre_mast_fix_20260509_155856/` (archived old run)
- `research/async_state/h12_polytope_pair/` (fresh rerun state)
Что считаю:
- совпадение с упрощённой сеткой с разрешением длинных target-примитивов (включая 3 полные мачты).
Формулы / reasoning:
- старая проверка отбрасывала любой длинный сегмент при наличии промежуточных узлов;
- из-за этого 3 вертикальные мачты не могли быть засчитаны принципиально;
- после фикса длинные сегменты разрешаются, если они входят в target segment set.
Промежуточные результаты:
- smoke после фикса дал кандидата `24-T|r1:1|a36|p0|line_arrangement_core|central_bundle:5` с `11/11` target segments, `3/3` masts, `8/8` rays, но с `46` extra segments.
Что это значит:
- предыдущий вывод «мачты не восстанавливаются» был частично методическим артефактом;
- текущая задача сместилась в сторону подавления лишних линий при сохранении полного target cover.
Сложность:
- средняя; теперь ключевой риск — over-rich candidates.
Следующий шаг:
- продолжать live run и продвигать score в сторону меньшего `extra_segments` при сохранении `11/11`.

## 2026-05-09 17:32 — complement service implemented
Цель:
Запустить отдельный H12 complement-search поверх фиксированного лидера, а не поверх всей pair-search задачи.
Гипотеза:
`12_polytope_pair_double_rotation_match`
Скрипт:
`research/async_jobs/h12_complement_search.py`
Артефакты:
- `research/async_jobs/h12_complement_search.py`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/scripts/render_best_complement_candidate.py`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/data/complement_target_truth.md`
- `research/async_state/h12_complement_smoke/`
Что считаю:
- complement layer к лидеру `T-T|r1:2|a22.5|p0|edge_union|central_bundle:3`;
- exact missing set `universal \ leader`;
- staged search сначала по `16-cell`, затем по `tesseract`, затем при сигнале по orientation seeds.
Формулы / reasoning:
- candidate оценивается как дополнение, а не как новая сетка с нуля;
- topology signature фильтрует эквивалентные union/complement варианты до вызова Rust hot kernel;
- score приоритизирует `missing_after_union_vs_universal`, затем `extra_after_union_vs_universal`.
Промежуточные результаты:
- truth extraction подтвердил `16` missing segments;
- smoke на `A16_base` сразу дал best candidate с `14/16` совпавшими complement segments, `2` missing и `9` extra after union;
- resume smoke подтвердил переход между checkpoint и следующей стадией (`A16_base -> A16_readout`).
Что это значит:
- complement-search не декоративный, а сразу дал сильный сигнал именно по `16-cell`.
Сложность:
- контролируемая; реальный сервис должен продолжить staged search асинхронно.
Следующий шаг:
- задеплоить `runes-h12-complement.service` и запустить полноценный фоновой поиск.

## 2026-05-09 17:34 — complement service deployed and live
Цель:
Запустить полноценный complement-search как живой resumable service и зафиксировать первые сильные результаты.
Гипотеза:
`12_polytope_pair_double_rotation_match`
Скрипт:
`research/async_jobs/h12_complement_search.py`
Артефакты:
- `/home/ilja/.config/systemd/user/runes-h12-complement.service`
- `research/async_state/h12_complement/state.json`
- `research/async_state/h12_complement/summary.md`
- `research/async_state/h12_complement/log.md`
- `research/async_state/h12_complement/best_candidates.json`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/figures/h12_complement_report.md`
Что считаю:
- staged complement search from the fixed leader to `universal-lattice.py`;
- first `16-cell`, then `tesseract`, then orientation-seed expansion only if needed;
- exact complement match and exact union match as separate mathematical objectives.
Формулы / reasoning:
- exact complement asks whether the added layer equals `universal \\ leader`;
- union quality asks whether `leader ∪ complement_candidate` reproduces the universal segment set with minimal extra lines;
- these are related but not identical objectives, so they are tracked separately.
Промежуточные результаты:
- live service is active in `runes-research.slice`;
- `A16_projection|16|r3:4|a18|p0|line_arrangement_core|central_bundle:2|o0` produced an exact complement match `16/16`;
- `A16_readout|16|r1:1|a7.5|p1|line_arrangement_core|central_bundle:3|o0` produced a union candidate with `0` missing universal segments and `9` extra segments;
- all `15` fixed nodes are preserved in the best union candidate.
Что это значит:
- the `16-cell` branch is now strongly supported;
- the main remaining task is not to recover missing target geometry, but to reduce extra segments while preserving the full union coverage.
Сложность:
- controlled async search; service is still exploring `A16_projection` and has not yet needed the `tesseract` branch.
Следующий шаг:
- continue the live run;
- if `16-cell` stalls on extra-segment suppression, open the `tesseract` complement stage and compare directly.
