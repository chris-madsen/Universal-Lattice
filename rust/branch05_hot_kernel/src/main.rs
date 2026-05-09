use nalgebra::Matrix4;
use rand::prelude::*;
use rand::rngs::StdRng;
use rand_distr::StandardNormal;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::cmp::Ordering;
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::PathBuf;

const TARGET_FAMILY_COUNT: usize = 5;
const TARGET_PROFILE: [f64; 5] = [3.0, 4.0, 6.0, 6.0, 8.0];
const FOCUSED_PROFILE: [usize; 5] = [1, 1, 1, 1, 6];
const ANGLE_TOL_DEG: f64 = 1.5;

#[derive(Debug, Deserialize)]
struct KernelInput {
    vectors: Vec<[f64; 4]>,
    projection_batch: usize,
    seed: u64,
}

#[derive(Debug, Serialize)]
struct KernelOutput {
    family5_hits: usize,
    exact_hits: usize,
    family5_rate: f64,
    exact_rate: f64,
    mean_profile_score: f64,
    best_counts: Vec<usize>,
    best_profile_score: f64,
    family_histogram: BTreeMap<usize, usize>,
}

fn random_projection(rng: &mut StdRng) -> [[f64; 4]; 2] {
    let mut data = [0.0_f64; 16];
    for x in &mut data {
        *x = rng.sample(StandardNormal);
    }
    let m = Matrix4::from_row_slice(&data);
    let q = m.qr().q();
    let mut rows = [[0.0; 4]; 2];
    for c in 0..4 {
        rows[0][c] = q[(0, c)];
        rows[1][c] = q[(1, c)];
    }
    rows
}

fn project_vec(rows: &[[f64; 4]; 2], vec: &[f64; 4]) -> [f64; 2] {
    let mut out = [0.0_f64; 2];
    for r in 0..2 {
        let mut acc = 0.0;
        for c in 0..4 {
            acc += rows[r][c] * vec[c];
        }
        out[r] = acc;
    }
    out
}

fn angle_mod_180(vec: &[f64; 2]) -> f64 {
    (vec[1].atan2(vec[0]).to_degrees() + 180.0) % 180.0
}

fn clustered_family_counts(vectors: &[[f64; 4]], rows: &[[f64; 4]; 2]) -> Vec<usize> {
    let mut angles: Vec<f64> = vectors
        .iter()
        .map(|v| project_vec(rows, v))
        .filter(|p| (p[0] * p[0] + p[1] * p[1]).sqrt() > 1e-9)
        .map(|p| angle_mod_180(&p))
        .collect();

    if angles.is_empty() {
        return Vec::new();
    }

    angles.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));
    let mut groups: Vec<usize> = Vec::new();
    let mut last = angles[0];
    let mut count = 1usize;
    for angle in angles.into_iter().skip(1) {
        if (angle - last).abs() <= ANGLE_TOL_DEG {
            count += 1;
        } else {
            groups.push(count);
            count = 1;
        }
        last = angle;
    }
    groups.push(count);
    groups
}

fn profile_score(counts: &[usize]) -> f64 {
    let families = counts.len();
    if families == 0 {
        return 1e9;
    }
    let total: f64 = counts.iter().map(|x| *x as f64).sum();
    let mut counts_sorted: Vec<f64> = counts.iter().map(|x| *x as f64).collect();
    counts_sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));

    let mut target_scaled: Vec<f64> = TARGET_PROFILE.iter().map(|value| total * value / 27.0).collect();
    target_scaled.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));

    let usable_target: Vec<f64> = if families < target_scaled.len() {
        target_scaled[..families].to_vec()
    } else {
        let mut extended = target_scaled;
        while extended.len() < families {
            extended.push(0.0);
        }
        extended
    };

    let l1: f64 = counts_sorted
        .iter()
        .zip(usable_target.iter())
        .map(|(a, b)| (a - b).abs())
        .sum();

    100.0 * ((families as isize - TARGET_FAMILY_COUNT as isize).abs() as f64) + l1
}

fn evaluate(input: &KernelInput) -> KernelOutput {
    let mut rng = StdRng::seed_from_u64(input.seed);
    let mut family5_hits = 0usize;
    let mut exact_hits = 0usize;
    let mut mean_profile_score = 0.0_f64;
    let mut family_histogram: BTreeMap<usize, usize> = BTreeMap::new();
    let mut best_counts = Vec::new();
    let mut best_profile_score = f64::INFINITY;
    let mut best_family_gap = usize::MAX;

    for _ in 0..input.projection_batch {
        let rows = random_projection(&mut rng);
        let counts = clustered_family_counts(&input.vectors, &rows);
        let mut sorted_counts = counts.clone();
        sorted_counts.sort_unstable();
        let fam_count = counts.len();
        let score = profile_score(&counts);
        mean_profile_score += score;
        *family_histogram.entry(fam_count).or_insert(0) += 1;
        if fam_count == TARGET_FAMILY_COUNT {
            family5_hits += 1;
        }
        if sorted_counts == FOCUSED_PROFILE {
            exact_hits += 1;
        }
        let gap = fam_count.abs_diff(TARGET_FAMILY_COUNT);
        if score < best_profile_score || (score == best_profile_score && gap < best_family_gap) {
            best_profile_score = score;
            best_family_gap = gap;
            best_counts = sorted_counts;
        }
    }

    mean_profile_score /= input.projection_batch as f64;
    KernelOutput {
        family5_hits,
        exact_hits,
        family5_rate: family5_hits as f64 / input.projection_batch as f64,
        exact_rate: exact_hits as f64 / input.projection_batch as f64,
        mean_profile_score,
        best_counts,
        best_profile_score,
        family_histogram,
    }
}

fn main() {
    let input_path = env::args().nth(1).map(PathBuf::from).expect("usage: branch05_hot_kernel <input.json>");
    let raw = fs::read_to_string(input_path).expect("failed to read input json");
    let input: KernelInput = serde_json::from_str(&raw).expect("failed to parse input json");
    let output = evaluate(&input);
    println!("{}", serde_json::to_string_pretty(&json!(output)).expect("failed to encode output"));
}
