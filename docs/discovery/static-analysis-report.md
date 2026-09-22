# 4 Microservices Analysis

This chapter analyses the TrainTicket microservices benchmark before its migration to a modular monolith. The analysis comprises two complementary parts. Static analysis reconstructs the architecture represented by source code and configuration, whereas dynamic analysis will observe interactions in the running system under controlled workloads. This distinction is important because a declared dependency may not be exercised at runtime, while calls originating from prebuilt images may not be present in the locally available source.

## 4.1 Static Analysis of the Microservices System

### 4.1.1 Objective and scope

The objective of the static analysis was to establish a reproducible architectural baseline before making any migration changes. The investigation covered system components, REST interfaces, outgoing HTTP calls, caller–callee relationships, persistence responsibilities, technologies, shared libraries and potentially duplicated types. These results provide evidence for the subsequent domain analysis, module-boundary design and migration-order decision.

The declared source baseline was Git commit `313886e99befb94be6cd45f085c98e0019f59829`. The working tree additionally contained the previously documented compatibility corrections to `.env` and `docker-compose.yml`, including the MongoDB 4.4 image pins. These corrections were necessary to reproduce the legacy deployment and were not classified as modular-monolith changes. No service was merged or internally refactored during this phase.

Only production code under `src/main` was used to extract endpoints and service calls. Test sources and generated `target` directories were excluded. Maven descriptors, application configuration and `docker-compose.yml` were included because they describe build-time and deployment-time architectural properties. Inspection of Compose remained static configuration analysis: it established what the deployment declares, not what containers actually use at runtime.

### 4.1.2 Measurement definitions

The following definitions were used to make the results reproducible:

- A **reactor project** is either the root Maven aggregator or a child declared by a `<module>` element in the root `pom.xml`.
- A **catalogued component** is a distinct component discovered in the source/build structure, Compose configuration, or both.
- A **REST endpoint** is a production controller method carrying a Spring request-mapping annotation. Its reconstructed path combines controller-level and method-level mappings.
- An **HTTP call site** is a production source location at which a named remote service URL is constructed or used.
- A **unique HTTP edge** is an ordered caller–callee pair, independent of the number of call sites or endpoints between that pair.
- **Fan-in** is the number of distinct services that call a service; **fan-out** is the number of distinct services called by it.
- **Source-configured persistence responsibility** is evidence that a service configures a datastore, supplemented by its entities and repositories. This term is narrower than domain data ownership.
- A **Compose-provisioned datastore** is a MongoDB or MySQL component declared in `docker-compose.yml`; its presence does not prove that a running service connects to it.
- A **duplicated type name** is a Java class, interface or enumeration name occurring in more than one module. It identifies a review candidate, not necessarily duplicated semantics.

### 4.1.3 Automated analysis method

The analysis was automated by the Python program [`architecture_inventory.py`](../../tools/architecture_inventory.py). It uses only the Python standard library and is executed from the repository root as follows:

```powershell
python .\tools\architecture_inventory.py
```

The program first parses the root and module Maven descriptors to identify reactor membership, artifacts, frameworks, database drivers and use of `ts-common`. It then parses the top-level Compose service definitions to collect images, build contexts, ports and database components. Production Java controllers are scanned for Spring request-mapping annotations, after which class-level and method-level paths are combined to reconstruct each available REST interface.

Outgoing dependencies are extracted from literal service URLs and the repository’s `getServiceUrl(...)` pattern. Local URL-variable uses are followed to recover the callee, endpoint and HTTP method where possible. Application configuration is inspected for active JDBC and MongoDB declarations; commented examples are excluded. Entity and repository declarations are then associated with their source modules. Source persistence and Compose datastores are compared, but retained as separate evidence layers.

Finally, the analyzer calculates caller and callee sets, fan-in, fan-out, an adjacency matrix and a Mermaid dependency graph. It also compares Java type names across modules. Each generated observation contains a repository-relative file and line reference where applicable. Results are written to [`docs/discovery/generated`](generated/).

The program additionally produces candidate contexts and a provisional migration ranking. These outputs are marked `INFERRED_REQUIRES_REVIEW`: context assignment uses service-name heuristics, while the initial ranking favours lower static HTTP degree. They are not treated as observed results or final architectural decisions.

### 4.1.4 Research artifacts

**Table 4.1: Principal static-analysis artifacts**

| Artifact | Purpose |
|---|---|
| [`service-catalog.csv`](generated/service-catalog.csv) | Components, classifications, images, ports and technologies |
| [`endpoints.csv`](generated/endpoints.csv) | REST methods, paths, controllers and evidence |
| [`http-dependencies.csv`](generated/http-dependencies.csv) | Production HTTP call sites and caller–callee evidence |
| [`callers-callees.csv`](generated/callers-callees.csv) | Aggregated callers, callees, fan-in and fan-out |
| [`dependency-matrix.csv`](generated/dependency-matrix.csv) | Directed service-dependency matrix |
| [`dependency-graph.mmd`](generated/dependency-graph.mmd) | Mermaid representation of the dependency graph |
| [`data-ownership.csv`](generated/data-ownership.csv) | Source-configured stores, entities and repositories |
| [`deployment-datastores.csv`](generated/deployment-datastores.csv) | Datastores declared by Compose |
| [`source-compose-datastore-mismatches.csv`](generated/source-compose-datastore-mismatches.csv) | Source/Compose datastore-type differences |
| [`duplicated-types.csv`](generated/duplicated-types.csv) | Type names occurring in multiple modules |
| [`quality-report.csv`](generated/quality-report.csv) | Validation status and review items |

The machine-readable artifacts constitute the detailed evidence appendix. This avoids manually transcribing hundreds of observations and permits regeneration after controlled repository changes.

### 4.1.5 Validation

The generated results were checked independently using repository searches rather than relying only on the analyzer’s internal counts. All 42 Maven child modules and 68 Compose components were represented in the catalog. The 262 generated endpoint rows exactly matched the 262 production method-mapping annotations found independently; no duplicate service/method/path row or malformed path was found. All HTTP callers and callees resolved to catalogued components, and the 90 unique caller–callee pairs matched the 90 edges in the generated graph.

The 25 source persistence rows matched 25 independently detected active MySQL JDBC configurations, while 25 deployment datastore rows matched the 25 Compose database definitions. Every generated `file:line` reference resolved to an existing source line. Two consecutive executions on unchanged inputs produced identical SHA-256 hashes, and the Python program passed byte-code compilation.

Validation initially revealed that commented MongoDB examples and multiple configuration examples were being counted. The persistence extractor was corrected to ignore commented lines and consolidate each service/store combination. The generated and independent counts subsequently matched. This correction demonstrates the importance of validation independent of the automation implementation.

### 4.1.6 Results

**Table 4.2: Verified static architecture inventory**

| Measure | Result |
|---|---:|
| Maven child modules | 42 |
| Reactor projects including root aggregator | 43 |
| Compose components | 68 |
| Distinct source/deployment components | 75 |
| Source-inspected service modules | 41 |
| Other local source/deployment modules | 5 |
| Shared-library modules | 1 |
| Image-only services | 2 |
| Database and infrastructure components | 26 |
| REST endpoints | 262 |
| Production HTTP call sites | 158 |
| Unique source-level HTTP edges | 90 |
| Source-configured persistence responsibilities | 25 |
| Compose-provisioned datastores | 25 |
| Cross-module duplicated Java type names | 45 |

The component total is larger than either the Maven or Compose view because the build, source and deployment structures are not identical. Components were therefore classified instead of assuming that every directory, reactor module and Compose service represents the same architectural unit.

#### 4.1.6.1 REST interface surface

The largest declared API surfaces belonged to `ts-admin-basic-info-service` with 21 endpoints, `ts-order-service` and `ts-order-other-service` with 16 each, `ts-travel-service` with 13 and `ts-travel2-service` with 12. Endpoint count measures interface size only; it does not measure runtime traffic, implementation complexity or business importance. Individual observations can be traced to source annotations, such as the base path in [`AdminBasicInfoController.java`](../../ts-admin-basic-info-service/src/main/java/adminbasic/controller/AdminBasicInfoController.java#L21).

#### 4.1.6.2 Service-dependency structure

The 158 HTTP call sites reduced to 90 unique directed service edges. Tables 4.3 and 4.4 show the highest fan-in and fan-out values.

**Table 4.3: Highest observed static fan-in**

| Service | Fan-in | Fan-out |
|---|---:|---:|
| `ts-order-service` | 8 | 1 |
| `ts-order-other-service` | 8 | 1 |
| `ts-station-service` | 8 | 0 |
| `ts-train-service` | 7 | 0 |
| `ts-route-service` | 7 | 0 |
| `ts-travel-service` | 6 | 4 |
| `ts-seat-service` | 6 | 3 |

These services have comparatively broad consumer sets; changing their external contracts may therefore affect several callers. This indicates potential coordination risk but does not establish that they belong in one module.

**Table 4.4: Highest observed static fan-out**

| Service | Fan-in | Fan-out |
|---|---:|---:|
| `ts-preserve-service` | 1 | 11 |
| `ts-preserve-other-service` | 0 | 11 |
| `ts-rebook-service` | 0 | 8 |
| `ts-admin-basic-info-service` | 0 | 5 |
| `ts-admin-travel-service` | 0 | 5 |
| `ts-cancel-service` | 0 | 5 |
| `ts-travel-plan-service` | 0 | 5 |

The high fan-out of the preserve services is consistent with an orchestration role in booking workflows. This interpretation requires confirmation through business-logic inspection and runtime traces.

One call remains partially unresolved. `ts-wait-order-service` constructs a `ts-preserve-service` URL in [`PollThread.java`](../../ts-wait-order-service/src/main/java/waitorder/utils/PollThread.java#L43), while an indirectly invoked method posts to `/api/v1/contactservice/preserve` at [line 74](../../ts-wait-order-service/src/main/java/waitorder/utils/PollThread.java#L74). The target/path naming difference requires source and runtime investigation.

#### 4.1.6.3 Persistence and deployment discrepancy

The checked-in source contains 25 active MySQL JDBC configurations. For example, `ts-order-service` configures MySQL in [`application.yml`](../../ts-order-service/src/main/resources/application.yml#L10) and declares Spring Data JPA and the MySQL driver in its [`pom.xml`](../../ts-order-service/pom.xml#L31). In contrast, Compose provisions 24 MongoDB containers and one MySQL container. Nineteen services have a direct mismatch between their local source configuration and the datastore component named for them in Compose. For example, Compose declares `ts-order-mongo` in [`docker-compose.yml`](../../docker-compose.yml#L124), whereas the inspected source configures MySQL.

This does not prove that a running service uses both database types. Compose may execute prebuilt `${IMG_REPO}/*:${IMG_TAG}` images whose implementation differs from the checked-in source. Static analysis cannot establish the producing Git revision or runtime database connection of an unlabelled image. Source configuration, deployment declaration and future runtime connections must therefore remain separate evidence layers. The candidate owner of `ts-account-mongo` was also left unresolved because its name does not establish ownership reliably.

#### 4.1.6.4 Source availability and duplicated types

Two deployed services have no locally inspectable implementation: `ts-ticketinfo-service` ([`docker-compose.yml`](../../docker-compose.yml#L240)) and `ts-food-map-service` ([`docker-compose.yml`](../../docker-compose.yml#L431)). Their internal endpoints, dependencies, persistence and rules cannot be determined from this clone.

The reactor contains the shared `ts-common` library ([`pom.xml`](../../pom.xml#L18)). Cross-module comparison also found 45 duplicated type names. Same-named types may represent genuinely duplicated code, context-specific models, transport objects or persistence representations. Their fields, behaviour, ownership and lifecycle must be compared before any consolidation decision is made.

### 4.1.7 Architectural implications

The automated candidate groupings include administration, booking and order lifecycle, consignment, customer communication, food and delivery, identity and customer management, payment and assurance, and rail network and timetable management. These are hypotheses intended to make assumptions reviewable; service names alone cannot determine bounded contexts.

Likewise, low static coupling is insufficient to select the first migration target. A defensible order must also consider business cohesion, transaction boundaries, persistence responsibility, runtime frequency and latency, failure propagation, test coverage, source availability and rollback risk. Consequently, neither final module boundaries nor a final migration order were established during static analysis.

### 4.1.8 Threats to validity

The extraction uses annotation recognition, regular expressions and local variable analysis rather than a complete Java compiler front end. Calls assembled through complex interprocedural logic, reflection, generated clients or external configuration may be missed. Static dependencies indicate possible communication, not actual use, frequency or performance. Prebuilt-image internals remain unavailable, and the images may represent a different revision. Finally, duplicated names do not demonstrate duplicated semantics.

The baseline Maven command used `-DskipTests`; tests were compiled but not executed. No automated test-success claim is therefore made.

### 4.1.9 Summary and transition to dynamic analysis

The automated static analysis established a reproducible inventory with complete Maven and Compose coverage. It identified 262 REST endpoints, 158 production HTTP call sites, 90 unique service edges, 25 source-configured persistence responsibilities and 45 cross-module duplicated type names. It also exposed two unavailable implementations and a material discrepancy between MySQL-oriented source and the MongoDB-oriented deployment configuration.

These results describe the architecture visible in repository artifacts, not the architecture exercised at runtime. The next analysis stage will execute controlled business scenarios and collect distributed traces, service logs and container metrics. Static and runtime edges will be classified as `OBSERVED_IN_BOTH`, `STATIC_ONLY`, `RUNTIME_ONLY`, `IMAGE_ONLY` or `UNRESOLVED`. Absence from a trace will mean only that an edge was not exercised by the recorded workload; it will not be treated as proof that the dependency is unused. Final module boundaries will be reviewed after static evidence, dynamic evidence and domain analysis have been considered together.
