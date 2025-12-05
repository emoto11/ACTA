from __future__ import annotations
from typing import Dict

from mesa import Model
from mesa.space import ContinuousSpace

from acta.sim.failure_models import FailureModel
from acta.sim.agent import WorkerAgent, TaskAgent, CommanderAgent
from acta.config_loader import FailureModelConfig, ScenarioConfig


class ACTAScenarioModel(Model):
    def __init__(self, cfg: ScenarioConfig, seed: int | None = None):
        super().__init__(seed=seed)

        self.cfg = cfg
        self.time_step = cfg.time_step

        self.space = ContinuousSpace(
            x_max=cfg.space_width,
            y_max=cfg.space_height,
            torus=False,
        )

        # 司令拠点
        self.command_center = CommanderAgent(
            model=self,
            communication_range=cfg.communication_range,
        )
        self.space.place_agent(self.command_center, tuple(cfg.command_center_pos))

        # タスク
        self.tasks: Dict[int, TaskAgent] = {}
        for t_spec in cfg.tasks:
            agent = TaskAgent(
                model=self,
                task_id=t_spec.task_id,
                required_work=t_spec.required_work,
                remaining_work=t_spec.remaining_work,
            )
            self.tasks[t_spec.task_id] = agent
            self.space.place_agent(agent, tuple(t_spec.position))

        # ワーカー
        self.workers: Dict[int, WorkerAgent] = {}
        for w_spec in cfg.workers:
            agent = WorkerAgent(
                model=self,
                worker_id=w_spec.worker_id,
                speed=w_spec.speed,
                service_rate=w_spec.service_rate,
                initial_state=w_spec.initial_state,
                initial_H=w_spec.initial_H,
            )
            self.workers[w_spec.worker_id] = agent
            self.space.place_agent(agent, tuple(w_spec.position))

        self.failure_model: FailureModel = self._build_failure_model(cfg.failure_model)

    def _build_failure_model(self, fm_cfg: FailureModelConfig) -> FailureModel:
        module = import_module(fm_cfg.module)
        cls = getattr(module, fm_cfg.class_name)
        return cls(**fm_cfg.params)

    def step(self):
        # すべてのエージェントの step() を呼ぶ
        # （SimultaneousActivation 風に advance フェーズも欲しくなったら
        #   do("step") → do("advance") と分けて実装）
        self.agents.do("step")
        # self.steps は Mesa が自動更新

    def all_tasks_done(self) -> bool:
        return all(t.status == "done" for t in self.tasks.values())

    def get_makespan(self) -> float:
        # TaskAgent.finished_step の最大値 × time_step
        finished_steps = [
            t.finished_step for t in self.tasks.values() if t.finished_step is not None
        ]
        if not finished_steps:
            return 0.0
        return max(finished_steps) * self.time_step