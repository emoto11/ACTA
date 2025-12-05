from __future__ import annotations
from typing import Optional
import math

from mesa import Agent


class TaskAgent(Agent):
    def __init__(
        self,
        model,
        task_id: int,
        required_work: float,
        remaining_work: float,
    ):
        super().__init__(model)
        self.task_id = task_id
        self.required_work = required_work
        self.remaining_work = remaining_work
        self.status = "pending"  # pending / in_progress / done

        # 完了したステップ番号（Model.steps）
        self.finished_step: Optional[int] = None

    def step(self):
        # Task自体は能動的に何もしない。
        if self.remaining_work <= 0 and self.status != "done":
            self.status = "done"
            # Model.steps は Mesa が自動で更新してくれる
            self.finished_step = self.model.steps