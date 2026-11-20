"""
Domain Models and Enums for GDPR Consent Management Engine (GDPR Art. 6(1)(a) & Art. 7).
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConsentPurpose(str, Enum):
    MARKETING_EMAIL = "MARKETING_EMAIL"
    MARKETING_SMS = "MARKETING_SMS"
    OPTIONAL_ANALYTICS = "OPTIONAL_ANALYTICS"
    THIRD_PARTY_SHARING = "THIRD_PARTY_SHARING"


class ConsentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    REVOKED_UPON_ERASURE = "REVOKED_UPON_ERASURE"


class ProcessingLawfulBasis(str, Enum):
    """GDPR Art. 6 Lawful bases for data processing."""
    CONSENT = "CONSENT"  # Art. 6(1)(a) - requires Policy Gate check
    CONTRACT = "CONTRACT"  # Art. 6(1)(b) - core order processing, does NOT require marketing consent
    LEGAL_OBLIGATION = "LEGAL_OBLIGATION"  # Art. 6(1)(c) - accounting/tax records
    LEGITIMATE_INTEREST = "LEGITIMATE_INTEREST"  # Art. 6(1)(f) - security/fraud prevention


class PolicyGateDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class ConsentRecord(BaseModel):
    consent_id: str
    user_id: str
    purpose: ConsentPurpose
    is_granted: bool
    status: ConsentStatus
    policy_version: str
    granted_at: Optional[str] = None
    withdrawn_at: Optional[str] = None
    updated_at: str
    source: str
    history: List[Dict[str, Any]] = Field(default_factory=list)


class GrantConsentRequest(BaseModel):
    purpose: ConsentPurpose
    policy_version: str = Field(default="v1.2", description="Privacy policy version consented to")
    source: str = Field(default="USER_DASHBOARD", description="Channel/Touchpoint of consent capture")


class RevokeConsentRequest(BaseModel):
    purpose: ConsentPurpose
    source: str = Field(default="USER_DASHBOARD", description="Channel/Touchpoint of consent withdrawal")


class ConsentResponse(BaseModel):
    consent_id: str
    user_id: str
    purpose: ConsentPurpose
    is_granted: bool
    status: ConsentStatus
    policy_version: str
    granted_at: Optional[str] = None
    withdrawn_at: Optional[str] = None
    updated_at: str
    source: str
    message: str


class PolicyGateCheckRequest(BaseModel):
    user_id: str
    purpose: ConsentPurpose
    required_policy_version: Optional[str] = None


class PolicyGateResult(BaseModel):
    decision: PolicyGateDecision
    reason: str
    user_id: str
    purpose: ConsentPurpose
    policy_version_checked: Optional[str] = None
    evaluated_at: str
    correlation_id: str


class MarketingDispatchResult(BaseModel):
    status: str
    dispatched: bool
    recipient_id: str
    channel: str
    campaign_name: str
    gate_decision: PolicyGateDecision
    rejection_reason: Optional[str] = None

