"""Persistent and versioned store with snapshot isolation, audit logging, and rollback."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.core.models import FaultReport


class AuditEntry:
    def __init__(
        self,
        version: int,
        action: str,  # "CREATE", "UPDATE", "DELETE", "ROLLBACK"
        fault_id: str,
        timestamp: datetime,
        diff: Dict[str, Any],
        author: str = "System"
    ):
        self.version = version
        self.action = action
        self.fault_id = fault_id
        self.timestamp = timestamp
        self.diff = diff
        self.author = author

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "action": self.action,
            "fault_id": self.fault_id,
            "timestamp": self.timestamp.isoformat(),
            "diff": self.diff,
            "author": self.author
        }


class PersistentFaultStore:
    """Auditable, versioned repository with snapshot rollback and point-in-time querying."""

    def __init__(self):
        # Current active state
        self._current_state: Dict[str, FaultReport] = {}
        # Version history: version_number -> Dict[fault_id, FaultReport]
        self._version_snapshots: Dict[int, Dict[str, FaultReport]] = {}
        # Immutable audit trail
        self._audit_log: List[AuditEntry] = []
        self._current_version = 0

    @property
    def current_version(self) -> int:
        return self._current_version

    def get_audit_log(self) -> List[AuditEntry]:
        return list(self._audit_log)

    def insert(self, report: FaultReport, author: str = "Engineer") -> int:
        """Insert a new fault report and snapshot the state."""
        self._current_version += 1
        rep_copy = deepcopy(report)
        rep_copy.version = self._current_version
        rep_copy.updated_at = datetime.now(timezone.utc)
        
        self._current_state[report.fault_id] = rep_copy
        self._version_snapshots[self._current_version] = deepcopy(self._current_state)

        entry = AuditEntry(
            version=self._current_version,
            action="CREATE",
            fault_id=report.fault_id,
            timestamp=datetime.now(timezone.utc),
            diff={"new_record": report.fault_id, "asset_id": report.asset_id},
            author=author
        )
        self._audit_log.append(entry)
        return self._current_version

    def update(self, fault_id: str, updates: Dict[str, Any], author: str = "Engineer") -> Optional[int]:
        """Apply updates to an existing report, creating a new auditable version."""
        if fault_id not in self._current_state or self._current_state[fault_id].is_deleted:
            return None

        self._current_version += 1
        existing = self._current_state[fault_id]
        raw = existing.model_dump()
        
        diff: Dict[str, Any] = {}
        for k, v in updates.items():
            if k in raw and raw[k] != v:
                diff[k] = {"old": raw[k], "new": v}
                raw[k] = v

        raw["version"] = self._current_version
        raw["updated_at"] = datetime.now(timezone.utc)
        updated_report = FaultReport.model_validate(raw)
        
        self._current_state[fault_id] = updated_report
        self._version_snapshots[self._current_version] = deepcopy(self._current_state)

        entry = AuditEntry(
            version=self._current_version,
            action="UPDATE",
            fault_id=fault_id,
            timestamp=datetime.now(timezone.utc),
            diff=diff,
            author=author
        )
        self._audit_log.append(entry)
        return self._current_version

    def soft_delete(self, fault_id: str, author: str = "Engineer") -> Optional[int]:
        """Tombstone a report in a new version snapshot."""
        if fault_id not in self._current_state or self._current_state[fault_id].is_deleted:
            return None

        self._current_version += 1
        self._current_state[fault_id].is_deleted = True
        self._current_state[fault_id].version = self._current_version
        self._current_state[fault_id].updated_at = datetime.now(timezone.utc)
        
        self._version_snapshots[self._current_version] = deepcopy(self._current_state)

        entry = AuditEntry(
            version=self._current_version,
            action="DELETE",
            fault_id=fault_id,
            timestamp=datetime.now(timezone.utc),
            diff={"is_deleted": True},
            author=author
        )
        self._audit_log.append(entry)
        return self._current_version

    def rollback_to_version(self, target_version: int, author: str = "Administrator") -> bool:
        """Roll back current store state to an exact historical version."""
        if target_version not in self._version_snapshots:
            return False

        self._current_version += 1
        self._current_state = deepcopy(self._version_snapshots[target_version])
        self._version_snapshots[self._current_version] = deepcopy(self._current_state)

        entry = AuditEntry(
            version=self._current_version,
            action="ROLLBACK",
            fault_id="ALL",
            timestamp=datetime.now(timezone.utc),
            diff={"restored_to_version": target_version},
            author=author
        )
        self._audit_log.append(entry)
        return True

    def get_as_of_version(self, version: int) -> Optional[List[FaultReport]]:
        """Retrieve snapshot of all active records at a specific version."""
        if version not in self._version_snapshots:
            return None
        return [r for r in self._version_snapshots[version].values() if not r.is_deleted]

    def get_current_records(self) -> List[FaultReport]:
        """Return all active records in the latest version."""
        return [r for r in self._current_state.values() if not r.is_deleted]

