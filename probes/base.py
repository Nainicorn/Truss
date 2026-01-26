"""Base class for all probes."""

from abc import ABC, abstractmethod

from schemas import TaskSpec, CandidateOutput
from schemas.probe import ProbeResult


class BaseProbe(ABC):
    """Abstract base class for evaluation probes.

    All probes are deterministic (no LLM, no network calls).
    Evidence policy:
    - FAIL/ERROR: MUST include evidence
    - UNCERTAIN: should include evidence when possible
    - PASS: may be empty
    """

    @abstractmethod
    def run(
        self, task: TaskSpec, candidate: CandidateOutput
    ) -> ProbeResult:
        """Execute probe and return result with evidence.

        Args:
            task: Task specification with constraints
            candidate: Candidate output to evaluate

        Returns:
            ProbeResult with verdict, evidence, and reasoning
        """
        pass

    @property
    @abstractmethod
    def probe_id(self) -> str:
        """Unique probe identifier."""
        pass

    @property
    @abstractmethod
    def probe_type(self) -> str:
        """Probe type (used in ProbePlan generation)."""
        pass
