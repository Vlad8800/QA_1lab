"""
GDPR Consent Management Package.
"""
from app.consent.gate import ConsentPolicyGate, get_policy_gate
from app.consent.routes import consent_service, policy_gate, router as consent_router
from app.consent.schemas import (
    ConsentPurpose,
    ConsentRecord,
    ConsentResponse,
    ConsentStatus,
    GrantConsentRequest,
    MarketingDispatchResult,
    PolicyGateCheckRequest,
    PolicyGateDecision,
    PolicyGateResult,
    ProcessingLawfulBasis,
    RevokeConsentRequest,
)
from app.consent.service import (
    ConsentAccessDeniedException,
    ConsentManagementService,
    SubjectNotFoundException,
)

__all__ = [
    "ConsentPurpose",
    "ConsentStatus",
    "ProcessingLawfulBasis",
    "PolicyGateDecision",
    "ConsentRecord",
    "GrantConsentRequest",
    "RevokeConsentRequest",
    "ConsentResponse",
    "PolicyGateCheckRequest",
    "PolicyGateResult",
    "MarketingDispatchResult",
    "ConsentAccessDeniedException",
    "SubjectNotFoundException",
    "ConsentPolicyGate",
    "get_policy_gate",
    "ConsentManagementService",
    "consent_service",
    "policy_gate",
    "consent_router",
]

