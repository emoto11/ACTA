# scripts/acta_viz.py
from __future__ import annotations

import mesa
from mesa.visualization import SolaraViz, make_space_component
from mesa.visualization.components import AgentPortrayalStyle

from acta.config_loader import load_scenario_config
from acta.sim.model import ACTAScenarioModel
from acta.sim.agent import WorkerAgent, TaskAgent, CommanderAgent


DEFAULT_SCENARIO = "configs/scenarios/toy_scenario_001.yml"


class ACTAVisModel(ACTAScenarioModel):
    """SolaraViz 用のラッパーモデル."""

    def __init__(self, scenario_path: str = DEFAULT_SCENARIO, seed: int = 0):
        cfg = load_scenario_config(scenario_path)
        super().__init__(cfg=cfg, seed=seed)


# --- エージェントの描画スタイル ---
def agent_portrayal(agent):
    # Worker: 青い丸
    if isinstance(agent, WorkerAgent):
        return AgentPortrayalStyle(color="tab:blue", size=50)

    # Task: 状態で色を変える
    if isinstance(agent, TaskAgent):
        if agent.status == "pending":
            color = "tab:gray"
        elif agent.status == "in_progress":
            color = "tab:orange"
        else:  # done
            color = "tab:green"
        return AgentPortrayalStyle(color=color, size=40, marker="s")

    # CommandCenter: 赤いダイヤ
    if isinstance(agent, CommanderAgent):
        return AgentPortrayalStyle(color="tab:red", size=60, marker="D")

    # その他（今はたぶん出てこない）
    return AgentPortrayalStyle(color="black", size=30)


# 初期モデル（可視化はここから始まる）
initial_model = ACTAVisModel()

# 連続空間のコンポーネント（ドキュメント推奨のやり方）
space_component = make_space_component(agent_portrayal)

# とりあえずモデルパラメータはいじらないので空でOK
model_params = {}

# SolaraViz ページ
page = SolaraViz(
    initial_model,
    components=[space_component],
    model_params=model_params,
    name="ACTA Toy Scenario",
)

# solara run が拾うエントリポイント
Page = page
