"""
Consent Management Service.
Handles GRANT and REVOKE lifecycle operations, history tracking, Anti-IDOR checks,
idempotency, immediate cache invalidation, and mock business dispatch operations.
"""
from datetime import datetime, timezone
import logging
import uuid
from typing import List, Optional

from app.consent.gate import ConsentPolicyGate, get_policy_gate
from app.consent.schemas import (
    ConsentPurpose,
    ConsentRecord,
    ConsentResponse,
    ConsentStatus,
    MarketingDispatchResult,
    PolicyGateDecision,
)
from app.export.repository import UserDataRepository, get_default_repository
from app.privacy.context import get_correlation_id

logger = logging.getLogger("app.consent.service")


class ConsentAccessDeniedException(Exception):
    """Raised when an actor attempts an unauthorized IDOR access to another user's consent settings."""
    pass


class SubjectNotFoundException(Exception):
    """Raised when user does not exist."""
    pass


class ConsentManagementService:
    """
    Manages user consents under GDPR Art. 6(1)(a) & Art. 7.
    """

    def __init__(
        self,
        repository: Optional[UserDataRepository] = None,
        policy_gate: Optional[ConsentPolicyGate] = None,
    ):
        self._custom_repository = repository
        self._custom_gate = policy_gate

    @property
    def repository(self) -> UserDataRepository:
        if self._custom_repository is not None:
            return self._custom_repository
        return get_default_repository()

    @property
    def gate(self) -> ConsentPolicyGate:
        if self._custom_gate is not None:
            return self._custom_gate
        return get_policy_gate()

    def get_user_consents(
        self,
        subject_id: str,
        authenticated_actor_id: str,
        actor_role: str = "user",
    ) -> List[ConsentRecord]:
        """Lists all consent records for a user with authorization check."""
        self._check_authorization(subject_id, authenticated_actor_id, actor_role)
        raw_consents = self.repository.get_consents_by_user_id(subject_id)
        results = []
        for c in raw_consents:
            results.append(
                ConsentRecord(
                    consent_id=c["consent_id"],
                    user_id=c["user_id"],
                    purpose=ConsentPurpose(c["purpose"]),
                    is_granted=c["is_granted"],
                    status=ConsentStatus(c.get("status", "ACTIVE" if c["is_granted"] else "REVOKED")),
                    policy_version=c["policy_version"],
                    granted_at=c.get("granted_at"),
                    withdrawn_at=c.get("withdrawn_at"),
                    updated_at=c["updated_at"],
                    source=c["source"],
                    history=c.get("history", []),
                )
            )
        return results

    def grant_consent(
        self,
        subject_id: str,
        purpose: ConsentPurpose,
        policy_version: str,
        source: str,
        authenticated_actor_id: str,
        actor_role: str = "user",
        correlation_id: Optional[str] = None,
    ) -> ConsentResponse:
        """
        Grants purpose-specific consent idempotently with evidentiary audit record.
        """
        corr_id = correlation_id or get_correlation_id() or "consent_grant_trace"
        self._check_authorization(subject_id, authenticated_actor_id, actor_role)

        # Check subject existence
        if not self.repository.get_user_by_id(subject_id):
            raise SubjectNotFoundException(f"User '{subject_id}' not found.")

        now_utc = datetime.now(timezone.utc).isoformat()
        consent_id = f"cns_{uuid.uuid4().hex[:8]}"

        record = self.repository.upsert_grant_consent(
            consent_id=consent_id,
            user_id=subject_id,
            purpose=purpose.value,
            policy_version=policy_version,
            source=source,
            timestamp=now_utc,
        )

        # Immediate invalidation of policy gate cache
        self.gate.invalidate_cache(subject_id, purpose.value)

        logger.info(
            "Consent successfully granted",
            extra={
                "event_type": "CONSENT_GRANTED",
                "user_id": subject_id,
                "purpose": purpose.value,
                "policy_version": policy_version,
                "source": source,
                "actor_id": authenticated_actor_id,
                "correlation_id": corr_id,
            }
        )

        return ConsentResponse(
            consent_id=record["consent_id"],
            user_id=record["user_id"],
            purpose=ConsentPurpose(record["purpose"]),
            is_granted=record["is_granted"],
            status=ConsentStatus(record["status"]),
            policy_version=record["policy_version"],
            granted_at=record.get("granted_at"),
            withdrawn_at=record.get("withdrawn_at"),
            updated_at=record["updated_at"],
            source=record["source"],
            message=f"Consent granted for {purpose.value} under {policy_version}.",
        )

    def revoke_consent(
        self,
        subject_id: str,
        purpose: ConsentPurpose,
        source: str,
        authenticated_actor_id: str,
        actor_role: str = "user",
        correlation_id: Optional[str] = None,
    ) -> ConsentResponse:
        """
        Revokes purpose-specific consent idempotently, invalidating cache immediately.
        """
        corr_id = correlation_id or get_correlation_id() or "consent_revoke_trace"
        self._check_authorization(subject_id, authenticated_actor_id, actor_role)

        if not self.repository.get_user_by_id(subject_id):
            raise SubjectNotFoundException(f"User '{subject_id}' not found.")

        now_utc = datetime.now(timezone.utc).isoformat()
        record = self.repository.revoke_consent(
            user_id=subject_id,
            purpose=purpose.value,
            source=source,
            timestamp=now_utc,
        )

        if not record:
            # If no consent existed at all, create an explicit revoked marker
            consent_id = f"cns_{uuid.uuid4().hex[:8]}"
            record = {
                "consent_id": consent_id,
                "user_id": subject_id,
                "purpose": purpose.value,
                "is_granted": False,
                "status": "REVOKED",
                "policy_version": "v1.2",
                "granted_at": None,
                "withdrawn_at": now_utc,
                "updated_at": now_utc,
                "source": source,
                "history": [
                    {
                        "action": "REVOKE",
                        "policy_version": "v1.2",
                        "timestamp": now_utc,
                        "source": source
                    }
                ]
            }
            self.repository._consents.append(record)

        # Immediate invalidation
        self.gate.invalidate_cache(subject_id, purpose.value)

        logger.info(
            "Consent successfully revoked",
            extra={
                "event_type": "CONSENT_REVOKED",
                "user_id": subject_id,
                "purpose": purpose.value,
                "source": source,
                "actor_id": authenticated_actor_id,
                "correlation_id": corr_id,
            }
        )

        return ConsentResponse(
            consent_id=record["consent_id"],
            user_id=record["user_id"],
            purpose=ConsentPurpose(record["purpose"]),
            is_granted=record["is_granted"],
            status=ConsentStatus(record["status"]),
            policy_version=record["policy_version"],
            granted_at=record.get("granted_at"),
            withdrawn_at=record.get("withdrawn_at"),
            updated_at=record["updated_at"],
            source=record["source"],
            message=f"Consent for {purpose.value} revoked successfully.",
        )

    def dispatch_marketing_email(
        self,
        recipient_user_id: str,
        campaign_name: str,
        correlation_id: Optional[str] = None,
    ) -> MarketingDispatchResult:
        """
        Simulates an actual dependent business operation (marketing campaign dispatch).
        INTERCEPTED by Policy Gate: If gate returns DENY, zero email side-effects occur.
        """
        corr_id = correlation_id or get_correlation_id() or "mkt_dispatch_trace"

        # POLICY GATE ENFORCEMENT
        gate_result = self.gate.evaluate_access(
            user_id=recipient_user_id,
            purpose=ConsentPurpose.MARKETING_EMAIL,
            correlation_id=corr_id,
        )

        if gate_result.decision != PolicyGateDecision.ALLOW:
            logger.warning(
                "Marketing email blocked by Consent Policy Gate",
                extra={
                    "event_type": "MARKETING_EMAIL_BLOCKED",
                    "recipient_id": recipient_user_id,
                    "campaign": campaign_name,
                    "gate_decision": gate_result.decision.value,
                    "reason": gate_result.reason,
                    "correlation_id": corr_id,
                }
            )
            return MarketingDispatchResult(
                status="DENIED_BY_POLICY_GATE",
                dispatched=False,
                recipient_id=recipient_user_id,
                channel="EMAIL",
                campaign_name=campaign_name,
                gate_decision=gate_result.decision,
                rejection_reason=gate_result.reason,
            )

        # SIDE EFFECT: Actual email transmission executed only if ALLOWED
        logger.info(
            "Marketing email dispatched successfully under valid consent",
            extra={
                "event_type": "MARKETING_EMAIL_DISPATCHED",
                "recipient_id": recipient_user_id,
                "campaign": campaign_name,
                "gate_decision": gate_result.decision.value,
                "correlation_id": corr_id,
            }
        )
        return MarketingDispatchResult(
            status="SUCCESS_DISPATCHED",
            dispatched=True,
            recipient_id=recipient_user_id,
            channel="EMAIL",
            campaign_name=campaign_name,
            gate_decision=gate_result.decision,
            rejection_reason=None,
        )

    def _check_authorization(self, subject_id: str, actor_id: str, actor_role: str):
        is_owner = (actor_id == subject_id)
        is_privileged = (actor_role.lower() in {"admin", "dpo", "data_protection_officer"})
        if not (is_owner or is_privileged):
            raise ConsentAccessDeniedException(
                f"Access denied: Actor '{actor_id}' is not authorized to manage consents for user '{subject_id}'."
            )

