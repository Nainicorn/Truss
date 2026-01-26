"""Consistency check probe - detects contradictions and format issues."""

import re

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


class ConsistencyCheckProbe(BaseProbe):
    """Check for logical inconsistencies and format issues.

    Deterministic checks:
    1. Empty content
    2. Obvious contradictions (e.g., "yes" and "no" in same response)
    3. Excessive length (> 100k chars warns)
    """

    def run(
        self, task: TaskSpec, candidate: CandidateOutput
    ) -> ProbeResult:
        """Check consistency of candidate output."""
        evidence = []
        errors = []

        # Check 1: Empty content
        if not candidate.content.strip():
            errors.append("Empty response")
            evidence.append(
                Evidence(
                    source=EvidenceSource.TEXT_SPAN,
                    excerpt="Content is empty or whitespace-only",
                    locator="content",
                )
            )

        # Check 2: Obvious contradictions (simple pattern matching)
        content_lower = candidate.content.lower()

        # Look for common contradiction patterns
        contradiction_patterns = [
            (r"\byes\b", r"\bno\b"),
            (r"\btrue\b", r"\bfalse\b"),
            (r"\bagreed?\b", r"\bdisagreed?\b"),
            (r"\bcorrect\b", r"\bincorrect\b"),
        ]

        for pattern1, pattern2 in contradiction_patterns:
            has_1 = re.search(pattern1, content_lower) is not None
            has_2 = re.search(pattern2, content_lower) is not None
            if has_1 and has_2:
                errors.append(
                    f"Contradiction detected: both '{pattern1}' and '{pattern2}'"
                )
                evidence.append(
                    Evidence(
                        source=EvidenceSource.CONSISTENCY_CHECK,
                        excerpt=f"Found both '{pattern1}' and '{pattern2}'",
                        locator="contradiction",
                    )
                )
                break  # Report first contradiction found

        # Check 3: Warn on excessive length
        if len(candidate.content) > 100000:
            errors.append(f"Excessive length: {len(candidate.content)} chars")
            evidence.append(
                Evidence(
                    source=EvidenceSource.CONSISTENCY_CHECK,
                    excerpt=f"Content is {len(candidate.content)} characters",
                    locator="length",
                )
            )

        if errors:
            verdict = ProbeVerdict.FAIL
            reasoning = "; ".join(errors)
        else:
            verdict = ProbeVerdict.PASS
            reasoning = "No consistency issues detected"
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
        return "consistency_check"

    @property
    def probe_type(self) -> str:
        return "consistency_check"
