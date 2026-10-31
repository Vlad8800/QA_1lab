"""Architecture experiment: the same consent scenario survives decomposition."""

from app.anonymization.service import AnonymizationWorkflowService
from app.consent.architecture.adapter import ConsentServiceAdapter
from app.consent.architecture.workflows import ConsentWorkflow, ErasureWorkflow, ExportWorkflow, MarketingWorkflow
from app.consent.gate import ConsentPolicyGate
from app.consent.schemas import ConsentPurpose, GrantConsentRequest
from app.consent.service import ConsentManagementService
from app.export.repository import UserDataRepository
from app.export.service import PersonalDataExportService


def test_privacy_workflow_grant_then_dispatch():
    repository = UserDataRepository()
    gate = ConsentPolicyGate(repository)
    consent = ConsentManagementService(repository, gate)
    adapter = ConsentServiceAdapter(consent)
    consent_workflow = ConsentWorkflow(adapter)
    marketing_workflow = MarketingWorkflow(adapter)
    request = GrantConsentRequest(
        purpose=ConsentPurpose.MARKETING_EMAIL,
        policy_version="v1.2",
        source="LAB8_ARCHITECTURE_TEST",
    )

    granted = consent_workflow.grant_consent(
        "usr_103", request.purpose, request.policy_version, request.source, "usr_103",
    )
    dispatched = marketing_workflow.dispatch("usr_103", "Lab 8 campaign")

    assert granted.is_granted is True
    assert dispatched.dispatched is True
    assert gate.evaluate_access("usr_103", ConsentPurpose.MARKETING_EMAIL).decision.value == "ALLOW"


def test_data_rights_workflow_uses_separate_export_and_erasure_ports():
    repository = UserDataRepository()
    exporter = ExportWorkflow(PersonalDataExportService(repository))
    eraser = ErasureWorkflow(AnonymizationWorkflowService(repository))

    exported = exporter.export("usr_103", "usr_103")
    erased = eraser.erase("usr_103", "usr_103")

    assert exported.subject_id == "usr_103"
    assert erased.subject_id == "usr_103"
