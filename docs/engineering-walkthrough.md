# Engineering Walkthrough

This document explains the architectural decisions, engineering practices, and implementation strategy behind the Job Market Intelligence Platform.

Unlike the Engineering Guide, which focuses on development workflows, this document explains *why* the repository is structured the way it is and the trade-offs considered throughout its implementation.

---

# Project Goals

The project was designed with two objectives.

The first objective is to collect and analyze job market data for data-related roles in the United States.

The second objective is to demonstrate engineering practices commonly expected in modern Data Engineering environments rather than simply producing analytical outputs.

For that reason, the project prioritizes:

- modular architecture
- maintainability
- validation
- automated testing
- reproducibility
- documentation

over implementing the largest possible number of technologies.

---

# High-Level Architecture

```text
                    Adzuna API
                         │
                         ▼
                 Validation Layer
                         │
                         ▼
              Transformation Layer
                         │
                         ▼
        PostgreSQL Operational Database
                         │
                         ▼
           Dimensional Warehouse
                         │
                         ▼
      Analytical Queries / Notebooks
```

The ingestion pipeline is intentionally separated from warehouse construction.

Operational data represents the source of truth.

The warehouse is a derived analytical model generated from operational data.

This separation simplifies maintenance and makes warehouse rebuilds deterministic.

---

# Design Principles

Several principles guided the implementation of the repository.

## Single Responsibility

Each module has one clearly defined responsibility.

Examples include:

- API communication
- validation
- transformation
- persistence
- warehouse generation

Keeping responsibilities isolated makes the project easier to extend and test.

---

## Explicit Data Flow

The repository follows an explicit pipeline.

```text
Fetch

↓

Validate

↓

Transform

↓

Persist

↓

Build Warehouse
```

Each stage has clearly defined inputs and outputs.

Business rules are not mixed with persistence logic.

---

## Deterministic Processing

Given the same source data, the pipeline should always produce the same operational records and warehouse.

This principle simplifies debugging and enables reliable testing.

---

# Repository Organization

The repository separates responsibilities into dedicated packages.

```text
ingestion/
```

Responsible for external communication with the Adzuna API.

---

```text
processing/
```

Contains validation and transformation logic.

Business rules live here rather than inside database models.

---

```text
db/
```

Operational database models and database configuration.

---

```text
warehouse/
```

Star schema models and warehouse loading logic.

Operational storage and analytical storage remain independent.

---

```text
tests/
```

Automated tests covering business logic rather than only implementation details.

---

```text
docs/
```

Engineering documentation and architectural decisions.

---

# Pipeline Design

The ingestion pipeline follows a linear sequence of independent processing stages.

```text
Raw API Record

↓

Validation

↓

Transformation

↓

Persistence

↓

Warehouse
```

Each stage performs a single responsibility before passing data to the next one.

This design keeps the pipeline easier to understand, simplifies testing, and allows individual stages to evolve independently.

For example, validation rules can change without affecting transformation logic, and warehouse changes do not require modifications to ingestion.

Separating these responsibilities also improves failure isolation by making it easier to determine where an error originated.

---

# Validation Strategy

One of the most significant architectural decisions in the repository was introducing a dedicated validation layer before transformation.

Instead of assuming the external API always returns valid data, every raw record is validated immediately after retrieval.

```text
Raw Record

↓

Validation

↓

Accepted

or

Rejected
```

Only valid records continue through the pipeline.

Invalid records are rejected, logged, and excluded from persistence.

This approach prevents malformed source data from propagating into the operational database and warehouse.

Examples of validation rules include:

- Required listing identifier
- Required job title
- Required location display name
- Required creation date
- Valid ISO-8601 timestamp
- Future date protection
- Salary consistency checks
- Numeric salary validation

Validation intentionally operates on the raw API payload instead of transformed objects.

Doing so preserves information that could otherwise be lost during parsing.

For example, an invalid timestamp and a missing timestamp may both become `None` after transformation, making them impossible to distinguish later.

By validating first, the pipeline can report the exact reason why a record was rejected.

---

## Validation Results

Every processed record falls into one of four categories.

| Status | Description |
|----------|-------------|
| Inserted | Valid record successfully persisted |
| Skipped | Record already exists in the operational database |
| Rejected | Business validation failed |
| Error | Unexpected runtime or persistence failure |

Separating rejected records from unexpected errors provides a clearer picture of pipeline health.

A rejected record indicates poor source data.

An error indicates a software or infrastructure problem.

These situations require different responses and therefore should not be reported together.

---

# Transformation Strategy

After validation, raw API records are converted into ORM models used by the operational database.

Transformation focuses exclusively on converting external data into the project's internal representation.

Typical responsibilities include:

- parsing timestamps
- extracting nested fields
- normalizing optional values
- converting numeric types

Business validation is intentionally excluded from this stage.

Because validation has already been completed, transformation code can remain simpler and easier to maintain.

This separation reduces coupling between validation rules and transformation logic.

---

# Operational Database

The operational database stores validated source records.

Its purpose is to preserve the original business entities retrieved from the API before any analytical modeling takes place.

The operational database serves as the single source of truth for warehouse generation.

Keeping operational storage independent from analytical storage provides several advantages.

- Warehouse rebuilds become deterministic.
- Historical transformations remain reproducible.
- Multiple warehouse designs can be generated from the same operational data.
- Changes to analytical models do not require re-ingesting external data.

This architecture follows a common pattern found in modern data platforms where ingestion and analytics remain loosely coupled.

---

# Warehouse Design

The warehouse uses a dimensional star schema optimized for analytical workloads.

Current dimensions include:

- Company
- Job
- Location
- Date

These dimensions connect to a central fact table representing job listings.

The separation between dimensions and facts reduces redundancy while simplifying aggregation and reporting.

Warehouse generation is intentionally executed as a separate process.

```bash
py -m warehouse.build_warehouse
```

This decision provides several benefits.

- Warehouse logic remains independent from ingestion.
- Failed warehouse builds do not affect operational storage.
- Warehouse models can evolve without modifying the ingestion pipeline.
- Rebuilding analytical structures becomes straightforward.

The warehouse is therefore treated as a derived representation of operational data rather than as the primary storage location.

---

# Testing Strategy

Testing is treated as a core component of the repository rather than as a final verification step.

The project follows a test-driven mindset whenever practical, where business rules are validated through automated tests before or alongside implementation.

The current test suite covers multiple layers of the application.

- API client behavior
- Data validation
- Data transformation
- Pipeline execution
- Database models

Rather than focusing only on code coverage, the repository prioritizes validating business behavior.

Examples include:

- Rejecting records with missing required fields
- Rejecting invalid timestamps
- Rejecting inconsistent salary ranges
- Skipping duplicate records
- Successfully inserting valid records

This approach provides greater confidence that the pipeline behaves correctly under realistic scenarios rather than simply exercising individual functions.

---

## Unit Tests

Most repository tests are unit tests.

Individual modules are tested in isolation with mocked dependencies where appropriate.

This makes tests:

- fast
- deterministic
- independent from external services

Because external APIs and databases are isolated during unit testing, failures are easier to diagnose.

---

## Pipeline Tests

The pipeline includes dedicated behavioral tests.

Rather than verifying only individual functions, these tests verify the interaction between multiple pipeline stages.

Typical scenarios include:

- Valid records are inserted.
- Duplicate records are skipped.
- Invalid records are rejected before transformation.
- Unexpected failures increase the error counter.

Pipeline tests provide confidence that the complete ingestion flow behaves as expected.

---

## Continuous Integration

Every change pushed to the repository is automatically verified through GitHub Actions.

The CI workflow executes the automated test suite to detect regressions before changes are merged.

Automated testing provides several benefits.

- Faster feedback
- Consistent verification
- Improved confidence when refactoring
- Reduced risk of introducing regressions

Maintaining a green test suite is considered a requirement before merging changes.

---

# Configuration Management

Application configuration is separated from source code through environment variables.

Sensitive information such as API credentials and database connection details is never hardcoded.

Configuration values include:

- Adzuna credentials
- Database host
- Database port
- Database name
- Database user
- Database password

A `.env.example` file documents the expected configuration without exposing secrets.

This approach simplifies deployment across different environments while preventing sensitive data from being committed to version control.

---

# Logging Strategy

The repository uses centralized logging throughout the ingestion process.

Instead of relying on print statements, each pipeline stage reports meaningful events using Python's logging framework.

Typical log messages include:

- Pipeline startup
- Record insertion
- Duplicate detection
- Validation failures
- Unexpected exceptions
- Pipeline summary

Validation failures are intentionally logged as warnings rather than errors.

Unexpected software failures are logged as errors.

Distinguishing between these situations provides a clearer understanding of pipeline health.

At the end of every execution, the pipeline reports summary statistics similar to:

```text
Inserted: 183

Skipped: 54

Rejected: 7

Errors: 1
```

When validation failures occur, an additional summary groups rejection reasons by frequency.

This information helps identify recurring data quality issues from the external API.

---

# Engineering Trade-offs

No engineering decision is free of trade-offs.

Several implementation choices intentionally favor maintainability and simplicity over additional complexity.

---

## Validation Before Transformation

The repository validates raw API records before transformation.

Advantages:

- Better error reporting
- Preservation of malformed source data
- Simpler transformation logic

Trade-off:

- Validation rules must understand the external API structure.

---

## Separate Operational Database and Warehouse

Operational storage and analytical storage are intentionally independent.

Advantages:

- Deterministic warehouse rebuilds
- Easier schema evolution
- Clear separation of responsibilities

Trade-off:

- Additional storage requirements.
- Separate execution step for warehouse generation.

---

## SQLAlchemy ORM

The project uses SQLAlchemy instead of writing raw SQL for operational persistence.

Advantages:

- Readable models
- Easier maintenance
- Better abstraction

Trade-off:

- Slight performance overhead compared to raw SQL.

Given the project size, maintainability was considered more important than maximizing write performance.

---

## Modular Architecture

The repository separates ingestion, validation, transformation, persistence, warehouse generation, and analytics into independent modules.

Advantages:

- Easier testing
- Improved readability
- Better extensibility

Trade-off:

- Slightly larger number of files and modules.

The additional organization was considered worthwhile because responsibilities remain clearly separated.

---

# Future Improvements

Although the repository already demonstrates a complete ingestion workflow, several enhancements remain possible.

Current priorities include:

- Expand validation rules.
- Improve warehouse idempotency.
- Add PostgreSQL integration tests.
- Generate structured pipeline quality reports.
- Introduce pipeline metadata tracking.
- Deploy the project on AWS.
- Add workflow orchestration.
- Introduce Infrastructure as Code.

These improvements focus on increasing operational robustness rather than simply adding new technologies.

---

# Lessons Learned

Building the Job Market Intelligence Platform reinforced several engineering principles that extend beyond this specific repository.

## External Data Should Never Be Trusted

One of the earliest assumptions was that the external API would consistently provide valid data.

As the project evolved, it became clear that relying on this assumption would complicate downstream processing and reduce data quality.

Introducing a dedicated validation layer significantly improved the reliability of the ingestion pipeline while keeping transformation logic focused on data conversion rather than business validation.

---

## Separation of Responsibilities Simplifies Evolution

Keeping validation, transformation, persistence, warehouse generation, and analytics independent made the repository substantially easier to extend.

Each component can evolve without requiring large changes throughout the rest of the system.

This became particularly valuable when introducing validation after the transformation layer had already been implemented.

---

## Testing Improves Design

Writing automated tests exposed several opportunities to simplify interfaces and reduce coupling between modules.

Rather than serving only as verification, tests also influenced architectural decisions by encouraging smaller, more focused components.

---

## Documentation Should Evolve With the Code

Engineering documentation quickly becomes inaccurate if it is treated as an afterthought.

Keeping documentation synchronized with implementation makes the repository easier to maintain and significantly improves its value as a learning resource and portfolio project.

---

# Interview Discussion Points

This repository demonstrates several engineering concepts that commonly appear during Data Engineering interviews.

Potential discussion topics include:

- Why validation occurs before transformation.
- Reasons for separating operational and analytical storage.
- Trade-offs between ORM and raw SQL.
- Advantages of modular pipeline design.
- Unit testing versus pipeline testing.
- Designing idempotent ingestion pipelines.
- Handling malformed external data.
- Logging and observability.
- Configuration management.
- Warehouse modeling decisions.

Candidates should be able to explain not only what was implemented, but also the reasoning behind each decision.

---

# Example Interview Questions

## Why validate records before transformation?

Transformation should assume that incoming data already satisfies business requirements.

Validating raw API records preserves malformed input, produces more accurate error reporting, and keeps transformation logic simpler.

---

## Why keep the warehouse separate from ingestion?

Operational storage represents the source of truth.

Keeping warehouse generation independent allows analytical models to evolve without modifying ingestion or requiring additional API requests.

---

## Why distinguish rejected records from errors?

Rejected records indicate expected business validation failures caused by poor source data.

Errors indicate unexpected software or infrastructure failures.

Reporting them separately provides a more accurate view of pipeline health and simplifies troubleshooting.

---

## Why use SQLAlchemy?

SQLAlchemy provides maintainable object models, database abstraction, and readable persistence logic.

Although raw SQL may offer slightly better performance, maintainability and clarity were prioritized for this project.

---

## Why create automated tests?

Automated tests reduce regression risk, increase confidence during refactoring, and verify business behavior consistently across future changes.

Testing also encourages cleaner software design by promoting modular, independently testable components.

---

# Project Evolution

The repository has evolved incrementally through multiple iterations.

Major milestones include:

- Initial API ingestion pipeline.
- PostgreSQL operational database.
- Configuration management improvements.
- Warehouse implementation.
- Idempotent ingestion.
- Automated testing.
- GitHub Actions continuous integration.
- Source data validation.
- Engineering documentation.
- Architecture decision records.

Each iteration focused on improving software quality rather than simply increasing the number of technologies used.

---

# Closing Remarks

The primary objective of this repository is not to recreate a production-scale data platform.

Instead, it aims to demonstrate the engineering practices involved in designing a maintainable, testable, and extensible data ingestion system.

Throughout its development, emphasis has been placed on software engineering principles including separation of concerns, validation, reproducibility, testing, documentation, and incremental improvement.

Although the repository will continue evolving, the current architecture provides a solid foundation for future enhancements such as cloud deployment, orchestration, infrastructure automation, and expanded analytical capabilities.