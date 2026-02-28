# ACTA
Optimization Framework of Task Allocation in Extreme Environments with Asymmetric-Communication Condition

# 概要
ACTA は、極限環境におけるモジュラーロボット／ワーカー群のタスクアロケーションを対象とした、シミュレーションフレームワークです。
中央集権的なタスク実行ルートの決定（GAによるルート最適化）と、自律分散型のタスク選択（近傍オークション・合意形成）を同一基盤上で比較・評価できることを目的としています。

# ディレクトリ構成
```
ACTA/
├── configs/    # シナリオ定義（YAML）
├── src/acta/
│ ├── sim/      # シミュレーション本体（Mesa）
│ │ ├── agent/  # シミュレーション上で動かす各種エージェント
│ │ ├── task_selection/    # タスク選択（ＧＡ型や自律分散型など）
│ │ ├── failure_models.py  # 故障発生モデル
│ │ ├── indo_state.py      # ワーカーや中央拠点が保有する情報
│ │ └── model.py           # シミュレーションの
│ ├── ga/      # GA・評価関数
│ ├── utils/   # logggerなど
│ └── config_loader.py     # シナリオ定義の読み込み
├── scripts/
│ ├── run_sim_once.py      # 単一実験実行
│ ├── batch_run.sh         # seed sweep 用のサンプルスクリプト
│ ├── acta_viz.py          # 可視化用スクリプト
│ ├── scenario_maker       # シナリオ作成用スクリプト
│ └── analysis/            # 出力結果に対する作図用スクリプト
├── results/ # 実験結果（CSV 等）
├── figures/ # 実験結果（PNG 等）
├── pyproject.toml
└── README.md
```

# Installation 
Ubuntuでの実行を想定
## Step 0 — Install **uv** and **ffmpeg**
```bash 
sudo apt update
sudo apt install uv 
sudo apt install ffmpeg
``` 

```bash 
uv --version 
```
```uv 0.9.5```のような表示が出ることを確認

## Step 1 — Clone project 
```bash 
git clone https://github.com/Yuki-Tanigaki/ACTA.git
cd ACTA
```
## Step 2 — Create virtual environment & install dependencies
```bash 
uv venv source.venv/bin/activate  
uv sync 
```

# 実行方法
## 単一シナリオ実行
```python 
uv run python scripts/run_sim_once.py \
  --scenario configs/scenarios/toy_scenario_001.yml \
  --seed 0000 \
  --log-file
```
## seed sweep（例：0–9）
```bash 
./scripts/batch_run.sh
```

## 単一シナリオの可視化
```python 
uv run solara run scripts/acta_viz.py
```

## 実行結果の処理（例）
```python 
uv run python scripts/plot_info_age.py --dir results --pattern "circle20_lam100_k15_r10_int050_seed*_commander.csv" --out info_age_stats.png
uv run python scripts/plot_total_remaining_work.py --dir results --pattern "circle20_lam100_k15_r10_int050_seed*_tasks.csv" --out total_remaining_work.png
uv run python scripts/plot_workers_metrics.py --dir results --pattern "circle20_lam100_k15_r10_int050_seed*_workers.csv" --out circle20_lam100_k15_r10_int050_workers_metrics.png
uv run python scripts/plot_worker_trajectories.py --dir results --pattern "circle20_lam100_k15_r10_int050_seed*_workers.csv" --out circle20_lam100_k15_r10_int050_traj.png
```
評価指標:
- 中央拠点の情報鮮度（情報遅れ）の推移
- 残タスク量の推移図
- 全ワーカーの累積疲労度、全ワーカーの累積移動距離、全ワーカーの情報鮮度合計推移
- 総移動距離値が中央値の試行について各ワーカーの移動軌跡

# シナリオ設定例（toy_scenario_001.yml）
1. 基本情報  
scenario_name: シナリオ名。出力フォルダ名やログ識別子に使う。  
output_dir: 結果を保存するディレクトリ。

2. 空間・通信条件  
space.width, space.height: 2D 連続空間のサイズ（例：100×100）  
space.range: 通信可能距離。ここで定義した距離以内にいるワーカー同士のみが、情報共有や近傍合意を行える。

3. シミュレーションの時間設定  
sim.max_steps: 最大ステップ数。これを超えるとシミュレーションが強制終了する  
sim.time_step: 1 ステップあたりの時間（Δt）

4. 司令拠点（Command Center）  
command_center.position: 司令拠点の座標。

5. 修理拠点（Repair Depot）  
repair_depot.position: 修理拠点の座標。  
repair_depot.repair_duration: 修理に必要なステップ数。  

6. 故障モデル  
failure_model.module: 故障モデル実装がある Python モジュールパス。  
failure_model.class: 利用するクラス名。  
failure_model.params: モデルパラメータ。  

	特にWeibullモデルでは：  
	lam: スケールパラメータ（疲労度 H に対する 63% 故障点）  
	k: 形状パラメータ（故障率の増え方の形）

7. タスク選択（中央集権 / GA / 自律分散 ADS の切り替え）  
- 7.1 最近傍（ベースライン）
未完了タスクのうち、現在位置から最も近いものを選ぶ単純ルール。
	```
	task_selection:
		module: acta.sim.task_selection
		class: NearestIncompleteTaskSelector
		params: {}
	```
- 7.2 GA による中央集権的タスクルート決定
一定間隔で GA を走らせ、全体最適（近似）な計画を作って配布する。
	```
	task_selection:
		module: acta.sim.task_selection
		class: GABasedTaskSelector
		params:
			interval: 50
			pop_size: 100
			generations: 1000
			elitism_rate: 0.1
			seed: 1234
			L_max: 5
			trials: 5
	```
- 7.3 ADS（自律分散：近傍合意型）  
ワーカーが通信範囲内（1-hop 近傍）で claim を交換し、競合があればスコアで勝者を決める。
	```
	task_selection:
	module: acta.sim.task_selection
	class: ADSBaseSelector
	params:
		alpha_risk: 1.0
		max_rounds: 5
	```

8. 入力データ（ワーカー・タスク）  
workers_csv: ワーカー初期配置や性能を定義する CSV。  
tasks_csv: タスク座標や仕事量などを定義する CSV。


---

# 引継ぎメモ（まずこれだけ読めば動かせる）

このリポジトリは、極限環境におけるタスクアロケーションのシミュレーション基盤です。
中央集権（GA）と自律分散（ADS）を同一条件で実行し、結果CSV（results）を集計・作図（figures）します。

## ディレクトリの役割（ざっくり）
- `configs/`：シナリオ定義（YAML）。`configs/ga/` と `configs/ads/` に条件一式が入る
- `src/acta/`：シミュレーション本体（Mesa、タスク選択、故障モデル、config_loader等）
- `scripts/`：
  - `run_sim_once.py`：YAMLを1つ指定してシミュレーションを1回回す入口
  - `batch_run.sh`：動作確認（GAの1条件を自動選択して seed0–9 を回す）
  - `batch_run_36x10.sh`：本番（GA→ADSを全条件、seed0–9で回す）
  - `scenario_maker/`：YAML生成（必要なときだけ）
  - `analysis/`：結果集計・作図
- `tasks/`：タスクCSV（※本環境では既に存在する前提）
- `workers/`：ワーカーCSV
- `results/`：実験出力（CSV等。GitHubには中身を置かない運用）
- `figures/`：図出力（PNG等。GitHubには中身を置かない運用）

---

## 使い方（yaml生成 → 実行 → 集計 → 図出力）
以下はすべてリポジトリルート（ACTA/）で実行する。


### Step 0. 環境構築（uv）
```bash
uv sync
```
## Step 1. YAML生成（必要なときだけ）

configs/ga/ と configs/ads/ が既にあるならスキップでOK。再生成したいときだけ実行。
```bash
uv run python scripts/scenario_maker/generate_scenario_yaml_ga.py
uv run python scripts/scenario_maker/generate_scenario_yaml_ads.py
```
## Step 2. 動作確認（GA 1条件×seed0–9 → 図出力まで）
2-1) 実行（GA 1条件×seed0–9）

batch_run.sh は configs/ga/*.yml から1つ自動選択して seed0–9 を回す。
```bash
bash scripts/batch_run.sh
```
2-2) OUTDIR（出力先）取得

batch_run.sh と同じ選び方で、今回の output_dir（結果が出たフォルダ）を取得する。

```bash
SCENARIO="$(ls -1 configs/ga/*.yml | sort | head -n 1)"
OUTDIR="$(grep -m1 '^output_dir:' "$SCENARIO" | awk '{print $2}')"
echo "[SCENARIO] $SCENARIO"
echo "[OUTDIR]   $OUTDIR"
2-3) 作図（平均）
uv run python scripts/analysis/plot_total_remaining_work.py \
  --dir "$OUTDIR" --pattern "*_tasks.csv" \
  --out "smoke_total_remaining_work.png" --figdir figures

uv run python scripts/analysis/plot_info_age.py \
  --dir "$OUTDIR" --pattern "*_commander.csv" \
  --out "smoke_info_age.png"

uv run python scripts/analysis/plot_worker_trajectories.py \
  --dir "$OUTDIR" --pattern "*_seed0000_workers.csv" \
  --out "smoke_traj_seed0000.png" --figdir figures
```
## Step 3. 本番（36条件×seed0–9）
```bash
bash scripts/batch_run_36x10.sh
```
## Step 4. makespan集計（36条件・seed0–9）
```bash
uv run python scripts/analysis/make_makespan_table_36_seed0_9.py
```

補足：出力CSVの n_GA / n_ADS が 10 でない行は、その条件のseedが欠けている → 追加実行対象。

## Step 5. 図出力（まとめて作る：OUTDIRリストを回す）

全条件の図を出すと数が多いので、作図したい条件だけ OUTDIRS に列挙して一括生成する。
（残タスク量・情報鮮度はseed0–9をまとめて読む＝平均、軌跡は代表seed0000）

5-1) その場で一括作図（コマンド一発）
```bash
OUTDIRS=(
  "results/GA/sobol20_lam250_k20_r25_int250"
  "results/ADS/sobol20_lam250_k20_r25_a1p0_mr5"
  # 追加したい条件をここに書く
)

for OUTDIR in "${OUTDIRS[@]}"; do
  name="$(basename "$OUTDIR")"

  uv run python scripts/analysis/plot_total_remaining_work.py \
    --dir "$OUTDIR" --pattern "*_tasks.csv" \
    --out "${name}_remaining_work.png" --figdir figures

  uv run python scripts/analysis/plot_info_age.py \
    --dir "$OUTDIR" --pattern "*_commander.csv" \
    --out "${name}_info_age.png"

  uv run python scripts/analysis/plot_worker_trajectories.py \
    --dir "$OUTDIR" --pattern "*_seed0000_workers.csv" \
    --out "${name}_traj_seed0000.png" --figdir figures
done
```
5-2) スクリプト化（おすすめ）

上の内容を scripts/plot_selected.sh に保存して実行すると楽。
```bash
cat > scripts/plot_selected.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

OUTDIRS=(
  "results/GA/sobol20_lam250_k20_r25_int250"
  "results/ADS/sobol20_lam250_k20_r25_a1p0_mr5"
)

for OUTDIR in "${OUTDIRS[@]}"; do
  name="$(basename "$OUTDIR")"

  uv run python scripts/analysis/plot_total_remaining_work.py \
    --dir "$OUTDIR" --pattern "*_tasks.csv" \
    --out "${name}_remaining_work.png" --figdir figures

  uv run python scripts/analysis/plot_info_age.py \
    --dir "$OUTDIR" --pattern "*_commander.csv" \
    --out "${name}_info_age.png"

  uv run python scripts/analysis/plot_worker_trajectories.py \
    --dir "$OUTDIR" --pattern "*_seed0000_workers.csv" \
    --out "${name}_traj_seed0000.png" --figdir figures
done
EOF

chmod +x scripts/plot_selected.sh
bash scripts/plot_selected.sh
```
---

# TODO:
- 情報鮮度による全体<->自律の戦略変更 の実装
- 可視化ツール
	- 中央拠点の通信範囲の可視化
	- ワーカーの故障状態の可視化
	- タスクがワーカーに隠れないようにサイズを調整
