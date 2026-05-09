# Log

## YYYY-MM-DD HH:MM — baseline
Цель:
Гипотеза:
Скрипт:
Артефакты:
Что считаю:
Формулы / reasoning:
Промежуточные результаты:
Что это значит:
Сложность:
Следующий шаг:

## 2026-05-08 21:06 — baseline
Цель: зафиксировать arrangement-аспекты решётки, которые делают ветку `08_f4_root_arrangement` не декоративной, а содержательной.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_arrangement_targets.json`
- `data/baseline_arrangement_targets.md`
Что считаю:
- anchor nodes;
- arrangement intersections;
- false intersections;
- центральные degrees.
Формулы / reasoning:
- если у решётки при продолжении maximal lines возникает большой слой false intersections, то arrangement-подход выглядит естественно, а не натянуто.
Промежуточные результаты:
- anchor / arrangement / false intersections: `15` / `93` / `78`
Что это значит:
- ветка `08` получает прямую структурную мотивацию из уже извлечённой сигнатуры решётки.
Сложность:
- низкая.
Следующий шаг:
- сделать prune на arrangement-plausibility и понять, усиливает ли baseline эту ветку по сравнению с уже ослабленными 01–03.

## 2026-05-08 21:06 — prune
Цель: проверить, усиливает ли baseline сама идея arrangement-подхода, а не только абстрактная связь с `F4`.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage prune`
Артефакты:
- `data/prune_arrangement_plausibility.json`
- `data/prune_arrangement_plausibility.md`
Что считаю:
- отношение false intersections к anchor nodes.
Формулы / reasoning:
- если false-intersection слой большой, arrangement-ветка получает естественный structural boost;
- если он мал, то arrangement-подход был бы подозрительно избыточным.
Промежуточные результаты:
- anchor nodes: `15`
- false intersections: `78`
- false/anchor ratio: `5.200`
- assessment: `arrangement_plausible`
Что это значит:
- `08_f4_root_arrangement` сейчас выглядит не ослабленной, а наоборот содержательно мотивированной веткой.
Сложность:
- низкая.
Следующий шаг:
- перейти к реальному search/analysis этой ветки и строить уже F4-связанный arrangement scaffold.

## 2026-05-08 21:08 — search-f4-root-scaffold
Цель: построить первый содержательный F4-scaffold, а не держать ветку `08` на одном только baseline-мотиве.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage search`
Артефакты:
- `data/search_f4_root_scaffold.json`
- `data/search_f4_root_scaffold.md`
Что считаю:
- полный набор корней `F4`;
- short и long shells;
- число root lines до отождествления по знаку;
- грубую статистику family-count для случайных 2D-проекций root-line arrangement.
Формулы / reasoning:
- `F4` важна не как абстрактное слово, а как конкретная 48-корневая 4D-система;
- long shell из 24 корней связывает ветку `08` с 24-cell, а short shell даёт дополнительную arrangement-структуру.
Промежуточные результаты:
- total / short / long roots: `48` / `24` / `24`
- total root lines: `24`
- projected family-count histogram: `{23: 76, 21: 126, 22: 116, 17: 16, 19: 67, 24: 38, 20: 103, 18: 33, 13: 4, 15: 11, 14: 2, 16: 4, 11: 2, 12: 2}`
- best projected family count: `11`
Что это значит:
- ветка `08` теперь имеет честный 4D F4-scaffold для дальнейшего анализа;
- можно дальше разбирать, какой именно sub-arrangement или local readout мог бы давать нашу решётку.
Сложность:
- низкая-средняя; это уже содержательный search, но пока ещё не тяжёлый.
Следующий шаг:
- перейти к analysis и решить, какие подсемейства F4-root arrangement имеет смысл сравнивать с lattice grammar в первую очередь.

## 2026-05-08 21:11 — analyze-f4-shells
Цель: понять, какой shell `F4` вообще ближе к нашей решётке по family-count: long shell (24-cell) или short shell.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_f4_shells.json`
- `data/analyze_f4_shells.md`
Что считаю:
- отдельные random-projection family-count histograms для short и long shells `F4`.
Формулы / reasoning:
- если одна из оболочек сама по себе ближе к target family-count `5`, именно её sub-arrangements логичнее сравнивать с lattice grammar в первую очередь.
Промежуточные результаты:
- short-shell histogram: `{12: 307, 10: 91, 11: 173, 9: 22, 8: 6, 7: 1}`
- short-shell best family count: `7`
- long-shell histogram: `{8: 7, 12: 310, 11: 158, 10: 108, 9: 16, 7: 1}`
- long-shell best family count: `7`
Что это значит:
- анализ показывает, какая оболочка `F4` ближе к target family-count на грубом уровне и куда направлять следующий sub-arrangement search.
Сложность:
- низкая-средняя.
Следующий шаг:
- если одна оболочка явно ближе, строить search именно по её подсемействам и local readout; если обе далеки, искать уже смешанные или локально вырезанные arrangements.

## 2026-05-08 21:29 — analyze-f4-shells-and-subarrangements
Цель: понять не только shell-level картину, но и проверить реальные `F4` sub-arrangements вместо whole-shell.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_f4_shells.json`
- `data/analyze_f4_shells.md`
Что считаю:
- shell-level family-count histograms для short и long shells;
- стратифицированный scan по `F4` sub-arrangement классам `Lk_Sm`.
Формулы / reasoning:
- whole shells сами по себе далеки от target family-count `5`;
- поэтому следующий честный шаг — искать не по whole-shell, а по подсемействам направлений с оценкой по family-profile, а не только по числу семей.
Промежуточные результаты:
- short-shell best family count: `7`
- long-shell best family count: `7`
- top sub-arrangement record: `{'class': 'L8_S2', 'long_count': 8, 'short_count': 2, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 1, 6], 'profile_score': 6.074074074074074}`
Что это значит:
- ветка `08` перешла от общего F4-scaffold к реальному sub-arrangement screening;
- теперь уже можно видеть, какие смеси short/long lines хоть как-то резонируют с target family-profile.
Сложность:
- средняя, но пока контролируемая.
Следующий шаг:
- если несколько классов `Lk_Sm` дают устойчиво хорошие profile scores, углубляться именно в них; если картина рыхлая, параллельно открыть `09_f4_b4_hybrid`.

## 2026-05-08 21:39 — finalize-focused-refinement
Цель: проверить, устойчивы ли первые попадания `L8_S2`/`L4_S6` на существенно большей выборке.
Гипотеза: `08_f4_root_arrangement`
Скрипт: `research/B_symmetry_arrangement_models/08_f4_root_arrangement/scripts/run.py --stage finalize`
Артефакты:
- `data/finalize_f4_focus.json`
- `data/finalize_f4_focus.md`
Что считаю:
- focused resampling для лучших классов initial screening;
- частоты попаданий в `family_count=5`;
- частоты exact-profile совпадения `[1,1,1,1,6]`.
Формулы / reasoning:
- sparse single-hit на 100 сэмплах ещё ничего не доказывает;
- нужен локальный добор статистики по реально перспективным классам и нескольким контролям.
Промежуточные результаты:
- best focus class: `L5_S5`
- family5 hits / exact-profile hits: `1` / `1`
- best focus witness: `{'class': 'L5_S5', 'long_count': 5, 'short_count': 5, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 1, 6], 'profile_score': 6.074074074074074, 'exact_profile_hit': True}`
Что это значит:
- теперь у ветки `08` есть не просто разовый hit, а оценка устойчивости лучшего `F4` sub-arrangement класса.
Сложность:
- средняя.
Следующий шаг:
- сравнить устойчивость `08`-классов с hybrid-веткой `09`, где short shell разбит на axis и half-компоненты.

## 2026-05-08 23:13 — axis-long-bridge
Цель: проверить, не был ли слабый `08`-сигнал скрыто axis+long-доминирующим после разложения short-shell на `axis + half`.
Гипотеза: `08_f4_root_arrangement`
Скрипт: ad hoc decomposition scan using `09` helpers over decomposed versions of `L5_S5`, `L4_S6`, `L6_S4`, `L8_S2`
Артефакты:
- `data/analyze_axis_long_bridge.json`
- `data/analyze_axis_long_bridge.md`
Что считаю:
- разложенные классы `A/L/H`, совместимые с сильнейшими historical `L/S`-классами ветки `08`;
- family5-rate;
- exact-profile-rate.
Формулы / reasoning:
- если лучшие `08`-классы после разложения переходят в axis-heavy winners, значит `09`/`05` просто раскрывают скрытую структуру `08`;
- если же decomposition остаётся слабой, branch `08` полезнее как control/reference, чем как источник axis-scaffold.
Промежуточные результаты:
- best decomposed class: `A0_L6_H4`
- family5 / exact rates: `0.0016` / `0.0004`
Что это значит:
- decomposition не превратила `08` в сильную axis+long ветку;
- strongest decomposed class остался half-heavy, а не axis-dominant;
- значит `axis+long` как сильный сигнал приходит существенно из `09/05`, а не из pure `08`.
Сложность:
- средняя.
Следующий шаг:
- оставить `08` supporting/reference branch;
- не тащить её в front-runner только на основании axis-language.
