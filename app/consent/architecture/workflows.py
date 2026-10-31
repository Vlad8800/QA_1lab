"""Three independent privacy responsibilities with constructor-injected ports."""

from app.anonymization.schemas import AnonymizationResponse
from app.consent.architecture.contracts import ConsentPort, ErasurePort, ExportPort, MarketingPort
from app.consent.schemas import (
    ConsentPurpose, ConsentRecord, ConsentResponse, MarketingDispatchResult,
)
from app.export.schemas import PersonalDataExportResponse


class ConsentWorkflow:
    """Read and change consent; knows only the consent contract."""

    def __init__(self, consent: ConsentPort):
        self._consent = consent

    def get_user_consents(self, subject_id: str, authenticated_actor_id: str, actor_role: str = "user") -> list[ConsentRecord]:
        return self._consent.list(subject_id, authenticated_actor_id, actor_role)

    def grant_consent(
        self, subject_id: str, purpose: ConsentPurpose, policy_version: str,
        source: str, authenticated_actor_id: str, actor_role: str = "user",
        correlation_id: str | None = None,
    ) -> ConsentResponse:
        return self._consent.grant(
            subject_id, purpose, policy_version, source,
            authenticated_actor_id, actor_role, correlation_id,
        )

    def revoke_consent(
        self, subject_id: str, purpose: ConsentPurpose, source: str,
        authenticated_actor_id: str, actor_role: str = "user",
        correlation_id: str | None = None,
    ) -> ConsentResponse:
        return self._consent.revoke(
            subject_id, purpose, source, authenticated_actor_id, actor_role, correlation_id,
        )


class MarketingWorkflow:
    """Dispatch marketing through its own narrow contract."""

    def __init__(self, marketing: MarketingPort):
        self._marketing = marketing

    def dispatch(self, recipient_user_id: str, campaign_name: str, correlation_id: str | None = None) -> MarketingDispatchResult:
        return self._marketing.dispatch(recipient_user_id, campaign_name, correlation_id)


class ExportWorkflow:
    """Serve a subject's export request through an injected export contract."""

    def __init__(self, exporter: ExportPort):
        self._exporter = exporter

    def export(self, subject_id: str, actor_id: str) -> PersonalDataExportResponse:
        return self._exporter.export_user_data(subject_id, actor_id)


class ErasureWorkflow:
    """Serve a subject's erasure request through an injected erasure contract."""

    def __init__(self, eraser: ErasurePort):
        self._eraser = eraser

    def erase(self, subject_id: str, actor_id: str) -> AnonymizationResponse:
        return self._eraser.anonymize_user(subject_id, actor_id)
