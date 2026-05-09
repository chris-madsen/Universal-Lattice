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

## 2026-05-08 21:32 — baseline
Цель: разложить `F4` на осевую, half-integer и long компоненты, чтобы hybrid-ветка опиралась на явную структуру, а не на красивую фразу.
Гипотеза: `09_f4_b4_hybrid`
Скрипт: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_hybrid_shells.json`
- `data/baseline_hybrid_shells.md`
Что считаю:
- counts по axis / half / long shells.
Формулы / reasoning:
- оси хорошо соответствуют идее вертикального scaffold;
- long shell соответствует диагональной 24-cell части;
- half shell даёт дополнительный refinement layer.
Промежуточные результаты:
- axis lines: `4`
- half lines: `8`
- long lines: `12`
Что это значит:
- hybrid-ветка получила явную внутреннюю декомпозицию для последующего search.
Сложность:
- низкая.
Следующий шаг:
- перейти к sampling-search по классам `A/L/H`.

## 2026-05-08 21:32 — search-hybrid-sampling
Цель: проверить hybrid-классы `A/L/H`, а не держать `09` на одном только мотиве “оси плюс диагонали”.
Гипотеза: `09_f4_b4_hybrid`
Скрипт: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage search`
Артефакты:
- `data/search_hybrid_sampling.json`
- `data/search_hybrid_sampling.md`
Что считаю:
- sampling по классам `A[[-1.  0.  0.  0.]
 [ 0. -1.  0.  0.]
 [ 0.  0. -1.  0.]
 [ 0.  0.  0. -1.]
 [ 0.  0.  0.  1.]
 [ 0.  0.  1.  0.]
 [ 0.  1.  0.  0.]
 [ 1.  0.  0.  0.]]_L[[-1. -1.  0.  0.]
 [-1.  0. -1.  0.]
 [-1.  0.  0. -1.]
 [-1.  0.  0.  1.]
 [-1.  0.  1.  0.]
 [-1.  1.  0.  0.]
 [ 0. -1. -1.  0.]
 [ 0. -1.  0. -1.]
 [ 0. -1.  0.  1.]
 [ 0. -1.  1.  0.]
 [ 0.  0. -1. -1.]
 [ 0.  0. -1.  1.]
 [ 0.  0.  1. -1.]
 [ 0.  0.  1.  1.]
 [ 0.  1. -1.  0.]
 [ 0.  1.  0. -1.]
 [ 0.  1.  0.  1.]
 [ 0.  1.  1.  0.]
 [ 1. -1.  0.  0.]
 [ 1.  0. -1.  0.]
 [ 1.  0.  0. -1.]
 [ 1.  0.  0.  1.]
 [ 1.  0.  1.  0.]
 [ 1.  1.  0.  0.]]_H[[-0.5 -0.5 -0.5 -0.5]
 [-0.5 -0.5 -0.5  0.5]
 [-0.5 -0.5  0.5 -0.5]
 [-0.5 -0.5  0.5  0.5]
 [-0.5  0.5 -0.5 -0.5]
 [-0.5  0.5 -0.5  0.5]
 [-0.5  0.5  0.5 -0.5]
 [-0.5  0.5  0.5  0.5]
 [ 0.5 -0.5 -0.5 -0.5]
 [ 0.5 -0.5 -0.5  0.5]
 [ 0.5 -0.5  0.5 -0.5]
 [ 0.5 -0.5  0.5  0.5]
 [ 0.5  0.5 -0.5 -0.5]
 [ 0.5  0.5 -0.5  0.5]
 [ 0.5  0.5  0.5 -0.5]
 [ 0.5  0.5  0.5  0.5]]`.
Формулы / reasoning:
- это естественное продолжение ветки `08`: там нашли резонансные `L/S`-смеси, а здесь явно раскладываем short shell на axis и half-integer части.
Промежуточные результаты:
- top record: `{'class': 'A4_L6_H0', 'axis_count': 4, 'long_count': 6, 'half_count': 0, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 1, 6], 'profile_score': 6.074074074074074}`
Что это значит:
- видно, усиливает ли явное hybrid-разложение сигнал по сравнению с чистой `F4` веткой.
Сложность:
- средняя, но контролируемая.
Следующий шаг:
- если есть хорошие `A/L/H` классы, оставить `09` активной параллельно с `08`; если нет, вернуть в planned/weak.

## 2026-05-08 21:40 — analyze-focused-hybrid
Цель: проверить устойчивость лучших hybrid-классов и напрямую сравнить их с `08_f4_root_arrangement`.
Гипотеза: `09_f4_b4_hybrid`
Скрипт: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_hybrid_refine.json`
- `data/analyze_hybrid_refine.md`
Что считаю:
- focused resampling лучших `A/L/H` классов;
- частоты попаданий в `family_count=5`;
- частоты exact-profile `[1,1,1,1,6]`;
- прямое сравнение с веткой `08`.
Формулы / reasoning:
- initial single-hit на 100 сэмплах слишком слаб, чтобы делать выводы;
- нужно добрать статистику и отдельно проверить, действительно ли half-shell помогает, или лучший hybrid на деле редуцируется к axis+long.
Промежуточные результаты:
- best focus class: `A4_L6_H0`
- family5 hits / exact-profile hits: `1` / `0`
- best focus witness: `{'class': 'A4_L6_H0', 'axis_count': 4, 'long_count': 6, 'half_count': 0, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 3, 4], 'profile_score': 3.6296296296296298, 'exact_profile_hit': False}`
Что это значит:
- теперь можно честно сравнивать pure `F4` sub-arrangement и hybrid `F4/B4` трактовки, а не спорить на уровне красивых слов.
Сложность:
- средняя.
Следующий шаг:
- если axis+long снова доминирует, это усиливает переход к `05_24cell_tesseract_interaction`; если half-shell начнёт выигрывать, углублять `09` дальше.

## 2026-05-08 23:13 — axis-long-push
Цель: проверить отдельно pure `axis+long` без half-shell, чтобы понять, является ли эта осевая трактовка самостоятельным сильным направлением, а не только fallback-объяснением.
Гипотеза: `09_f4_b4_hybrid`
Скрипт: ad hoc focused scan via `split_f4_shells()` / `sample_alh_classes()`
Артефакты:
- `data/analyze_axis_long_push.json`
- `data/analyze_axis_long_push.md`
Что считаю:
- классы `A/L/H0` для `A in {2,3,4}` и `L in {4..8}`;
- family5-rate;
- exact-profile-rate.
Формулы / reasoning:
- если pure `axis+long` сам по себе даёт сильный сигнал, это уже не просто “ветка 09 схлопнулась”, а содержательный bridge в сторону `05`;
- если без half-shell сигнал исчезает, значит half-layer всё-таки был нужен.
Промежуточные результаты:
- best class: `A2_L4_H0`
- family5 / exact rates: `0.1456` / `0.0000`
Что это значит:
- pure `axis+long` внутри `09` даёт сильный family-5 сигнал сам по себе;
- это намного сильнее старого focused leader `A4_L6_H0 = 0.0004`;
- half-shell здесь не обязателен для structural resonance.
Сложность:
- средняя.
Следующий шаг:
- использовать этот результат как handoff в `05`, где `axis+long` уже должен считаться first-class scaffold, а не только побочным чтением hybrid-ветки.
