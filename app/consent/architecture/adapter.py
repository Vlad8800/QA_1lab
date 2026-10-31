"""One boundary translates stable consent contracts to the concrete service."""

from app.consent.schemas import ConsentPurpose
from app.consent.service import ConsentManagementService


class ConsentServiceAdapter:
    def __init__(self, service: ConsentManagementService):
        self._service = service

    def list(self, subject_id, actor_id, role):
        return self._service.get_user_consents(subject_id, actor_id, role)

    def grant(self, subject_id, purpose: ConsentPurpose, version, source, actor_id, role, correlation_id):
        return self._service.grant_consent(
            subject_id=subject_id, purpose=purpose, agreement_version=version,
            source=source, authenticated_actor_id=actor_id,
            actor_role=role, correlation_id=correlation_id,
        )

    def revoke(self, subject_id, purpose: ConsentPurpose, source, actor_id, role, correlation_id):
        return self._service.revoke_consent(
            subject_id=subject_id, purpose=purpose, source=source,
            authenticated_actor_id=actor_id, actor_role=role,
            correlation_id=correlation_id,
        )

    def dispatch(self, recipient_user_id, campaign_name, correlation_id):
        return self._service.dispatch_marketing_email(recipient_user_id, campaign_name, correlation_id)
