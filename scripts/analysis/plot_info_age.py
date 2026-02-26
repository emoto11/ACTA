#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def load_and_merge(csv_files: list[Path]) -> pd.DataFrame:
    """
    複数 seed の commander.csv を読み込み、
    step を index にして info_age_sum を横に結合する
    """
    dfs = []

    for f in csv_files:
        seed = f.stem.split("_seed")[-1].split("_")[0]
        df = pd.read_csv(f)
        df = df.set_index("step")
        df = df.rename(columns={"info_age_sum": f"seed_{seed}"})
        dfs.append(df)

    merged = pd.concat(dfs, axis=1).sort_index()
    return merged


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    step ごとに平均・分散・標準偏差を計算
    """
    stats = pd.DataFrame(index=df.index)
    stats["mean"] = df.mean(axis=1)
    stats["var"] = df.var(axis=1)       # 不偏分散（ddof=1）
    stats["std"] = df.std(axis=1)
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="commander.csv が置いてあるディレクトリ",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*_commander.csv",
        help="読み込む CSV の glob パターン",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("info_age_stats.csv"),
        help="出力 CSV",
    )
    args = parser.parse_args()

    csv_files = sorted(args.dir.glob(args.pattern))
    if not csv_files:
        raise FileNotFoundError("対象となる commander.csv が見つかりません")

    print(f"Loaded {len(csv_files)} files")

    merged = load_and_merge(csv_files)
    stats = compute_stats(merged)

    step = stats.index.to_numpy()
    mean = stats["mean"].to_numpy()
    std = stats["std"].to_numpy()

    plt.figure(figsize=(8, 5))

    # 平均曲線
    plt.plot(step, mean, label="Mean info age")

    # ± std の帯
    plt.fill_between(
        step,
        mean - std,
        mean + std,
        alpha=0.3,
        label="±1 std",
    )
    Path("figures").mkdir(parents=True, exist_ok=True)
    out_path = Path("figures") / args.out

    # ===== style: no title + big labels/ticks =====
    LABEL_FS = 22
    TICK_FS  = 18
    LEG_FS   = 14   # 凡例

    plt.xlabel("Step", fontsize=LABEL_FS)
    plt.ylabel("Information age (sum)", fontsize=LABEL_FS)
    plt.tick_params(axis="both", which="major", labelsize=TICK_FS)
    plt.legend(fontsize=LEG_FS)
    plt.grid(True)

    # plt.xlabel("Step")
    # plt.ylabel("Information age (sum)")
    # plt.title("Commander information age (mean ± std)")
    # plt.legend()
    # plt.grid(True)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
