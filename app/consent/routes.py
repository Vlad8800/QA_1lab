"""
FastAPI Router for GDPR Consent Management Engine (Art. 6 & Art. 7).
Endpoints:
- GET /api/users/{id}/consents (List all consents)
- POST /api/users/{id}/consents/grant (GRANT specific consent)
- POST /api/users/{id}/consents/revoke (REVOKE specific consent)
- POST /api/policy-gate/check (Evaluate policy gate without side-effects)
- POST /api/marketing/dispatch (Simulate consent-dependent marketing operation)
"""
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.consent.gate import get_policy_gate
from app.consent.schemas import (
    ConsentPurpose,
    ConsentRecord,
    ConsentResponse,
    GrantConsentRequest,
    MarketingDispatchResult,
    PolicyGateCheckRequest,
    PolicyGateResult,
    RevokeConsentRequest,
)
from app.consent.service import (
    ConsentAccessDeniedException,
    ConsentManagementService,
    SubjectNotFoundException,
)
from app.export.routes import _resolve_authenticated_principal

router = APIRouter(tags=["GDPR Consent Management & Policy Gate"])

# Shared service instances
consent_service = ConsentManagementService()
policy_gate = get_policy_gate()


class MarketingCampaignRequest(BaseModel):
    recipient_user_id: str
    campaign_name: str = Field(default="Spring Special Offer 2026")


@router.get(
    "/api/users/{id}/consents",
    response_model=List[ConsentRecord],
    summary="List all purpose-specific consents for subject with audit history",
)
def list_user_consents_endpoint(
    id: str,
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header("user"),
    authorization: Optional[str] = Header(None),
):
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)
    try:
        return consent_service.get_user_consents(id, actor_id, role)
    except ConsentAccessDeniedException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except SubjectNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/api/users/{id}/consents/grant",
    response_model=ConsentResponse,
    summary="Grant specific consent (GDPR Art. 6(1)(a))",
)
def grant_consent_endpoint(
    id: str,
    payload: GrantConsentRequest,
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header("user"),
    authorization: Optional[str] = Header(None),
    x_correlation_id: Optional[str] = Header(None),
):
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)
    try:
        return consent_service.grant_consent(
            subject_id=id,
            purpose=payload.purpose,
            policy_version=payload.policy_version,
            source=payload.source,
            authenticated_actor_id=actor_id,
            actor_role=role,
            correlation_id=x_correlation_id,
        )
    except ConsentAccessDeniedException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except SubjectNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/api/users/{id}/consents/revoke",
    response_model=ConsentResponse,
    summary="Revoke specific consent (GDPR Art. 7(3))",
)
def revoke_consent_endpoint(
    id: str,
    payload: RevokeConsentRequest,
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header("user"),
    authorization: Optional[str] = Header(None),
    x_correlation_id: Optional[str] = Header(None),
):
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)
    try:
        return consent_service.revoke_consent(
            subject_id=id,
            purpose=payload.purpose,
            source=payload.source,
            authenticated_actor_id=actor_id,
            actor_role=role,
            correlation_id=x_correlation_id,
        )
    except ConsentAccessDeniedException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except SubjectNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/api/policy-gate/check",
    response_model=PolicyGateResult,
    summary="Evaluate Policy Gate directly without side effects",
)
def check_policy_gate_endpoint(
    payload: PolicyGateCheckRequest,
    x_correlation_id: Optional[str] = Header(None),
):
    return policy_gate.evaluate_access(
        user_id=payload.user_id,
        purpose=payload.purpose,
        required_policy_version=payload.required_policy_version,
        correlation_id=x_correlation_id,
    )


@router.post(
    "/api/marketing/dispatch",
    response_model=MarketingDispatchResult,
    summary="Execute business operation conditioned on MARKETING_EMAIL consent",
)
def dispatch_marketing_campaign_endpoint(
    payload: MarketingCampaignRequest,
    x_correlation_id: Optional[str] = Header(None),
):
    """
    Business action demonstrating that the Policy Gate actually governs execution.
    If consent is revoked or missing, returns DENIED_BY_POLICY_GATE with no side effects.
    """
    return consent_service.dispatch_marketing_email(
        recipient_user_id=payload.recipient_user_id,
        campaign_name=payload.campaign_name,
        correlation_id=x_correlation_id,
    )

