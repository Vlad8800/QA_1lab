"""
Data schemas for Personal Data Export according to GDPR Article 15 (Right of Access).
Strictly minimizes data by excluding security-sensitive fields (hashes, tokens, antifraud flags).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UserProfileExport(BaseModel):
    """Personal profile data provided by or collected about the user."""
    full_name: str
    email: str
    phone_number: Optional[str] = None
    shipping_address: Optional[str] = None
    registered_at: str
    locale: str = "uk-UA"


class UserSettingsExport(BaseModel):
    """User preferences and account settings."""
    language: str = "uk"
    theme: str = "light"
    email_notifications_enabled: bool = True
    sms_notifications_enabled: bool = False
    currency: str = "UAH"


class UserActivityItem(BaseModel):
    """Audit item representing user's interaction history with the system."""
    activity_id: str
    timestamp: str
    action: str
    resource: str
    status: str


class UserOrderItem(BaseModel):
    """Transactional order record associated with the user."""
    order_id: str
    created_at: str
    status: str
    total_amount: float
    currency: str = "UAH"
    items_count: int


class UserConsentItem(BaseModel):
    """GDPR consent record associated with the user."""
    consent_id: str
    purpose: str
    is_granted: bool
    policy_version: str
    updated_at: str
    source: str


class DocumentedOmission(BaseModel):
    """Explains intentional absence of categories (e.g. no transactional history)."""
    category: str
    reason: str
    status: str = "EMPTY_OR_NOT_APPLICABLE"


class PersonalDataExportResponse(BaseModel):
    """
    Standardized, versioned JSON contract for GDPR Article 15 Personal Data Export.
    Contains metadata, subject identifier, data categories, and isolated sections.
    """
    schema_version: str = Field(default="1.0.0", description="SemVer contract schema version")
    export_id: str = Field(..., description="Unique traceability identifier for this export package")
    generated_at: str = Field(..., description="ISO-8601 UTC timestamp of export generation")
    subject_id: str = Field(..., description="Unique subject identifier (user_id)")
    data_categories: List[str] = Field(..., description="Inventory of data categories included in export")
    
    # Structured data sections
    profile: Optional[UserProfileExport] = None
    settings: Optional[UserSettingsExport] = None
    activity_history: List[UserActivityItem] = Field(default_factory=list)
    orders: List[UserOrderItem] = Field(default_factory=list)
    consents: List[UserConsentItem] = Field(default_factory=list)
    
    # Predictable documented omissions instead of silent missing fields
    documented_omissions: List[DocumentedOmission] = Field(default_factory=list)

