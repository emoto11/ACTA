#!/bin/bash
#!/usr/bin/env bash
set -e

SCENARIO="configs/ga/circle20_lam100_k15_r10_int050.yml"

for SEED in {0..9}; do
    echo "=== Running simulation with seed=${SEED} ==="
    uv run python scripts/run_sim_once.py \
        --scenario "${SCENARIO}" \
        --seed "${SEED}" \
        --log-file
done
