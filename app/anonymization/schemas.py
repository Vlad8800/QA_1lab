"""
Pydantic Schemas for GDPR Article 17 Anonymization / Erasure Workflow.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EntityProcessingSummary(BaseModel):
    action: str = Field(..., description="Action applied: DELETE, ANONYMIZE, RETAIN, or SKIP")
    records_affected: int = Field(..., description="Count of affected rows/documents")
    retention_rationale: Optional[str] = Field(None, description="Legal/technical justification")


class AnonymizationRequest(BaseModel):
    reason: Optional[str] = Field("USER_REQUESTED_ERASURE", description="Reason for erasure")
    confirm_irreversible: bool = Field(True, description="Confirmation that operation is permanent")


class AnonymizationResponse(BaseModel):
    status: str = Field(..., description="Result status: SUCCESS, ALREADY_ANONYMIZED, or FAILED")
    subject_id: str = Field(..., description="Identifier of the subject")
    anonymized_at: str = Field(..., description="ISO 8601 UTC timestamp of execution")
    correlation_id: str = Field(..., description="Audit trace correlation identifier")
    processed_entities: Dict[str, EntityProcessingSummary] = Field(..., description="Breakdown of actions applied per entity")
    technical_summary: str = Field(..., description="Summary explanation of referential integrity and data scrubbing")


class ErasureVerificationResult(BaseModel):
    subject_id: str
    is_profile_anonymized: bool
    email_is_anonymized: bool
    direct_pii_cleared: bool
    security_fields_cleared: bool
    settings_deleted: bool
    activity_deleted: bool
    consents_revoked: bool
    orders_retained: bool
    orders_count: int
    referential_integrity_intact: bool

