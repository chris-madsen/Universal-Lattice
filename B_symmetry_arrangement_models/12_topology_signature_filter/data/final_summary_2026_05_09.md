# Hypothesis 12 Final Summary (2026-05-09)

## Проверяемая идея

Если переводить кандидаты в canonical topological signature (signed-permutation invariant), можно заранее отсекать эквивалентные варианты до дорогой projection-evaluation.

## Что получили

По структуре пространства:
- raw candidates: `38,478`
- unique signatures: `14,510`
- compression: `2.651826x`

По итоговому A/B (одинаковый budget `50000` поколений):
- `no_filter`: `3,600,000` candidate eval, `345,600,000` projection eval, `5004.95s`
- `with_filter`: `168,929` candidate eval, `16,217,184` projection eval, `12811.92s`
- `with_filter` explored signatures: `3,677` (`9.5561%` от `38,478`)
- `with_filter` skipped in-batch equivalent: `1,685,396`
- `with_filter` skipped by signature cap: `1,910,927`

## Вердикт по гипотезе 12

Подтверждено:
- как механизм эквивалентностной дедупликации фильтр работает.
- объём реально выполненных expensive eval сокращается радикально.

Не подтверждено:
- как ускорение wall-clock в текущем режиме (`signature_cap=1` + текущая политика обхода) фильтр не выигрывает.

## Практический вывод

Гипотеза 12 закрыта на текущем этапе:
- механизм нужен и полезен;
- для следующего шага требуется не “доказывать заново”, а тюнинг policy (cap/backfill/scheduling), если цель именно ускорение по времени.

## Сетка: подошла или нет

Прямой ответ:
- строгий финальный match сетки по ветке 12 не зафиксирован;
- найдено устойчивое сильное приближение в `A2`-классах.

Факты:
- best peak (no_filter): `A2_B2-0_B1-3_B0-1@12`, `family5_rate=0.3854167`, `best_counts=[1,1,1,1,2]`;
- best peak (with_filter): `A2_B2-0_B1-4_B0-0@03`, `family5_rate=0.3333333`, `best_counts=[1,1,1,1,2]`;
- лидирующие по частотности классы в обоих прогонах: `A2_B2-0_B1-4_B0-0`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-2_B0-2`.

## Источники ветки 12

- `data/topology_signature_space_report.md`
- `../result.md`
- `../log.md`
