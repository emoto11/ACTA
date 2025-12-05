from __future__ import annotations
from typing import Optional
import math

from mesa import Agent
from acta.sim.agent.task_agent import TaskAgent
from acta.sim.failure_models import FailureModel


class WorkerAgent(Agent):
    def __init__(
        self,
        model,
        worker_id: int,
        speed: float,
        service_rate: float,
        initial_state: str = "healthy",
        initial_H: float = 0.0,
    ):
        super().__init__(model)
        self.worker_id = worker_id
        self.speed = speed               # u: 移動速度 [距離 / 時間]
        self.service_rate = service_rate # v: タスク処理能力 [仕事量 / 時間]

        # 故障関係のパラメータ・状態
        self.state = initial_state       # "healthy" / "failed" など
        self.H = initial_H               # 累積稼働時間

        # メトリクス用
        self.total_move_distance = 0.0

        # いま向かっているタスク
        self.target_task: Optional[TaskAgent] = None

    # ------------------------------------------------------------------
    # 1 ステップの挙動
    # ------------------------------------------------------------------
    def step(self):
        # すでに全タスクが終わっていれば何もしない
        if self.model.all_tasks_done():
            return

        dt = self.model.time_step

        # --- ターン開始時に故障判定 ---
        if self.state == "healthy":
            self._maybe_fail_at_step_start(dt)

        # 故障していても、「移動＋作業」は行う
        # 故障後は処理能力が低下する

        # 向かうべきタスクを決める（最も近い未完了タスク）
        if self.target_task is None or self.target_task.status == "done":
            self.target_task = self._select_nearest_pending_task()

        if self.target_task is None:
            # 未完了タスクがない → 何もせず終了（H も増やさない）
            return

        # ターゲットへ移動 or 作業
        tx, ty = self.target_task.pos
        x, y = self.pos  # ContinuousSpace が持っている現位置

        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)

        # このステップで進める最大距離
        max_step_dist = self.speed * dt

        if dist < 1e-8:
            # すでにタスク位置にいる → 作業のみ
            if self.target_task.status != "done":
                self._work_on_task(self.target_task, dt)
            # 作業 or 待機で dt 時間稼働したとみなす
            self.H += dt
            return

        if dist <= max_step_dist:
            # タスク地点まで一気に到達 → 残り時間で作業
            new_pos = (tx, ty)
            self.total_move_distance += dist
            self.model.space.move_agent(self, new_pos)

            move_time = dist / self.speed
            remaining_dt = max(dt - move_time, 0.0)

            if remaining_dt > 1e-8 and self.target_task.status != "done":
                self._work_on_task(self.target_task, remaining_dt)

            # このステップ全体で dt 時間稼働したとみなす
            self.H += dt
        else:
            # まだ届かない → 方向だけ合わせて一歩進む（移動だけ）
            ratio = max_step_dist / dist
            new_x = x + dx * ratio
            new_y = y + dy * ratio
            step_dist = max_step_dist

            new_pos = (new_x, new_y)
            self.total_move_distance += step_dist
            self.model.space.move_agent(self, new_pos)

            # dt 時間移動したので、その分 H を増やす
            self.H += dt

    # ------------------------------------------------------------------
    # タスク選択・作業処理
    # ------------------------------------------------------------------
    def _select_nearest_pending_task(self) -> Optional[TaskAgent]:
        pending_tasks = [t for t in self.model.tasks.values() if t.status != "done"]
        if not pending_tasks:
            return None

        x, y = self.pos
        best_task: Optional[TaskAgent] = None
        best_dist = float("inf")
        for t in pending_tasks:
            tx, ty = t.pos
            d = math.hypot(tx - x, ty - y)
            if d < best_dist:
                best_dist = d
                best_task = t
        return best_task

    def _work_on_task(self, task: TaskAgent, dt: float):
        task.status = "in_progress"

        # 故障状態に応じて処理能力を切り替え
        if self.state == "healthy":
            eff_rate = self.service_rate              # v
        else:
            eff_rate = self.service_rate * self.failure_model.eta  # η v

        work = eff_rate * dt
        task.remaining_work -= work
        if task.remaining_work <= 0:
            task.remaining_work = 0.0
            task.status = "done"
            if task.finished_step is None:
                task.finished_step = self.model.steps

    # ------------------------------------------------------------------
    # 故障判定（ターン開始時）
    # ------------------------------------------------------------------
    def _maybe_fail_at_step_start(self, dt: float):
        """ターン開始時の累積稼働時間 H に基づいて故障するか判定."""
        p_fail = self.model.failure_model.failure_prob_at_step_start(self.H, dt)
        if p_fail <= 0.0:
            return
        if self.random.random() < p_fail:
            self.state = "failed"