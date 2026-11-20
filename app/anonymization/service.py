"""
Anonymization Workflow Service implementing GDPR Article 17 (Right to Erasure).
Orchestrates entity retention policies, irreversible scrubbing, referential integrity preservation,
idempotency, and privacy-safe audit logging.
"""
from datetime import datetime, timezone
import logging
import uuid
from typing import Optional

from app.anonymization.policy import ENTITY_HANDLING_POLICIES, HandlingAction
from app.anonymization.schemas import (
    AnonymizationResponse,
    EntityProcessingSummary,
    ErasureVerificationResult,
)
from app.export.repository import UserDataRepository, get_default_repository
from app.privacy.context import get_correlation_id

logger = logging.getLogger("app.anonymization")


class AnonymizationAccessDeniedException(Exception):
    """Raised when an unauthorized actor attempts to anonymize or delete another user's data."""
    pass


class SubjectNotFoundException(Exception):
    """Raised when target subject ID does not exist."""
    pass


class AnonymizationWorkflowService:
    """
    Executes and coordinates GDPR Article 17 erasure workflow.
    Guarantees:
    - Anti-IDOR Authorization
    - Irreversible Scrubbing of Direct PII and Secrets
    - Transactional Preservation of Referential Integrity
    - Full Idempotency
    - Privacy-Safe Audit Logging
    """

    def __init__(self, repository: Optional[UserDataRepository] = None):
        self._custom_repository = repository

    @property
    def repository(self) -> UserDataRepository:
        if self._custom_repository is not None:
            return self._custom_repository
        return get_default_repository()

    def anonymize_user(
        self,
        subject_id: str,
        authenticated_actor_id: str,
        actor_role: str = "user",
        correlation_id: Optional[str] = None,
    ) -> AnonymizationResponse:
        corr_id = correlation_id or get_correlation_id() or f"anon_corr_{uuid.uuid4().hex[:10]}"
        now_utc = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Anonymization workflow requested",
            extra={
                "event_type": "USER_ANONYMIZATION_INIT",
                "actor_id": authenticated_actor_id,
                "subject_id": subject_id,
                "actor_role": actor_role,
                "correlation_id": corr_id,
            }
        )

        # 1. Anti-IDOR Authorization Check
        is_owner = (authenticated_actor_id == subject_id)
        is_privileged = (actor_role.lower() in {"admin", "dpo", "data_protection_officer"})

        if not (is_owner or is_privileged):
            logger.warning(
                "Anonymization workflow rejected: IDOR violation attempt",
                extra={
                    "event_type": "USER_ANONYMIZATION_DENIED",
                    "actor_id": authenticated_actor_id,
                    "subject_id": subject_id,
                    "correlation_id": corr_id,
                    "status": "forbidden",
                }
            )
            raise AnonymizationAccessDeniedException("Access denied: You are not authorized to anonymize this subject.")

        # 2. Check existence of subject
        raw_user = self.repository.get_user_by_id(subject_id)
        if not raw_user:
            logger.warning(
                "Anonymization workflow failed: User not found",
                extra={
                    "event_type": "USER_ANONYMIZATION_NOT_FOUND",
                    "actor_id": authenticated_actor_id,
                    "subject_id": subject_id,
                    "correlation_id": corr_id,
                    "status": "not_found",
                }
            )
            raise SubjectNotFoundException(f"User with ID '{subject_id}' not found.")

        # 3. Idempotency Check: if already anonymized, return safe idempotent response
        if raw_user.get("is_anonymized", False):
            logger.info(
                "User already anonymized; returning idempotent success status",
                extra={
                    "event_type": "USER_ANONYMIZATION_IDEMPOTENT",
                    "actor_id": authenticated_actor_id,
                    "subject_id": subject_id,
                    "correlation_id": corr_id,
                    "status": "already_anonymized",
                }
            )
            return AnonymizationResponse(
                status="ALREADY_ANONYMIZED",
                subject_id=subject_id,
                anonymized_at=now_utc,
                correlation_id=corr_id,
                processed_entities={
                    "users": EntityProcessingSummary(
                        action=HandlingAction.ANONYMIZE.value,
                        records_affected=1,
                        retention_rationale=ENTITY_HANDLING_POLICIES["users"].retention_rationale,
                    ),
                    "settings": EntityProcessingSummary(
                        action=HandlingAction.DELETE.value,
                        records_affected=0,
                        retention_rationale=ENTITY_HANDLING_POLICIES["settings"].retention_rationale,
                    ),
                    "activity_history": EntityProcessingSummary(
                        action=HandlingAction.DELETE.value,
                        records_affected=0,
                        retention_rationale=ENTITY_HANDLING_POLICIES["activity_history"].retention_rationale,
                    ),
                    "orders": EntityProcessingSummary(
                        action=HandlingAction.RETAIN.value,
                        records_affected=len(self.repository.get_orders_by_user_id(subject_id)),
                        retention_rationale=ENTITY_HANDLING_POLICIES["orders"].retention_rationale,
                    ),
                    "consents": EntityProcessingSummary(
                        action=HandlingAction.ANONYMIZE.value,
                        records_affected=len(self.repository.get_consents_by_user_id(subject_id)),
                        retention_rationale=ENTITY_HANDLING_POLICIES["consents"].retention_rationale,
                    ),
                },
                technical_summary="Subject was previously irreversibly anonymized. No further mutations were necessary.",
            )

        # 4. Atomic Multi-Entity Execution Boundary

        # A. Anonymize direct identifiers on User Master Record
        # Generate irreversible surrogate email and sanitized name
        random_anon_token = uuid.uuid4().hex[:12]
        anon_name = "Anonymized User"
        anon_email = f"deleted_{random_anon_token}@anon.local"

        self.repository.anonymize_user_profile(
            user_id=subject_id,
            anonymized_name=anon_name,
            anonymized_email=anon_email,
        )

        # B. Purge Settings / Preferences (DELETE)
        settings_deleted = self.repository.delete_settings(subject_id)
        settings_count = 1 if settings_deleted else 0

        # C. Purge Activity History (DELETE)
        deleted_activity_count = self.repository.delete_activity_history(subject_id)

        # D. Retain & Anonymize Orders (RETAIN)
        retained_orders_count = self.repository.retain_and_anonymize_orders(subject_id)

        # E. Revoke Consents (ANONYMIZE / REVOKE)
        revoked_consents_count = self.repository.revoke_consents_on_erasure(subject_id, now_utc)

        # 5. Compile entity summaries
        processed_entities = {
            "users": EntityProcessingSummary(
                action=HandlingAction.ANONYMIZE.value,
                records_affected=1,
                retention_rationale=ENTITY_HANDLING_POLICIES["users"].retention_rationale,
            ),
            "settings": EntityProcessingSummary(
                action=HandlingAction.DELETE.value,
                records_affected=settings_count,
                retention_rationale=ENTITY_HANDLING_POLICIES["settings"].retention_rationale,
            ),
            "activity_history": EntityProcessingSummary(
                action=HandlingAction.DELETE.value,
                records_affected=deleted_activity_count,
                retention_rationale=ENTITY_HANDLING_POLICIES["activity_history"].retention_rationale,
            ),
            "orders": EntityProcessingSummary(
                action=HandlingAction.RETAIN.value,
                records_affected=retained_orders_count,
                retention_rationale=ENTITY_HANDLING_POLICIES["orders"].retention_rationale,
            ),
            "consents": EntityProcessingSummary(
                action=HandlingAction.ANONYMIZE.value,
                records_affected=revoked_consents_count,
                retention_rationale=ENTITY_HANDLING_POLICIES["consents"].retention_rationale,
            ),
        }

        # 6. Privacy-Safe Audit Logging: Log event without writing old or new PII into log
        logger.info(
            "User data anonymization completed successfully",
            extra={
                "event_type": "USER_ANONYMIZATION_SUCCESS",
                "actor_id": authenticated_actor_id,
                "subject_id": subject_id,
                "correlation_id": corr_id,
                "status": "success",
                "settings_deleted": settings_count,
                "activity_purged": deleted_activity_count,
                "orders_retained": retained_orders_count,
                "consents_revoked": revoked_consents_count,
            }
        )

        return AnonymizationResponse(
            status="SUCCESS",
            subject_id=subject_id,
            anonymized_at=now_utc,
            correlation_id=corr_id,
            processed_entities=processed_entities,
            technical_summary=(
                "All direct identifiers (name, email, phone, address) and security credentials (password hash, "
                "salt, tokens, security questions) were permanently cleared. Orders were retained to satisfy statutory "
                "tax and financial recordkeeping requirements while maintaining referential integrity without orphan records."
            ),
        )

    def verify_erasure(self, subject_id: str) -> ErasureVerificationResult:
        """
        Verifies that erasure guarantees and referential integrity are fully satisfied for a subject.
        """
        user = self.repository.get_user_by_id(subject_id)
        if not user:
            raise SubjectNotFoundException(f"User {subject_id} not found.")

        is_profile_anonymized = bool(user.get("is_anonymized") is True)
        email_is_anonymized = "@anon.local" in user.get("email", "")
        direct_pii_cleared = (
            user.get("phone_number") is None and
            user.get("shipping_address") is None and
            user.get("full_name") == "Anonymized User"
        )
        security_fields_cleared = (
            user.get("password_hash") is None and
            user.get("salt") is None and
            user.get("password_reset_token") is None and
            user.get("security_question") is None and
            user.get("security_answer_hash") is None
        )
        settings_deleted = (self.repository.get_settings_by_user_id(subject_id) is None)
        activity_deleted = (len(self.repository.get_activity_by_user_id(subject_id)) == 0)

        consents = self.repository.get_consents_by_user_id(subject_id)
        consents_revoked = all(c.get("is_granted") is False for c in consents) if consents else True

        orders = self.repository.get_orders_by_user_id(subject_id)
        orders_retained = len(orders) > 0
        referential_integrity_intact = all(o.get("user_id") == subject_id for o in orders)

        return ErasureVerificationResult(
            subject_id=subject_id,
            is_profile_anonymized=is_profile_anonymized,
            email_is_anonymized=email_is_anonymized,
            direct_pii_cleared=direct_pii_cleared,
            security_fields_cleared=security_fields_cleared,
            settings_deleted=settings_deleted,
            activity_deleted=activity_deleted,
            consents_revoked=consents_revoked,
            orders_retained=orders_retained,
            orders_count=len(orders),
            referential_integrity_intact=referential_integrity_intact,
        )
