"""Tests for envault.audit module."""

import json
import pytest
from pathlib import Path

from envault.audit import AuditLog, AuditError, AUDIT_LOG_FILENAME


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def audit_log(tmp_dir):
    return AuditLog(tmp_dir)


class TestAuditLogRecord:
    def test_creates_log_file_on_first_record(self, audit_log, tmp_dir):
        audit_log.record("lock")
        assert (tmp_dir / AUDIT_LOG_FILENAME).exists()

    def test_record_writes_valid_json(self, audit_log, tmp_dir):
        audit_log.record("unlock", user="alice")
        lines = (tmp_dir / AUDIT_LOG_FILENAME).read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["action"] == "unlock"
        assert entry["user"] == "alice"

    def test_record_appends_multiple_entries(self, audit_log):
        audit_log.record("lock")
        audit_log.record("unlock")
        entries = audit_log.read()
        assert len(entries) == 2

    def test_record_includes_timestamp(self, audit_log):
        audit_log.record("lock")
        entry = audit_log.read()[0]
        assert "timestamp" in entry
        assert entry["timestamp"].endswith("+00:00")

    def test_record_stores_details(self, audit_log):
        audit_log.record("sync", details="pushed to shared dir")
        entry = audit_log.read()[0]
        assert entry["details"] == "pushed to shared dir"

    def test_record_raises_on_invalid_path(self, tmp_dir):
        bad_log = AuditLog(tmp_dir / "nonexistent" / "nested")
        with pytest.raises(AuditError):
            bad_log.record("lock")


class TestAuditLogRead:
    def test_read_returns_empty_list_when_no_log(self, audit_log):
        assert audit_log.read() == []

    def test_read_limit_returns_last_n_entries(self, audit_log):
        for action in ["lock", "unlock", "sync", "keygen"]:
            audit_log.record(action)
        entries = audit_log.read(limit=2)
        assert len(entries) == 2
        assert entries[-1]["action"] == "keygen"

    def test_read_all_entries_without_limit(self, audit_log):
        for _ in range(5):
            audit_log.record("lock")
        assert len(audit_log.read()) == 5


class TestAuditLogClear:
    def test_clear_removes_log_file(self, audit_log, tmp_dir):
        audit_log.record("lock")
        audit_log.clear()
        assert not (tmp_dir / AUDIT_LOG_FILENAME).exists()

    def test_clear_on_missing_file_does_not_raise(self, audit_log):
        audit_log.clear()  # no file exists yet

    def test_read_after_clear_returns_empty(self, audit_log):
        audit_log.record("lock")
        audit_log.clear()
        assert audit_log.read() == []
