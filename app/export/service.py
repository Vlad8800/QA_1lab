"""
Personal Data Export Service implementing GDPR Article 15 (Right of Access).
Enforces Anti-IDOR Authorization, Aggregation across all sources, and Data Minimization.
"""
from datetime import datetime, timezone
import logging
import uuid
from typing import Optional

from app.export.repository import UserDataRepository, get_default_repository
from app.export.schemas import (
    DocumentedOmission,
    PersonalDataExportResponse,
    UserActivityItem,
    UserConsentItem,
    UserOrderItem,
    UserProfileExport,
    UserSettingsExport,
)

logger = logging.getLogger("app.export")


class AccessDeniedException(Exception):
    """Raised when an actor attempts an unauthorized IDOR access to another user's personal data."""
    pass


class SubjectNotFoundException(Exception):
    """Raised when the requested subject ID does not exist."""
    pass


class PersonalDataExportService:
    """
    Coordinates aggregation, authorization, minimization, and auditing
    for personal data export packages.
    """

    def __init__(self, repository: Optional[UserDataRepository] = None):
        self._custom_repository = repository

    @property
    def repository(self) -> UserDataRepository:
        if self._custom_repository is not None:
            return self._custom_repository
        return get_default_repository()

    def export_user_data(
        self,
        subject_id: str,
        authenticated_actor_id: str,
        actor_role: str = "user"
    ) -> PersonalDataExportResponse:
        """
        Exports all personal data for the given subject.
        
        Security controls:
        1. IDOR Prevention: Compares authenticated principal with requested subject ID.
        2. Data Minimization: Excludes security-sensitive fields (hashes, tokens, fraud scores).
        3. Auditing: Emits privacy-safe event logs without dumping raw PII.
        4. Omission Handling: Predictably documents empty sources instead of failing.
        """
        logger.info(
            "Personal data export initiated",
            extra={
                "event_type": "PERSONAL_DATA_EXPORT_INIT",
                "actor_id": authenticated_actor_id,
                "subject_id": subject_id,
                "actor_role": actor_role,
            }
        )

        # 1. Anti-IDOR Access Control Check
        # Only the subject itself OR designated privileged officers (admin/DPO) may export data
        is_owner = (authenticated_actor_id == subject_id)
        is_privileged = (actor_role.lower() in {"admin", "dpo", "data_protection_officer"})

        if not (is_owner or is_privileged):
            logger.warning(
                "Personal data export blocked: IDOR violation attempt",
                extra={
                    "event_type": "PERSONAL_DATA_EXPORT_DENIED",
                    "actor_id": authenticated_actor_id,
                    "subject_id": subject_id,
                    "status": "forbidden",
                }
            )
            raise AccessDeniedException("Access denied: You are not authorized to export data for this subject.")

        # 2. Check subject existence
        raw_user = self.repository.get_user_by_id(subject_id)
        if not raw_user:
            logger.warning(
                "Personal data export failed: Subject not found",
                extra={
                    "event_type": "PERSONAL_DATA_EXPORT_NOT_FOUND",
                    "actor_id": authenticated_actor_id,
                    "subject_id": subject_id,
                    "status": "not_found",
                }
            )
            raise SubjectNotFoundException(f"User with ID '{subject_id}' not found.")

        # 3. Source Aggregation & Strict Minimization
        data_categories = []
        documented_omissions = []

        # Category: Profile (Filter out password hashes, tokens, risk flags)
        profile_export = UserProfileExport(
            full_name=raw_user["full_name"],
            email=raw_user["email"],
            phone_number=raw_user.get("phone_number"),
            shipping_address=raw_user.get("shipping_address"),
            registered_at=raw_user["registered_at"],
            locale=raw_user.get("locale", "uk-UA"),
        )
        data_categories.append("profile")

        # Category: Settings
        raw_settings = self.repository.get_settings_by_user_id(subject_id)
        settings_export = None
        if raw_settings:
            settings_export = UserSettingsExport(
                language=raw_settings.get("language", "uk"),
                theme=raw_settings.get("theme", "light"),
                email_notifications_enabled=raw_settings.get("email_notifications_enabled", True),
                sms_notifications_enabled=raw_settings.get("sms_notifications_enabled", False),
                currency=raw_settings.get("currency", "UAH"),
            )
            data_categories.append("settings")
        else:
            documented_omissions.append(
                DocumentedOmission(
                    category="settings",
                    reason="No custom preferences configured; system defaults apply."
                )
            )

        # Category: Activity History
        raw_activity = self.repository.get_activity_by_user_id(subject_id)
        activity_items = []
        if raw_activity:
            activity_items = [
                UserActivityItem(
                    activity_id=act["activity_id"],
                    timestamp=act["timestamp"],
                    action=act["action"],
                    resource=act["resource"],
                    status=act["status"],
                )
                for act in raw_activity
            ]
            data_categories.append("activity_history")
        else:
            documented_omissions.append(
                DocumentedOmission(
                    category="activity_history",
                    reason="No interaction history recorded for this account."
                )
            )

        # Category: Orders
        raw_orders = self.repository.get_orders_by_user_id(subject_id)
        order_items = []
        if raw_orders:
            order_items = [
                UserOrderItem(
                    order_id=ord_rec["order_id"],
                    created_at=ord_rec["created_at"],
                    status=ord_rec["status"],
                    total_amount=ord_rec["total_amount"],
                    currency=ord_rec.get("currency", "UAH"),
                    items_count=ord_rec["items_count"],
                )
                for ord_rec in raw_orders
            ]
            data_categories.append("orders")
        else:
            documented_omissions.append(
                DocumentedOmission(
                    category="orders",
                    reason="User has not created any commercial orders."
                )
            )

        # Category: Consents
        raw_consents = self.repository.get_consents_by_user_id(subject_id)
        consent_items = []
        if raw_consents:
            consent_items = [
                UserConsentItem(
                    consent_id=c["consent_id"],
                    purpose=c["purpose"],
                    is_granted=c["is_granted"],
                    policy_version=c["policy_version"],
                    updated_at=c["updated_at"],
                    source=c["source"],
                )
                for c in raw_consents
            ]
            data_categories.append("consents")
        else:
            documented_omissions.append(
                DocumentedOmission(
                    category="consents",
                    reason="No explicit GDPR consent records present."
                )
            )

        # 4. Assembly of standardized, versioned export package
        export_id = f"exp_{uuid.uuid4().hex[:12]}"
        now_utc = datetime.now(timezone.utc).isoformat()

        response = PersonalDataExportResponse(
            schema_version="1.0.0",
            export_id=export_id,
            generated_at=now_utc,
            subject_id=subject_id,
            data_categories=data_categories,
            profile=profile_export,
            settings=settings_export,
            activity_history=activity_items,
            orders=order_items,
            consents=consent_items,
            documented_omissions=documented_omissions,
        )

        # 5. Audit Logging without leaking full exported JSON
        logger.info(
            "Personal data export package generated successfully",
            extra={
                "event_type": "PERSONAL_DATA_EXPORT_SUCCESS",
                "export_id": export_id,
                "actor_id": authenticated_actor_id,
                "subject_id": subject_id,
                "categories_count": len(data_categories),
                "omissions_count": len(documented_omissions),
                "status": "success",
            }
        )

        return response

