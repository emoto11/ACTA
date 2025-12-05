# ACTA
Optimization Framework of Task Allocation in Extreme Environments with Asymmetric-Communication Condition

uv run python scripts/run_sim_once.py --scenario configs/scenarios/toy_scenario_001.yml --seed 0

uv run solara run scripts/acta_viz.py


TODO:
- パラメータの再確認
　ワーカーとタスクは専用のcsvから読み込む形式に


- 故障モデルを入れる
　故障モデルは独立させる
　故障時のワーカー挙動はワーカーに任せる

failure_model (exp λ, η) を WorkerAgent に組み込んで
p_i(t) = 1 - exp(-λ H_i) で確率的に「今ステップで故障するか」を判定

故障したら処理能力 η v に落とす or 完全停止＋修理に向かう

修理拠点ロジック

「H が閾値を超えたら、次のタスクに行かず修理拠点へ向かう」
みたいな素朴なルールから入れる

司令拠点と AoI の導入

まずは簡単に、
「毎ステップ、司令拠点の知っているタスク完了状態がどれだけ古いか」
を測るような AoI を入れてみる
