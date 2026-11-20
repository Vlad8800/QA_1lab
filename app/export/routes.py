"""
FastAPI Router for GDPR Article 15 Personal Data Export.
Endpoints:
- GET /api/users/{id}/personal-data
- GET /api/v1/users/{id}/personal-data
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status

from app.export.schemas import PersonalDataExportResponse
from app.export.service import (
    AccessDeniedException,
    PersonalDataExportService,
    SubjectNotFoundException,
)

router = APIRouter(tags=["GDPR Personal Data Export"])

# Global shared service instance
export_service = PersonalDataExportService()


def _resolve_authenticated_principal(
    x_actor_id: Optional[str] = Header(None, description="Authenticated actor user ID"),
    x_actor_role: Optional[str] = Header("user", description="Actor authorization role (user, admin, dpo)"),
    authorization: Optional[str] = Header(None, description="Bearer token authentication header"),
) -> tuple[str, str]:
    """
    Extracts authenticated user identity from security context.
    Supports either direct actor headers or Bearer tokens.
    """
    actor_id = x_actor_id
    role = x_actor_role or "user"

    if not actor_id and authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            # Simple bearer convention: token_usr_101 or usr_101
            actor_id = token.replace("token_", "").replace("_token", "")

    if not actor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    return actor_id, role


@router.get(
    "/api/users/{id}/personal-data",
    response_model=PersonalDataExportResponse,
    summary="Export all personal data for subject (GDPR Art. 15)",
)
@router.get(
    "/api/v1/users/{id}/personal-data",
    response_model=PersonalDataExportResponse,
    summary="Export all personal data for subject (GDPR Art. 15 - Versioned)",
)
def export_personal_data_endpoint(
    id: str,
    x_actor_id: Optional[str] = Header(None),
    x_actor_role: Optional[str] = Header("user"),
    authorization: Optional[str] = Header(None),
):
    """
    Retrieves full personal data export package for the specified user ID.
    Enforces Anti-IDOR validation: requester must match the target user ID unless role is admin/dpo.
    """
    actor_id, role = _resolve_authenticated_principal(x_actor_id, x_actor_role, authorization)

    try:
        export_package = export_service.export_user_data(
            subject_id=id,
            authenticated_actor_id=actor_id,
            actor_role=role,
        )
        return export_package

    except AccessDeniedException as exc:
        # IDOR violation: Controlled rejection without body data or leak
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc)
        )
    except SubjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )

