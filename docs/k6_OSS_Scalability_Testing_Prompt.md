# Antigravity Master Prompt — Local k6 OSS Scalability Testing

You are working on my existing project. Your task is to implement a fully local, automated scalability/load-testing system using **Grafana k6 OSS** as the load-generation engine.

## IMPORTANT

- First inspect the entire existing project structure before changing anything.
- Do NOT blindly create a new architecture if the project already has suitable components.
- Reuse the existing frontend, backend, database, authentication, routing, and UI patterns where appropriate.
- Do not replace working functionality.
- Keep the implementation modular so the system can later scale from one local k6 worker to multiple distributed workers.
- This is a development/testing platform. Do not generate uncontrolled traffic.
- Never run a load test against a third-party/public website unless I explicitly configure and authorize that target.
- Default testing target should be localhost/local development applications.
- Do not expose arbitrary internal-network scanning functionality.
- Validate the target URL before starting a test.
- Add reasonable safety limits to prevent accidental resource exhaustion on my laptop.

---

## 1. FIRST: INSPECT THE EXISTING PROJECT

Before implementing anything:

1. Identify:
   - Frontend framework
   - Backend framework
   - Database
   - Existing API structure
   - Authentication
   - Existing job/task system
   - Existing dashboard components
   - Existing environment configuration
   - Existing Docker configuration
   - Existing logging/error handling
   - Existing testing infrastructure

2. Identify where the following should live:
   - Load-test API
   - k6 execution service
   - Generated k6 scripts
   - Test configurations
   - Test results
   - Test history
   - Dashboard UI

3. Produce a short implementation plan based on the actual repository.

Do not modify code until the inspection is complete.

---

## 2. LOCAL K6 OSS

Use **Grafana k6 OSS**, not Grafana Cloud.

The first implementation must run completely locally.

Requirements:

- Detect whether k6 is installed.
- If k6 is missing, provide/install the appropriate Windows installation method.
- Verify installation using:

```bash
k6 version
```

- Do not assume a specific installation path.
- Detect the executable path dynamically.
- Make the backend configurable through an environment variable such as:

```text
K6_PATH
```

- If `K6_PATH` is not provided, automatically detect k6 from PATH.
- Return a clear error if k6 cannot be found.

The system must work on Windows.

Do not require Kubernetes, Prometheus, Grafana Cloud, Kafka, Redis, or multiple machines for the MVP.

---

## 3. CORE ARCHITECTURE

Implement this initial architecture:

```text
Frontend
    ↓
Backend API
    ↓
Test Controller
    ↓
k6 OSS process
    ↓
Target Application
    ↓
k6 result output
    ↓
Result Parser
    ↓
Database
    ↓
Dashboard
```

The backend should control the k6 process.

Requirements:

- Start k6 programmatically.
- Capture stdout.
- Capture stderr.
- Capture exit code.
- Capture process start time.
- Capture process completion time.
- Detect crashes.
- Detect manually cancelled tests.
- Store test status.

Test states:

```text
CREATED
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

---

## 4. TEST CONFIGURATION

Create a test configuration model.

At minimum support:

- target URL
- virtual users
- duration
- ramp-up duration
- ramp-down duration
- HTTP method
- optional request body
- optional headers
- test name

Example:

```text
targetUrl:
    http://localhost:3000

virtualUsers:
    100

rampUp:
    30s

duration:
    2m

rampDown:
    30s
```

For the MVP, support GET requests first.

Design the configuration so POST/PUT/DELETE and complex user journeys can be added later.

---

## 5. GENERATED K6 SCRIPT

Do NOT require users to manually write k6 scripts.

The backend should generate a temporary k6 JavaScript test script from the test configuration.

Example conceptual structure:

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 100 },
        { duration: '2m', target: 100 },
        { duration: '30s', target: 0 }
    ]
};

export default function () {
    const response = http.get('TARGET_URL');

    check(response, {
        'status is successful': (r) => r.status >= 200 && r.status < 400,
    });
}
```

Do not hardcode the user's target URL directly into unsafe shell commands.

Avoid shell injection.

Pass values safely.

---

## 6. SAFETY LIMITS

Because the initial system runs on my laptop, implement conservative default limits.

Example development defaults:

```text
maxVirtualUsers = 1000
maxDuration = 10 minutes
```

Make these configurable through environment variables.

Before starting a test:

1. Validate target URL.
2. Validate virtual-user count.
3. Validate duration.
4. Validate ramp-up/ramp-down.
5. Prevent empty/invalid URLs.
6. Prevent unsupported protocols.
7. Prevent multiple uncontrolled tests from consuming the machine.
8. Allow only one active heavy test initially.

The UI must clearly warn:

> Load testing generates real traffic. Only test applications you own or have explicit authorization to test.

---

## 7. LOCAL TEST MANAGEMENT API

Create backend APIs similar to:

```text
POST /api/load-tests
```

Create a test.

```text
GET /api/load-tests
```

List previous tests.

```text
GET /api/load-tests/:id
```

Get test details.

```text
POST /api/load-tests/:id/start
```

Start test.

```text
POST /api/load-tests/:id/cancel
```

Cancel test.

```text
GET /api/load-tests/:id/results
```

Get test results.

```text
GET /api/load-tests/:id/logs
```

Get test logs.

Do not duplicate existing API conventions if the project already has a standard routing structure.

---

## 8. RESULT COLLECTION

The system must collect useful k6 metrics.

At minimum:

- requests
- requests per second
- virtual users
- iteration count
- iteration duration
- HTTP request duration
- average response time
- median response time
- p90
- p95
- p99
- HTTP failures
- HTTP error rate
- checks passed
- checks failed
- min response time
- max response time
- test duration

Prefer machine-readable k6 output rather than scraping human-readable console output whenever practical.

Use k6's supported JSON/structured output mechanism.

Do not rely exclusively on parsing terminal text.

---

## 9. RESULT DATABASE

Store:

### Test

- id
- name
- target
- configuration
- status
- createdAt
- startedAt
- completedAt
- duration

### Metrics

- requestCount
- requestRate
- vus
- avgResponseTime
- medianResponseTime
- p90
- p95
- p99
- minResponseTime
- maxResponseTime
- errorRate
- checksPassed
- checksFailed

### Logs

- timestamp
- level
- message

Use the project's existing database technology if possible.

Do not introduce another database unnecessarily.

---

## 10. LIVE TEST MONITORING

The dashboard should show a running test.

At minimum:

```text
Status
Current VUs
Requests/sec
Average latency
p95 latency
Error rate
Requests completed
Elapsed time
```

If the existing application already uses WebSockets or Server-Sent Events, reuse it.

Otherwise implement a simple polling mechanism for the MVP.

Do not introduce WebSockets just for the sake of complexity.

---

## 11. DASHBOARD

Create a clean dashboard for:

### A. Create Test

Fields:

```text
Test Name
Target URL
Virtual Users
Ramp-up
Duration
Ramp-down
```

Button:

```text
Start Test
```

### B. Running Test

Display live:

```text
RUNNING

Virtual Users
Requests/sec
Response Time
p95
Error Rate
Progress
```

### C. Completed Test

Display:

```text
Total Requests
Average Response
p95
p99
Error Rate
Peak VUs
Requests/sec
```

Include useful charts if the existing UI system supports them.

Do not redesign the entire application.

Follow the existing design system.

---

## 12. AUTOMATIC SCALABILITY TEST

After the basic single test works, implement an automated capacity-test mode.

Example:

User enters:

```text
Target:
    http://localhost:3000

Starting VUs:
    100

Maximum VUs:
    1000

Increment:
    100

Duration per level:
    30 seconds
```

The system automatically executes:

```text
100 VUs
   ↓
200 VUs
   ↓
300 VUs
   ↓
...
   ↓
1000 VUs
```

Collect metrics for every level.

Store each level as a test stage.

---

## 13. BREAKING-POINT DETECTION

Implement basic rule-based detection.

Do NOT use AI initially.

Allow configurable thresholds such as:

```text
maxP95Latency
maxErrorRate
```

Example:

```text
maxP95Latency = 1000ms
maxErrorRate = 5%
```

If:

```text
p95 > threshold
```

OR:

```text
errorRate > threshold
```

mark the stage as degraded/failed.

Then report:

```text
First degradation point
Maximum successful stage
First failed stage
```

Do not claim that this is the exact physical breaking point.

Call it:

```text
Observed performance threshold
```

because the result depends on the test configuration and infrastructure.

---

## 14. TEST TYPES

Implement in this order:

### Phase 1

Basic load test

### Phase 2

Ramp test

### Phase 3

Stress test

### Phase 4

Spike test

### Phase 5

Endurance/soak test

Do not implement everything simultaneously.

Keep each test type modular.

---

## 15. USER JOURNEY SUPPORT — FUTURE-READY

Design the architecture so later we can support:

```text
Open website
    ↓
Login
    ↓
Search
    ↓
Open product
    ↓
Add to cart
    ↓
Checkout
```

But DO NOT implement complex browser automation in the first MVP.

For the MVP:

```text
HTTP/API testing first.
```

Later we may integrate:

```text
k6 browser
Playwright
recorded workflows
OpenAPI import
```

---

## 16. TEMPORARY FILE MANAGEMENT

Generated k6 scripts and result files must use a controlled temporary directory.

For example:

```text
./storage/load-tests/
```

Use unique test IDs.

Example:

```text
storage/load-tests/
    test-abc123/
        script.js
        results.json
        stdout.log
        stderr.log
```

Clean up temporary files according to a configurable retention policy.

Never overwrite another test's files.

---

## 17. PROCESS MANAGEMENT

The backend must correctly handle:

- process start
- process completion
- process failure
- process cancellation
- timeout
- Windows process termination
- orphaned processes

When cancelling a test, terminate the associated k6 process safely.

Do not leave orphaned k6 processes running.

Add logging for process lifecycle events.

---

## 18. WINDOWS COMPATIBILITY

This system must work on Windows.

Do not assume Linux commands.

Avoid shell-specific commands where possible.

Use Node.js APIs for:

- process execution
- filesystem
- path handling
- temporary files
- process termination

Use cross-platform path utilities.

If Docker is optional, do not make Docker mandatory for the local MVP.

---

## 19. SECURITY

Important:

Never construct shell commands by concatenating user-controlled strings.

Do not do:

```javascript
exec("k6 run " + userInput)
```

Use safe argument arrays/process APIs.

Validate:

- URL
- protocol
- numeric values
- durations
- headers
- request body

Do not store secrets in generated scripts.

Do not log authentication tokens or passwords.

---

## 20. ERROR HANDLING

Provide useful errors such as:

```text
k6 executable not found

Invalid target URL

Test already running

Virtual user limit exceeded

Test duration exceeds configured limit

k6 process failed

Target application unreachable

Test cancelled
```

Do not expose raw stack traces to normal users.

Keep detailed logs available for development/debugging.

---

## 21. TESTING THE IMPLEMENTATION

After implementation, DO NOT immediately test against an external website.

Create/use a local test endpoint.

For example, use the existing application if it has a safe local endpoint.

Run a very small test:

```text
5 VUs
10 seconds
```

Verify:

- k6 starts
- requests reach local application
- results are collected
- database record is created
- dashboard displays results
- process terminates
- no orphan process remains

Then test:

```text
10 VUs
30 seconds
```

Then:

```text
50 VUs
1 minute
```

Only after these work should higher loads be attempted.

---

## 22. DEVELOPMENT COMMANDS

After implementation, provide the exact commands required to:

1. Start backend
2. Start frontend
3. Verify k6
4. Run the application
5. Start a test
6. View results

Do not invent commands.

Use the project's actual package manager and scripts after inspecting `package.json` and the repository.

---

## 23. DOCUMENTATION

Create/update documentation explaining:

- What k6 OSS is
- How the integration works
- Installation requirements
- Windows setup
- Environment variables
- How to create a load test
- How virtual users work
- How scalability testing works
- How results are calculated
- Safety limits
- Troubleshooting
- Future distributed architecture

Clearly distinguish:

```text
Virtual users
```

from:

```text
Real users
```

and explain that k6 virtual users are simulated workloads.

---

## 24. FUTURE DISTRIBUTED ARCHITECTURE

Do not implement this yet, but keep interfaces clean enough for future:

```text
                    Controller
                        ↓
                    Job Queue
                        ↓
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       k6 Worker      k6 Worker      k6 Worker
          ↓             ↓             ↓
          └─────────────┼─────────────┘
                        ↓
                   Target App
```

Future technologies could include:

```text
Docker
Kubernetes
Redis
Multiple cloud workers
```

But these are NOT required for the MVP.

---

## 25. IMPORTANT DEVELOPMENT RULES

- Inspect first.
- Plan second.
- Implement incrementally.
- Keep the existing application working.
- Do not rewrite unrelated code.
- Do not add unnecessary dependencies.
- Prefer open-source/free components.
- Keep the MVP local.
- Keep k6 OSS as the load engine.
- Use safe process execution.
- Never accidentally attack arbitrary websites.
- Never run uncontrolled high-load tests automatically.
- Use conservative defaults.
- Log important operations.
- Handle Windows correctly.
- Test with very small loads first.
- After each major implementation step, verify that the application still starts.

---

# FINAL DELIVERABLE

When finished, provide:

1. Files created
2. Files modified
3. Dependencies added
4. k6 installation status
5. Environment variables required
6. Exact commands to run the system
7. Test performed
8. Test result
9. Known limitations
10. Recommended next implementation step

Do not simply tell me what code I should write.

Actually inspect and implement the system in the existing project, following the architecture and safety requirements above.
