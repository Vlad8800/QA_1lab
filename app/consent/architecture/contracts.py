"""Structural interfaces isolate workflows from concrete service signatures."""

from typing import Protocol

from app.anonymization.schemas import AnonymizationResponse
from app.consent.schemas import (
    ConsentPurpose, ConsentRecord, ConsentResponse, MarketingDispatchResult,
)
from app.export.schemas import PersonalDataExportResponse


class ConsentPort(Protocol):
    def list(self, subject_id: str, actor_id: str, role: str) -> list[ConsentRecord]: ...

    def grant(
        self, subject_id: str, purpose: ConsentPurpose, version: str,
        source: str, actor_id: str, role: str, correlation_id: str | None,
    ) -> ConsentResponse: ...

    def revoke(
        self, subject_id: str, purpose: ConsentPurpose, source: str,
        actor_id: str, role: str, correlation_id: str | None,
    ) -> ConsentResponse: ...


class MarketingPort(Protocol):
    def dispatch(
        self, recipient_user_id: str, campaign_name: str, correlation_id: str | None,
    ) -> MarketingDispatchResult: ...


class ExportPort(Protocol):
    def export_user_data(
        self, subject_id: str, authenticated_actor_id: str, actor_role: str = "user",
    ) -> PersonalDataExportResponse: ...


class ErasurePort(Protocol):
    def anonymize_user(
        self, subject_id: str, authenticated_actor_id: str,
        actor_role: str = "user", correlation_id: str | None = None,
    ) -> AnonymizationResponse: ...
