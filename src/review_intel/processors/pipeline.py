"""
Processing pipeline — orchestrates sequential processing steps.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


@dataclass
class StepStats:
    """Statistics from a single processing step."""
    name: str
    input_count: int = 0
    output_count: int = 0
    removed_count: int = 0
    flagged_count: int = 0
    duration_ms: float = 0


@dataclass
class ProcessingResult:
    """Aggregate result of the full processing pipeline."""
    input_count: int = 0
    output_count: int = 0
    step_results: dict[str, StepStats] = field(default_factory=dict)
    output: list[ReviewSchema] = field(default_factory=list)
    total_duration_ms: float = 0

    @property
    def removal_rate(self) -> float:
        if self.input_count == 0:
            return 0.0
        return 1.0 - (self.output_count / self.input_count)


class ProcessingStep(ABC):
    """Base class for a processing pipeline step."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        """Process reviews and return filtered/modified list."""
        ...


class ReviewPipeline:
    """Orchestrates sequential processing steps."""

    def __init__(self, steps: list[ProcessingStep] | None = None):
        self.steps = steps or []

    def add_step(self, step: ProcessingStep) -> None:
        self.steps.append(step)

    async def process(self, reviews: list[ReviewSchema]) -> ProcessingResult:
        result = ProcessingResult(input_count=len(reviews))
        start = time.monotonic()

        current = reviews
        for step in self.steps:
            step_start = time.monotonic()
            input_count = len(current)
            current = await step.process(current)
            step_stats = StepStats(
                name=step.name,
                input_count=input_count,
                output_count=len(current),
                removed_count=input_count - len(current),
                duration_ms=(time.monotonic() - step_start) * 1000,
            )
            result.step_results[step.name] = step_stats
            logger.info(
                "Step '%s': %d → %d reviews (-%d) in %.0fms",
                step.name, input_count, len(current),
                step_stats.removed_count, step_stats.duration_ms,
            )

        result.output = current
        result.output_count = len(current)
        result.total_duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Pipeline complete: %d → %d reviews (%.1f%% removed) in %.0fms",
            result.input_count, result.output_count,
            result.removal_rate * 100, result.total_duration_ms,
        )
        return result
