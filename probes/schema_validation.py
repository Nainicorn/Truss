"""Schema validation probe - validates output structure."""

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


class SchemaValidationProbe(BaseProbe):
    """Validate CandidateOutput round-trips and has required fields.

    Deterministic checks:
    1. Can serialize to JSON and back (round-trip)
    2. Required fields present (candidate_id, content)
    3. JSON schema validation
    """

    def run(
        self, task: TaskSpec, candidate: CandidateOutput
    ) -> ProbeResult:
        """Validate candidate output schema compliance."""
        evidence = []
        errors = []

        # Check required fields
        if not candidate.candidate_id:
            errors.append("Missing candidate_id")
            evidence.append(
                Evidence(
                    source=EvidenceSource.SCHEMA_VALIDATION,
                    excerpt="candidate_id is empty",
                    locator="field:candidate_id",
                )
            )

        if not candidate.content:
            errors.append("Missing content")
            evidence.append(
                Evidence(
                    source=EvidenceSource.SCHEMA_VALIDATION,
                    excerpt="content is empty",
                    locator="field:content",
                )
            )

        # Try round-trip: JSON → object → JSON
        try:
            json_str = candidate.model_dump_json()
            restored = CandidateOutput.model_validate_json(json_str)
            if restored != candidate:
                errors.append("Round-trip equality failed")
                evidence.append(
                    Evidence(
                        source=EvidenceSource.SCHEMA_VALIDATION,
                        excerpt="Object changed after round-trip",
                        locator="round-trip",
                    )
                )
        except Exception as e:
            errors.append(f"Round-trip failed: {str(e)[:50]}")
            evidence.append(
                Evidence(
                    source=EvidenceSource.SCHEMA_VALIDATION,
                    excerpt=str(e)[:100],
                    locator="round-trip",
                )
            )

        if errors:
            verdict = ProbeVerdict.FAIL
            reasoning = "; ".join(errors)
        else:
            verdict = ProbeVerdict.PASS
            reasoning = "Schema validation passed"
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
        return "schema_validation"

    @property
    def probe_type(self) -> str:
        return "schema_validation"
