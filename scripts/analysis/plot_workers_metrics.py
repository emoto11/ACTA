#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


METRICS = {
    "H": ("Total cumulative fatigue (sum H)", "Sum H"),
    "cum_distance": ("Total cumulative distance (sum)", "Sum distance"),
    "info_age_sum": ("Total info age (sum)", "Sum info age"),
}


def load_and_merge_workers_sum(csv_files: list[Path], col: str) -> pd.DataFrame:
    """
    *_workers.csv を複数 seed 分読み込み、step ごとの col 合計を seed 列として横結合
    """
    dfs: list[pd.DataFrame] = []

    for f in csv_files:
        seed = f.stem.split("_seed")[-1].split("_")[0]
        df = pd.read_csv(f)

        required = {"step", "worker_id", col}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"{f} is not a workers log or missing columns {sorted(missing)} "
                f"(needed: step, worker_id, {col})."
            )

        total = (
            df.groupby("step", as_index=True)[col]
            .sum()
            .to_frame(name=f"seed_{seed}")
        )
        dfs.append(total)

    return pd.concat(dfs, axis=1).sort_index()


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = pd.DataFrame(index=df.index)
    stats["mean"] = df.mean(axis=1)
    stats["std"] = df.std(axis=1)   # ddof=1
    return stats


def plot_band(ax, step, mean, std, title: str, ylabel: str):
    ax.plot(step, mean, label="Mean")
    ax.fill_between(step, mean - std, mean + std, alpha=0.3, label="±1 std")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(True)
    ax.legend()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("."), help="workers.csv があるディレクトリ")
    parser.add_argument("--pattern", type=str, default="*_workers.csv", help="読み込む glob パターン")
    parser.add_argument("--recursive", action="store_true", help="サブディレクトリも探索する")
    parser.add_argument("--figdir", type=Path, default=Path("figures"), help="図の保存先")
    parser.add_argument("--out", type=str, default="workers_3metrics.png", help="出力画像名（figdir配下）")
    args = parser.parse_args()

    if args.recursive:
        csv_files = sorted(args.dir.rglob(args.pattern))
    else:
        csv_files = sorted(args.dir.glob(args.pattern))

    if not csv_files:
        raise FileNotFoundError("対象となる *_workers.csv が見つかりません")

    print(f"Loaded {len(csv_files)} files")

    # 3指標それぞれ stats を作る
    stats_map: dict[str, pd.DataFrame] = {}
    for col in ("H", "cum_distance", "info_age_sum"):
        merged = load_and_merge_workers_sum(csv_files, col)
        stats_map[col] = compute_stats(merged)

    # step は共通のはず（ズレる場合は union になるので、plot前に揃えるなら join でもOK）
    step = stats_map["H"].index.to_numpy()

    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)

    for ax, col in zip(axes, ("H", "cum_distance", "info_age_sum")):
        title, ylabel = METRICS[col]
        s = stats_map[col].reindex(step)  # 念のため
        plot_band(ax, step, s["mean"].to_numpy(), s["std"].to_numpy(), title, ylabel)

    axes[-1].set_xlabel("Step")
    fig.suptitle("Workers aggregated metrics (mean ± std over seeds)")

    plt.tight_layout()
    args.figdir.mkdir(parents=True, exist_ok=True)
    out_path = args.figdir / args.out
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
