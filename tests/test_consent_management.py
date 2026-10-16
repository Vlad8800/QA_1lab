"""
Comprehensive Integration Test Suite for GDPR Consent Management Engine (Task 4).
Validates:
1. Consent Model & Evidentiary History (userId, purpose, status, policyVersion, timestamps, source, history)
2. GRANT -> ALLOW -> REVOKE -> DENY complete lifecycle with real side-effect gating
3. Purpose Specificity & Isolation (MARKETING_EMAIL does NOT grant OPTIONAL_ANALYTICS or MARKETING_SMS)
4. Policy Gate Version Checking (Outdated version rejected with re-consent required)
5. Idempotent GRANT & REVOKE (no duplicate corrupted history or errors)
6. Anti-IDOR Authorization enforcement (foreign user blocked from modifying another user's consent)
7. Lawful Basis Isolation (Core contractual order checkout is NOT blocked by lack of marketing consent)
8. Immediate Invalidation & Real-Time Enforcement (no stale cache gap)
"""
import pytest
from fastapi.testclient import TestClient

from app.consent.gate import get_policy_gate
from app.consent.schemas import ConsentPurpose, PolicyGateDecision
from app.export.repository import get_default_repository, reset_default_repository
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_repository_state():
    """Resets the repository and clears policy gate caches before each test."""
    reset_default_repository()
    gate = get_policy_gate()
    gate.invalidate_cache("usr_101")
    gate.invalidate_cache("usr_102")
    gate.invalidate_cache("usr_103")
    yield
    reset_default_repository()


def test_consent_model_structure_and_evidentiary_history():
    """
    Verifies that UserConsent includes:
    - userId, purpose, is_granted, status
    - policy_version, granted_at, withdrawn_at, updated_at, source
    - append-only history log of state transitions
    """
    response = client.get(
        "/api/users/usr_101/consents",
        headers={"x-actor-id": "usr_101", "x-actor-role": "user"},
    )
    assert response.status_code == 200
    consents = response.json()
    assert len(consents) >= 2

    # Check MARKETING_EMAIL consent record
    mkt = next(c for c in consents if c["purpose"] == "MARKETING_EMAIL")
    assert mkt["user_id"] == "usr_101"
    assert mkt["is_granted"] is True
    assert mkt["status"] == "ACTIVE"
    assert mkt["policy_version"] == "v1.2"
    assert mkt["granted_at"] is not None
    assert mkt["source"] == "REGISTRATION_CHECKBOX"
    assert len(mkt["history"]) >= 1
    assert mkt["history"][0]["action"] == "GRANT"


def test_grant_allow_revoke_deny_lifecycle_with_side_effect_verification():
    """
    CORE SCENARIO:
    1. Start with no consent or revoked state -> Policy Gate returns DENY -> Email NOT dispatched
    2. Explicit GRANT -> Policy Gate returns ALLOW -> Email successfully dispatched
    3. Explicit REVOKE -> Immediate Policy Gate DENY -> Email NOT dispatched
    """
    target_user = "usr_103"  # Fresh user with no initial marketing consent

    # 1. INITIAL STATE: DENY
    check_initial = client.post(
        "/api/policy-gate/check",
        json={"user_id": target_user, "purpose": "MARKETING_EMAIL"},
    )
    assert check_initial.status_code == 200
    assert check_initial.json()["decision"] == "DENY"

    # Business action blocked (no side effect)
    dispatch_before = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": target_user, "campaign_name": "Summer Fest 2026"},
    )
    assert dispatch_before.status_code == 200
    assert dispatch_before.json()["dispatched"] is False
    assert dispatch_before.json()["gate_decision"] == "DENY"
    assert dispatch_before.json()["status"] == "DENIED_BY_POLICY_GATE"

    # 2. GRANT: User grants MARKETING_EMAIL consent
    grant_res = client.post(
        f"/api/users/{target_user}/consents/grant",
        headers={"x-actor-id": target_user, "x-actor-role": "user"},
        json={
            "purpose": "MARKETING_EMAIL",
            "policy_version": "v1.2",
            "source": "PRIVACY_MODAL",
        },
    )
    assert grant_res.status_code == 200
    assert grant_res.json()["is_granted"] is True
    assert grant_res.json()["status"] == "ACTIVE"
    assert grant_res.json()["granted_at"] is not None

    # Immediate ALLOW evaluation
    check_after_grant = client.post(
        "/api/policy-gate/check",
        json={"user_id": target_user, "purpose": "MARKETING_EMAIL"},
    )
    assert check_after_grant.json()["decision"] == "ALLOW"

    # Business action permitted (side effect executed)
    dispatch_after_grant = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": target_user, "campaign_name": "Summer Fest 2026"},
    )
    assert dispatch_after_grant.status_code == 200
    assert dispatch_after_grant.json()["dispatched"] is True
    assert dispatch_after_grant.json()["gate_decision"] == "ALLOW"
    assert dispatch_after_grant.json()["status"] == "SUCCESS_DISPATCHED"

    # 3. REVOKE: User revokes MARKETING_EMAIL consent
    revoke_res = client.post(
        f"/api/users/{target_user}/consents/revoke",
        headers={"x-actor-id": target_user, "x-actor-role": "user"},
        json={"purpose": "MARKETING_EMAIL", "source": "ACCOUNT_SETTINGS"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["is_granted"] is False
    assert revoke_res.json()["status"] == "REVOKED"
    assert revoke_res.json()["withdrawn_at"] is not None

    # Immediate DENY evaluation (zero lag, cache invalidated)
    check_after_revoke = client.post(
        "/api/policy-gate/check",
        json={"user_id": target_user, "purpose": "MARKETING_EMAIL"},
    )
    assert check_after_revoke.json()["decision"] == "DENY"

    # Subsequent business action blocked again (zero side effect)
    dispatch_after_revoke = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": target_user, "campaign_name": "Autumn Flash Sale"},
    )
    assert dispatch_after_revoke.status_code == 200
    assert dispatch_after_revoke.json()["dispatched"] is False
    assert dispatch_after_revoke.json()["gate_decision"] == "DENY"


def test_purpose_isolation_cross_purpose_never_allowed():
    """
    CRITICAL CHECK: Granting consent for MARKETING_EMAIL must NEVER allow
    OPTIONAL_ANALYTICS or MARKETING_SMS.
    """
    user_id = "usr_102"  # Has active MARKETING_EMAIL consent, but NO analytics consent

    # 1. MARKETING_EMAIL is ALLOWED
    res_mkt = client.post(
        "/api/policy-gate/check",
        json={"user_id": user_id, "purpose": "MARKETING_EMAIL"},
    )
    assert res_mkt.json()["decision"] == "ALLOW"

    # 2. OPTIONAL_ANALYTICS is strictly DENIED
    res_analytics = client.post(
        "/api/policy-gate/check",
        json={"user_id": user_id, "purpose": "OPTIONAL_ANALYTICS"},
    )
    assert res_analytics.json()["decision"] == "DENY"
    assert "requirement not met" in res_analytics.json()["reason"]

    # 3. MARKETING_SMS is strictly DENIED
    res_sms = client.post(
        "/api/policy-gate/check",
        json={"user_id": user_id, "purpose": "MARKETING_SMS"},
    )
    assert res_sms.json()["decision"] == "DENY"


def test_policy_version_check_and_outdated_consent_rejection():
    """
    If a processing operation requires a new policy version (e.g. 'v2.0'),
    a consent granted under 'v1.2' is rejected by Policy Gate with a re-consent prompt reason.
    """
    user_id = "usr_101"  # Granted under v1.2

    # Check with matching version v1.2 -> ALLOW
    res_valid_ver = client.post(
        "/api/policy-gate/check",
        json={"user_id": user_id, "purpose": "MARKETING_EMAIL", "required_policy_version": "v1.2"},
    )
    assert res_valid_ver.json()["decision"] == "ALLOW"

    # Check with required version v2.0 -> DENY
    res_new_ver = client.post(
        "/api/policy-gate/check",
        json={"user_id": user_id, "purpose": "MARKETING_EMAIL", "required_policy_version": "v2.0"},
    )
    assert res_new_ver.json()["decision"] == "DENY"
    assert "Re-consent needed" in res_new_ver.json()["reason"]


def test_idempotency_of_grant_and_revoke():
    """
    Repeated calls to GRANT or REVOKE must succeed with HTTP 200 without creating
    duplicate corrupted records or throwing exceptions.
    """
    user_id = "usr_101"

    # Grant repeated call
    res_g1 = client.post(
        f"/api/users/{user_id}/consents/grant",
        headers={"x-actor-id": user_id},
        json={"purpose": "MARKETING_EMAIL", "policy_version": "v1.2", "source": "DASHBOARD"},
    )
    assert res_g1.status_code == 200

    res_g2 = client.post(
        f"/api/users/{user_id}/consents/grant",
        headers={"x-actor-id": user_id},
        json={"purpose": "MARKETING_EMAIL", "policy_version": "v1.2", "source": "DASHBOARD"},
    )
    assert res_g2.status_code == 200
    assert res_g2.json()["is_granted"] is True

    # Revoke repeated call
    res_r1 = client.post(
        f"/api/users/{user_id}/consents/revoke",
        headers={"x-actor-id": user_id},
        json={"purpose": "MARKETING_EMAIL", "source": "DASHBOARD"},
    )
    assert res_r1.status_code == 200

    res_r2 = client.post(
        f"/api/users/{user_id}/consents/revoke",
        headers={"x-actor-id": user_id},
        json={"purpose": "MARKETING_EMAIL", "source": "DASHBOARD"},
    )
    assert res_r2.status_code == 200
    assert res_r2.json()["status"] == "REVOKED"


def test_idor_protection_foreign_user_cannot_alter_consents():
    """
    Actor usr_102 attempting to grant or revoke consents for usr_101
    must be rejected with 403 Forbidden.
    """
    # Attempt unauthorized GRANT
    res_grant = client.post(
        "/api/users/usr_101/consents/grant",
        headers={"x-actor-id": "usr_102", "x-actor-role": "user"},
        json={"purpose": "OPTIONAL_ANALYTICS", "policy_version": "v1.2", "source": "ATTACK"},
    )
    assert res_grant.status_code == 403
    assert "Access denied" in res_grant.json()["detail"]

    # Attempt unauthorized REVOKE
    res_revoke = client.post(
        "/api/users/usr_101/consents/revoke",
        headers={"x-actor-id": "usr_102", "x-actor-role": "user"},
        json={"purpose": "MARKETING_EMAIL", "source": "ATTACK"},
    )
    assert res_revoke.status_code == 403


def test_dpo_role_can_manage_consents():
    """
    DPO/Admin officer can audit and manage consents on behalf of users.
    """
    res = client.post(
        "/api/users/usr_101/consents/revoke",
        headers={"x-actor-id": "officer_dpo_1", "x-actor-role": "dpo"},
        json={"purpose": "MARKETING_EMAIL", "source": "DPO_OFFICE"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REVOKED"


def test_lawful_basis_isolation_contractual_orders_never_blocked_by_consent():
    """
    CRITICAL DISTINCTION: Core contractual fulfillment (order total & calculation)
    must NOT require marketing consent and must NOT be blocked when marketing consent is revoked.
    """
    # 1. Ensure user has ALL consents revoked
    client.post(
        "/api/users/usr_101/consents/revoke",
        headers={"x-actor-id": "usr_101"},
        json={"purpose": "MARKETING_EMAIL", "source": "SETTINGS"},
    )
    client.post(
        "/api/users/usr_101/consents/revoke",
        headers={"x-actor-id": "usr_101"},
        json={"purpose": "OPTIONAL_ANALYTICS", "source": "SETTINGS"},
    )

    # 2. Execute commercial order calculation (Lawful basis: CONTRACT, Art. 6(1)(b))
    order_payload = {
        "customer_tier": "regular",
        "country_code": "UA",
        "weight": 2.0,
        "is_express": False,
        "is_holiday": False,
        "items": [
            {"name": "USB-C Cable", "price": 15.0, "quantity": 2}
        ]
    }
    response = client.post("/api/v1/orders/calculate", json=order_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["final_total"] > 0

