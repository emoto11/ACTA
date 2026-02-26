#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def trial_total_distance(workers_csv: Path) -> float:
    """
    1試行（1ファイル）について、
    最終 step における全ワーカー cum_distance 合計を返す。
    """
    df = pd.read_csv(workers_csv)

    required = {"step", "worker_id", "cum_distance"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{workers_csv} missing columns: {sorted(missing)}")

    last_step = df["step"].max()
    last = df[df["step"] == last_step]

    # 最終 step における各ワーカーの累積距離（cum_distance）を合計
    total = float(last["cum_distance"].sum())
    return total


def pick_median_trial(files: list[Path]) -> tuple[Path, float]:
    """
    総移動距離（最終 step の全ワーカー cum_distance 合計）が中央値の試行を返す。
    偶数本の場合は「下側の中央値」（index = (n-1)//2）を選ぶ。
    """
    scored: list[tuple[Path, float]] = []
    for f in files:
        scored.append((f, trial_total_distance(f)))

    scored.sort(key=lambda x: x[1])
    idx = (len(scored) - 1) // 2
    return scored[idx][0], scored[idx][1]


def plot_trajectories(workers_csv: Path, out_path: Path, thin: int = 1) -> None:
    """
    指定した試行の workers.csv から worker_id ごとに (x,y) を線で描く。
    thin>1 なら step を間引いて描画（重い場合に有効）。
    """
    df = pd.read_csv(workers_csv)

    required = {"step", "worker_id", "x", "y"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{workers_csv} missing columns: {sorted(missing)}")

    if thin > 1:
        # 各workerごとにstep順を保って thin 間引き
        df = (
            df.sort_values(["worker_id", "step"])
              .groupby("worker_id", as_index=False, group_keys=False)
              .apply(lambda g: g.iloc[::thin])
        )
    else:
        df = df.sort_values(["worker_id", "step"])

    plt.figure(figsize=(8, 8))
    ax = plt.gca()

    for wid, g in df.groupby("worker_id", sort=True):
        ax.plot(g["x"].to_numpy(), g["y"].to_numpy(), label=f"worker {wid}")

        # 開始点・終了点にマーカー（色指定なし：デフォルトに任せる）
        ax.scatter(g["x"].iloc[0], g["y"].iloc[0], marker="o")
        ax.scatter(g["x"].iloc[-1], g["y"].iloc[-1], marker="x")


    # 変更後（タイトルなし＋大きく）
    LABEL_FS = 26
    TICK_FS  = 20
    LEG_FS   = 12  # 軌跡は凡例が邪魔なら小さめ推奨

    ax.set_xlabel("x", fontsize=LABEL_FS)
    ax.set_ylabel("y", fontsize=LABEL_FS)
    # ax.set_title(...)  ←削除 or コメントアウト
    ax.tick_params(axis="both", which="major", labelsize=TICK_FS)
    ax.legend(loc="best", fontsize=LEG_FS, ncol=2)

    # ax.set_xlabel("x")
    # ax.set_ylabel("y")
    # ax.set_title(f"Worker trajectories (median trial)\n{workers_csv.name}")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True)

    # ワーカーが多いと凡例が邪魔なので、必要なら消せるようにしたい場合は後でオプション化します
    # ax.legend(loc="best", fontsize="small", ncol=2)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("."), help="workers.csv が置いてあるディレクトリ")
    parser.add_argument("--pattern", type=str, default="*_workers.csv", help="対象ファイルの glob パターン")
    parser.add_argument("--recursive", action="store_true", help="サブディレクトリも探索する")
    parser.add_argument("--figdir", type=Path, default=Path("figures"), help="保存先ディレクトリ")
    parser.add_argument("--out", type=str, default="worker_trajectories_median.png", help="出力ファイル名（figdir配下）")
    parser.add_argument("--thin", type=int, default=1, help="軌跡点の間引き（例: 5 なら 5stepごと）")
    args = parser.parse_args()

    files = sorted(args.dir.rglob(args.pattern) if args.recursive else args.dir.glob(args.pattern))
    if not files:
        raise FileNotFoundError("対象となる *_workers.csv が見つかりません")

    median_file, median_total = pick_median_trial(files)
    print(f"Picked median trial: {median_file} (total_distance={median_total:.6f})")

    args.figdir.mkdir(parents=True, exist_ok=True)
    out_path = args.figdir / args.out

    plot_trajectories(median_file, out_path, thin=max(1, args.thin))
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
