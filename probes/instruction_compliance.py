"""Instruction compliance probe - checks constraints are addressed."""

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


class InstructionComplianceProbe(BaseProbe):
    """Check if candidate content addresses task constraints.

    Smart validation:
    1. Parse numeric constraints (e.g., "100 words max", "under 50 chars")
    2. Validate word count and length limits
    3. Fallback to keyword matching for non-numeric constraints
    """

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _validate_numeric_constraint(self, constraint: str, content: str) -> tuple[bool, str]:
        """Parse and validate numeric constraints like '100 words max', 'under 50 characters'.

        Returns: (is_valid, message)
        """
        constraint_lower = constraint.lower().strip()

        # Pattern: "X words max" or "max X words"
        words_max = re.search(r'(\d+)\s*words?\s*max|max\s*(\d+)\s*words?', constraint_lower)
        if words_max:
            max_words = int(words_max.group(1) or words_max.group(2))
            actual_words = self._count_words(content)
            if actual_words <= max_words:
                return True, f"Word count ({actual_words}) within limit ({max_words})"
            else:
                return False, f"Word count ({actual_words}) exceeds limit ({max_words})"

        # Pattern: "under X words"
        words_under = re.search(r'under\s*(\d+)\s*words?', constraint_lower)
        if words_under:
            max_words = int(words_under.group(1))
            actual_words = self._count_words(content)
            if actual_words < max_words:
                return True, f"Word count ({actual_words}) under limit ({max_words})"
            else:
                return False, f"Word count ({actual_words}) not under limit ({max_words})"

        # Pattern: "X characters max"
        chars_max = re.search(r'(\d+)\s*char(?:acter)?s?\s*max|max\s*(\d+)\s*char(?:acter)?s?', constraint_lower)
        if chars_max:
            max_chars = int(chars_max.group(1) or chars_max.group(2))
            actual_chars = len(content)
            if actual_chars <= max_chars:
                return True, f"Character count ({actual_chars}) within limit ({max_chars})"
            else:
                return False, f"Character count ({actual_chars}) exceeds limit ({max_chars})"

        # Pattern: "under X characters"
        chars_under = re.search(r'under\s*(\d+)\s*char(?:acter)?s?', constraint_lower)
        if chars_under:
            max_chars = int(chars_under.group(1))
            actual_chars = len(content)
            if actual_chars < max_chars:
                return True, f"Character count ({actual_chars}) under limit ({max_chars})"
            else:
                return False, f"Character count ({actual_chars}) not under limit ({max_chars})"

        # Pattern: "at least X words" or "minimum X words"
        words_min = re.search(r'(?:at\s+least|minimum)\s*(\d+)\s*words?', constraint_lower)
        if words_min:
            min_words = int(words_min.group(1))
            actual_words = self._count_words(content)
            if actual_words >= min_words:
                return True, f"Word count ({actual_words}) meets minimum ({min_words})"
            else:
                return False, f"Word count ({actual_words}) below minimum ({min_words})"

        # Not a numeric constraint
        return None, None

    def run(
        self, task: TaskSpec, candidate: CandidateOutput
    ) -> ProbeResult:
        """Check if all constraints are satisfied by the content."""
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
        evidence = []
        failed_constraints = []

        for i, constraint in enumerate(task.constraints):
            # Try numeric validation first
            is_valid, message = self._validate_numeric_constraint(constraint, candidate.content)

            if is_valid is not None:
                # Numeric constraint was parsed
                if not is_valid:
                    failed_constraints.append(constraint)
                    evidence.append(
                        Evidence(
                            source=EvidenceSource.TEXT_SPAN,
                            excerpt=message,
                            locator=f"constraint:{i}",
                        )
                    )
            else:
                # Fallback: keyword matching for non-numeric constraints
                content_lower = candidate.content.lower()
                if constraint.lower() not in content_lower:
                    failed_constraints.append(constraint)
                    evidence.append(
                        Evidence(
                            source=EvidenceSource.TEXT_SPAN,
                            excerpt=f"Constraint not found: '{constraint}'",
                            locator=f"constraint:{i}",
                        )
                    )

        if failed_constraints:
            verdict = ProbeVerdict.FAIL
            reasoning = (
                f"Failed constraints ({len(failed_constraints)}): "
                + ", ".join(failed_constraints[:2])
            )
        else:
            verdict = ProbeVerdict.PASS
            reasoning = f"All {len(task.constraints)} constraint(s) satisfied"
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
