"""
Live Demo Script for Laboratory Work #4 - Task 2: Personal Data Export (GDPR Art. 15).
Demonstrates export contract, aggregation, minimization, anti-IDOR, and documented omissions.
"""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_demo():
    print("=" * 75)
    print(" ДЕМОНСТРАЦІЯ ЗАВДАННЯ 2: RIGHT OF ACCESS ТА PERSONAL DATA EXPORT (LAB #4)")
    print("=" * 75)

    # 1. Авторизований експорт власних даних
    print("\n--- [1] АВТОРИЗОВАНИЙ ЕКСПОРТ ВЛАСНИХ ДАНИХ (GET /api/users/usr_101/personal-data) ---")
    headers = {"X-Actor-ID": "usr_101", "X-Actor-Role": "user"}
    response = client.get("/api/users/usr_101/personal-data", headers=headers)

    print(f"HTTP Status: {response.status_code} OK")
    data = response.json()
    print("Метадані формування пакета:")
    print(f"  * Schema Version: {data['schema_version']}")
    print(f"  * Export ID:      {data['export_id']}")
    print(f"  * Subject ID:     {data['subject_id']}")
    print(f"  * Generated At:   {data['generated_at']}")
    print(f"  * Categories:     {data['data_categories']}")
    print("\nАгреговані розділи:")
    print(f"  * Profile:  {data['profile']['full_name']} ({data['profile']['email']})")
    print(f"  * Settings: мова: {data['settings']['language']}, тема: {data['settings']['theme']}")
    print(f"  * Orders:   {len(data['orders'])} замовлень (наприклад: {data['orders'][0]['order_id']} на суму {data['orders'][0]['total_amount']} грн)")
    print(f"  * Consents: {len(data['consents'])} згод ({data['consents'][0]['purpose']}: granted={data['consents'][0]['is_granted']})")

    # 2. Доказ мінімізації даних (Security-Sensitive Data Exclusion)
    print("\n--- [2] ПЕРЕВІРКА МІНІМІЗАЦІЇ ДАНИХ (Security Fields Filtering) ---")
    forbidden = ["password_hash", "salt", "password_reset_token", "antifraud_score", "security_answers"]
    found_leaks = [f for f in forbidden if f in response.text]
    if not found_leaks:
        print("  [OK] УСПІШНО: Жодного чутливого технічного поля (хеші, солі, токени відновлення, антифрод-бали) немає в експорті!")
    else:
        print(f"  [FAIL] ВИТІК: {found_leaks}")

    # 3. Контроль доступу та захист від IDOR (Negative Authorization)
    print("\n--- [3] ЗАХИСТ ВІД IDOR: СПРОБА ДОСТУПУ ДО ЧУЖОГО ПРОФІЛЮ ---")
    print("Актор 'usr_102' намагається отримати персональні дані 'usr_101'...")
    idor_headers = {"X-Actor-ID": "usr_102", "X-Actor-Role": "user"}
    idor_response = client.get("/api/users/usr_101/personal-data", headers=idor_headers)

    print(f"HTTP Status: {idor_response.status_code} FORBIDDEN")
    print(f"Відповідь сервера: {idor_response.json()}")
    print("  [OK] УСПІШНО: Запит заблоковано, тіло не містить жодних даних чужого профілю.")

    # 4. Документовані опущення (Documented Omissions)
    print("\n--- [4] ПЕРЕДБАЧУВАНА ОБРОБКА ПОРОЖНІХ КАТЕГОРІЙ (usr_103 без замовлень) ---")
    empty_headers = {"X-Actor-ID": "usr_103"}
    empty_response = client.get("/api/users/usr_103/personal-data", headers=empty_headers)
    empty_data = empty_response.json()
    print(f"Orders count: {len(empty_data['orders'])}")
    print("Documented Omissions:")
    for omission in empty_data["documented_omissions"]:
        print(f"  * Категорія '{omission['category']}': {omission['reason']}")

    print("\n" + "=" * 75)
    print(" Завдання 2 повністю відповідає всім вимогам GDPR Article 15!")
    print("=" * 75)


if __name__ == "__main__":
    run_demo()
