"""Architecture experiment: the same consent scenario survives decomposition."""

from app.consent.gate import ConsentPolicyGate
from app.consent.privacy_god_object import PrivacyOperationsGodObject
from app.consent.schemas import ConsentPurpose, GrantConsentRequest
from app.consent.service import ConsentManagementService
from app.export.repository import UserDataRepository


def test_privacy_workflow_grant_then_dispatch():
    repository = UserDataRepository()
    gate = ConsentPolicyGate(repository)
    consent = ConsentManagementService(repository, gate)
    workflow = PrivacyOperationsGodObject(repository, gate, consent)
    request = GrantConsentRequest(
        purpose=ConsentPurpose.MARKETING_EMAIL,
        policy_version="v1.2",
        source="LAB8_ARCHITECTURE_TEST",
    )

    granted = workflow.grant("usr_103", "usr_103", request)
    dispatched = workflow.dispatch("usr_103", "Lab 8 campaign")

    assert granted.is_granted is True
    assert dispatched.dispatched is True
    assert workflow.is_allowed(workflow.check_policy("usr_103", ConsentPurpose.MARKETING_EMAIL))
