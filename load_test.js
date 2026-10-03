import http from 'k6/http';
import { check, sleep } from 'k6';

// 1. Формалізація числових SLO відповідно до ISO/IEC 25010
export const options = {
thresholds: {
  http_req_duration: ['p(95)<200'],
  http_req_failed: ['rate<0.01'],
},

  // 2. Модель навантаження
  // РЕЖИМ 1 (Нормальне навантаження -> PASS): 15 віртуальних користувачів протягом 30 секунд
  stages: [
    { duration: '5s', target: 15 },   // Ramp-up (плавний розгін)
    { duration: '20s', target: 15 },  // Steady state (стабільна робота)
    { duration: '5s', target: 0 },    // Ramp-down (завершення)
  ],

  /* 
  // РЕЖИМ 2 (Підвищене навантаження для фіксації FAIL):
  // Розкоментуйте цей блок замість верхнього stages, щоб гарантовано отримати FAIL за p95 / throughput
  stages: [
    { duration: '5s', target: 150 },
    { duration: '20s', target: 150 },
    { duration: '5s', target: 0 },
  ],
  */
};

// Базова URL-адреса вашого запущеного локального сервісу
const BASE_URL = 'http://127.0.0.1:8000/api/v1/orders/calculate';

export default function () {
  // Тіло типового запиту на розрахунок замовлення
  const payload = JSON.stringify({
    customer_tier: 'gold',
    country_code: 'UA',
    weight: 2.5,
    is_express: false,
    is_holiday: false,
    items: [
      {
        name: 'Wireless Mouse',
        price: 25.0,
        quantity: 2,
      },
      {
        name: 'USB-C Cable',
        price: 10.0,
        quantity: 1,
      },
    ],
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Виконання HTTP POST-запиту
  const response = http.post(BASE_URL, payload, params);

  // Валідація коректності відповіді сервісу
  check(response, {
    'status is 200': (r) => r.status === 200,
    'total is correct': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'success' && body.final_total > 0;
      } catch (e) {
        return false;
      }
    },
  });

  // Пауза між запитами одного віртуального користувача (імітація реального клієнта)
  sleep(0.05);
}