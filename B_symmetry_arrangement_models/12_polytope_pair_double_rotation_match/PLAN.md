# H12 Beautiful-First Search Service

## Summary

Запустить настоящую 12-ю гипотезу как resumable systemd-сервис: beautiful-first поиск пар 4D-источников с double rotation, topology signature и сравнением с `simplified_lattice_central_bundle.py`.

Full coarse не запускать. Основной поиск идёт через `FFT + GA + ACO + Rust + topological signature`.

## Key Changes

- Создать новую ветку:
  - `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/`
- Старую `12_topology_signature_filter` оставить только как исторический неудачный заход и источник reusable filter-кода.
- Новый сервис запускать в существующем `runes-research.slice`.
- Сделать stateful async job:
  - `state.json`
  - `summary.md`
  - `log.md`
  - `best_candidates.json`
  - `checkpoint` после каждой пачки поколений.
- Сервис должен поддерживать stop/restart/resume без пересчёта с нуля.

## Algorithm

- Search unit:
  - source pair
  - double-rotation ratio
  - base angle
  - plane decomposition
  - deterministic projection family
  - readout mode
- Sources:
  - `24-cell`
  - `tesseract`
  - `16-cell`
- Source pairs:
  - `(24,24)`
  - `(24,T)`
  - `(24,16)`
  - `(T,T)`
  - `(T,16)`
  - `(16,16)`
- Beautiful variants first:
  - ratios: `1:1`, `1:2`, `1:3`, `2:3`, `3:4`, `1:4`
  - angles: `7.5`, `15`, `18`, `22.5`, `30`, `36`, `45`, `60`, `72`, `90`
  - plane decompositions: `3`
  - readout modes: `3`
- Topological signature removes affine multiplication.
- Affine/similarity fit runs only for topology-survivors.

## Output And Logging

Use clear mathematical language, not branch05 internal slang.

Each log checkpoint should say:

- how many candidates checked;
- how many unique topological signatures;
- how many candidates matched the simplified topology;
- best source pair;
- best rotation;
- best projection family;
- whether the simplified grid was matched;
- which parts matched:
  - 3 vertical masts;
  - 8 central rays;
  - 11 segments;
  - 15 nodes;
  - central point;
  - angle classes;
- what failed for near misses.

Summary should include human-readable progress:

- `generation progress`
- `candidate progress`
- `unique topology signatures`
- `topology matches`
- `best grid match`
- `ETA` in hours/minutes

## Rendering

Add a render script for best candidates:

- draw target simplified lattice;
- draw candidate lattice;
- draw overlay;
- draw difference map:
  - matched segments;
  - missing target segments;
  - extra candidate segments;
- write a short report explaining:
  - “сетку нашли / не нашли”;
  - “насколько подошла”;
  - “что именно совпало”;
  - “что именно не совпало”.

## Systemd

Use existing research slice settings:

- soft CPU priority, not hard CPU cap;
- high niceness;
- batch scheduling;
- idle I/O;
- `Restart=always`;
- resume from state on restart.

Service name:

- `runes-h12-polytope-pair.service`

State directory:

- `research/async_state/h12_polytope_pair/`

## Test Plan

- Count calculator confirms beautiful-first space:
  - `3,240` structural families
  - `155,520` deterministic projected candidates before GA/ACO expansion
- Target extractor confirms simplified lattice:
  - `11` segments
  - `15` nodes
  - `3` vertical masts
  - `8` central rays
- Resume test:
  - run a small job;
  - stop service;
  - restart;
  - verify it continues from checkpoint.
- Rust/Python parity:
  - sample candidates evaluated by both backends produce same topology signature and score.
- Rendering test:
  - best candidate report and overlay images are produced.

## Assumptions

- Existing `runes-research.slice` is reused.
- Old H12 files are not deleted; they are demoted historically.
- No affine grid multiplication.
- Full coarse scan is not part of v1.
