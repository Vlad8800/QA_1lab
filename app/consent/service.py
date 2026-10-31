"""Stable public consent API composed from focused operations (lab 8 PASS)."""

from typing import Optional

from app.consent.gate import ConsentPolicyGate, get_policy_gate
from app.consent.schemas import ConsentPurpose
from app.consent.architecture.errors import ConsentAccessDeniedException, SubjectNotFoundException
from app.consent.architecture.operations import (
    ConsentAuthorization, ConsentReadOperations, ConsentWriteOperations, MarketingOperations,
)
from app.export.repository import UserDataRepository, get_default_repository


class ConsentManagementService:
    """Compatibility facade; business decisions live in focused components."""

    def __init__(self, repository: Optional[UserDataRepository] = None, policy_gate: Optional[ConsentPolicyGate] = None):
        self._custom_repository = repository
        self._custom_gate = policy_gate
        authorization = ConsentAuthorization()
        self._reader = ConsentReadOperations(lambda: self.repository, authorization)
        self._writer = ConsentWriteOperations(lambda: self.repository, lambda: self.gate, authorization)
        self._marketing = MarketingOperations(lambda: self.gate)

    @property
    def repository(self) -> UserDataRepository:
        return self._custom_repository if self._custom_repository is not None else get_default_repository()

    @property
    def gate(self) -> ConsentPolicyGate:
        return self._custom_gate if self._custom_gate is not None else get_policy_gate()

    def get_user_consents(self, subject_id: str, authenticated_actor_id: str, actor_role: str = "user"):
        return self._reader.get_user_consents(subject_id, authenticated_actor_id, actor_role)

    def grant_consent(self, subject_id: str, purpose: ConsentPurpose, agreement_version: str, source: str, authenticated_actor_id: str, actor_role: str = "user", correlation_id: Optional[str] = None):
        return self._writer.grant_consent(
            subject_id, purpose, agreement_version, source, authenticated_actor_id,
            actor_role, correlation_id,
        )

    def revoke_consent(self, subject_id: str, purpose: ConsentPurpose, source: str, authenticated_actor_id: str, actor_role: str = "user", correlation_id: Optional[str] = None):
        return self._writer.revoke_consent(
            subject_id, purpose, source, authenticated_actor_id, actor_role, correlation_id,
        )

    def dispatch_marketing_email(self, recipient_user_id: str, campaign_name: str, correlation_id: Optional[str] = None):
        return self._marketing.dispatch_marketing_email(recipient_user_id, campaign_name, correlation_id)
