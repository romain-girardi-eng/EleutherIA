import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const queries = [
  'liberum arbitrium',
  'ἐφ\' ἡμῖν',
  'Stoic determinism',
  'Aristotle voluntary action',
  'Augustine free will',
];

export default function () {
  const query = queries[Math.floor(Math.random() * queries.length)];

  const payload = JSON.stringify({
    query: query,
    limit: 10,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post(`${BASE_URL}/api/search/hybrid`, payload, params);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => r.json('results') !== undefined,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });

  errorRate.add(!success);

  sleep(0.5);
}
