---
name: ring:dev-k6-load-testing
description: |
  Load testing skill using k6 — ensures services meet performance SLOs under
  realistic load before merging. Validates throughput, latency percentiles,
  error rates, and resource behavior under stress.
  Standalone skill, not gated — invoke on demand or as part of CI.

trigger: |
  - After integration testing passes
  - Before production deploy of performance-sensitive changes
  - New API endpoints or significant throughput-path changes
  - Need to validate SLOs under load (latency, error rate, throughput)
  - CI pipeline requires load test gate

skip_when: |
  - Task is documentation-only, configuration-only, or non-code
  - No HTTP/gRPC endpoints affected by the change
  - Changes limited to static assets, configs, or non-runtime code
  - Service has no network-facing interface

related:
  complementary: [ring:dev-integration-testing, ring:dev-chaos-testing, ring:dev-sre]

output_schema:
  format: markdown
  required_sections:
    - name: "Load Test Summary"
      pattern: "^## Load Test Summary"
      required: true
    - name: "Scenario Results"
      pattern: "^## Scenario Results"
      required: true
    - name: "Thresholds"
      pattern: "^## Thresholds"
      required: true
  metrics:
    - name: result
      type: enum
      values: [PASS, FAIL]
    - name: scenarios_run
      type: integer
    - name: peak_vus
      type: integer
    - name: p95_latency_ms
      type: float
    - name: p99_latency_ms
      type: float
    - name: error_rate_pct
      type: float
    - name: rps_peak
      type: float
---

# k6 Load Testing

Performance under load is non-negotiable. This skill generates and runs k6 test scripts that validate service SLOs before code ships.

**Block conditions:**
- p95 latency > threshold = FAIL
- Error rate > 1% under normal load = FAIL
- No load tests for new endpoints = FAIL
- Thresholds not defined in script = FAIL

## Step 1: Validate Input

Required:
- `target_url` — base URL of the service under test (e.g. `http://localhost:3000`)
- `endpoints` — list of endpoints to test, each with method, path, and optional payload
- `language` — project language (go | typescript) for framework-specific guidance

Optional:
- `scenarios` — custom scenario definitions (default: smoke → load → stress → soak)
- `thresholds` — custom thresholds (defaults below)
- `vus_max` — maximum virtual users (default: 100)
- `duration` — test duration per stage (default: 30s per stage)
- `auth_header` — authorization header if endpoints require auth
- `existing_tests` — path to existing k6 scripts to extend

## Step 2: Generate k6 Test Script

Create test file at `load-tests/k6/{service-name}.js` (or `load-tests/k6/{service-name}.ts` for TypeScript projects using k6 with bundler).

### Default Thresholds

```javascript
export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // ms
    http_req_failed: ['rate<0.01'],                    // <1% errors
    http_reqs: ['rate>10'],                            // minimum throughput
  },
};
```

Override with project-specific values from `PROJECT_RULES.md` or input `thresholds`.

### Default Scenarios

Generate four progressive scenarios:

```javascript
export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
      tags: { scenario: 'smoke' },
    },
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 50 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 0 },
      ],
      startTime: '30s',
      tags: { scenario: 'load' },
    },
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '30s', target: 0 },
      ],
      startTime: '3m',
      tags: { scenario: 'stress' },
    },
    soak: {
      executor: 'constant-vus',
      vus: 30,
      duration: '5m',
      startTime: '5m30s',
      tags: { scenario: 'soak' },
    },
  },
};
```

### Script Structure

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('custom_error_rate');
const latencyTrend = new Trend('custom_latency');

// Thresholds and scenarios (see above)
export const options = { /* ... */ };

// Setup — runs once before test
export function setup() {
  // Health check: verify service is reachable
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'service is up': (r) => r.status === 200,
  });
  if (healthRes.status !== 200) {
    throw new Error(`Service not reachable at ${BASE_URL}`);
  }
  return { baseUrl: BASE_URL };
}

// Default function — runs per VU iteration
export default function (data) {
  // Group requests by endpoint
  // Add checks for each response
  // Track custom metrics
  // Sleep between iterations (think time)
}

// Teardown — runs once after test
export function teardown(data) {
  // Cleanup if needed
}
```

### Per-Endpoint Pattern

For each endpoint in `endpoints`:

```javascript
import { group } from 'k6';

group('POST /api/v1/resource', () => {
  const payload = JSON.stringify({
    // From endpoint definition or generated
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // auth_header if provided
    },
    tags: { endpoint: 'POST /api/v1/resource' },
  };

  const res = http.post(`${data.baseUrl}/api/v1/resource`, payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'response has id': (r) => r.json('id') !== undefined,
    'latency < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(res.status >= 400);
  latencyTrend.add(res.timings.duration);

  sleep(1); // Think time between requests
});
```

## Step 3: Run Tests

### Prerequisites Check

```bash
# Verify k6 is installed
which k6 || echo "k6 not found — install: brew install k6 | go install go.k6.io/k6@latest | docker pull grafana/k6"

# Verify target service is running
curl -sf ${TARGET_URL}/health || echo "Service not reachable"
```

### Execution

```bash
# Run with JSON output for parsing
k6 run load-tests/k6/${SERVICE_NAME}.js \
  --out json=load-tests/k6/results/${SERVICE_NAME}-$(date +%Y%m%d-%H%M%S).json \
  --summary-trend-stats="avg,min,med,max,p(90),p(95),p(99)" \
  2>&1 | tee load-tests/k6/results/${SERVICE_NAME}-latest.log
```

If k6 is not installed locally, use Docker:

```bash
docker run --rm -i \
  --network=host \
  -v $(pwd)/load-tests/k6:/scripts \
  grafana/k6 run /scripts/${SERVICE_NAME}.js
```

### CI Integration (optional)

```yaml
# GitHub Actions example
load-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: grafana/setup-k6-action@v1
    - uses: grafana/run-k6-action@v1
      with:
        path: load-tests/k6/${{ matrix.service }}.js
```

## Step 4: Analyze Results

Parse k6 output and evaluate against thresholds.

### Pass Criteria

| Metric | Default Threshold | Result |
|--------|-------------------|--------|
| p95 latency | < 500ms | PASS/FAIL |
| p99 latency | < 1000ms | PASS/FAIL |
| Error rate | < 1% | PASS/FAIL |
| Min throughput | > 10 req/s | PASS/FAIL |

### Failure Analysis

If any threshold fails:
1. Identify which scenario triggered the failure (smoke/load/stress/soak)
2. Check if failure is at specific VU count (capacity limit) or gradual degradation
3. Correlate with endpoint — which endpoints are slowest?
4. Check error types — timeouts vs 5xx vs connection refused
5. Recommend: profile endpoint, check DB queries, review connection pool sizing

## Step 5: Output Report

```markdown
## Load Test Summary

| Metric | Value |
|--------|-------|
| Result | PASS/FAIL |
| Scenarios | smoke ✅, load ✅, stress ⚠️, soak ✅ |
| Peak VUs | 100 |
| Total Requests | 12,345 |
| Duration | 10m 30s |

## Scenario Results

### Smoke (1 VU, 30s)
- Avg latency: 45ms | p95: 82ms | p99: 120ms
- Error rate: 0%
- RPS: 22

### Load (50 VUs, 2m)
- Avg latency: 120ms | p95: 280ms | p99: 450ms
- Error rate: 0.2%
- RPS: 850

### Stress (100 VUs, 2m)
- Avg latency: 350ms | p95: 680ms | p99: 1200ms
- Error rate: 1.5%
- RPS: 1100

### Soak (30 VUs, 5m)
- Avg latency: 95ms | p95: 210ms | p99: 380ms
- Error rate: 0.1%
- RPS: 520

## Thresholds

| Threshold | Target | Actual | Status |
|-----------|--------|--------|--------|
| http_req_duration p(95) | < 500ms | 680ms | ❌ FAIL |
| http_req_duration p(99) | < 1000ms | 1200ms | ❌ FAIL |
| http_req_failed | < 1% | 1.5% | ❌ FAIL |
| http_reqs rate | > 10/s | 1100/s | ✅ PASS |

## Recommendations
- Stress scenario exceeded latency thresholds at 100 VUs
- Investigate: [specific endpoint] accounts for 60% of p99 latency
- Consider: connection pool sizing, query optimization, caching
```

## Conventions

- **File location:** `load-tests/k6/` directory at project root
- **Naming:** `{service-name}.js` or `{service-name}.{scenario}.js` for split files
- **Results:** `load-tests/k6/results/` — gitignored
- **Shared utilities:** `load-tests/k6/lib/` for auth helpers, data generators
- **Environment config:** use k6 `__ENV` for target URL, auth tokens
- **Think time:** always include `sleep()` between iterations to simulate real users
- **Checks:** every request must have at least one `check()` assertion
- **Tags:** tag requests with endpoint name for per-endpoint analysis
- **Idempotency:** tests should be safe to run repeatedly (use unique IDs, clean up in teardown)
