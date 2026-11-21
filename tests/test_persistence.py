"""Unit tests for Persistent and Versioned Storage with audit trail and rollback."""
from src.algorithms.persistence import PersistentFaultStore


def test_persistent_store_crud_and_versions(sample_fault_report):
    store = PersistentFaultStore()
    assert store.current_version == 0

    # 1. Insert (CREATE)
    v1 = store.insert(sample_fault_report, author="EngineerA")
    assert v1 == 1
    assert store.current_version == 1
    recs_v1 = store.get_current_records()
    assert len(recs_v1) == 1
    assert recs_v1[0].power_loss_kwh == 3200.0

    # 2. Update
    v2 = store.update(sample_fault_report.fault_id, {"power_loss_kwh": 4500.0}, author="EngineerB")
    assert v2 == 2
    assert store.current_version == 2
    recs_v2 = store.get_current_records()
    assert recs_v2[0].power_loss_kwh == 4500.0

    # 3. Snapshot isolation
    snap1 = store.get_as_of_version(1)
    assert snap1[0].power_loss_kwh == 3200.0
    snap2 = store.get_as_of_version(2)
    assert snap2[0].power_loss_kwh == 4500.0

    # 4. Rollback to version 1
    success = store.rollback_to_version(1, author="Supervisor")
    assert success is True
    assert store.current_version == 3
    recs_after_rollback = store.get_current_records()
    assert recs_after_rollback[0].power_loss_kwh == 3200.0

    # 5. Audit log entries
    audit = store.get_audit_log()
    assert len(audit) == 3
    assert audit[0].action == "CREATE"
    assert audit[1].action == "UPDATE"
    assert audit[2].action == "ROLLBACK"

