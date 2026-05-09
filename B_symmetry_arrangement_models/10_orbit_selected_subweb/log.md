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

## 2026-05-08 22:10 — baseline
Цель: формализовать, из каких orbit-блоков вообще может состоять selected subweb внутри богатого `tesseract + 24-cell` union.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_orbit_blocks.json`
- `data/baseline_orbit_blocks.md`
Что считаю:
- минимальные orbit-блоки, с которыми сейчас реально работаем;
- перенос сигнала из ветки `05` в orbit-язык.
Формулы / reasoning:
- если full union слишком богат, нужен язык симметрийно мотивированного отбора;
- на текущем шаге естественные блоки — это осевые линии тессеракта и directional lines 24-cell.
Промежуточные результаты:
- tesseract axis lines: `4`
- 24-cell direction lines: `12`
- imported branch 05 signal: `{'best_family5_class': 'T3_C4', 'best_family5_rate': 0.033, 'best_exact_class': 'T4_C6', 'best_exact_rate': 0.0006666666666666666}`
Что это значит:
- ветка `10` получила минимальную осмысленную постановку, а не пустой placeholder.
Сложность:
- низкая.
Следующий шаг:
- сделать prune: показать, почему orbit-selection сейчас выглядит необходимым, а не декоративным.

## 2026-05-08 22:10 — prune
Цель: зафиксировать, почему `orbit_selected_subweb` сейчас нужен по данным, а не просто как запасная идея.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage prune`
Артефакты:
- `data/prune_orbit_selection_case.json`
- `data/prune_orbit_selection_case.md`
Что считаю:
- разрыв между богатством raw full union и силой selected scaffold-классов из ветки `05`.
Формулы / reasoning:
- если raw union стабильно слишком богат, а selected classes уже дают сильный резонанс, значит нужен язык осмысленного отбора, а не полный граф.
Промежуточные результаты:
- full-union best family count: `8`
- branch05 best family5 rate: `0.033000`
- assessment: `orbit_selection_plausible`
Что это значит:
- ветка `10` теперь не декоративная: у неё есть прямой data-driven повод жить.
Сложность:
- низкая.
Следующий шаг:
- переходить к search по орбитальному языку отбора, а не только по числу T/C линий.

## 2026-05-08 22:27 — search
Цель: перейти от общего лозунга `selected subweb` к реальному orbit-языку отбора.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage search`
Артефакты:
- `data/search_orbit_templates.json`
- `data/search_orbit_templates.md`
Что считаю:
- search по template-ам вида `axis_dims + bucket_counts(B2,B1,B0)`.
Формулы / reasoning:
- вместо произвольного выбора C-линий вводится орбитальная параметризация через overlap-бакеты относительно выбранного axis-subset.
Промежуточные результаты:
- top orbit template: `A2_B2-1_B1-1_B0-2`
- hits family5 / exact: `250` / `0`
Что это значит:
- теперь у ветки `10` есть первый реальный search-слой, а не только baseline/prune.
Сложность:
- средняя.
Следующий шаг:
- сравнить лучшие orbit-template-ы с сильными классами ветки `05` и посмотреть, не даёт ли orbit-язык более компактное объяснение.

## 2026-05-08 22:27 — analyze
Цель: понять, даёт ли orbit-template язык не просто search-результат, а более компактное объяснение сильных branch-05 сигналов.
Гипотеза: `10_orbit_selected_subweb`
Скрипт: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_orbit_templates.json`
- `data/analyze_orbit_templates.md`
Что считаю:
- сравнение лучших orbit-template-ов с сильнейшими class-level winners из ветки `05`.
Формулы / reasoning:
- branch `10` не обязана бить `05` по сырому hit-rate;
- её задача — дать более осмысленный symmetry-guided язык отбора, если он объясняет те же зоны резонанса компактнее.
Промежуточные результаты:
- branch10 best template: `A2_B2-1_B1-1_B0-2`
- family5 / exact rates: `0.1667` / `0.0000`
Что это значит:
- понятно, усиливает ли `10` интерпретацию `05`, или пока остаётся только красивой оболочкой.
Сложность:
- низкая.
Следующий шаг:
- если `10` даёт компактный orbit-язык для лучших `05` зон, можно переносить фокус на subgraph/readout внутри полного union уже через эту parameterization.
