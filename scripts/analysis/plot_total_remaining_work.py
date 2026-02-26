#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def load_and_merge_total_remaining(csv_files: list[Path]) -> pd.DataFrame:
    """
    複数 seed の *_tasks.csv を読み込み、
    step ごとの「残タスク量合計」を seed 列として横結合する
    """
    dfs: list[pd.DataFrame] = []

    for f in csv_files:
        seed = f.stem.split("_seed")[-1].split("_")[0]

        df = pd.read_csv(f)

        # step ごとに remaining_work を合計（task_id 行を集約）
        total = (
            df.groupby("step", as_index=True)["remaining_work"]
            .sum()
            .to_frame(name=f"seed_{seed}")
        )

        dfs.append(total)

    merged = pd.concat(dfs, axis=1).sort_index()
    return merged


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = pd.DataFrame(index=df.index)
    stats["mean"] = df.mean(axis=1)
    stats["var"] = df.var(axis=1)   # 不偏分散(ddof=1)
    stats["std"] = df.std(axis=1)
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("."), help="tasks.csv が置いてあるディレクトリ")
    parser.add_argument("--pattern", type=str, default="*_tasks.csv", help="読み込む CSV glob パターン")
    parser.add_argument("--out", type=str, default="total_remaining_work.png", help="出力画像ファイル名（figures/ 配下）")
    parser.add_argument("--figdir", type=Path, default=Path("figures"), help="図の保存先ディレクトリ")
    args = parser.parse_args()

    csv_files = sorted(args.dir.glob(args.pattern))
    if not csv_files:
        raise FileNotFoundError("対象となる *_tasks.csv が見つかりません")

    print(f"Loaded {len(csv_files)} files")

    merged = load_and_merge_total_remaining(csv_files)
    stats = compute_stats(merged)

    step = stats.index.to_numpy()
    mean = stats["mean"].to_numpy()
    std = stats["std"].to_numpy()

    plt.figure(figsize=(8, 5))
    plt.plot(step, mean, label="Mean total remaining work")
    plt.fill_between(step, mean - std, mean + std, alpha=0.3, label="±1 std")


    from matplotlib.ticker import MultipleLocator  # ← import に追加

    ax = plt.gca()
    ax.set_xlim(0, 500)
    ax.xaxis.set_major_locator(MultipleLocator(50))

    # 変更後（タイトルなし＋大きく）
    LABEL_FS = 22
    TICK_FS  = 18
    LEG_FS   = 14

    plt.xlabel("Step", fontsize=LABEL_FS)
    plt.ylabel("Total remaining work", fontsize=LABEL_FS)
    plt.tick_params(axis="both", which="major", labelsize=TICK_FS)
    plt.legend(fontsize=LEG_FS)
    # plt.xlabel("Step")
    # plt.ylabel("Total remaining work")
    # plt.title("Total remaining work (mean ± std)")
    # plt.legend()
    plt.grid(True)
    plt.tight_layout()

    args.figdir.mkdir(parents=True, exist_ok=True)
    out_path = args.figdir / args.out
    plt.savefig(out_path, dpi=300)
    plt.close()

    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
