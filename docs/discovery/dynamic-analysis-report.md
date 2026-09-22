# 4.2 Dynamic Analysis of the Microservices System

## 4.2.1 Objective and scope

The dynamic analysis examined the deployed TrainTicket system under a controlled
workload before any modular-monolith migration. Its objective was to complement
the source-level architecture inventory with runtime evidence concerning
deployment identity, request outcomes, latency, failures, container stability,
resource consumption and observable network connections. The experiment was
read-only with respect to application state: it did not restart or modify a
container, change an image, merge services, or execute booking, payment,
cancellation or rebooking operations.

This was an initial non-invasive baseline rather than a distributed-tracing
experiment. The distinction matters because the chosen method can establish an
external request's outcome and can sample container-level connections, but it
cannot reconstruct every internal HTTP request chain.

## 4.2.2 Measurement definitions

An **HTTP success** is a measured response with a status code from 200 to 399. A
**semantic success** additionally satisfies a scenario-specific business check:
application status `1` for login, or at least one returned journey for ticket
search. **Scenario latency** is elapsed time at the workload client and therefore
includes the dashboard proxy and any downstream processing. A **runtime edge**
is an ordered pair of containers for which an `ESTABLISHED` or `TIME_WAIT` TCP
socket was sampled. It proves an active or recently completed connection, not an
HTTP request count. A **matching log line** is a line containing a predefined
failure pattern; several lines can belong to one incident.

Static/runtime comparison used the following classifications. An edge present
in both evidence sets is `OBSERVED_IN_BOTH`; an observed runtime edge absent
from the production-Java call-site inventory is `RUNTIME_ONLY`; and a static
edge not seen during this workload is `NOT_EXERCISED`. The last classification
does not mean unused, unreachable or safe to remove. The categories `IMAGE_ONLY`
and `UNRESOLVED` remain available when the evidence supports them, but neither
occurred in this run.

## 4.2.3 Automated method

The experiment was automated by
[`dynamic_analysis.py`](../../tools/dynamic_analysis.py), which uses the Python
standard library and the Docker command-line interface. It was executed against
the already-running Compose deployment as follows:

```powershell
python .\tools\dynamic_analysis.py --iterations 20 --stats-samples 5 --stats-interval 1
```

Docker inspection recorded the service name, container and image identifiers,
start time, state, health configuration, restart count, network address,
repository digest and available image labels. The immutable image identifier
establishes which local image content ran, although it cannot identify a
producing Git commit when source-revision metadata is absent.

The workload issued 20 requests for each of three scenarios through
`http://localhost:8080`: login, a `Shang Hai` to `Su Zhou` G-train search, and
the corresponding D-train search. The two searches used a departure date seven
days in the future. For each request, the collector retained the method, gateway
route, HTTP and application status, response shape and size, result count,
response hash, error type and elapsed time. It did not retain passwords, cookies,
tokens, authorization headers or response bodies. The response hash permits
equality checks without preserving the content.

Latency was measured with a monotonic high-resolution clock. The reported p95
uses linear interpolation at the 95th-percentile position in the ordered sample.
Docker resource statistics were sampled five times at one-second intervals and
summarized by their mean and maximum. Logs emitted after the experiment start
were screened for exceptions, timeouts, connection refusals, unavailability and
HTTP 5xx indicators; only aggregate counts and sanitized notes were stored.

To observe connections, the collector read `/proc/net/tcp` and
`/proc/net/tcp6` in application containers before and after the workload.
Docker network metadata mapped remote IP addresses to Compose services. Both
`ESTABLISHED` and `TIME_WAIT` entries were retained so that recently completed
short-lived connections could be observed.

The final measured run occurred from `2026-08-23T16:57:07Z` to
`2026-08-23T16:57:57Z`. Detailed observations are retained under
[`dynamic-generated`](dynamic-generated/), while the separate
[`dynamic-analysis-README.md`](dynamic-analysis-README.md) contains operational
reproduction instructions.

## 4.2.4 Results

### 4.2.4.1 Deployment state and provenance

Docker reported 68 running containers: 42 application containers and 26
database or infrastructure containers. All 68 lacked a configured Docker health
check, demonstrating that the `running` state could not be interpreted as
application readiness. One application container, `ts-voucher-service`, had a
non-zero restart count of eight. The counter demonstrates prior process restarts
but does not by itself identify their cause.

Image references and immutable local image IDs were recorded for every
container, together with repository digests and OCI labels where available.
This preserves the identity of the executed deployment. Where a source-revision
label or repository digest is absent, however, the evidence cannot establish the
Git commit from which an image was produced.

### 4.2.4.2 Scenario outcomes and latency

**Table 4.5: Gateway-observed scenario results**

| Scenario | Requests | HTTP successes | Semantic successes | Mean (ms) | Median (ms) | p95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Login | 20 | 20 | 20 | 212.574 | 146.325 | 544.598 | 831.399 |
| G-train search | 20 | 20 | 0 | 27.919 | 24.846 | 53.052 | 53.345 |
| D-train search | 20 | 20 | 0 | 23.231 | 20.082 | 36.866 | 42.160 |

All login responses returned HTTP 200, application status `1` and the message
`login success`. Login was therefore successful at both the transport and
application levels in all 20 iterations.

Both travel endpoints returned HTTP 200 but an empty JSON array in every
iteration. Subsequent inspection of the request class packaged in the deployed
image showed that it expects `startingPlace` and `java.util.Date`, whereas the
checked-in UI/common model uses `startPlace` and a formatted string. The
collector had followed the checked-in contract. These 40 search observations are
therefore invalid workload-construction trials and are excluded from
architectural and performance conclusions. The login observations remain valid.

### 4.2.4.3 Runtime connections and static comparison

The socket sampler observed three directed connections, all in `TIME_WAIT`:

| Caller | Callee | Port |
|---|---|---:|
| `ts-ui-dashboard` | `ts-auth-service` | 12340 |
| `ts-ui-dashboard` | `ts-travel-service` | 12346 |
| `ts-ui-dashboard` | `ts-travel2-service` | 16346 |

These connections correspond to the three attempted gateway scenarios. Relative to the
production-Java dependency inventory, they were classified `RUNTIME_ONLY`
because that static extraction did not treat the dashboard's proxy
configuration as a Java service call. All 90 source-level HTTP edges were
classified `NOT_EXERCISED`. No `OBSERVED_IN_BOTH` edge was established by this
coarse sampling method. This result describes observation coverage, not the
complete runtime architecture. In addition to socket-sampling limitations, the
search payload was incompatible with the DTO packaged in the deployed image and
therefore did not exercise the intended workflow.

### 4.2.4.4 Failure indicators

Sanitized log screening produced the following observations:

| Service | Indicator | Matching lines |
|---|---|---:|
| `ts-notification-service` | `connection refused` | 27 |
| `ts-notification-service` | `exception` | 12 |

The values are matching line counts, not counts of independent failures. A
single exception can generate several stack-trace lines and a failed connection
can be retried. Their concentration in `ts-notification-service` nevertheless
identifies a targeted runtime investigation candidate.

### 4.2.4.5 Resource observations

The largest mean memory observations among application containers were
approximately 302.7 MB for `ts-travel2-service`, 302.6 MB for
`ts-order-other-service`, 297.1 MB for `ts-config-service`, 296.4 MB for
`ts-food-service` and 295.8 MB for `ts-payment-service`. CPU usage was low and
variable during the short run. Five samples over this workload provide a
baseline snapshot only and are insufficient for capacity planning or sizing a
future modular monolith.

No matching Spring Boot startup messages remained in the logs inspected during
the final run. Startup duration was therefore unavailable, not zero. A separate
cold-start experiment must begin collection before Compose startup and must
distinguish container creation, process start, framework startup and externally
verified readiness.

## 4.2.5 Validation

The final artifacts contain exactly 68 container records and 60 request records.
The scenario totals reconcile with 20 iterations across three scenarios. The
static/runtime comparison contains 93 distinct pairs: 90 `NOT_EXERCISED` and
three `RUNTIME_ONLY`. Container classifications reconcile to 42 application and
26 infrastructure components. The generated artifacts passed a scan for the
configured password, bearer credentials, authorization values, cookies and
client-token fields. The collector also passed Python byte-code compilation.

These checks validate artifact consistency and redaction; they do not validate
that the limited workload exercised every service or dependency.

## 4.2.6 Threats to validity

The principal limitation is workload coverage. Login and two search routes were
attempted. Booking, payment, cancellation and rebooking were excluded
because they mutate business state and require a disposable dataset and a
documented restoration procedure. The baseline search payload was later found to
be incompatible with the packaged runtime DTO, so its search results cannot be
used as behavioral or performance evidence.

TCP socket sampling is incomplete. Short-lived connections can occur between
samples, multiple requests can reuse one persistent socket, and a sampled socket
does not reveal the internal HTTP method, route, status or latency. Consequently,
the experiment did not establish complete request chains, internal request
counts or database interactions. A missing runtime edge means only that the edge
was not observed under this workload and method.

The latency sample contains only 20 observations per scenario and represents a
single short run without a controlled warm-up, concurrency model or repeated
experimental runs. The p95 values are descriptive baseline measurements, not
general performance estimates. Resource measurements are similarly limited.
Log pattern matching may count several lines from one incident and requires
manual diagnosis before a root cause can be claimed.

Finally, prebuilt and image-only services restrict source-to-runtime
traceability. Image identifiers establish executable identity, but incomplete
provenance prevents the running implementation from being assumed equivalent to
the checked-in source.

## 4.2.7 Distributed-tracing experiment

### 4.2.7.1 Instrumentation design

A second experiment introduced automatic instrumentation through the separate
[`docker-compose.otel.yml`](../../docker-compose.otel.yml) override. This kept
observability configuration distinct from the baseline deployment and business
code. The pinned stack comprised OpenTelemetry Java Agent 2.31.0, OpenTelemetry
Collector Contrib 0.159.0 and Jaeger 2.20.0. The downloaded agent was verified by
SHA-256 before use.

Runtime command inspection identified 37 Java application containers, all of
which were configured to load the agent. Five application containers were not
covered by Java auto-instrumentation: the OpenResty dashboard, Python avatar and
voucher services, Go news service and Node.js ticket-office service. The
Collector accepted OTLP/HTTP spans from the agents and exported them to Jaeger
over OTLP/gRPC. Metrics and log export were disabled so that this experiment
measured tracing only.

Each controlled request carried a newly generated W3C `traceparent` value. The
non-secret trace identifier was written beside its scenario and iteration,
allowing Jaeger traces to be joined to the workload without relying on timestamp
proximity. The sanitizer retained only architectural HTTP, error and database
attributes; arbitrary attributes, request headers, query strings and bodies were
excluded. Trace-derived artifacts are stored separately under
[`dynamic-generated-otel-contract-verification`](dynamic-generated-otel-contract-verification/).

The 37 instrumented JVMs were recreated concurrently. Under the available
Docker CPU allocation, agent transformation and application initialization were
strongly resource-constrained. The services required by the workload were not
considered ready until their Spring completion messages appeared. This startup
period was operationally significant but was not used as an uninstrumented
versus instrumented overhead estimate because the two starts did not have
equivalent contention and cache conditions.

### 4.2.7.2 Trace coverage and request chains

An attempted 20-iteration run was interrupted by suspension of the execution
environment from 23 to 27 August 2026. It is preserved under
`dynamic-generated-otel-interrupted-20260823` but excluded from analysis because
its elapsed-time measurements cross a multi-day interruption.

The fresh contract-verification run used three iterations per scenario. Its
sanitized Jaeger export contained 21 unique traces and 1,119 spans. Exactly nine
traces matched the nine controlled request identifiers; 12 were marked
`UNMATCHED` and represent scheduled or background work. Twenty-two names
appeared in the Jaeger service API, including Jaeger itself.
Presence in the Compose instrumentation configuration and presence in the trace
dataset were kept separate: a configured service appears in Jaeger only after it
emits at least one sampled span.

**Table 4.6: Trace-correlated request chains**

| Scenario | Traces | Observed service sequence |
|---|---:|---|
| Login | 3 | `ts-auth-service` to `ts-verification-code-service` |
| G-train search | 3 | `ts-travel-service` to `ts-ticketinfo-service`, `ts-basic-service`, `ts-station-service`, `ts-route-service`, `ts-train-service`, `ts-price-service`, `ts-order-service`, `ts-seat-service` and `ts-config-service` |
| D-train search | 3 | `ts-travel2-service` to `ts-ticketinfo-service`, `ts-basic-service`, `ts-station-service` and `ts-route-service` |

All three login traces contained a cross-service call from `ts-auth-service` to
`ts-verification-code-service`: `GET
/api/v1/verifycode/verify/{verifyCode}`. The edge had three observed calls, no
recorded failures, a mean span duration of 186.527 ms, p95 of 211.275 ms and a
maximum of 214.316 ms. This edge is present in the static inventory and was
therefore classified `OBSERVED_IN_BOTH`.

All three G-train searches returned a non-empty result and exercised a
ten-service chain. The D-train endpoint returned an empty result in all three
iterations but still exercised a five-service chain. Of the 90 static edges, 11
were `OBSERVED_IN_BOTH` and 79 were `NOT_EXERCISED`. Five `RUNTIME_ONLY` edges
were observed, including calls involving the image-only
`ts-ticketinfo-service`; these require source/configuration review.

### 4.2.7.3 Database spans

Tracing observed 14 database span groups in the verification export. The spans
provide executed persistence evidence, but the three-iteration sample is too
small for stable database latency conclusions. Detailed operation counts and
latencies are retained in `trace-databases.csv`.

Background traces provided runtime evidence of MongoDB connections from services
including config, contacts, food-map, order, payment, price, route, security,
station, train, travel, travel2 and user. Because these traces were not joined to
a controlled request identifier, they demonstrate executed database operations
but not membership in a tested business request chain.

### 4.2.7.4 Instrumented scenario latency

**Table 4.7: Gateway latency during the instrumented run**

| Scenario | Requests | Semantic successes | Mean (ms) | Median (ms) | p95 (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Login | 3 | 3 | 645.686 | 634.541 | 744.189 | 756.372 |
| G-train search | 3 | 3 | 3993.867 | 4420.790 | 4534.698 | 4547.354 |
| D-train search | 3 | 0 | 1189.059 | 928.749 | 1741.168 | 1831.437 |

The verification produced three successful logins and three semantically
successful G-train searches. The D-train searches remained empty. With only
three observations per scenario, interpolated p95 values validate the
measurement pipeline but must not be interpreted as performance estimates or
tracing-overhead measurements.

### 4.2.7.5 Tracing limitations

The trace experiment resolved the principal ambiguity of TCP sampling by
supplying causal parent-child chains, routes, counts and per-hop latency for
login and search. Auto-instrumentation coverage was limited to Java;
calls originating in or terminating at uninstrumented technologies may appear
as incomplete traces. Jaeger's in-memory storage makes this experiment suitable
for controlled runs but not durable archival; sanitized CSV and JSON exports are
the retained research evidence.

A stronger performance comparison requires several independent warm runs,
equivalent preconditioning, a successful search scenario, and an explicitly
defined concurrency profile. State-changing workflows remain deferred until a
disposable dataset and restoration procedure are available.

## 4.2.8 Summary

The initial dynamic analysis established a reproducible, non-invasive baseline
for the deployed TrainTicket system. It recorded executable image identities,
68 running containers, one service with eight prior restarts, resource samples,
sanitized runtime failure indicators and 60 controlled requests. Login succeeded
semantically in all 20 executions with a measured p95 of 544.598 ms. The initial
search payload was later shown to follow the checked-in DTO rather than the
different contract packaged in the runtime image; its search outcomes and
latencies were consequently excluded.

The corrected OpenTelemetry contract-verification experiment correlated all nine
controlled requests with Jaeger traces. It verified the login chain and exposed
a ten-service G-train search chain and a five-service D-train search chain. The
comparison contained 11 `OBSERVED_IN_BOTH`, five `RUNTIME_ONLY` and 79
`NOT_EXERCISED` edges. Because this was a three-iteration verification run, a
larger repeated workload is still required before latency or runtime criticality
is used to finalize module boundaries or migration order.
