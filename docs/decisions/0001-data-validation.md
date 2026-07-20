# ADR 0001 - Validate Source Records Before Transformation

**Status:** Accepted

**Date:** 2026-07-20

---

# Context

The ingestion pipeline retrieves job listings from the Adzuna API.

External APIs cannot be assumed to always return complete or valid data. Missing required fields, malformed timestamps, and inconsistent salary values can negatively impact downstream processing if they are not detected early.

Initially, validation was considered after transforming API responses into ORM objects.

However, transformation may normalize invalid values (for example, converting malformed timestamps into `None`), making it impossible to distinguish between missing and malformed source data.

---

# Decision

All source records are validated immediately after retrieval and before transformation.

The pipeline follows the sequence:

```text
Fetch

↓

Validate

↓

Transform

↓

Persist
```

Records that fail validation are rejected and logged.

Only validated records continue through the remainder of the ingestion pipeline.

Validation operates on the raw API payload to preserve the original source information.

---

# Consequences

## Positive

- Prevents invalid data from entering the operational database.
- Keeps transformation logic focused exclusively on data conversion.
- Produces more accurate validation messages.
- Improves data quality before persistence.
- Simplifies downstream processing.
- Separates business validation failures from unexpected software errors.

---

## Trade-offs

Validation logic must understand the external API schema.

If the API changes, validation rules may require updates before transformation can proceed correctly.

This additional maintenance cost was considered acceptable given the improvements in data quality and error reporting.

---

# Alternatives Considered

## Validate After Transformation

Rejected.

Transformation may discard information needed to accurately diagnose source data issues.

---

## Raise Exceptions Immediately

Rejected.

A single malformed record should not stop the ingestion of thousands of valid records.

Rejecting invalid records while continuing the pipeline provides better operational resilience.

---

## Validate Only During Warehouse Construction

Rejected.

Poor-quality operational data would already have been persisted, making later correction more difficult and allowing invalid records to propagate through the system.

---

# Rationale

Data quality should be enforced as early as possible.

Validating raw source records reduces downstream complexity, improves observability, and creates a clear separation between validation, transformation, and persistence responsibilities.

This decision supports the repository's overall design principles of maintainability, modularity, and deterministic processing.