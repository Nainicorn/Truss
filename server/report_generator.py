"""Pure function for generating Markdown reports from RunRecord."""

import json


def generate_report_md(run_record: dict) -> str:
    """Generate Markdown report from RunRecord.

    Args:
        run_record: RunRecord dict

    Returns:
        Markdown string for the report
    """
    sections = []

    # Header
    sections.append(f"# Polaris Evaluation Run: {run_record.get('run_id', 'unknown')}\n")
    sections.append(f"**Created:** {run_record.get('created_at', 'unknown')}")
    sections.append(f"**Version:** {run_record.get('version', '1.0.0')}\n")

    # Summary
    sections.append("## Summary\n")
    sections.append(f"_Run ID: {run_record.get('run_id', 'unknown')}_\n")

    # Decision (separate section if available)
    if run_record.get('decision'):
        sections.append("## Decision\n")
        decision = run_record['decision']
        sections.append(f"- **Verdict:** {decision.get('verdict', 'unknown')}")
        sections.append(f"- **Confidence:** {decision.get('confidence', 0):.2f}")
        sections.append(f"- **Rationale:** {decision.get('rationale', 'N/A')}\n")
    else:
        sections.append("_No decision available (run incomplete)_\n")

    # Task Specification
    sections.append("## Task Specification\n")
    task_spec = run_record.get('task_spec', {})
    sections.append(f"**Description:** {task_spec.get('description', 'N/A')}\n")

    if task_spec.get('constraints'):
        sections.append("**Constraints:**")
        for constraint in task_spec['constraints']:
            sections.append(f"- {constraint}")
        sections.append('')

    # Candidate Output
    sections.append("## Candidate Output\n")
    candidate = run_record.get('candidate_output', {})
    sections.append(f"```\n{candidate.get('content', 'N/A')}\n```\n")

    # Probe Plan
    if run_record.get('probe_plan'):
        sections.append("## Probe Plan\n")
        for idx, probe in enumerate(run_record['probe_plan'].get('probes', []), 1):
            sections.append(f"{idx}. **{probe.get('name', 'unknown')}:** {probe.get('description', 'N/A')}")
        sections.append('')

    # Probe Results
    if run_record.get('probe_results'):
        sections.append("## Probe Results\n")
        for idx, result in enumerate(run_record['probe_results'], 1):
            sections.append(f"### {idx}. {result.get('probe_name', 'unknown')}\n")
            sections.append(f"- **Verdict:** {result.get('verdict', 'unknown')}")
            sections.append(f"- **Confidence:** {result.get('confidence', 0):.2f}")
            sections.append(f"- **Rationale:** {result.get('rationale', 'N/A')}\n")

            if result.get('evidence'):
                sections.append("**Evidence:**\n")
                for ev_idx, evidence in enumerate(result['evidence'], 1):
                    sections.append(f"{ev_idx}. **{evidence.get('type', 'unknown')}** (from {evidence.get('source', 'unknown')})")
                    sections.append(f"   ```")
                    content = evidence.get('content', 'N/A')
                    if isinstance(content, str):
                        sections.append(f"   {content}")
                    else:
                        sections.append(f"   {json.dumps(content)}")
                    sections.append(f"   ```\n")

            if result.get('failure_labels'):
                sections.append(f"**Failure Labels:** {', '.join(result['failure_labels'])}\n")

    # Execution Timeline
    if run_record.get('audit_trace', {}).get('node_events'):
        sections.append("## Execution Timeline\n")
        for event in run_record['audit_trace']['node_events']:
            duration = f" ({event.get('duration_ms', 0)}ms)" if event.get('duration_ms') else ''
            sections.append(f"- **{event.get('node_name', 'unknown')}**{duration} - {event.get('timestamp', 'unknown')}")
        sections.append('')

    # Configuration
    if run_record.get('config_snapshot'):
        sections.append("## Configuration\n")
        sections.append(f"```json\n{json.dumps(run_record['config_snapshot'], indent=2)}\n```\n")

    return '\n'.join(sections)
