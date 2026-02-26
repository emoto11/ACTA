#!/usr/bin/env bash
set -euo pipefail

# 20 seeds: 0..19
SEED_START=0
SEED_END=19

run_one_yaml () {
  local yml="$1"
  echo ""
  echo "=== scenario: $yml ==="

  # YAML内の output_dir を読む（例: results/GA/<scenario>）
  local outdir
  outdir="$(grep -m1 '^output_dir:' "$yml" | awk '{print $2}')"
  if [[ -z "${outdir:-}" ]]; then
    echo "[WARN] output_dir not found in $yml -> run anyway"
  else
    mkdir -p "$outdir"
  fi

  for seed in $(seq "$SEED_START" "$SEED_END"); do
    local seed4
    seed4="$(printf "%04d" "$seed")"

    # 既に結果があるならスキップ（再実行したいならこのifを消す）
    if [[ -n "${outdir:-}" ]] && compgen -G "${outdir}/*_seed${seed4}_commander.csv" > /dev/null; then
      echo "[SKIP] seed=$seed (already exists)"
      continue
    fi

    echo "[RUN] seed=$seed"
    # 失敗しても他を続行したいので set +e で包む
    set +e
    uv run python scripts/run_sim_once.py --scenario "$yml" --seed "$seed" --log-file
    status=$?
    set -e

    if [[ $status -ne 0 ]]; then
      echo "[FAIL] $yml seed=$seed (exit=$status)"
      # 続行はする（止めたいなら次行を有効化）
      # exit $status
    fi
  done
}

echo "=== GA YAML count ==="
find configs/ga -maxdepth 1 -type f -name "*.yml" | wc -l || true
echo "=== ADS YAML count ==="
find configs/ads -maxdepth 1 -type f -name "*.yml" | wc -l || true

# GA
if [[ -d configs/ga ]]; then
  echo ""
  echo "########## RUN GA ##########"
  while IFS= read -r yml; do
    run_one_yaml "$yml"
  done < <(find configs/ga -maxdepth 1 -type f -name "*.yml" | sort)
fi

# ADS
if [[ -d configs/ads ]]; then
  echo ""
  echo "########## RUN ADS ##########"
  while IFS= read -r yml; do
    run_one_yaml "$yml"
  done < <(find configs/ads -maxdepth 1 -type f -name "*.yml" | sort)
fi

echo ""
echo "DONE."
