# meflux --help

"""Non-stationary Stream Environment for Causality in Flux.

Simulates a continual stream of causal learning tasks with domain shifts,
mechanism drifts, and novel environments:
- Ecology domain (Lotka-Volterra predator-prey cycles)
- Financial domain (Stock price & volume cycles)
- Physical domain (polynomial/power/mechanics)
- Economic domain (supply-demand/linear/sigmoid)
"""

from typing import List, Generator, Optional
import numpy as np
from ..scm.generator import CausalTask, CausalTaskGenerator


class ContinualFluxStream:
    """Streams causal tasks sequentially under domain shift and non-stationarity."""

    def __init__(
        self,
        tasks: Optional[List[CausalTask]] = None,
        num_tasks: int = 16,
        samples_per_task: int = 600,
        seed: int = 42,
    ):
        if tasks is not None:
            self.tasks = tasks
        else:
            gen = CausalTaskGenerator(seed=seed)
            self.tasks = gen.generate_flux_stream(
                num_tasks=num_tasks,
                samples_per_task=samples_per_task,
            )
        self.current_idx = 0

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self):
        self.current_idx = 0
        return self

    def __next__(self) -> CausalTask:
        if self.current_idx >= len(self.tasks):
            raise StopIteration
        task = self.tasks[self.current_idx]
        self.current_idx += 1
        return task

    def get_task(self, idx: int) -> CausalTask:
        return self.tasks[idx]
