from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionDef:
    category: str
    action: str
    reversible: bool
    blast_radius: str
    description: str


TAXONOMY: dict[str, ActionDef] = {
    # Filesystem
    "filesystem.read": ActionDef(
        category="filesystem", action="read",
        reversible=True, blast_radius="none",
        description="Read files from the filesystem",
    ),
    "filesystem.write": ActionDef(
        category="filesystem", action="write",
        reversible=True, blast_radius="low",
        description="Write or modify files on the filesystem",
    ),
    "filesystem.delete": ActionDef(
        category="filesystem", action="delete",
        reversible=False, blast_radius="high",
        description="Delete files from the filesystem",
    ),
    "filesystem.exec": ActionDef(
        category="filesystem", action="exec",
        reversible=False, blast_radius="critical",
        description="Execute a file or binary on the filesystem",
    ),

    # Email
    "email.read": ActionDef(
        category="email", action="read",
        reversible=True, blast_radius="none",
        description="Read email messages",
    ),
    "email.draft": ActionDef(
        category="email", action="draft",
        reversible=True, blast_radius="none",
        description="Draft an email without sending",
    ),
    "email.send": ActionDef(
        category="email", action="send",
        reversible=False, blast_radius="medium",
        description="Send an email to a recipient",
    ),
    "email.delete": ActionDef(
        category="email", action="delete",
        reversible=False, blast_radius="high",
        description="Delete email messages",
    ),

    # Calendar
    "calendar.read": ActionDef(
        category="calendar", action="read",
        reversible=True, blast_radius="none",
        description="Read calendar events",
    ),
    "calendar.create": ActionDef(
        category="calendar", action="create",
        reversible=True, blast_radius="low",
        description="Create a calendar event",
    ),
    "calendar.delete": ActionDef(
        category="calendar", action="delete",
        reversible=False, blast_radius="medium",
        description="Delete a calendar event",
    ),

    # Shell
    "shell.exec": ActionDef(
        category="shell", action="exec",
        reversible=False, blast_radius="critical",
        description="Execute a shell command",
    ),

    # Network
    "network.fetch": ActionDef(
        category="network", action="fetch",
        reversible=True, blast_radius="none",
        description="Fetch data from a URL (GET)",
    ),
    "network.post": ActionDef(
        category="network", action="post",
        reversible=False, blast_radius="low",
        description="Send data to a URL (POST)",
    ),
    "network.exfiltrate": ActionDef(
        category="network", action="exfiltrate",
        reversible=False, blast_radius="critical",
        description="Exfiltrate data to an external endpoint",
    ),
}

# Aliases for common shorthand action names
ALIASES: dict[str, str] = {
    "read_file": "filesystem.read",
    "read_files": "filesystem.read",
    "write_file": "filesystem.write",
    "write_files": "filesystem.write",
    "delete_file": "filesystem.delete",
    "delete_files": "filesystem.delete",
    "exec_file": "filesystem.exec",
    "exec_command": "shell.exec",
    "run_command": "shell.exec",
    "send_email": "email.send",
    "read_email": "email.read",
    "draft_email": "email.draft",
    "delete_email": "email.delete",
    "read_calendar": "calendar.read",
    "create_event": "calendar.create",
    "delete_event": "calendar.delete",
    "fetch_url": "network.fetch",
    "http_get": "network.fetch",
    "http_post": "network.post",
    "exfiltrate": "network.exfiltrate",
}
