"""Lab 8 baseline: intentionally aggregated privacy workflow for coupling audit."""

from typing import Optional

from app.anonymization.schemas import AnonymizationResponse
from app.anonymization.service import AnonymizationWorkflowService
from app.consent.gate import ConsentPolicyGate, get_policy_gate
from app.consent.schemas import (
    ConsentPurpose, ConsentRecord, ConsentResponse, ConsentStatus,
    GrantConsentRequest, MarketingDispatchResult, PolicyGateDecision,
    PolicyGateResult, RevokeConsentRequest,
)
from app.consent.service import ConsentManagementService
from app.export.repository import UserDataRepository
from app.export.schemas import PersonalDataExportResponse
from app.export.service import PersonalDataExportService


class PrivacyOperationsGodObject:
    """Deliberately combines unrelated GDPR operations for the FAIL experiment.

    This is an intermediate architecture state, not the intended final design.
    """

    def __init__(
        self,
        repository: Optional[UserDataRepository] = None,
        gate: Optional[ConsentPolicyGate] = None,
        consent: Optional[ConsentManagementService] = None,
        exporter: Optional[PersonalDataExportService] = None,
        eraser: Optional[AnonymizationWorkflowService] = None,
    ):
        self.repository = repository
        self.gate = gate or get_policy_gate()
        self.consent = consent or ConsentManagementService(repository, self.gate)
        self.exporter = exporter or PersonalDataExportService(repository)
        self.eraser = eraser or AnonymizationWorkflowService(repository)

    def list_consents(self, user_id: str, actor_id: str) -> list[ConsentRecord]:
        return self.consent.get_user_consents(user_id, actor_id)

    def grant(self, user_id: str, actor_id: str, request: GrantConsentRequest) -> ConsentResponse:
        return self.consent.grant_consent(
            subject_id=user_id,
            purpose=request.purpose,
            policy_version=request.policy_version,
            source=request.source,
            authenticated_actor_id=actor_id,
        )

    def revoke(self, user_id: str, actor_id: str, request: RevokeConsentRequest) -> ConsentResponse:
        return self.consent.revoke_consent(
            subject_id=user_id,
            purpose=request.purpose,
            source=request.source,
            authenticated_actor_id=actor_id,
        )

    def check_policy(self, user_id: str, purpose: ConsentPurpose) -> PolicyGateResult:
        return self.gate.evaluate_access(user_id=user_id, purpose=purpose)

    def dispatch(self, user_id: str, campaign: str, correlation_id: Optional[str] = None) -> MarketingDispatchResult:
        return self.consent.dispatch_marketing_email(user_id, campaign, correlation_id)

    def export(self, user_id: str, actor_id: str) -> PersonalDataExportResponse:
        return self.exporter.export_user_data(user_id, actor_id)

    def erase(self, user_id: str, actor_id: str) -> AnonymizationResponse:
        return self.eraser.anonymize_user(user_id, actor_id)

    def is_active(self, record: ConsentRecord) -> bool:
        return record.status == ConsentStatus.ACTIVE and record.is_granted

    def is_allowed(self, result: PolicyGateResult) -> bool:
        return result.decision == PolicyGateDecision.ALLOW
