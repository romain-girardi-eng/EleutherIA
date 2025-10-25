# Load Testing with k6

## Installation

```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows (via Chocolatey)
choco install k6
```

## Running Tests

### GraphRAG Load Test

```bash
k6 run k6_graphrag_test.js

# With environment variables
BASE_URL=https://yourapi.com AUTH_TOKEN=your-jwt-token k6 run k6_graphrag_test.js
```

### Search Load Test

```bash
k6 run k6_search_test.js

# Custom base URL
BASE_URL=https://yourapi.com k6 run k6_search_test.js
```

### KG API Load Test

```bash
k6 run k6_kg_test.js
```

## Test Scenarios

### 1. GraphRAG Test (`k6_graphrag_test.js`)

- **Duration**: 4 minutes
- **Max VUs**: 20 concurrent users
- **Thresholds**:
  - 95% of requests < 5 seconds
  - Error rate < 10%

### 2. Search Test (`k6_search_test.js`)

- **Duration**: 7 minutes
- **Max VUs**: 100 concurrent users
- **Thresholds**:
  - 95% of requests < 2 seconds
  - Error rate < 5%

### 3. KG API Test (`k6_kg_test.js`)

- **Duration**: 5 minutes
- **Max VUs**: 200 concurrent users
- **Thresholds**:
  - 95% of requests < 1 second
  - Error rate < 2%

## Interpreting Results

```
scenarios: (100.00%) 1 scenario, 100 max VUs, 10m30s max duration
...
data_received..................: 45 MB  750 kB/s
data_sent......................: 3.2 MB 53 kB/s
http_req_blocked...............: avg=1.2ms   min=1µs     med=3µs
http_req_connecting............: avg=412µs   min=0s      med=0s
http_req_duration..............: avg=854ms   min=120ms   med=680ms   p(95)=1.8s
http_req_failed................: 2.50%  ✓ 125   ✗ 4875
http_req_receiving.............: avg=185µs   min=15µs    med=98µs
http_req_sending...............: avg=58µs    min=7µs     med=32µs
http_req_tls_handshaking.......: avg=0s      min=0s      med=0s
http_req_waiting...............: avg=854ms   min=120ms   med=680ms
http_reqs......................: 5000   83.3/s
iteration_duration.............: avg=1.2s    min=620ms   med=1.1s
iterations.....................: 5000   83.3/s
vus............................: 100    min=0   max=100
vus_max........................: 100    min=100 max=100
```

**Key Metrics**:
- `http_req_duration`: Response time (aim for p95 < threshold)
- `http_req_failed`: Error rate (aim for < 5%)
- `http_reqs`: Requests per second
- `vus`: Virtual users (concurrency)

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install k6
        run: |
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
            sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      - name: Run load tests
        env:
          BASE_URL: ${{ secrets.API_BASE_URL }}
          AUTH_TOKEN: ${{ secrets.API_AUTH_TOKEN }}
        run: |
          k6 run tests/load/k6_search_test.js
```

## Best Practices

1. **Start Small**: Begin with low VUs, gradually increase
2. **Monitor**: Watch server metrics (CPU, memory, database connections)
3. **Isolate**: Run tests against staging, not production
4. **Baseline**: Establish baseline performance before optimizing
5. **Repeat**: Run tests multiple times for consistency

## Troubleshooting

### High Error Rates

- Check API logs for errors
- Verify database connection pool size
- Check rate limiting configuration

### Slow Response Times

- Profile slow endpoints with cProfile
- Check database query performance
- Review cache hit rates
- Monitor external API latency (Gemini, Qdrant)

### Resource Exhaustion

- Increase database connection pool
- Add more memory to server
- Optimize garbage collection

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Examples](https://k6.io/docs/examples/)
- [Grafana k6 Cloud](https://k6.io/cloud/) - Paid service for advanced analytics
