"""
Entity Retention and Handling Policy for GDPR Article 17 (Right to Erasure).
Defines handling actions (DELETE, ANONYMIZE, RETAIN, SKIP) and explicit legal/technical rationale.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class HandlingAction(str, Enum):
    DELETE = "DELETE"
    ANONYMIZE = "ANONYMIZE"
    RETAIN = "RETAIN"
    SKIP = "SKIP"


@dataclass(frozen=True)
class EntityHandlingRule:
    entity_name: str
    action: HandlingAction
    description: str
    retained_fields: List[str]
    erased_or_masked_fields: List[str]
    retention_rationale: str


ENTITY_HANDLING_POLICIES: Dict[str, EntityHandlingRule] = {
    "users": EntityHandlingRule(
        entity_name="users",
        action=HandlingAction.ANONYMIZE,
        description="User master record and profile identity.",
        retained_fields=["id", "registered_at", "is_anonymized", "locale"],
        erased_or_masked_fields=[
            "full_name",
            "email",
            "phone_number",
            "shipping_address",
            "password_hash",
            "salt",
            "password_reset_token",
            "security_question",
            "security_answer_hash",
            "internal_notes",
        ],
        retention_rationale=(
            "Primary user key is retained as an anonymized technical anchor "
            "(full_name='Anonymized User', email='deleted_<uuid>@anon.local', credentials=None) "
            "to prevent foreign key corruption in dependent tax/invoice archives while making identification impossible."
        ),
    ),
    "settings": EntityHandlingRule(
        entity_name="settings",
        action=HandlingAction.DELETE,
        description="User UI themes, language, and notification communication preferences.",
        retained_fields=[],
        erased_or_masked_fields=[
            "user_id",
            "language",
            "theme",
            "email_notifications_enabled",
            "sms_notifications_enabled",
            "currency",
        ],
        retention_rationale=(
            "User preferences have no regulatory retention justification after erasure. "
            "Record is completely deleted from the database."
        ),
    ),
    "activity_history": EntityHandlingRule(
        entity_name="activity_history",
        action=HandlingAction.DELETE,
        description="Session logs, endpoint visit records, and behavioral history.",
        retained_fields=[],
        erased_or_masked_fields=["activity_id", "user_id", "timestamp", "action", "resource", "status"],
        retention_rationale=(
            "User-associated behavioral and browsing logs constitute personal data under GDPR Art. 4(1). "
            "They are completely purged unless required for active security investigations."
        ),
    ),
    "orders": EntityHandlingRule(
        entity_name="orders",
        action=HandlingAction.RETAIN,
        description="Commercial transactions, invoices, and accounting order records.",
        retained_fields=["order_id", "user_id", "created_at", "status", "total_amount", "currency", "items_count", "is_customer_anonymized"],
        erased_or_masked_fields=["customer_name", "shipping_address_snapshot", "billing_phone"],
        retention_rationale=(
            "Retained under statutory tax, financial audit, and accounting obligations "
            "(Commercial Code / Tax Code / Accounting Standards: 5-7 years mandatory retention period). "
            "Customer link points to the anonymized profile; personal shipping snapshots are erased."
        ),
    ),
    "consents": EntityHandlingRule(
        entity_name="consents",
        action=HandlingAction.ANONYMIZE,
        description="GDPR consent records and history.",
        retained_fields=["consent_id", "user_id", "purpose", "policy_version", "status", "revoked_at"],
        erased_or_masked_fields=["is_granted (set to False)", "source (updated to RIGHT_TO_ERASURE_WORKFLOW)"],
        retention_rationale=(
            "Under GDPR Art. 7(1) (Accountability principle), the data controller must retain evidence "
            "that consent was withdrawn and that erasure was executed, but all processing rights are permanently revoked."
        ),
    ),
}

