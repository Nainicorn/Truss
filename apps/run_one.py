"""CLI: Run a single evaluation."""

import argparse
import sys
from pathlib import Path

from graphs import create_graph
from schemas import TaskSpec, CandidateOutput
from schemas.run import RunRecord


def main():
    """Execute one evaluation run from JSON fixtures."""
    parser = argparse.ArgumentParser(
        description="Run a single Polaris evaluation"
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Path to task JSON file",
    )
    parser.add_argument(
        "--candidate",
        required=True,
        help="Path to candidate JSON file",
    )

    args = parser.parse_args()

    # Load fixtures
    try:
        task_path = Path(args.task)
        candidate_path = Path(args.candidate)

        if not task_path.exists():
            print(f"Error: Task file not found: {task_path}", file=sys.stderr)
            return 1

        if not candidate_path.exists():
            print(
                f"Error: Candidate file not found: {candidate_path}",
                file=sys.stderr,
            )
            return 1

        task_json = task_path.read_text()
        candidate_json = candidate_path.read_text()
    except Exception as e:
        print(f"Error: Failed to read files: {e}", file=sys.stderr)
        return 1

    # Validate schemas
    try:
        task = TaskSpec.model_validate_json(task_json)
        candidate = CandidateOutput.model_validate_json(candidate_json)
    except Exception as e:
        print(f"Error: Schema validation failed: {e}", file=sys.stderr)
        return 1

    # Create and run graph
    try:
        graph = create_graph()
        initial_state = {
            "task_spec": task.model_dump(),
            "candidate_output": candidate.model_dump(),
        }

        result = graph.invoke(initial_state)

        # Convert to RunRecord and validate
        run_record = RunRecord.model_validate(result["run_record"])

        # Output JSON to stdout
        print(run_record.model_dump_json(indent=2))

        return 0

    except Exception as e:
        print(f"Error: Graph execution failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
