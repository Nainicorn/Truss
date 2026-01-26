"""Instruction compliance probe - checks constraints are addressed."""

from schemas import (
    TaskSpec,
    CandidateOutput,
    ProbeVerdict,
    EvidenceSource,
    generate_id,
    utc_now,
)
from schemas.probe import ProbeResult, Evidence
from probes.base import BaseProbe


class InstructionComplianceProbe(BaseProbe):
    """Check if candidate content addresses task constraints.

    Simple deterministic check: for each constraint, look for keyword match
    (case-insensitive) in candidate content.
    """

    def run(
        self, task: TaskSpec, candidate: CandidateOutput
    ) -> ProbeResult:
        """Check if all constraints are mentioned in content."""
        # No constraints = pass
        if not task.constraints:
            return ProbeResult(
                result_id=generate_id("result"),
                probe_id=self.probe_id,
                verdict=ProbeVerdict.PASS,
                confidence=1.0,  # Deterministic
                evidence=[],  # PASS: evidence optional
                reasoning="No constraints specified",
                executed_at=utc_now(),
            )

        # Check each constraint
        content_lower = candidate.content.lower()
        evidence = []
        missing_constraints = []

        for i, constraint in enumerate(task.constraints):
            # Deterministic keyword check
            if constraint.lower() not in content_lower:
                missing_constraints.append(constraint)
                evidence.append(
                    Evidence(
                        source=EvidenceSource.TEXT_SPAN,
                        excerpt=f"Constraint not found: '{constraint}'",
                        locator=f"constraint:{i}",
                    )
                )

        if missing_constraints:
            verdict = ProbeVerdict.FAIL
            reasoning = (
                f"Missing constraints ({len(missing_constraints)}): "
                + ", ".join(missing_constraints[:2])
            )
        else:
            verdict = ProbeVerdict.PASS
            reasoning = f"All {len(task.constraints)} constraint(s) addressed"
            evidence = []  # PASS: evidence optional

        return ProbeResult(
            result_id=generate_id("result"),
            probe_id=self.probe_id,
            verdict=verdict,
            confidence=1.0,  # Deterministic
            evidence=evidence,
            reasoning=reasoning,
            executed_at=utc_now(),
        )

    @property
    def probe_id(self) -> str:
        return "instruction_compliance"

    @property
    def probe_type(self) -> str:
        return "instruction_compliance"
