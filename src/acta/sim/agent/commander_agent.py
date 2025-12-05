from __future__ import annotations
from typing import Optional
import math

from mesa import Agent


class CommanderAgent(Agent):
    def __init__(self, model, communication_range: float):
        super().__init__(model)
        self.communication_range = communication_range
        # AoI用の状態は後で足す

    def step(self):
        # まだ何もしない
        return