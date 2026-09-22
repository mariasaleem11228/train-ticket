# Dynamic analysis replication guide

This guide runs a read-only baseline against the already-running TrainTicket
Docker Compose deployment. It does not restart containers, modify images, save
response bodies, or change business data. The thesis-ready interpretation is in
[`dynamic-analysis-report.md`](dynamic-analysis-report.md).

## Prerequisites

1. Start Docker Desktop and the full Compose deployment.
2. Wait until `http://localhost:8080` is reachable. Container `running` status
   alone is not an application-readiness check.
3. Open PowerShell in the repository root. Your Windows account must have
   permission to access Docker Desktop.
4. Use Python 3.9 or newer. No third-party Python package is required.

## Run the baseline

```powershell
python .\tools\dynamic_analysis.py --iterations 20 --stats-samples 5 --stats-interval 1
```

The default workload performs 20 logins and 20 searches against each travel
service. It uses a date seven days in the future. Override it when necessary:

```powershell
python .\tools\dynamic_analysis.py --future-days 30 --iterations 30
```

The collector writes replaceable artifacts to `dynamic-generated/`:

| Artifact | Meaning |
|---|---|
| `dynamic-summary.json` | Run scope, high-level counts and limitations |
| `runtime-containers.csv` | Status, restart count, image ID, digests, labels and IPs |
| `resource-samples.csv` | Individual Docker CPU/memory samples |
| `resource-summary.csv` | Per-container mean/maximum CPU and memory |
| `scenario-requests.csv` | Sanitized outcome and latency of each request |
| `scenario-summary.csv` | Counts and min/mean/median/p95/max latency |
| `runtime-connections.csv` | Sampled live/recent TCP peers |
| `static-runtime-comparison.csv` | Workload-specific dependency classification |
| `failure-summary.csv` | Counts of sanitized failure-pattern matches in logs |
| `startup-summary.csv` | Spring-reported startup times when logs retain them |

Passwords are used in memory for the controlled login but are not written to
the artifacts. Cookies, tokens, authorization headers and response bodies are
also excluded. Response hashes permit equality checks without retaining data.

## Interpretation gates

- `successes` means HTTP success. Use `semantic_successes` to determine whether
  the business-level result was successful/non-empty.
- A row in `runtime-connections.csv` proves a sampled TCP connection, not a
  number of HTTP requests. Method and route are known only for the controlled
  gateway scenarios in this phase.
- `NOT_EXERCISED` means the static edge was not seen under this workload. It
  never means unused, unreachable or safe to remove.
- Log-pattern counts are screening signals. `exception` and `connection_refused`
  patterns require targeted log review because one event can occupy several
  lines or repeat.
- Five one-second resource samples characterize only this short run. Use a
  longer, repeated workload before capacity conclusions.
- Empty `startup-summary.csv` means matching historical startup lines were no
  longer retained; it does not mean startup took zero seconds.

## Next phase: distributed tracing

For caller/callee method, normalized route, per-hop latency, request chains and
reliable request counts, use the OpenTelemetry Java agent with an OpenTelemetry
Collector and Jaeger or Grafana Tempo. Keep this in a separate Compose override
and results directory. Because the deployment includes prebuilt/image-only
services and image/source discrepancies, first verify that each image can load
the same agent without changing its entry point. Record an uninstrumented
control run and an instrumented run of the identical workload to quantify
observability overhead.

Do not begin booking, payment, cancellation or rebooking automation until a
disposable dataset and cleanup/restore procedure have been agreed: those
scenarios mutate business state.

