import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '1m', target: 200 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    errors: ['rate<0.02'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test different KG endpoints
  const endpoints = [
    '/api/kg/nodes?type=person&limit=50',
    '/api/kg/nodes?school=Stoic&limit=50',
    '/api/kg/edges?relation=refutes&limit=50',
    '/api/kg/stats',
    '/api/health',
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const response = http.get(`${BASE_URL}${endpoint}`);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has data': (r) => r.body.length > 0,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);

  sleep(0.3);
}
