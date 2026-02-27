"""Simulated dangerous tools for demo agent.

These tools simulate real actions (file deletion, email sending, shell execution)
without actually performing them. They log what *would* happen so the demo can
show the contrast between unprotected and Truss-protected execution.
"""
from __future__ import annotations

import datetime


class ToolResult:
    """Result of a tool execution."""

    def __init__(self, tool: str, success: bool, output: str):
        self.tool = tool
        self.success = success
        self.output = output
        self.timestamp = datetime.datetime.utcnow().isoformat()

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return f"[{self.timestamp}] {self.tool} → {status}: {self.output}"


def delete_files(paths: list[str]) -> ToolResult:
    """Simulate deleting files. In a real agent this would call os.remove()."""
    deleted = ", ".join(paths)
    return ToolResult(
        tool="delete_files",
        success=True,
        output=f"Deleted {len(paths)} file(s): {deleted}",
    )


def send_email(to: str, subject: str, body: str) -> ToolResult:
    """Simulate sending an email. In a real agent this would call an SMTP/API."""
    return ToolResult(
        tool="send_email",
        success=True,
        output=f"Email sent to {to} — subject: {subject!r}",
    )


def exec_command(command: str) -> ToolResult:
    """Simulate executing a shell command. In a real agent this would call subprocess."""
    return ToolResult(
        tool="exec_command",
        success=True,
        output=f"Executed: {command}",
    )


# Registry maps tool names to (function, truss_action) pairs.
# truss_action is the action string sent to POST /api/gate.
TOOL_REGISTRY: dict[str, dict] = {
    "delete_files": {
        "fn": delete_files,
        "truss_action": "filesystem.delete",
    },
    "send_email": {
        "fn": send_email,
        "truss_action": "email.send",
    },
    "exec_command": {
        "fn": exec_command,
        "truss_action": "shell.exec",
    },
}
