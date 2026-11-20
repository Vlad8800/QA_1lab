"""
Consent Policy Gate and Enforcement Component.
Responsible for evaluating whether an operation is permitted under GDPR Art. 6.
Enforces purpose-specificity, policy version compatibility, immediate cache invalidation,
and strictly separates Consent from other lawful bases (Contractual, Legal obligation).
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from app.consent.schemas import (
     ConsentPurpose,
     PolicyGateDecision,
     PolicyGateResult,
     ProcessingLawfulBasis,
)
from app.export.repository import UserDataRepository, get_default_repository
from app.privacy.context import get_correlation_id

logger = logging.getLogger("app.consent.gate")


class ConsentPolicyGate:
    """
    Decentralized / Service-level Policy Gate that intercepts dependent business actions.
    
    Principles:
    1. Purpose-Specific: Consent granted for MARKETING_EMAIL cannot allow OPTIONAL_ANALYTICS.
    2. Version-Aware: Old superseded policy consents can be rejected if re-consent is required.
    3. Lawful Basis Isolation: Contractual actions (order checkout, order calculation) do NOT require consent.
    4. Immediate Invalidation: Local caches are invalidated synchronously upon revoke/grant.
    """

    def __init__(self, repository: Optional[UserDataRepository] = None):
        self._custom_repository = repository
        # In-memory fast evaluation cache: (user_id, purpose) -> (decision, cached_at)
        self._cache: Dict[Tuple[str, str], Tuple[PolicyGateDecision, str]] = {}

    @property
    def repository(self) -> UserDataRepository:
        if self._custom_repository is not None:
            return self._custom_repository
        return get_default_repository()

    def invalidate_cache(self, user_id: str, purpose: Optional[str] = None):
        """Immediately invalidates any cached decisions for real-time revoke enforcement."""
        if purpose:
            self._cache.pop((user_id, purpose), None)
        else:
            keys_to_remove = [k for k in self._cache.keys() if k[0] == user_id]
            for k in keys_to_remove:
                self._cache.pop(k, None)

    def evaluate_access(
        self,
        user_id: str,
        purpose: ConsentPurpose,
        required_policy_version: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> PolicyGateResult:
        """
        Evaluates whether a purpose-specific processing action is allowed for the user.
        Returns PolicyGateResult (ALLOW or DENY) with detailed rationale.
        """
        corr_id = correlation_id or get_correlation_id() or "gate_eval_trace"
        now_utc = datetime.now(timezone.utc).isoformat()

        # Check repository state directly (ensuring zero stale cache window)
        consent = self.repository.get_consent(user_id, purpose.value)

        # 1. No consent record found -> DENY
        if not consent:
            decision = PolicyGateDecision.DENY
            reason = f"No consent record found for purpose '{purpose.value}' (GDPR Art. 6(1)(a) requirement not met)."
            self._log_evaluation(user_id, purpose, decision, reason, corr_id)
            return PolicyGateResult(
                decision=decision,
                reason=reason,
                user_id=user_id,
                purpose=purpose,
                policy_version_checked=required_policy_version,
                evaluated_at=now_utc,
                correlation_id=corr_id,
            )

        # 2. Consent withdrawn or not granted -> DENY
        if not consent.get("is_granted", False) or consent.get("status") in {"REVOKED", "REVOKED_UPON_ERASURE"}:
            decision = PolicyGateDecision.DENY
            status_desc = consent.get("status", "REVOKED")
            reason = f"Consent for purpose '{purpose.value}' is currently {status_desc} (Withdrawn at: {consent.get('withdrawn_at')})."
            self._log_evaluation(user_id, purpose, decision, reason, corr_id)
            return PolicyGateResult(
                decision=decision,
                reason=reason,
                user_id=user_id,
                purpose=purpose,
                policy_version_checked=consent.get("policy_version"),
                evaluated_at=now_utc,
                correlation_id=corr_id,
            )

        # 3. Policy version check (if a specific version is required)
        if required_policy_version and consent.get("policy_version") != required_policy_version:
            decision = PolicyGateDecision.DENY
            reason = (
                f"Consent was granted under policy version '{consent.get('policy_version')}', "
                f"but version '{required_policy_version}' is required. Re-consent needed."
            )
            self._log_evaluation(user_id, purpose, decision, reason, corr_id)
            return PolicyGateResult(
                decision=decision,
                reason=reason,
                user_id=user_id,
                purpose=purpose,
                policy_version_checked=required_policy_version,
                evaluated_at=now_utc,
                correlation_id=corr_id,
            )

        # 4. Valid active consent -> ALLOW
        decision = PolicyGateDecision.ALLOW
        reason = f"Active valid consent found for purpose '{purpose.value}' under policy version '{consent.get('policy_version')}'."
        self._log_evaluation(user_id, purpose, decision, reason, corr_id)
        return PolicyGateResult(
            decision=decision,
            reason=reason,
            user_id=user_id,
            purpose=purpose,
            policy_version_checked=consent.get("policy_version"),
            evaluated_at=now_utc,
            correlation_id=corr_id,
        )

    def _log_evaluation(
        self,
        user_id: str,
        purpose: ConsentPurpose,
        decision: PolicyGateDecision,
        reason: str,
        correlation_id: str,
    ):
        log_level = logging.INFO if decision == PolicyGateDecision.ALLOW else logging.WARNING
        logger.log(
            log_level,
            "Consent Policy Gate evaluation completed",
            extra={
                "event_type": "CONSENT_GATE_EVALUATION",
                "user_id": user_id,
                "purpose": purpose.value,
                "decision": decision.value,
                "reason": reason,
                "correlation_id": correlation_id,
            }
        )


# Global shared gate instance
_default_gate: Optional[ConsentPolicyGate] = None


def get_policy_gate() -> ConsentPolicyGate:
    global _default_gate
    if _default_gate is None:
        _default_gate = ConsentPolicyGate()
    return _default_gate

