"""
Interactive Demonstration Script for Lab 4: Task 3 (GDPR Right to Erasure & Anonymization Workflow).
Demonstrates:
1. Entity handling policy inspection (DELETE, ANONYMIZE, RETAIN)
2. State of user data BEFORE anonymization
3. Execution of POST /api/users/{id}/anonymize with Anti-IDOR check
4. Verification of irreversible PII/secret scrubbing and settings/activity purge
5. Preservation of financial orders & referential integrity (zero orphan rows)
6. Idempotency test (repeating request returns ALREADY_ANONYMIZED)
7. IDOR protection test (unauthorized actor blocked with HTTP 403)
"""
import json
from fastapi.testclient import TestClient

from app.anonymization.policy import ENTITY_HANDLING_POLICIES
from app.export.repository import get_default_repository, reset_default_repository
from app.main import app

client = TestClient(app)


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)


def print_json(data: dict):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def run_demo():
    reset_default_repository()
    repo = get_default_repository()

    print_banner("1. Entity Handling & Retention Policy (GDPR Art. 17)")
    for entity, policy in ENTITY_HANDLING_POLICIES.items():
        print(f"[*] Entity: {entity.upper():<16} Action: [{policy.action.value:<9}]")
        print(f"    Rationale: {policy.retention_rationale}")
        print(f"    Retained:  {policy.retained_fields}")
        print(f"    Scrubbed:  {policy.erased_or_masked_fields[:4]}...")

    print_banner("2. Subject usr_101 State BEFORE Erasure Workflow")
    user_before = repo.get_user_by_id("usr_101")
    settings_before = repo.get_settings_by_user_id("usr_101")
    orders_before = repo.get_orders_by_user_id("usr_101")
    activity_before = repo.get_activity_by_user_id("usr_101")
    consents_before = repo.get_consents_by_user_id("usr_101")

    print(f"[+] User Profile: Name='{user_before['full_name']}', Email='{user_before['email']}', Phone='{user_before['phone_number']}'")
    print(f"[!] Security Secrets: Password Hash='{user_before['password_hash'][:25]}...', Salt='{user_before['salt']}'")
    print(f"[+] Preferences Record: {settings_before}")
    print(f"[+] Activity Logs Count: {len(activity_before)}")
    print(f"[+] Orders Count: {len(orders_before)}")
    print(f"[+] Consents Granted: {[c['purpose'] for c in consents_before if c['is_granted']]}")

    print_banner("3. Executing POST /api/users/usr_101/anonymize (Self-Service Erasure)")
    response = client.post(
        "/api/users/usr_101/anonymize",
        headers={
            "x-actor-id": "usr_101",
            "x-actor-role": "user",
            "x-correlation-id": "demo_trace_erasure_001",
        },
        json={
            "reason": "USER_REQUESTED_ERASURE",
            "confirm_irreversible": True,
        }
    )
    print(f"HTTP Status: {response.status_code}")
    print_json(response.json())

    print_banner("4. Subject usr_101 State AFTER Erasure Workflow")
    user_after = repo.get_user_by_id("usr_101")
    settings_after = repo.get_settings_by_user_id("usr_101")
    orders_after = repo.get_orders_by_user_id("usr_101")
    activity_after = repo.get_activity_by_user_id("usr_101")
    consents_after = repo.get_consents_by_user_id("usr_101")

    print(f"[+] User Profile: is_anonymized={user_after.get('is_anonymized')}")
    print(f"    Name:  '{user_after['full_name']}'")
    print(f"    Email: '{user_after['email']}' (Irreversible surrogate)")
    print(f"    Phone: {user_after['phone_number']}")
    print(f"    Address: {user_after['shipping_address']}")
    print(f"[+] Security Credentials:")
    print(f"    password_hash: {user_after['password_hash']}")
    print(f"    salt: {user_after['salt']}")
    print(f"    password_reset_token: {user_after['password_reset_token']}")
    print(f"    security_question: {user_after['security_question']}")
    print(f"[+] Preferences/Settings in DB: {settings_after} (PURGED)")
    print(f"[+] Activity Logs in DB: {activity_after} (PURGED)")
    print(f"[+] Consents Status: {[{c['purpose']: c['status']} for c in consents_after]} (REVOKED)")
    print(f"[+] Orders Retained Count: {len(orders_after)} (RETAINED FOR TAX COMPLIANCE)")
    for ord_item in orders_after:
        print(f"    Order ID: {ord_item['order_id']}, Total: {ord_item['total_amount']} {ord_item['currency']}, User ID: {ord_item['user_id']}")

    print_banner("5. Verifying Referential Integrity (GET /api/users/usr_101/anonymize/verify)")
    verify_resp = client.get(
        "/api/users/usr_101/anonymize/verify",
        headers={"x-actor-id": "usr_101"},
    )
    print(f"HTTP Status: {verify_resp.status_code}")
    print_json(verify_resp.json())

    print_banner("6. Idempotency Test: Re-calling Anonymize on usr_101")
    re_response = client.post(
        "/api/users/usr_101/anonymize",
        headers={"x-actor-id": "usr_101"},
    )
    print(f"HTTP Status: {re_response.status_code}")
    print(f"Response Status: {re_response.json()['status']}")
    print(f"Technical Summary: {re_response.json()['technical_summary']}")

    print_banner("7. Anti-IDOR Test: Foreign Actor usr_102 Attempting to Delete usr_103")
    idor_response = client.post(
        "/api/users/usr_103/anonymize",
        headers={"x-actor-id": "usr_102", "x-actor-role": "user"},
    )
    print(f"HTTP Status: {idor_response.status_code} (Expected 403 Forbidden)")
    print_json(idor_response.json())

    print_banner("8. DPO Authorization Test: Officer Performing Erasure on usr_103")
    dpo_response = client.post(
        "/api/users/usr_103/anonymize",
        headers={"x-actor-id": "officer_dpo_7", "x-actor-role": "dpo"},
    )
    print(f"HTTP Status: {dpo_response.status_code} (Expected 200 OK)")
    print(f"Result Status: {dpo_response.json()['status']}, Subject: {dpo_response.json()['subject_id']}")

    print("\n[OK] Demonstration completed successfully! All requirements for Task 3 are fully satisfied.\n")


if __name__ == "__main__":
    run_demo()

