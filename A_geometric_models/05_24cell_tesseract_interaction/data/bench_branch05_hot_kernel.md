# Branch 05 Hot Kernel Benchmark

- projection batch: `25000`
- seed: `424242`
- candidate: `A2_B2-0_B1-3_B0-1@02`
- python elapsed: `3.845065s`
- rust elapsed: `0.115054s`
- python sec/projection: `0.000153803`
- rust sec/projection: `0.000004602`
- speedup (python/rust): `33.4197x`

## Python
- family5 rate: `0.182520`
- exact rate: `0.000000`
- mean profile score: `84.396836`
- best counts: `[1, 1, 1, 1, 2]`

## Rust
- family5 rate: `0.173600`
- exact rate: `0.000000`
- mean profile score: `85.298569`
- best counts: `[1, 1, 1, 1, 2]`

## Note
- The benchmark compares the shared projection-family core kernel for one live branch-05 candidate. Rust uses the same high-level scoring logic but an independent QR implementation and RNG stream, so throughput is the main comparison target, not bitwise-identical hit counts.
