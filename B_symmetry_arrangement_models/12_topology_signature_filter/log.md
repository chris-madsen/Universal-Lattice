# Log

## 2026-05-09 03:00 — baseline
Цель:
- запустить первую версию topological-signature фильтра для branch `05`.
Гипотеза:
- существенная доля пространства branch `05` схлопывается в меньшее число симметрийных классов.
Скрипт:
- `scripts/run.py`
Артефакты:
- `data/topology_signature_space_report.json`
- `data/topology_signature_space_report.md`
Что считаю:
- полный размер параметризованного пространства branch `05`;
- число уникальных signature-классов;
- reduction ratio.
Формулы / reasoning:
- signed-permutation symmetry факторизация должна убрать эквивалентные перестановки/знаки осей.
Промежуточные результаты:
- raw candidate space: `38,478`
- unique topological signatures: `14,510`
- overall compression ratio: `2.651826x`
- high-compression roots reach `4.000000x` (например `A2_B2-0_B1-5_B0-0@01/@23`)
Что это значит:
- signed-permutation symmetry даёт сильное схлопывание эквивалентных конфигураций;
- topology-signature фильтр имеет смысл включать до expensive projection evaluation.
Сложность:
- средняя.
Следующий шаг:
- встроить фильтр в loop и сравнить с/без фильтра на одинаковом бюджете.

## 2026-05-09 03:40 — integration-into-branch05-tree
Цель:
- встроить topological_signature фильтр в live tree-search branch `05`.
Гипотеза:
- pre-eval symmetry factorization уберёт эквивалентные прогоны без потери полезных классов.
Скрипт:
- `research/async_jobs/branch05_ga_aco_tree_search.py`
- `research/common/topological_signature.py`
Артефакты:
- `research/async_state/branch05_topology_filter_smoke/ga_aco_summary.md`
- `research/async_state/branch05_topology_filter_smoke2/ga_aco_summary.md`
Что считаю:
- skip-equivalent в пределах поколения;
- skip-by-cap по уже считанным signatures;
- unique signature coverage в summary.
Формулы / reasoning:
- signature canonicalization по signed-permutation action в `R^4`.
Промежуточные результаты:
- фильтр успешно интегрирован;
- summary/log получают новые поля topology-filter;
- smoke run подтверждает рабочий loop (`topology filter: True`).
Что это значит:
- эквивалентные конфигурации можно отсекать до expensive projection eval.
Сложность:
- средняя.
Следующий шаг:
- запускать отдельный долгий async-run с фильтром и сравнить качество top candidates против baseline без фильтра на равном бюджете.

## 2026-05-09 04:25 — long-run AB resume + anti-stall
Цель:
- продолжить долгий A/B прогон (`with_filter` vs `no_filter`) после восстановления контекста.
Гипотеза:
- `signature_cap=1` полезен для дедупа, но может загонять `with_filter` в стагнацию (поколения идут, новых eval почти нет).
Скрипт:
- `research/async_jobs/branch05_ga_aco_tree_search.py`
- `research/async_jobs/branch05_topology_ab_runner.py`
Артефакты:
- `research/async_state/branch05_ab/no_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/with_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/comparison.md`
Что изменено:
- добавлен `anti-stall backfill` в topology-filter loop:
- если весь batch упирается в `signature_cap`, в eval пропускается небольшой least-seen backfill (без отключения фильтра).
Промежуточные результаты:
- после перезапуска на новом коде в `with_filter` снова пошёл рост eval:
- candidate evaluations: `1944 -> 2111`;
- unique signatures: `1944 -> 1955`;
- в логе появились записи `topology anti-stall backfill=4`.
- baseline `no_filter` продолжает run в штатном режиме (`~1.17M` candidate eval на текущем срезе).
Что это значит:
- фильтр остаётся включённым, но loop больше не “пустой” при полном попадании в cap.
- сравнение A/B теперь корректнее для длительного непрерывного прогона.
Сложность:
- средняя.
Следующий шаг:
- продолжать run до целевого бюджета и снимать сравнение по состоянию `comparison.md` в контрольных точках.

## 2026-05-09 07:31 — AB completed
Цель:
- получить завершённый A/B итог по topology-filter на одинаковом поколенческом бюджете.
Скрипт:
- `research/async_jobs/branch05_topology_ab_runner.py compare`
Артефакты:
- `research/async_state/branch05_ab/no_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/with_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/comparison.md`
Итог:
- `no_filter`: completed `50000/50000`, candidate evals=`3,600,000`, projection evals=`345,600,000`, elapsed=`5004.95s`;
- `with_filter`: completed `50000/50000`, candidate evals=`168,929`, projection evals=`16,217,184`, elapsed=`12811.92s`;
- `with_filter` unique signatures=`3,677` (`9.5561%` от `38,478`);
- topology skips (`with_filter`): batch_equivalent=`1,685,396`, signature_cap=`1,910,927`.
Вывод:
- как strict pre-eval dedup/filter текущая конфигурация радикально режет объём eval;
- при этом в текущей настройке фильтр не ускоряет wall-clock completion относительно baseline.
