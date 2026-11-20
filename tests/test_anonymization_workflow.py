"""
Comprehensive automated tests for GDPR Article 17 Right to Erasure & Anonymization Workflow.
Validates:
1. Entity handling policy (DELETE, ANONYMIZE, RETAIN)
2. Irreversible scrubbing of direct identifiers and credentials
3. Preservation of referential integrity (tax/invoicing orders retained without orphan rows)
4. Anti-IDOR authorization enforcement (foreign user blocked, self/DPO allowed)
5. Idempotency (calling multiple times returns ALREADY_ANONYMIZED safely)
6. Nonexistent subject returns 404
7. Privacy-safe audit logs (events logged with correlation_id, zero leaked PII)
8. Both POST and DELETE HTTP method support
"""
import logging
import pytest
from fastapi.testclient import TestClient

from app.anonymization.policy import ENTITY_HANDLING_POLICIES, HandlingAction
from app.anonymization.service import AnonymizationWorkflowService
from app.export.repository import UserDataRepository, get_default_repository, reset_default_repository
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_repository_state():
    """Resets the shared in-memory repository to baseline before each test."""
    reset_default_repository()
    yield
    reset_default_repository()


def test_entity_handling_policy_completeness():
    """Verifies that all relevant entities have explicit policies with documented retention rationales."""
    required_entities = {"users", "settings", "activity_history", "orders", "consents"}
    assert required_entities.issubset(set(ENTITY_HANDLING_POLICIES.keys()))

    assert ENTITY_HANDLING_POLICIES["users"].action == HandlingAction.ANONYMIZE
    assert ENTITY_HANDLING_POLICIES["settings"].action == HandlingAction.DELETE
    assert ENTITY_HANDLING_POLICIES["activity_history"].action == HandlingAction.DELETE
    assert ENTITY_HANDLING_POLICIES["orders"].action == HandlingAction.RETAIN
    assert ENTITY_HANDLING_POLICIES["consents"].action == HandlingAction.ANONYMIZE

    # Rationale must not be empty and must justify why the action was taken
    for name, policy in ENTITY_HANDLING_POLICIES.items():
        assert len(policy.retention_rationale.strip()) > 20


def test_successful_user_anonymization_and_erasure():
    """
    Tests full execution of anonymization for usr_101:
    - Returns HTTP 200 with SUCCESS
    - Scrubs direct PII and credentials
    - Deletes settings and activity
    - Retains orders intact
    - Revokes consents
    """
    repo = get_default_repository()
    # Confirm baseline data exists
    assert repo.get_user_by_id("usr_101")["full_name"] == "Олександр Коваленко"
    assert repo.get_settings_by_user_id("usr_101") is not None
    assert len(repo.get_activity_by_user_id("usr_101")) == 2
    assert len(repo.get_orders_by_user_id("usr_101")) == 2
    assert len(repo.get_consents_by_user_id("usr_101")) == 2

    # Execute anonymization request
    response = client.post(
        "/api/users/usr_101/anonymize",
        headers={"x-actor-id": "usr_101", "x-actor-role": "user", "x-correlation-id": "test_corr_101"},
        json={"reason": "USER_REQUESTED_ERASURE", "confirm_irreversible": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["subject_id"] == "usr_101"
    assert data["correlation_id"] == "test_corr_101"

    # Verify entity processing breakdown
    assert data["processed_entities"]["users"]["action"] == "ANONYMIZE"
    assert data["processed_entities"]["settings"]["action"] == "DELETE"
    assert data["processed_entities"]["activity_history"]["action"] == "DELETE"
    assert data["processed_entities"]["orders"]["action"] == "RETAIN"
    assert data["processed_entities"]["consents"]["action"] == "ANONYMIZE"

    # Verify User record scrubbing in DB
    updated_user = repo.get_user_by_id("usr_101")
    assert updated_user["is_anonymized"] is True
    assert updated_user["full_name"] == "Anonymized User"
    assert updated_user["email"].startswith("deleted_") and updated_user["email"].endswith("@anon.local")
    assert updated_user["phone_number"] is None
    assert updated_user["shipping_address"] is None
    assert updated_user["password_hash"] is None
    assert updated_user["salt"] is None
    assert updated_user["password_reset_token"] is None
    assert updated_user["security_question"] is None
    assert updated_user["security_answer_hash"] is None

    # Verify Preferences & History purge
    assert repo.get_settings_by_user_id("usr_101") is None
    assert len(repo.get_activity_by_user_id("usr_101")) == 0

    # Verify Consents revoked
    consents = repo.get_consents_by_user_id("usr_101")
    for c in consents:
        assert c["is_granted"] is False
        assert c["status"] == "REVOKED_UPON_ERASURE"


def test_referential_integrity_and_retention_of_orders():
    """
    CRITICAL CHECK: Retained orders must still exist, preserve transaction metrics,
    and maintain referential integrity pointing to usr_101 without orphan rows.
    """
    repo = get_default_repository()
    initial_orders = repo.get_orders_by_user_id("usr_101")
    assert len(initial_orders) == 2

    response = client.post(
        "/api/users/usr_101/anonymize",
        headers={"x-actor-id": "usr_101", "x-actor-role": "user"},
    )
    assert response.status_code == 200

    # Retrieve orders post-anonymization
    retained_orders = repo.get_orders_by_user_id("usr_101")
    assert len(retained_orders) == 2

    for order in retained_orders:
        assert order["user_id"] == "usr_101"  # Referential integrity preserved!
        assert order["total_amount"] in (1250.50, 420.00)  # Financial ledger intact
        assert order["is_customer_anonymized"] is True

    # User entity still exists as technical anchor
    anchor_user = repo.get_user_by_id("usr_101")
    assert anchor_user is not None
    assert anchor_user["id"] == "usr_101"
    assert anchor_user["is_anonymized"] is True


def test_idempotency_of_anonymization():
    """
    Calling anonymize repeatedly must NOT fail, throw errors, or alter the anonymized state.
    Second call returns status: ALREADY_ANONYMIZED with HTTP 200.
    """
    headers = {"x-actor-id": "usr_101", "x-actor-role": "user"}

    # First execution
    res1 = client.post("/api/users/usr_101/anonymize", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "SUCCESS"

    # Second execution (Idempotent replay)
    res2 = client.post("/api/users/usr_101/anonymize", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "ALREADY_ANONYMIZED"
    assert "previously irreversibly anonymized" in res2.json()["technical_summary"]

    # Third execution via DELETE method
    res3 = client.delete("/api/users/usr_101", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["status"] == "ALREADY_ANONYMIZED"


def test_idor_protection_foreign_user_cannot_anonymize():
    """
    Anti-IDOR: Actor usr_102 attempting to delete/anonymize usr_101 must be rejected with 403 Forbidden.
    """
    response = client.post(
        "/api/users/usr_101/anonymize",
        headers={"x-actor-id": "usr_102", "x-actor-role": "user"},
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    # Target data must remain completely untouched
    repo = get_default_repository()
    assert repo.get_user_by_id("usr_101")["full_name"] == "Олександр Коваленко"
    assert repo.get_user_by_id("usr_101").get("is_anonymized") is not True


def test_dpo_and_admin_can_execute_erasure():
    """
    Privileged actors (DPO / Admin) are permitted to process GDPR erasure requests on behalf of users.
    """
    response = client.post(
        "/api/users/usr_102/anonymize",
        headers={"x-actor-id": "officer_dpo_1", "x-actor-role": "dpo"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["subject_id"] == "usr_102"


def test_unauthenticated_request_rejected():
    """Requests without identity headers or tokens must be rejected with 401."""
    response = client.post("/api/users/usr_101/anonymize")
    assert response.status_code == 401


def test_nonexistent_user_returns_404():
    """Attempting to anonymize a non-existent subject ID returns 404 Not Found."""
    response = client.post(
        "/api/users/usr_nonexistent_999/anonymize",
        headers={"x-actor-id": "usr_nonexistent_999", "x-actor-role": "user"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_erasure_verification_endpoint():
    """Tests the diagnostic verification endpoint confirming data state and referential integrity."""
    # Before anonymization: not fully erased
    res_before = client.get(
        "/api/users/usr_101/anonymize/verify",
        headers={"x-actor-id": "usr_101"},
    )
    assert res_before.status_code == 200
    assert res_before.json()["is_profile_anonymized"] is False

    # Execute anonymization
    client.post(
        "/api/users/usr_101/anonymize",
        headers={"x-actor-id": "usr_101"},
    )

    # After anonymization: all verification criteria pass
    res_after = client.get(
        "/api/users/usr_101/anonymize/verify",
        headers={"x-actor-id": "usr_101"},
    )
    assert res_after.status_code == 200
    v = res_after.json()
    assert v["is_profile_anonymized"] is True
    assert v["email_is_anonymized"] is True
    assert v["direct_pii_cleared"] is True
    assert v["security_fields_cleared"] is True
    assert v["settings_deleted"] is True
    assert v["activity_deleted"] is True
    assert v["consents_revoked"] is True
    assert v["orders_retained"] is True
    assert v["referential_integrity_intact"] is True


def test_privacy_safe_audit_logging_during_anonymization(caplog):
    """
    Verifies that the anonymization workflow emits structured audit events
    containing correlation_id and subject_id, but ZERO deleted raw PII or secret hashes.
    """
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/users/usr_101/anonymize",
            headers={"x-actor-id": "usr_101", "x-actor-role": "user", "x-correlation-id": "audit_trace_999"},
        )
        assert response.status_code == 200

    log_text = caplog.text

    # Audit events must be present
    assert "USER_ANONYMIZATION_SUCCESS" in log_text or "anonymization completed successfully" in log_text

    # DELETED PII MUST NOT LEAK INTO AUDIT LOGS
    assert "Олександр Коваленко" not in log_text
    assert "+380501112233" not in log_text
    assert "Хрещатик" not in log_text
    assert "fakehashvalue9912093840293482039482034982039" not in log_text

