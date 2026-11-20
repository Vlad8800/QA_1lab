"""
FastAPI Router for GDPR Article 17 Right to Erasure & Anonymization Workflow.
Endpoints:
- POST /api/users/{id}/anonymize
- DELETE /api/users/{id}
- POST /api/v1/users/{id}/anonymize
- GET /api/users/{id}/anonymize/verify (diagnostic verification endpoint)
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status

from app.anonymization.schemas import (
    AnonymizationRequest,
    AnonymizationResponse,
    ErasureVerificationResult,
)
from app.anonymization.service import (
    AnonymizationAccessDeniedException,
    AnonymizationWorkflowService,
    SubjectNotFoundException,
)
from app.export.routes import _resolve_authenticated_principal

router = APIRouter(tags=["GDPR Anonymization & Erasure"])

# Shared service instance using common repository
anonymization_service = AnonymizationWorkflowService()


@router.post(
    "/api/users/{id}/anonymize",
    response_model=AnonymizationResponse,
    summary="Execute Right to Erasure / Anonymization workflow (GDPR Art. 17)",
)
@router.post(
    "/api/v1/users/{id}/anonymize",
    response_model=AnonymizationResponse,
    summary="Execute Right to Erasure / Anonymization workflow (GDPR Art. 17 - Versioned)",
)
@router.delete(
    "/api/users/{id}",
    response_model=AnonymizationResponse,
    summary="Execute Right to Erasure / Anonymization via DELETE HTTP method",
)
def anonymize_user_endpoint(
    id: str,
    payload: Optional[AnonymizationRequest] = None,
    x_actor_id: Optional[str] = Header(None, description="Authenticated actor user ID"),
    x_actor_role: Optional[str] = Header("user", description="Actor authorization role (user, admin, dpo)"),
    authorization: Optional[str] = Header(None, description="Bearer token authentication header"),
    x_correlation_id: Optional[str] = Header(None, description="Trace correlation ID"),
):
    """
    Executes compliant anonymization workflow for the specified user ID:
    - IDOR protection: User can only trigger for themselves, or DPO/admin role required.
    - Scrambles direct identifiers into non-reversible values.
    - Purges preferences and activity history.
    - Retains tax/invoicing records without orphan rows.
    - Idempotent: Subsequent calls return ALREADY_ANONYMIZED safely.
    """
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)

    try:
        result = anonymization_service.anonymize_user(
            subject_id=id,
            authenticated_actor_id=actor_id,
            actor_role=role,
            correlation_id=x_correlation_id,
        )
        return result

    except AnonymizationAccessDeniedException as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except SubjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )


@router.get(
    "/api/users/{id}/anonymize/verify",
    response_model=ErasureVerificationResult,
    summary="Verify that erasure guarantees and referential integrity are satisfied",
)
def verify_erasure_endpoint(
    id: str,
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header("user"),
    authorization: Optional[str] = Header(None),
):
    """
    Diagnostic verification check endpoint confirming zero PII leakage and retention rules.
    """
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)

    # Only owner or DPO/Admin can verify
    if actor_id != id and role.lower() not in {"admin", "dpo", "data_protection_officer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot verify erasure status of another user."
        )

    try:
        return anonymization_service.verify_erasure(id)
    except SubjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )

