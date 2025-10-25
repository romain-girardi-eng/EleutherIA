import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% of requests under 5s
    errors: ['rate<0.1'],              // Error rate under 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export default function () {
  // GraphRAG query test
  const payload = JSON.stringify({
    query: 'What did Chrysippus think about fate and free will?',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  };

  const response = http.post(`${BASE_URL}/api/graphrag/query`, payload, params);

  const success = check(response, {
    'status is 200': (r) => r.status === 200 || r.status === 401,
    'response has answer': (r) => r.status === 200 ? r.json('answer') !== undefined : true,
    'response time < 5s': (r) => r.timings.duration < 5000,
  });

  errorRate.add(!success);

  sleep(1);
}
