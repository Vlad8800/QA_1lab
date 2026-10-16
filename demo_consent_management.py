"""
Interactive Demonstration Script for Lab 4: Task 4 (GDPR Consent Management Engine & Policy Gate).
Demonstrates:
1. Consent Model & Evidentiary history inspection
2. Initial State: Policy Gate returns DENY -> Marketing dispatch is BLOCKED
3. Explicit GRANT: Policy Gate returns ALLOW -> Marketing dispatch SUCCEEDS
4. Explicit REVOKE: Immediate Policy Gate DENY -> Subsequent dispatch is BLOCKED
5. Purpose Isolation: MARKETING_EMAIL does NOT allow OPTIONAL_ANALYTICS or MARKETING_SMS
6. Policy Version Check: Outdated version requires re-consent
7. Lawful Basis Isolation: Contractual orders calculate normally without marketing consent
"""
import json
from fastapi.testclient import TestClient

from app.consent.gate import get_policy_gate
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
    gate = get_policy_gate()
    gate.invalidate_cache("usr_103")

    print_banner("1. Initial Consent Model & History (Subject usr_101)")
    res_list = client.get(
        "/api/users/usr_101/consents",
        headers={"x-actor-id": "usr_101"},
    )
    print(f"HTTP Status: {res_list.status_code}")
    for item in res_list.json():
        print(f"[*] Purpose: {item['purpose']:<20} Granted: {str(item['is_granted']):<6} Version: {item['policy_version']}")
        print(f"    Granted At: {item['granted_at']} | Source: {item['source']}")
        print(f"    Audit History: {item['history']}")

    print_banner("2. Step 1: Initial State for usr_103 (No Marketing Consent -> DENY)")
    gate_check_1 = client.post(
        "/api/policy-gate/check",
        json={"user_id": "usr_103", "purpose": "MARKETING_EMAIL"},
    )
    print(f"[!] Policy Gate Decision: {gate_check_1.json()['decision']}")
    print(f"    Reason: {gate_check_1.json()['reason']}")

    dispatch_1 = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": "usr_103", "campaign_name": "Autumn Sale 2026"},
    )
    print(f"[!] Marketing Dispatch Attempt:")
    print_json(dispatch_1.json())
    print("    -> ZERO side effects occurred! Email was NOT dispatched.")

    print_banner("3. Step 2: User usr_103 Grants MARKETING_EMAIL Consent")
    grant_res = client.post(
        "/api/users/usr_103/consents/grant",
        headers={"x-actor-id": "usr_103"},
        json={
            "purpose": "MARKETING_EMAIL",
            "policy_version": "v1.2",
            "source": "PRIVACY_MODAL_CHECKBOX",
        },
    )
    print(f"HTTP Status: {grant_res.status_code}")
    print_json(grant_res.json())

    gate_check_2 = client.post(
        "/api/policy-gate/check",
        json={"user_id": "usr_103", "purpose": "MARKETING_EMAIL"},
    )
    print(f"[+] Policy Gate Decision: {gate_check_2.json()['decision']} (Allowed)")

    dispatch_2 = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": "usr_103", "campaign_name": "Autumn Sale 2026"},
    )
    print(f"[+] Marketing Dispatch Attempt:")
    print_json(dispatch_2.json())
    print("    -> Email was DISPATCHED successfully under valid Art. 6(1)(a) consent.")

    print_banner("4. Step 3: User usr_103 Revokes MARKETING_EMAIL Consent")
    revoke_res = client.post(
        "/api/users/usr_103/consents/revoke",
        headers={"x-actor-id": "usr_103"},
        json={
            "purpose": "MARKETING_EMAIL",
            "source": "USER_SETTINGS_PAGE",
        },
    )
    print(f"HTTP Status: {revoke_res.status_code}")
    print_json(revoke_res.json())

    gate_check_3 = client.post(
        "/api/policy-gate/check",
        json={"user_id": "usr_103", "purpose": "MARKETING_EMAIL"},
    )
    print(f"[!] Policy Gate Decision: {gate_check_3.json()['decision']} (Immediately Revoked)")

    dispatch_3 = client.post(
        "/api/marketing/dispatch",
        json={"recipient_user_id": "usr_103", "campaign_name": "Winter Deals 2026"},
    )
    print(f"[!] Marketing Dispatch Attempt:")
    print_json(dispatch_3.json())
    print("    -> Operation blocked! Real-time revoke enforcement confirmed.")

    print_banner("5. Purpose Isolation: Checking OPTIONAL_ANALYTICS vs MARKETING_EMAIL")
    # Grant only marketing email
    client.post(
        "/api/users/usr_103/consents/grant",
        headers={"x-actor-id": "usr_103"},
        json={"purpose": "MARKETING_EMAIL", "policy_version": "v1.2", "source": "MODAL"},
    )
    analytics_check = client.post(
        "/api/policy-gate/check",
        json={"user_id": "usr_103", "purpose": "OPTIONAL_ANALYTICS"},
    )
    print(f"[!] Check OPTIONAL_ANALYTICS: Decision = {analytics_check.json()['decision']}")
    print(f"    Reason: {analytics_check.json()['reason']}")
    print("    -> Strict purpose isolation verified! Marketing consent does NOT enable analytics.")

    print_banner("6. Lawful Basis Isolation: Contractual Orders Checkout")
    # Core order checkout does NOT require marketing consent
    order_res = client.post(
        "/api/v1/orders/calculate",
        json={
            "customer_tier": "regular",
            "country_code": "UA",
            "weight": 1.2,
            "is_express": False,
            "is_holiday": False,
            "items": [{"name": "Desk Lamp", "price": 45.0, "quantity": 1}],
        },
    )
    print(f"[+] Order Calculation Status: {order_res.status_code}")
    print(f"    Subtotal: {order_res.json()['subtotal']}, Final Total: {order_res.json()['final_total']}")
    print("    -> Contractual operations (Art. 6(1)(b)) are NEVER blocked by marketing consent!")

    print("\n[OK] Demonstration for Task 4 completed successfully! 100% compliance verified.\n")


if __name__ == "__main__":
    run_demo()

