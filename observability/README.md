# OpenTelemetry and Jaeger tracing

This directory adds distributed tracing without changing TrainTicket business
code or the baseline `docker-compose.yml`. The pinned stack is:

- OpenTelemetry Java Agent 2.31.0;
- OpenTelemetry Collector Contrib 0.159.0; and
- Jaeger 2.20.0.

The Java agent is configured for all 37 containers whose runtime command is
`java`. OpenResty, Python, Go and Node.js containers are explicitly outside this
first auto-instrumentation scope.

## 1. Download and verify the agent

```powershell
powershell -ExecutionPolicy Bypass -File .\observability\setup-opentelemetry-agent.ps1
```

The JAR is ignored by Git. The setup script verifies SHA-256
`D48673B2FF956B26D809BC34243649913D4EEFD9191C4E175B686DA633E0134B`.

## 2. Validate and start the tracing deployment

```powershell
docker compose -f docker-compose.yml -f docker-compose.otel.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.otel.yml pull jaeger otel-collector
docker compose -f docker-compose.yml -f docker-compose.otel.yml up -d --no-build
docker compose -f docker-compose.yml -f docker-compose.otel.yml restart ts-ui-dashboard
```

The last command refreshes OpenResty's cached backend addresses after Java
containers are recreated. On a constrained host, starting all instrumented
legacy JVMs concurrently can take more than ten minutes. Do not run a workload
until the required Spring services log `Started ... in ... seconds`.

Jaeger is available at <http://localhost:16686>. The Collector and Jaeger OTLP
ports are internal to `train-ticket_my-network` and are not published to the
host.

## 3. Execute a correlated workload

Preserve the uninstrumented baseline by using a distinct output directory:

```powershell
python .\tools\dynamic_analysis.py `
  --output .\docs\discovery\dynamic-generated-otel `
  --iterations 20 --stats-samples 5 --stats-interval 1
```

The workload adds a unique W3C `traceparent` header to every request and stores
only its non-secret trace ID. It does not store authentication headers, cookies,
tokens or response bodies.

Wait at least five seconds for Collector batching, then export sanitized traces:

```powershell
python .\tools\jaeger_trace_analysis.py `
  --scenario-requests .\docs\discovery\dynamic-generated-otel\scenario-requests.csv `
  --output .\docs\discovery\dynamic-generated-otel
```

The exporter allow-lists architectural attributes and generates:

- `trace-summary.json`: trace, span, service and classification counts;
- `trace-spans.csv`: sanitized individual spans;
- `trace-chains.csv`: controlled trace-to-scenario chains;
- `trace-edges.csv`: cross-service calls, counts, failures and latency;
- `trace-databases.csv`: database client operations and latency; and
- `static-trace-comparison.csv`: source-versus-trace edge classifications.

`UNMATCHED` traces are startup, initialization, scheduled or other background
activity outside the controlled request IDs. They must not be attributed to a
business scenario.

## 4. Stop or return to the baseline

Stop only the observability components while leaving services instrumented:

```powershell
docker compose -f docker-compose.yml -f docker-compose.otel.yml stop otel-collector jaeger
```

To recreate services without the agent, use the baseline Compose file. This is a
deployment restart and should be scheduled like any other cold start:

```powershell
docker compose -f docker-compose.yml up -d --no-build
docker compose restart ts-ui-dashboard
```

