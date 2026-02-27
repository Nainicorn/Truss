from __future__ import annotations

import pytest

from backend.classifier.action_classifier import ActionClassifier


@pytest.fixture
def classifier():
    return ActionClassifier()


# --- Taxonomy direct keys ---

class TestFilesystemActions:
    def test_filesystem_read(self, classifier):
        r = classifier.classify("filesystem.read")
        assert r.blast_radius == "none"
        assert r.reversible is True
        assert r.recognized is True

    def test_filesystem_write(self, classifier):
        r = classifier.classify("filesystem.write")
        assert r.blast_radius == "low"
        assert r.reversible is True

    def test_filesystem_delete(self, classifier):
        r = classifier.classify("filesystem.delete")
        assert r.blast_radius == "high"
        assert r.reversible is False

    def test_filesystem_exec(self, classifier):
        r = classifier.classify("filesystem.exec")
        assert r.blast_radius == "critical"
        assert r.reversible is False


class TestEmailActions:
    def test_email_read(self, classifier):
        r = classifier.classify("email.read")
        assert r.blast_radius == "none"
        assert r.reversible is True

    def test_email_draft(self, classifier):
        r = classifier.classify("email.draft")
        assert r.blast_radius == "none"
        assert r.reversible is True

    def test_email_send(self, classifier):
        r = classifier.classify("email.send")
        assert r.blast_radius == "medium"
        assert r.reversible is False

    def test_email_delete(self, classifier):
        r = classifier.classify("email.delete")
        assert r.blast_radius == "high"
        assert r.reversible is False


class TestShellActions:
    def test_shell_exec(self, classifier):
        r = classifier.classify("shell.exec")
        assert r.blast_radius == "critical"
        assert r.reversible is False


class TestNetworkActions:
    def test_network_fetch(self, classifier):
        r = classifier.classify("network.fetch")
        assert r.blast_radius == "none"
        assert r.reversible is True

    def test_network_post(self, classifier):
        r = classifier.classify("network.post")
        assert r.blast_radius == "low"
        assert r.reversible is False

    def test_network_exfiltrate(self, classifier):
        r = classifier.classify("network.exfiltrate")
        assert r.blast_radius == "critical"
        assert r.reversible is False


class TestCalendarActions:
    def test_calendar_read(self, classifier):
        r = classifier.classify("calendar.read")
        assert r.blast_radius == "none"
        assert r.reversible is True

    def test_calendar_create(self, classifier):
        r = classifier.classify("calendar.create")
        assert r.blast_radius == "low"
        assert r.reversible is True

    def test_calendar_delete(self, classifier):
        r = classifier.classify("calendar.delete")
        assert r.blast_radius == "medium"
        assert r.reversible is False


# --- Aliases ---

class TestAliases:
    def test_delete_files_alias(self, classifier):
        r = classifier.classify("delete_files")
        assert r.blast_radius == "high"
        assert r.reversible is False
        assert r.action_key == "filesystem.delete"

    def test_exec_command_alias(self, classifier):
        r = classifier.classify("exec_command")
        assert r.blast_radius == "critical"
        assert r.action_key == "shell.exec"

    def test_send_email_alias(self, classifier):
        r = classifier.classify("send_email")
        assert r.blast_radius == "medium"
        assert r.action_key == "email.send"

    def test_read_file_alias(self, classifier):
        r = classifier.classify("read_file")
        assert r.blast_radius == "none"
        assert r.action_key == "filesystem.read"

    def test_http_get_alias(self, classifier):
        r = classifier.classify("http_get")
        assert r.blast_radius == "none"
        assert r.action_key == "network.fetch"

    def test_exfiltrate_alias(self, classifier):
        r = classifier.classify("exfiltrate")
        assert r.blast_radius == "critical"
        assert r.action_key == "network.exfiltrate"


# --- Edge cases ---

class TestEdgeCases:
    def test_unknown_action_fails_safe(self, classifier):
        r = classifier.classify("totally_unknown_action")
        assert r.blast_radius == "high"
        assert r.reversible is False
        assert r.recognized is False

    def test_case_insensitive(self, classifier):
        r = classifier.classify("FILESYSTEM.DELETE")
        assert r.blast_radius == "high"
        assert r.recognized is True

    def test_whitespace_stripped(self, classifier):
        r = classifier.classify("  shell.exec  ")
        assert r.blast_radius == "critical"
        assert r.recognized is True

    def test_to_dict(self, classifier):
        r = classifier.classify("shell.exec")
        d = r.to_dict()
        assert d["blast_radius"] == "critical"
        assert d["reversible"] is False
        assert d["recognized"] is True
        assert "action_key" in d
