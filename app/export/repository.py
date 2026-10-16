"""
In-memory database repository simulating real relational/document store.
Stores both user personal data and internal security-sensitive fields (for minimization validation).
"""
from typing import Any, Dict, List, Optional


class UserDataRepository:
    """Simulates database store containing profile, settings, transactions, logs, and security data."""

    def __init__(self):
        # 1. Users database table (includes internal security fields that MUST be filtered)
        self._users: Dict[str, Dict[str, Any]] = {
            "usr_101": {
                "id": "usr_101",
                "full_name": "Олександр Коваленко",
                "email": "oleksandr.kovalenko@example.ua",
                "phone_number": "+380501112233",
                "shipping_address": "м. Київ, вул. Хрещатик, 24, кв. 12",
                "registered_at": "2025-01-15T09:30:00Z",
                "locale": "uk-UA",
                # Security-sensitive fields (MUST NEVER be exported):
                "password_hash": "$2b$12$e8x5Z89Z.fakehashvalue9912093840293482039482034982039",
                "salt": "a8f9c2e1b4d7",
                "password_reset_token": "rst_tok_991823901823091283",
                "security_question": "Дівоче прізвище матері?",
                "security_answer_hash": "$2b$12$secret_hashed_answer_12345",
                "antifraud_score": 12.5,
                "is_flagged_fraud": False,
                "internal_risk_level": "LOW",
                "internal_notes": "Верифікований клієнт, перевірено менеджером #4",
            },
            "usr_102": {
                "id": "usr_102",
                "full_name": "Марія Шевченко",
                "email": "maria.shevchenko@example.ua",
                "phone_number": "+380672223344",
                "shipping_address": "м. Львів, пл. Ринок, 10, кв. 5",
                "registered_at": "2025-02-10T14:15:00Z",
                "locale": "uk-UA",
                "password_hash": "$2b$12$k9y4A71Z.anotherfakehash8829384029348203948203498",
                "salt": "b7c2d9e4a1f3",
                "password_reset_token": None,
                "security_question": "Улюблене місто?",
                "security_answer_hash": "$2b$12$hashed_city_lviv",
                "antifraud_score": 45.0,
                "is_flagged_fraud": False,
                "internal_risk_level": "MEDIUM",
                "internal_notes": "Підозра на дублікат картки",
            },
            "usr_103": {
                "id": "usr_103",
                "full_name": "Іван Мельник",
                "email": "ivan.melnyk@example.ua",
                "phone_number": "+380934445566",
                "shipping_address": "м. Одеса, вул. Дерибасівська, 1",
                "registered_at": "2026-03-01T11:00:00Z",
                "locale": "uk-UA",
                "password_hash": "$2b$12$secret_hash_usr103",
                "salt": "c1d2e3f4a5b6",
                "password_reset_token": None,
                "antifraud_score": 5.0,
                "is_flagged_fraud": False,
                "internal_risk_level": "LOW",
            }
        }

        # 2. User Settings table
        self._settings: Dict[str, Dict[str, Any]] = {
            "usr_101": {
                "user_id": "usr_101",
                "language": "uk",
                "theme": "dark",
                "email_notifications_enabled": True,
                "sms_notifications_enabled": True,
                "currency": "UAH",
            },
            "usr_102": {
                "user_id": "usr_102",
                "language": "en",
                "theme": "light",
                "email_notifications_enabled": False,
                "sms_notifications_enabled": False,
                "currency": "EUR",
            },
            "usr_103": {
                "user_id": "usr_103",
                "language": "uk",
                "theme": "light",
                "email_notifications_enabled": True,
                "sms_notifications_enabled": False,
                "currency": "UAH",
            }
        }

        # 3. User Activity History table
        self._activity: List[Dict[str, Any]] = [
            {
                "activity_id": "act_001",
                "user_id": "usr_101",
                "timestamp": "2026-04-01T10:12:00Z",
                "action": "USER_LOGIN",
                "resource": "/api/v1/auth/login",
                "status": "SUCCESS",
            },
            {
                "activity_id": "act_002",
                "user_id": "usr_101",
                "timestamp": "2026-04-01T10:15:30Z",
                "action": "ORDER_CREATED",
                "resource": "/api/v1/orders/calculate",
                "status": "SUCCESS",
            },
            {
                "activity_id": "act_003",
                "user_id": "usr_102",
                "timestamp": "2026-04-02T16:20:00Z",
                "action": "PASSWORD_CHANGED",
                "resource": "/api/v1/auth/password",
                "status": "SUCCESS",
            },
        ]

        # 4. User Orders table
        self._orders: List[Dict[str, Any]] = [
            {
                "order_id": "ord_9001",
                "user_id": "usr_101",
                "created_at": "2026-04-01T10:15:30Z",
                "status": "DELIVERED",
                "total_amount": 1250.50,
                "currency": "UAH",
                "items_count": 3,
            },
            {
                "order_id": "ord_9002",
                "user_id": "usr_101",
                "created_at": "2026-04-05T12:00:00Z",
                "status": "PROCESSING",
                "total_amount": 420.00,
                "currency": "UAH",
                "items_count": 1,
            },
            {
                "order_id": "ord_9003",
                "user_id": "usr_102",
                "created_at": "2026-04-02T18:00:00Z",
                "status": "CANCELLED",
                "total_amount": 85.00,
                "currency": "EUR",
                "items_count": 2,
            },
        ]

        # 5. User GDPR Consents table with evidentiary metadata & audit history
        self._consents: List[Dict[str, Any]] = [
            {
                "consent_id": "cns_001",
                "user_id": "usr_101",
                "purpose": "MARKETING_EMAIL",
                "is_granted": True,
                "status": "ACTIVE",
                "policy_version": "v1.2",
                "granted_at": "2025-01-15T09:30:00Z",
                "withdrawn_at": None,
                "updated_at": "2025-01-15T09:30:00Z",
                "source": "REGISTRATION_CHECKBOX",
                "history": [
                    {
                        "action": "GRANT",
                        "policy_version": "v1.2",
                        "timestamp": "2025-01-15T09:30:00Z",
                        "source": "REGISTRATION_CHECKBOX"
                    }
                ]
            },
            {
                "consent_id": "cns_002",
                "user_id": "usr_101",
                "purpose": "OPTIONAL_ANALYTICS",
                "is_granted": False,
                "status": "REVOKED",
                "policy_version": "v1.2",
                "granted_at": "2025-01-15T09:30:00Z",
                "withdrawn_at": "2025-06-20T11:00:00Z",
                "updated_at": "2025-06-20T11:00:00Z",
                "source": "PRIVACY_DASHBOARD",
                "history": [
                    {
                        "action": "GRANT",
                        "policy_version": "v1.2",
                        "timestamp": "2025-01-15T09:30:00Z",
                        "source": "REGISTRATION_CHECKBOX"
                    },
                    {
                        "action": "REVOKE",
                        "policy_version": "v1.2",
                        "timestamp": "2025-06-20T11:00:00Z",
                        "source": "PRIVACY_DASHBOARD"
                    }
                ]
            },
            {
                "consent_id": "cns_003",
                "user_id": "usr_102",
                "purpose": "MARKETING_EMAIL",
                "is_granted": True,
                "status": "ACTIVE",
                "policy_version": "v1.2",
                "granted_at": "2025-02-10T14:15:00Z",
                "withdrawn_at": None,
                "updated_at": "2025-02-10T14:15:00Z",
                "source": "REGISTRATION_CHECKBOX",
                "history": [
                    {
                        "action": "GRANT",
                        "policy_version": "v1.2",
                        "timestamp": "2025-02-10T14:15:00Z",
                        "source": "REGISTRATION_CHECKBOX"
                    }
                ]
            },
        ]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def get_settings_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._settings.get(user_id)

    def get_activity_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return [act for act in self._activity if act["user_id"] == user_id]

    def get_orders_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return [ord_rec for ord_rec in self._orders if ord_rec["user_id"] == user_id]

    def get_consents_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return [c for c in self._consents if c["user_id"] == user_id]

    def get_consent(self, user_id: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Returns the current consent record for a specific user and purpose."""
        for c in self._consents:
            if c["user_id"] == user_id and c["purpose"] == purpose:
                return c
        return None

    def upsert_grant_consent(
        self,
        consent_id: str,
        user_id: str,
        purpose: str,
        policy_version: str,
        source: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Grants consent idempotently, recording timestamp, policy version, channel source, and audit history.
        """
        existing = self.get_consent(user_id, purpose)
        if existing:
            # If already granted with same policy version, do not duplicate redundant history
            if existing.get("is_granted") is True and existing.get("policy_version") == policy_version:
                return existing

            existing["is_granted"] = True
            existing["status"] = "ACTIVE"
            existing["policy_version"] = policy_version
            existing["granted_at"] = timestamp
            existing["withdrawn_at"] = None
            existing["updated_at"] = timestamp
            existing["source"] = source
            if "history" not in existing:
                existing["history"] = []
            existing["history"].append({
                "action": "GRANT",
                "policy_version": policy_version,
                "timestamp": timestamp,
                "source": source
            })
            return existing

        # New consent record
        new_record = {
            "consent_id": consent_id,
            "user_id": user_id,
            "purpose": purpose,
            "is_granted": True,
            "status": "ACTIVE",
            "policy_version": policy_version,
            "granted_at": timestamp,
            "withdrawn_at": None,
            "updated_at": timestamp,
            "source": source,
            "history": [
                {
                    "action": "GRANT",
                    "policy_version": policy_version,
                    "timestamp": timestamp,
                    "source": source
                }
            ]
        }
        self._consents.append(new_record)
        return new_record

    def revoke_consent(
        self,
        user_id: str,
        purpose: str,
        source: str,
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """
        Revokes consent idempotently, updating status, recording withdrawn_at and appending history.
        """
        existing = self.get_consent(user_id, purpose)
        if not existing:
            return None

        # If already revoked, return without duplicate history
        if existing.get("is_granted") is False and existing.get("status") == "REVOKED":
            return existing

        existing["is_granted"] = False
        existing["status"] = "REVOKED"
        existing["withdrawn_at"] = timestamp
        existing["updated_at"] = timestamp
        existing["source"] = source
        if "history" not in existing:
            existing["history"] = []
        existing["history"].append({
            "action": "REVOKE",
            "policy_version": existing.get("policy_version", "v1.0"),
            "timestamp": timestamp,
            "source": source
        })
        return existing

    # --- Anonymization & Erasure Operations (GDPR Art. 17) ---

    def anonymize_user_profile(
        self,
        user_id: str,
        anonymized_name: str,
        anonymized_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Irreversibly scrubs direct identifiers and credentials from the user profile,
        retaining minimal technical linkage (is_anonymized=True).
        """
        user = self._users.get(user_id)
        if not user:
            return None

        user["full_name"] = anonymized_name
        user["email"] = anonymized_email
        user["phone_number"] = None
        user["shipping_address"] = None
        user["password_hash"] = None
        user["salt"] = None
        user["password_reset_token"] = None
        user["security_question"] = None
        user["security_answer_hash"] = None
        user["internal_notes"] = "[REDACTED - RIGHT TO ERASURE]"
        user["is_anonymized"] = True
        return user

    def delete_settings(self, user_id: str) -> bool:
        """Deletes user preferences/settings completely (DELETE policy)."""
        if user_id in self._settings:
            del self._settings[user_id]
            return True
        return False

    def delete_activity_history(self, user_id: str) -> int:
        """Purges user activity history logs (DELETE policy). Returns deleted items count."""
        initial_len = len(self._activity)
        self._activity = [act for act in self._activity if act["user_id"] != user_id]
        return initial_len - len(self._activity)

    def revoke_consents_on_erasure(self, user_id: str, timestamp: str) -> int:
        """Revokes all GDPR consents and marks them as terminated upon erasure (ANONYMIZE/REVOKE policy)."""
        revoked_count = 0
        for consent in self._consents:
            if consent["user_id"] == user_id:
                consent["is_granted"] = False
                consent["revoked_at"] = timestamp
                consent["status"] = "REVOKED_UPON_ERASURE"
                consent["source"] = "RIGHT_TO_ERASURE_WORKFLOW"
                revoked_count += 1
        return revoked_count

    def retain_and_anonymize_orders(self, user_id: str) -> int:
        """
        Preserves commercial and financial order records for legal tax/accounting retention (RETAIN policy),
        while ensuring referential integrity to the anonymized user.
        Returns retained orders count.
        """
        count = 0
        for order in self._orders:
            if order["user_id"] == user_id:
                order["is_customer_anonymized"] = True
                count += 1
        return count


# Shared repository singleton instance for live runtime consistency
_default_repository: Optional[UserDataRepository] = None


def get_default_repository() -> UserDataRepository:
    """Returns the shared UserDataRepository instance."""
    global _default_repository
    if _default_repository is None:
        _default_repository = UserDataRepository()
    return _default_repository


def reset_default_repository() -> UserDataRepository:
    """Resets repository data for isolated test executions."""
    global _default_repository
    _default_repository = UserDataRepository()
    return _default_repository

