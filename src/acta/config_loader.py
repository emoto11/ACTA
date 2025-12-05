from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


@dataclass
class WorkerSpec:
    worker_id: int
    position: Tuple[float, float]
    speed: float
    service_rate: float
    initial_state: str
    initial_H: float


@dataclass
class TaskSpec:
    task_id: int
    position: Tuple[float, float]
    required_work: float
    remaining_work: float
    status: str


@dataclass
class FailureModelConfig:
    module: str          # "acta.failure_models"
    class_name: str      # "ExpFailureModel"
    params: Dict[str, Any]


@dataclass
class ScenarioConfig:
    scenario_name: str
    space_width: float
    space_height: float

    max_steps: int
    time_step: float

    command_center_pos: Tuple[float, float]
    repair_depot_pos: Tuple[float, float]
    repair_duration: int

    communication_range: float
    failure_model: FailureModelConfig

    workers: List[WorkerSpec]
    tasks: List[TaskSpec]


def load_scenario_config(path: str | Path) -> ScenarioConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    workers = [
        WorkerSpec(
            worker_id=w["id"],
            position=tuple(w["position"]),
            speed=w["speed"],
            service_rate=w["service_rate"],
            initial_state=w.get("initial_state", "healthy"),
            initial_H=w.get("initial_H", 0.0),
        )
        for w in raw["workers"]
    ]

    tasks = [
        TaskSpec(
            task_id=t["id"],
            position=tuple(t["position"]),
            required_work=t["required_work"],
            remaining_work=t["remaining_work"],
            status=t.get("status", "pending"),
        )
        for t in raw["tasks"]
    ]

    fm_raw = raw["failure_model"]
    failure_model = FailureModelConfig(
        module=fm_raw["module"],
        class_name=fm_raw["class"],
        params=fm_raw.get("params", {}),
    )

    cfg = ScenarioConfig(
        scenario_name=raw["scenario_name"],
        space_width=raw["space"]["width"],
        space_height=raw["space"]["height"],
        max_steps=raw["sim"]["max_steps"],
        time_step=raw["sim"]["time_step"],
        command_center_pos=tuple(raw["command_center"]["position"]),
        repair_depot_pos=tuple(raw["repair_depot"]["position"]),
        repair_duration=raw["repair_depot"]["repair_duration"],
        communication_range=raw["communication"]["range"],
        failure_model=failure_model,
        workers=workers,
        tasks=tasks,
    )
    return cfg
