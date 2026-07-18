# Engineering Walkthrough

This document explains the current engineering design of the Job Market Intelligence Platform. It is intended as both a learning resource and an interview-preparation guide. It describes what the repository does today, why the main components exist, where the design is incomplete, and how the same problems might be approached at larger scale.

The following labels are used throughout:

- **Current implementation** describes code that exists now.
- **Known problem** describes confirmed behavior or a limitation in the current code.
- **Planned improvement** describes a reasonable next step, not completed work.
- **Production-scale alternative** describes an option that may become useful at higher volume or operational complexity. It is not automatically better for this project.
- **Assumption** identifies something that has not been established by the code or repository evidence.

## 1. Project purpose

The project collects US job listings for data-related roles from the Adzuna API and stores them in PostgreSQL. Its business purpose is to support analysis of job titles, employers, locations, salaries, skills, and remote-work signals.

From an engineering perspective, the project demonstrates several parts of a data pipeline:

1. communicating with an external HTTP API;
2. parsing semi-structured JSON responses;
3. loading normalized records into a relational database;
4. beginning to transform those records into a dimensional warehouse;
5. testing selected behavior with pytest;
6. analyzing stored data from a notebook.

The project is deliberately small enough to run locally. PostgreSQL is the system of record, Python is the pipeline language, and Docker provides a repeatable local database service. No workflow orchestrator or cloud platform is currently required to understand or run the core design.

### How to explain this in an interview

> I built the project to answer a real business question about the data job market while practicing an end-to-end data workflow. Python extracts and transforms listings from Adzuna, PostgreSQL stores the data, and a developing dimensional layer is intended to support repeatable analytics. The current project is local and portfolio-sized, so I have focused on understandable components rather than adding distributed tools that the data volume does not need.

## 2. Current architecture

The current repository contains two database-loading paths and one analysis path:

```text
Adzuna API
    |
    v
ingestion/api_client.py
    |
    v
processing/transform.py
    |
    v
pipeline.py --------------------------> PostgreSQL: job_listings
                                             |
                                             v
                                  warehouse/build_warehouse.py
                                             |
                                             v
                          dim_* tables + fact_job_listing

notebooks/01_eda.ipynb ----------------> reads job_listings directly
```

**Current implementation:** [`pipeline.py`](../pipeline.py) initializes database tables, extracts listings, transforms them into `JobListing` objects, and loads `job_listings`. Warehouse construction is a separate command in [`warehouse/build_warehouse.py`](../warehouse/build_warehouse.py). The ingestion pipeline does not call the warehouse builder.

The main separation of responsibilities is:

- [`ingestion/api_client.py`](../ingestion/api_client.py): HTTP communication and pagination;
- [`processing/transform.py`](../processing/transform.py): conversion from API dictionaries to model fields;
- [`db/models.py`](../db/models.py): the source-listing ORM model and shared declarative base;
- [`db/connection.py`](../db/connection.py): database engine, session factory, and table initialization;
- [`warehouse/`](../warehouse/): dimensional models and loader functions;
- [`tests/`](../tests/): current unit-style tests;
- [`notebooks/01_eda.ipynb`](../notebooks/01_eda.ipynb): exploratory analysis of `job_listings`.

**Known problem:** the repository does not yet expose one command that completes ingestion and warehouse construction safely. Calling the scripts separately is possible, but a successful ingestion run does not mean the warehouse is current.

**Planned improvement: To be completed.** A later orchestration task should provide explicit commands for ingestion, warehouse construction, and the complete workflow after warehouse idempotency is fixed.

### How to explain this in an interview

> I separated API extraction, transformation, database infrastructure, and warehouse loading into different modules so each responsibility is easier to understand and test. At the moment, raw ingestion and warehouse construction are separate entry points. I would not describe the warehouse flow as complete yet because it still needs safe rerun behavior and a single documented orchestration path.

## 3. Current end-to-end data flow

The active ingestion flow is implemented by `run()` in [`pipeline.py`](../pipeline.py):

1. `init_db()` calls `Base.metadata.create_all(engine)`.
2. `fetch_all_roles()` loops through six configured search roles.
3. `fetch_all_jobs()` requests up to five pages for each role by default.
4. Each returned dictionary is tagged with the search role that produced it.
5. `parse_job()` creates a `JobListing` ORM object.
6. Records without an Adzuna ID are rejected during parsing and logged by the pipeline.
7. `session.get()` checks whether that `source_listing_id` already exists.
8. New objects are added to one SQLAlchemy session.
9. One commit persists the batch; an unhandled load error rolls the batch back.

The optional warehouse flow currently runs separately:

1. read every row from `job_listings`;
2. load or look up company, job-title, location, and date dimension rows;
3. insert a fact row containing dimension keys and salary values;
4. commit the warehouse transaction after all source rows are processed.

**Known problem:** this is not a fully safe end-to-end flow. A warehouse build appends a new fact for every source row each time it runs. In addition, missing `created`, `title`, or location values can prevent a warehouse build from completing.

**Known problem:** `fetch_all_jobs()` catches request errors, logs them, and stops fetching that role. The outer pipeline may still commit data from other roles and report completion, so a completed run can contain partial extraction results.

### How to explain this in an interview

> The ingestion entry point first ensures tables exist, fetches paginated data for each search role, transforms each API result into the database model, and commits new listings as one batch. The warehouse is currently a second step. One limitation I identified is that extraction errors can result in a partial successful run, so a future version should record run status and distinguish complete from partial extraction.

## 4. Repository structure

```text
.
|-- analytics/                 # Empty SQL placeholders
|-- app/                       # Currently only a package marker
|-- config/                    # Centralized database configuration
|-- db/
|   |-- connection.py         # Engine, session factory, create_all
|   `-- models.py             # Shared Base and JobListing
|-- ingestion/
|   `-- api_client.py         # Adzuna HTTP client and pagination
|-- notebooks/
|   `-- 01_eda.ipynb          # Analysis against job_listings
|-- processing/
|   `-- transform.py          # API dictionary to JobListing
|-- tests/                     # Current pytest suite
|-- warehouse/                # Dimensions, fact, and loaders
|-- docker-compose.yml         # Local PostgreSQL service
|-- logger.py                  # Logging configuration
|-- pipeline.py               # Raw ingestion entry point
|-- requirements.txt          # Runtime and analysis dependencies
`-- requirements-dev.txt      # Dependencies needed by current tests
```

Python package marker files such as `__init__.py` allow modules to be imported with names such as `db.models` and `warehouse.fact_models`.

**Known problem:** `app/` and the two analytics SQL files are placeholders rather than implemented layers. They should not be described as working application or analytics functionality.

## 5. PostgreSQL and Docker setup

[`docker-compose.yml`](../docker-compose.yml) defines a PostgreSQL 15 container. It creates a development database and stores its data in the named `postgres_data` volume. A named volume keeps database files outside the disposable container so the data survives ordinary container recreation.

The port mapping is:

```yaml
ports:
  - "5433:5432"
```

PostgreSQL listens on port `5432` inside the container. A program running on the host reaches it through port `5433`.

Docker solves a reproducibility problem: developers do not need to manually install and configure the same PostgreSQL version. It does not containerize the Python application; only the database service is defined.

The standard local configuration is now explicit. Python running directly on the host uses `DB_HOST=localhost` and `DB_PORT=5433`. If Python later runs as another service inside the same Compose network, it must use `DB_HOST=db` and `DB_PORT=5432`, because containers communicate through the service name and internal port rather than the published host port.

No Docker change was required: the existing `5433:5432` mapping already represents the intended host-to-container boundary. [`.env.example`](../.env.example) and the Python defaults now match the host-execution side of that mapping.

**Production-scale alternative:** a managed PostgreSQL service could handle backups, upgrades, monitoring, and high availability. That would solve operational requirements, not improve the current transformation logic, so it is not necessary merely to make the portfolio stack larger.

### How to explain this in an interview

> I use Docker Compose to provide a repeatable local PostgreSQL service with persistent storage. PostgreSQL listens on port 5432 inside the container and Docker publishes it as port 5433 on the host. My local Python defaults therefore use `localhost:5433`; code running inside the Docker network would use the `db` service on port 5432. Keeping that distinction explicit avoids environment-specific connection errors.

## 6. SQLAlchemy model registration and shared `Base`

SQLAlchemy's declarative `Base` is the registry from which ORM table metadata is collected. The project defines one base in [`db/models.py`](../db/models.py):

```python
class Base(DeclarativeBase):
    pass
```

`JobListing`, every dimension, and `FactJobListing` inherit from this same class. This means their table definitions belong to one `Base.metadata` collection.

[`db/connection.py`](../db/connection.py) imports the warehouse model classes before calling:

```python
Base.metadata.create_all(engine)
```

The imported class names are not otherwise used in that module. Importing them executes their class definitions, which registers the tables in the shared metadata. Current inspection confirms six registered tables:

- `job_listings`;
- `dim_company`;
- `dim_job`;
- `dim_location`;
- `dim_date`;
- `fact_job_listing`.

This avoids the common problem of defining multiple declarative bases or calling `create_all()` before model modules have been imported.

**Trade-off:** importing warehouse models from the connection module couples infrastructure code to downstream models. A dedicated model-registration module could make that dependency more explicit.

**Known problem:** `create_all()` creates missing tables but is not a schema migration system. It will not reliably evolve existing tables when columns or constraints change.

**Planned improvement: To be completed.** Introduce schema migrations after the warehouse schema and constraints are stabilized.

### How to explain this in an interview

> I used a shared SQLAlchemy declarative Base so all source and warehouse models are registered in the same metadata collection. Database initialization imports the model modules before calling `create_all`, which lets SQLAlchemy discover all six tables. `create_all` is appropriate for initial development setup, but it is not a replacement for versioned migrations once the schema starts evolving.

## 7. Extraction from the Adzuna API

[`ingestion/api_client.py`](../ingestion/api_client.py) contains three levels of extraction:

- `fetch_jobs()` performs one HTTP request for one role and page;
- `fetch_all_jobs()` paginates one role;
- `fetch_all_roles()` repeats pagination for all configured roles.

The client sends credentials and query parameters through `requests.get()`, uses a ten-second timeout, raises for non-successful HTTP status codes, and parses the JSON response. A timeout prevents a request from waiting forever.

`fetch_jobs()` accepts optional keyword-only `app_id` and `app_key` arguments. When an argument is omitted, the function reads the matching environment variable at call time. Normal local execution can therefore continue to use values loaded from `.env`, while tests can pass explicit dummy credentials without depending on the developer's machine. `fetch_all_jobs()` and `fetch_all_roles()` accept and forward the same optional values. If either resolved credential is missing, the client raises a clear error before making an HTTP request. Credential values are not included in logs or error messages.

Pagination stops when the configured maximum is reached, when a page contains no results, or when a request error occurs. Short sleeps are used between pages and roles. This is a simple form of request pacing; it is not a complete retry or rate-limit strategy.

Each result is modified to include `search_role`. This makes it possible to know which configured query returned the listing.

**Known problem:** a listing may match more than one search role. Because `job_listings.source_listing_id` is the primary key and existing records are skipped, only the first stored search role is retained.

**Planned improvement: To be completed.** Introduce bounded retry/backoff for transient failures, report partial extraction explicitly, and decide how multiple search-role matches should be modeled.

**Production-scale alternative:** a larger ingestion service might use durable queues, centralized rate-limit handling, and checkpointed page state. Those mechanisms would be justified by higher volume or stronger recovery requirements; they are unnecessary for the present API volume.

### How to explain this in an interview

> I separated a single API request from pagination and from looping over search roles. Credentials can be passed explicitly, which makes tests independent of my local `.env`, while omitted values still resolve from the environment for normal execution. I use a timeout and basic request pacing, but the current client does not yet retry transient errors or persist extraction checkpoints. At this scale, a small synchronous client is appropriate, and I would add operational complexity only when the failure and volume requirements justify it.

## 8. Transformation and loading

[`processing/transform.py`](../processing/transform.py) translates an Adzuna response dictionary into a `JobListing` ORM object. It extracts values from nested company, location, and category objects; converts salary values to floats; and parses the source timestamp.

The transformation layer solves a schema-boundary problem. API JSON is nested and controlled by an external provider, while the database model is flat and controlled by this project. Keeping field mapping in one function makes changes easier to locate.

The location `area` list is reduced to its final element, which the code treats as the most specific location component. ISO timestamp strings ending in `Z` are changed to an explicit UTC offset before `datetime.fromisoformat()` is used.

**Known problem:** an invalid date is silently converted to `None`. The source row is not quarantined and the reason is not recorded.

**Known problem:** the function returns an ORM object rather than a persistence-independent data object. This is simple, but it couples transformation to SQLAlchemy.

**Known problem:** `job_listings` is described informally as raw storage, but it contains flattened, transformed fields and does not preserve the original JSON response.

**Planned improvement: To be completed.** Add explicit validation behavior and decide whether the project needs true raw JSON retention or should call this layer staging/current-state storage.

**Production-scale alternative:** schema validation tools, raw object storage, and distributed transformation engines can help with high volume and replay requirements. For the current volume, a Python function and PostgreSQL are easier to operate.

### How to explain this in an interview

> The transform function is an adapter between Adzuna's nested JSON and my relational model. It handles nested fields, salary conversion, and timestamp parsing in one place. The current implementation creates ORM objects directly, which is convenient for a small pipeline, although a larger system might validate into persistence-independent records and retain the original payload for replay.

## 9. Current warehouse structure

The warehouse is an initial star-schema design. A star schema places measurable business events in a fact table and descriptive context in dimensions.

| Table | Current purpose | Key |
|---|---|---|
| `dim_company` | One stored company name | `company_key` surrogate key |
| `dim_job` | One normalized job title found by the loader | `job_key` surrogate key |
| `dim_location` | Display location and area combination | `location_key` surrogate key |
| `dim_date` | Posting calendar attributes | `date_key` in `YYYYMMDD` form |
| `fact_job_listing` | One current Adzuna listing with dimension references and salary range | `fact_id` surrogate key; unique `source_listing_id` business key |

A surrogate key is a warehouse-generated identifier with no source-system meaning. It allows facts to reference dimension rows independently of changing source text. `dim_date.date_key` is a meaningful integer rather than an auto-generated key, which is a common date-dimension convention.

The official fact grain at this stage is:

> One row in `fact_job_listing` represents one unique Adzuna job listing currently stored by the platform.

`fact_id` and `source_listing_id` serve different purposes. `fact_id` is the warehouse surrogate primary key: it identifies the physical warehouse row. `source_listing_id` is the business key supplied by Adzuna: it identifies which real source listing the row represents. Company, job, location, and date keys remain foreign keys that describe the listing; they do not define its identity.

The Adzuna ID is persisted as `job_listings.source_listing_id`, forwarded by the warehouse builder, and stored as the required `fact_job_listing.source_listing_id`. PostgreSQL enforces a named unique constraint on the fact business key. Application checks are useful, but the database constraint is the final protection against two fact rows claiming to represent the same listing.

Title, company, location, and posting date cannot safely form a business key. A company may advertise multiple genuinely distinct roles with the same title, location, and date, and those listings must remain separate.

Dimension loaders perform a lookup before inserting. They call `session.flush()` so database-generated keys are available immediately without committing the overall transaction. Company values are trimmed, and job titles are trimmed and converted to lowercase by their loaders.

### How to explain this in an interview

> I defined the fact grain as one row per unique current Adzuna listing. The warehouse keeps `fact_id` as its surrogate primary key, while `source_listing_id` carries the source-system business identity and has a PostgreSQL uniqueness constraint. Dimension keys describe the listing but do not identify it, because different listings can legitimately share the same title, company, location, and date.

## 10. Current warehouse limitations

The most important warehouse concept is the **grain**: the exact real-world event represented by one fact row. The current-state grain is now explicit and protected by the unique Adzuna business key. This does not yet make the warehouse loader safely rerunnable.

Confirmed limitations include:

- a second warehouse run attempts to insert the same business keys and will fail on the unique constraint rather than silently duplicate facts;
- all fact foreign keys are nullable;
- `dim_job.title` has no database uniqueness constraint;
- `dim_location` has no uniqueness constraint for its identifying attributes;
- `build_warehouse()` assumes `job.title`, `job.location_display`, and `job.created` are usable even though the source model permits missing location and date values;
- salary values use floating-point columns;
- the fact does not retain salary prediction status, contract attributes, source category, or search-role information;
- the warehouse represents current listings and does not preserve listing snapshots or changes over time.

Loader-side lookup checks help in a single process, but database constraints are still needed to enforce identity when code changes or concurrent writers exist.

Records without a source ID are rejected by `parse_job()` with a clear validation error. The pipeline logs that parse failure and does not persist the record. The fact loader performs the same validation defensively. The project does not generate identity from unstable descriptive fields.

`Base.metadata.create_all()` will not rename the existing `job_listings.id` column or add the new fact column and constraint to tables that already exist. Because old fact rows contain no reliable source ID to backfill, the safest practical development approach is to back up anything important, recreate the local development database, rerun ingestion, and then build the warehouse once. No schema reset is performed automatically by the project or this walkthrough.

**Planned improvement: To be completed.** Add conflict-aware fact loading and a PostgreSQL integration test that runs the warehouse twice. Also enforce natural-key uniqueness for dimensions and establish an unknown-member policy.

The current-state design keeps at most one fact for each Adzuna ID. A future snapshot design would use a different grain, such as one row per `(source_listing_id, observation_date)` or ingestion run, so the same listing could appear intentionally at multiple points in time. Snapshot history is not implemented in the current model.

**Production-scale alternative:** at larger scale, set-based SQL transformations, bulk upserts, partitioned facts, incremental watermarks, or a transformation framework could replace row-by-row ORM loading. The correct choice depends on volume and operational requirements.

### How to explain this in an interview

> The current fact grain is one unique current Adzuna listing. I retain a warehouse surrogate `fact_id`, but I also store Adzuna's ID as `source_listing_id` and enforce it as unique in PostgreSQL. That prevents silent duplicate facts. The loader still needs conflict handling so a rerun succeeds instead of failing, and a future snapshot warehouse would deliberately use a different composite grain.

## 11. Testing strategy

The current pytest suite contains 26 tests covering:

- construction and representation of a `JobListing` Python object;
- successful transformation and selected missing or malformed fields;
- salary conversion;
- API response handling through mocked HTTP calls;
- pagination stopping and collection behavior;
- correct request parameters, including explicitly injected dummy credentials;
- expected pagination pacing without performing real waits;
- the missing-credential guard;
- database configuration defaults and environment overrides;
- SQLAlchemy URL construction, numeric port conversion, and safe secret representation;
- source-listing parsing, persistence, fact propagation, and missing-ID rejection;
- fact business-key uniqueness and preservation of dimension foreign keys.

The tests are currently unit-style tests. They do not connect to PostgreSQL and do not verify table creation, database constraints, transactions, warehouse loaders, or end-to-end behavior. `test_job_listing_creation()` verifies Python attribute assignment, not database persistence.

Mocking `requests.get()` is appropriate because unit tests should not depend on Adzuna availability, consume rate limits, or require network access. Every API test either mocks `requests.get()` directly or mocks `fetch_jobs()` at the pagination boundary, so the suite cannot reach Adzuna. The `mocker` fixture comes from `pytest-mock`.

Tests pass explicit dummy `app_id` and `app_key` values when exercising authenticated behavior. The missing-credential test removes both environment variables and verifies that validation fails before `requests.get()` is called. Pagination tests replace `time.sleep()` with a mock: they assert the expected `0.5`-second calls, preserving verification of rate-limiting behavior without delaying the suite.

The current suite was most recently run with:

```powershell
py -m pytest -q -p no:cacheprovider
```

and completed with 26 passing tests in the inspected environment.

**Planned improvement: To be completed.** Add warehouse unit tests and PostgreSQL integration tests for constraints, rollback, upsert behavior, and rerun counts.

**Production-scale alternative:** a mature pipeline might also have contract tests against recorded API schemas, data-quality tests, migration tests, and scheduled end-to-end tests. Live external API calls should remain outside the normal unit-test suite.

### How to explain this in an interview

> I use pytest for transformation and API-client behavior. API tests inject dummy credentials, mock every HTTP boundary, and mock sleep calls, so they do not depend on my local `.env`, the live provider, or real delays. The existing suite is still mostly unit-level. I have identified that database constraints, transaction rollback, and warehouse reruns need PostgreSQL integration tests before adding CI as a meaningful quality gate.

## 12. Development dependencies

[`requirements-dev.txt`](../requirements-dev.txt) is a pinned, standalone dependency set for the existing tests:

```text
requests==2.33.1
python-dotenv==1.2.2
sqlalchemy==2.0.40

pytest==8.4.1
pytest-mock==3.14.1
```

The first three packages are runtime libraries imported by the code exercised in the tests. `pytest` is the test runner, and `pytest-mock` supplies the `mocker` fixture used by API tests.

Keeping a focused development file solves two problems:

1. a developer can install the exact direct dependencies needed by the current suite;
2. test setup does not require notebook, visualization, or unused database-driver packages.

Install and run the suite with:

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest -q -p no:cacheprovider
```

**Trade-off:** runtime pins are duplicated between `requirements.txt` and `requirements-dev.txt`, so they must be kept aligned manually. Including all runtime dependencies through `-r requirements.txt` is a common alternative, but it would also install packages unrelated to the existing tests.

### How to explain this in an interview

> I added a small pinned development dependency file containing the runtime libraries exercised by the tests plus pytest and pytest-mock. This makes the current test setup reproducible without installing notebook and visualization dependencies. The trade-off is duplicated version pins, which I need to keep synchronized with the main requirements file.

## 13. Transactions and session ownership

A database transaction groups changes into one unit: either they are committed together or rolled back together.

The project creates sessions in orchestration functions rather than inside each dimension loader:

- `pipeline.run()` owns the raw-load session;
- `warehouse.build_warehouse()` owns the warehouse session;
- individual warehouse loaders add rows and call `flush()`, but do not commit.

This ownership is a good current decision. If every loader committed independently, a failure could leave some dimensions committed and the fact incomplete. With one outer transaction, an unhandled database error triggers `rollback()`, and `finally` closes the session.

`flush()` is different from `commit()`. It sends pending SQL to the database within the current transaction, which allows auto-generated keys to be read, but the changes can still be rolled back.

**Trade-off:** one transaction for the entire batch is simple and atomic, but a very large batch would hold locks and transaction state for longer.

**Production-scale alternative:** larger loads might use bounded batches, staging tables, checkpointing, and an atomic publish or merge step. Batch boundaries would need to preserve a clear recovery rule.

### How to explain this in an interview

> The orchestration layer owns the SQLAlchemy session and transaction. Loader functions can flush to obtain generated keys, but they do not commit independently. That means one failed warehouse build can be rolled back as a unit. For much larger loads I would consider bounded batches or staging-and-merge patterns, but the current single transaction is understandable for this volume.

## 14. Configuration and environment variables

API and database settings are read from environment variables, with `python-dotenv` loading a local `.env` file. [`.env.example`](../.env.example) documents the expected names without containing real credentials:

- `ADZUNA_APP_ID`;
- `ADZUNA_APP_KEY`;
- `DB_HOST`;
- `DB_PORT`;
- `DB_NAME`;
- `DB_USER`;
- `DB_PASSWORD`.

Keeping secrets outside source code is the correct principle. `.env` is ignored by Git, while `.env.example` is safe to share as a template.

The API functions also accept explicit credentials. These parameters are mainly useful for testing and controlled callers; leaving them unset preserves environment-backed application behavior. The values are passed only to the HTTP request parameters and are not logged.

Database configuration is centralized in [`config/settings.py`](../config/settings.py). `get_database_config()` reads the current environment and returns a frozen `DatabaseConfig` containing host, numeric port, database name, user, and password. Calling a function rather than defining environment-derived constants means tests can change environment variables and request a fresh configuration without reloading the module.

The database connection flow is:

```text
.env / process environment
        |
        v
get_database_config()
        |
        v
immutable DatabaseConfig
        |
        v
SQLAlchemy URL.create()
        |
        v
db.connection engine + SessionLocal
```

`db.connection` loads `.env`, calls the configuration factory, and creates the process-wide engine. Environment variables therefore need to be set before `db.connection` is imported. The factory itself is not frozen at module import: calling it again reads the current environment, which makes focused configuration tests deterministic.

The SQLAlchemy URL is built with `URL.create()` rather than string interpolation. This correctly handles credentials containing URL-sensitive characters. `DatabaseConfig` is immutable, its password is omitted from its normal representation, and SQLAlchemy masks the password when the URL is converted to a normal string. The connection logger uses only host, port, and database name.

The analysis notebook still creates its own direct pg8000 connection. It is currently a separate analysis client, not part of the application engine/session infrastructure; consolidating notebook connection code is outside this task.

**Production-scale alternative:** deployed systems normally inject secrets through the platform's secret manager or runtime environment instead of storing a `.env` file on the server.

### How to explain this in an interview

> I keep database settings in environment variables and resolve them through one small configuration factory. It returns an immutable object and uses SQLAlchemy's structured URL builder, so credentials are not manually interpolated or shown in safe representations. The factory reads the environment each time it is called, which keeps tests deterministic, while the application creates one engine after loading its local `.env`. Host execution uses `localhost:5433`; Docker-network execution would use `db:5432`.

## 15. Logging and error handling

[`logger.py`](../logger.py) configures two handlers:

- a console handler at the requested level;
- a rotating file handler that records debug-level messages.

Rotation limits each log file to approximately 5 MB and keeps three backups, preventing unbounded file growth. Modules obtain named loggers with `logging.getLogger(__name__)`, while the entry point calls `setup_logging()`.

The pipeline logs major stages and final inserted, skipped, and error counts. API errors include role and page context. An unhandled database-load error is logged with a traceback by `logger.exception()`.

**Known problem:** calling `setup_logging()` more than once adds more handlers, which can duplicate output. Runtime log files are also present in the repository working tree and are not useful source artifacts.

**Known problem:** broad exception handling around parsing can classify programming defects as bad input. Invalid date parsing is silently ignored inside the transformer. API request failures are logged but converted into partial extraction rather than an explicit failed/partial run state.

**Planned improvement: To be completed.** Make logging setup idempotent, add a run identifier and structured run summary, classify validation versus programming errors, and record run status.

**Production-scale alternative:** centralized structured logging and metrics would allow alerting by run, role, error type, and data freshness. Local rotating logs are sufficient for current development but not multi-instance operation.

### How to explain this in an interview

> I use module-level loggers and configure console plus rotating file output at the entry point. The logs include stages, counts, and API role/page context. The next observability improvement is to give each pipeline execution a run ID and explicit success, partial, or failed status instead of treating logged request errors as a completed run.

## 16. Idempotency

An idempotent operation can be repeated with the same input without creating additional unintended results.

Raw ingestion uses the Adzuna ID as the `job_listings.source_listing_id` primary key. Before adding a listing, the pipeline checks for that ID and skips it if present. This prevents duplicate source rows during ordinary sequential reruns.

This is insert-only deduplication, not a true upsert. An **upsert** inserts a missing row and updates an existing row. The current pipeline does not refresh changed salaries, descriptions, titles, or last-seen times.

Warehouse loading is not yet idempotent. `fact_job_listing.source_listing_id` is unique, so PostgreSQL prevents duplicate facts, but `load_fact_job_listing()` still always attempts an insert. Repeating `build_warehouse()` therefore raises a uniqueness error instead of completing successfully.

Loader-side dimension lookups reduce duplicates in a single sequential process, but missing database uniqueness constraints still leave some dimensions unprotected.

**Planned improvement: To be completed.** Add conflict-aware current-state fact loading and test that two identical warehouse runs complete with unchanged fact counts.

### How to explain this in an interview

> Raw ingestion prevents duplicate source IDs but does not update changed listings. The fact table now has the same source business identity and PostgreSQL prevents duplicate facts. That establishes correctness of the grain, but idempotency also requires the second run to succeed, so the next step is conflict-aware loading plus a two-run integration test.

## 17. Analytics layer

The implemented analysis is in [`notebooks/01_eda.ipynb`](../notebooks/01_eda.ipynb). It connects directly to PostgreSQL and selects from `job_listings`. It analyzes counts, skills found through regular expressions, salary ranges, locations, and remote-work terms.

[`analytics/views.sql`](../analytics/views.sql) and [`analytics/queries.sql`](../analytics/queries.sql) currently exist as empty placeholders. The notebook does not query the dimensional warehouse.

**Current implementation:** exploratory analysis exists over the flattened source table.

**Known problem:** there is no implemented SQL analytics layer proving that the warehouse supports a BI consumer. Notebook logic also contains business definitions, such as remote classification, that are not centralized or tested.

**Planned improvement: To be completed.** After the warehouse grain is corrected, add a small set of documented analytical views or queries and point the notebook or a BI tool at those outputs.

**Production-scale alternative:** reusable transformations could be managed through versioned SQL models and data-quality tests. A semantic or metrics layer may help when many reports need identical definitions, but it would be premature for the current repository.

### How to explain this in an interview

> The current notebook reads the source listing table and contains the exploratory definitions for skills, salaries, and remote work. The SQL analytics files and warehouse consumer are not implemented yet. My plan is to stabilize the warehouse first, then move reusable business definitions into tested SQL views so a notebook or BI tool uses consistent logic.

## 18. Important engineering decisions

| Decision | Problem solved | Current trade-off | Alternative |
|---|---|---|---|
| PostgreSQL instead of CSV-only storage | Persistent keys, constraints, SQL queries, and concurrent access | Requires database setup | SQLite for a simpler demo; managed PostgreSQL for deployment |
| Docker for local PostgreSQL | Reproducible database version and isolated setup | Host/container configuration must be understood | Native installation or managed database |
| Immutable database configuration factory | One tested source of truth with runtime environment overrides | The process-wide engine still uses the configuration resolved when `db.connection` is imported | Application factory or explicit engine construction for multi-database processes |
| SQLAlchemy ORM models | Python-visible schema and session/transaction management | ORM loading can encourage row-by-row queries | SQLAlchemy Core or direct bulk SQL |
| One shared declarative `Base` | Registers source and warehouse tables together | Connection module imports model modules for side effects | Explicit model registry package |
| Separate API, transform, and load modules | Localizes responsibilities and changes | Transform still depends on the ORM model | Validated data-transfer object between layers |
| One commit per current batch | Atomic load behavior | Not ideal for very large batches | Staging plus merge or bounded transactions |
| Synchronous extraction | Simple and adequate for the current request count | Requests and sleeps are sequential | Concurrent requests only if allowed and operationally useful |
| Focused development requirements | Reproducible current tests without analytics packages | Duplicate runtime pins | Main requirements include or dependency groups in a future packaging setup |

### How to explain this in an interview

> My decisions are based on the current problem size. PostgreSQL gives me relational integrity and SQL analytics, Docker makes the database reproducible, and SQLAlchemy manages models and transactions. I kept extraction synchronous and the code in one project because the API volume does not justify distributed systems. I can still identify where bulk SQL, managed infrastructure, or stronger packaging would become useful later.

## 19. Known technical debt

Technical debt means a known design or implementation limitation that should be managed deliberately. It does not mean every item must be fixed immediately.

### Highest priority

1. Make warehouse builds idempotent.
2. Handle other missing source fields consistently during warehouse loading.
3. Add PostgreSQL integration tests for constraints, transactions, and reruns.
4. Provide one reliable end-to-end execution path.

### Next priority

1. Decide between current-state upserts and historical snapshots.
2. Represent listings returned by multiple search roles correctly.
3. Add explicit extraction-run status and partial-failure reporting.
4. Add database uniqueness constraints for dimension natural keys.
5. Replace floating-point salary storage with a deliberate financial type and retain salary metadata.

### Documentation and repository hygiene

1. Implement or remove empty placeholder layers.
2. Stop tracking runtime logs.
3. Align README claims with executable behavior and sample sizes.
4. Add migrations after the model stabilizes.
5. Add continuous integration after the planned database integration coverage is stable.

### Later roadmap

- **Schema migrations: To be completed.**
- **Analytics views over the warehouse: To be completed.**
- **Continuous integration: To be completed.**
- **Deployment or scheduled execution: To be completed and only if a concrete hosting requirement is selected.**
- **Airflow evaluation: To be completed only after scheduling, retries, backfills, and dependency-management needs exceed a simple job.**

## 20. Interview explanation guide

The answers below are short starting points. They should be adapted to the exact question rather than memorized word for word.

### How to explain the project end to end

> The project fetches job listings from Adzuna for six data-related search roles. A Python client handles requests and pagination, a transform function maps nested JSON into a SQLAlchemy listing model, and the ingestion entry point writes source IDs to PostgreSQL in one transaction. A separate warehouse builder maps the listings into company, job, location, and date dimensions plus a salary fact. The fact grain is one current Adzuna listing and is protected by a unique source business key, although rerun conflict handling is still planned.

### How to explain ETL versus the current design

> The ingestion path follows extract, transform, and load: extract from the API, transform the response fields, and load PostgreSQL. The project also has a second transformation from the listing table into a star schema. I would describe the source table as flattened staging or current-state storage rather than truly raw data because the original JSON is not retained.

### How to explain the star schema

> A star schema separates measurable events from descriptive attributes. The current fact stores salary values and references company, job title, location, and date dimensions. Its grain is one current Adzuna listing, identified by a unique `source_listing_id`. `fact_id` remains a surrogate warehouse key, while dimension foreign keys provide descriptive context rather than business identity.

### How to explain surrogate and natural keys

> Dimension surrogate keys are generated by the warehouse and let fact rows reference stable dimension records. Natural keys are the business attributes used to identify a dimension member, such as a normalized company name. The current dimensions use surrogate primary keys, but some natural-key uniqueness constraints are still missing, so database-level enforcement is planned.

### How to explain transaction handling

> The orchestration functions own the SQLAlchemy sessions. Loader functions flush when they need generated keys but do not commit. This keeps the current batch in one transaction, so an unhandled error can roll it back rather than leaving half of a warehouse load committed.

### How to explain idempotency honestly

> The source table prevents duplicate IDs during sequential reruns, but existing rows are skipped rather than updated. PostgreSQL now also prevents duplicate fact business keys. The warehouse is still not idempotent because a repeated insert fails rather than becoming a no-op or update, so conflict handling and a rerun integration test remain necessary.

### How to explain testing honestly

> The current 12-test suite covers transformation and mocked API behavior. It does not call the live API or a database, which keeps unit tests fast, but it also means database constraints and warehouse behavior are not covered. My next testing layer would use disposable PostgreSQL for integration tests, followed by CI once the tests no longer depend on local environment credentials.

### How to explain scaling decisions

> At the current volume, synchronous requests, PostgreSQL, and a single Python project are reasonable. If volume or reliability requirements increased, I would first improve bulk loading, incremental processing, run metadata, retries, and database operations. I would only introduce distributed processing or a workflow orchestrator when there was a demonstrated need for parallelism, backfills, scheduling dependencies, or stronger operational recovery.

### How to discuss unfinished work

> I treat unfinished areas as explicit engineering work rather than hiding them. The API-to-PostgreSQL path has unit tests around transformation and mocked HTTP behavior, and the warehouse now has an explicit source business key and enforced current-state grain. Rerun handling, broader warehouse constraints, analytics consumers, and PostgreSQL integration tests are still priorities before adding cloud or orchestration tools.

## Appendix: confirmed current commands

Install the dependencies used by the existing tests:

```powershell
py -m pip install -r requirements-dev.txt
```

Run the current test suite without creating `.pytest_cache`:

```powershell
py -m pytest -q -p no:cacheprovider
```

Run source ingestion, which requires valid API and PostgreSQL environment settings:

```powershell
py pipeline.py
```

Run the current warehouse builder separately:

```powershell
py warehouse/build_warehouse.py
```

The warehouse command is documented here as current behavior, not as a safe rerunnable production command.
