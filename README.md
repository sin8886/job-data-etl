# Job Data ETL Pipeline

A production-oriented Python ETL pipeline for processing job-posting data. The project demonstrates configurable cleaning, data-quality validation, incremental loading, PostgreSQL upserts, S3 archival, audit tracking, retries, Prefect orchestration, Docker-based local infrastructure, and GitHub Actions CI.

## What This Project Does

The pipeline processes raw CSV job data through the following stages:

1. Extract the configured CSV input.
2. Clean and normalize fields using `clean_config.yaml`.
3. Store the cleaned CSV locally and upload raw and cleaned files to S3.
4. Filter records already present in PostgreSQL using the business key `(company_name, job_title, location)`.
5. Validate row count, critical-column null rates, and `job_id` uniqueness.
6. Load companies and jobs with PostgreSQL UPSERT statements.
7. Retry transient load failures with exponential backoff.
8. Generate a run report and record pipeline status in `pipeline_runs`.

Historical backfills use the same transform, validation, load, and reporting components while skipping the incremental pre-filter.

## Technology Stack

- Python 3.11
- pandas
- PostgreSQL and psycopg2
- PyYAML configuration
- Typer CLI commands
- boto3 and Amazon S3
- Prefect scheduling and flow execution
- Docker and Docker Compose
- pytest and Ruff
- GitHub Actions

## Project Structure

```text
DE/
├── main.py                         # Incremental and backfill pipeline entry point
├── etl_flow.py                     # Prefect flow and daily schedule
├── clean.py                        # Configurable CSV cleaning pipeline
├── clean_config.yaml               # Cleaning rules and paths
├── quality.py                      # Data-quality checks
├── audit.py                        # Pipeline-run audit persistence
├── load_to_postgres.py             # PostgreSQL loading and UPSERT logic
├── exceptions.py                   # Pipeline-specific exceptions
├── pipeline/
│   ├── extract.py                  # Input path resolution
│   ├── transform.py                # Cleaning-stage adapter
│   ├── incremental.py              # Existing business-key filtering
│   ├── validate.py                 # Validation orchestration
│   ├── load.py                     # Data-frame to PostgreSQL adapter
│   ├── retry.py                    # Exponential-backoff retry helper
│   ├── report.py                   # Run report generation
│   ├── backfill.py                 # Historical backfill flow
│   └── storage/s3.py               # S3 client and upload helpers
├── tests/                          # Unit, integration, retry, S3, and idempotency tests
├── sql/
│   ├── schema.sql                  # PostgreSQL schema, constraints, and indexes
│   ├── migrations/                 # Versioned database migrations
│   ├── business_queries.sql        # Example analytical queries
│   ├── analysis.sql                # Query-plan analysis examples
│   ├── constraints.sql             # Constraint documentation
│   └── indexes.sql                 # Optional index statements
├── .github/workflows/ci.yml        # PostgreSQL-backed CI checks
├── Dockerfile                      # Application image definition
├── docker-compose.yml               # Local PostgreSQL and application services
├── requirements.txt                # Python dependencies
└── pyproject.toml                  # Ruff configuration
```

The repository also contains optional local helpers for generating test data, processing large CSV files in chunks, and producing a top-companies visualization. These helpers are not part of the default `main.py` execution path.

## Configuration

Cleaning behavior is configured in `clean_config.yaml`:

- Input and output CSV paths
- Columns to drop
- Invalid-value replacement
- Company-name normalization
- Salary-estimate cleanup
- Duplicate removal
- Critical-column null-rate monitoring

Database, S3, and logging settings are supplied through environment variables. Use a local `.env` file for development, and keep it outside version control.

Common database variables include:

```text
DB_NAME=job_db
DB_USER=postgres
DB_PASSWORD=your-local-password
DB_HOST=localhost
DB_PORT=5432
```

S3 uploads require:

```text
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-bucket-name
```

AWS credentials should be supplied through the AWS SDK credential chain, an IAM role, or a local AWS profile. Do not commit access keys to the repository.

## Run Locally

### Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Run tests

```bash
pytest
```

The test suite covers cleaning, quality checks, validation failures, retry behavior, incremental business-key filtering, S3 client behavior, and database idempotency.

### Run the incremental pipeline

Use the configured input path:

```bash
python main.py
```

Provide a specific CSV input when needed:

```bash
python main.py --input data/raw/DataAnalyst.csv
```

### Run a historical backfill

```bash
python main.py --backfill data/raw/DataAnalyst.csv
```

The `--backfill` mode reuses the existing transform, validation, PostgreSQL load, and report stages without applying the incremental filter first.

## PostgreSQL and Docker Compose

Start the local PostgreSQL and application services with:

```bash
docker compose up -d
```

The database service initializes from `sql/schema.sql`, stores data in the `postgres_data` named volume, and exposes the configured host port. The application service waits for PostgreSQL health, loads `.env`, mounts the project directory, and runs `python main.py`.

Apply the versioned company-identity migration to an existing database when required:

```bash
psql -d job_db -f sql/migrations/20260820_day20_company_identity.sql
```

The database enforces company identity with `lower(btrim(name))` and job uniqueness with `(company_id, title, location)`. These constraints support the loader's UPSERT behavior and repeated-run idempotency.

## Prefect

`etl_flow.py` wraps the main pipeline in a Prefect flow named `job-data-etl`. Running the module serves a daily schedule at 09:00 in the `Asia/Shanghai` timezone:

```bash
python etl_flow.py
```

The flow delegates to the existing `main()` entry point and does not introduce a separate business-logic implementation.

## S3 Storage

During the incremental pipeline, the raw input is uploaded under `raw/` and the cleaned output is uploaded under `clean/`. The S3 helper validates the bucket and region settings before uploading and reports the destination in the application log.

## CI

GitHub Actions runs on pushes and pull requests targeting `main`. The workflow:

1. Starts PostgreSQL 18 as a service.
2. Installs Python 3.11 and project dependencies.
3. Initializes `sql/schema.sql`.
4. Runs `ruff check .`.
5. Runs `pytest`.

## Outputs

Typical runtime outputs include:

- `data/clean/jobs_clean.csv`
- `report.md`
- Application logs under `logs/` or the configured log path
- S3 objects under `raw/` and `clean/`
- Audit rows in the PostgreSQL `pipeline_runs` table

Generated files, local logs, virtual environments, caches, and environment files should remain uncommitted according to `.gitignore` and `.dockerignore`.

## Future Improvements

Possible future improvements that do not change the current pipeline contract include:

- Add broader data-quality checks such as range validation and drift monitoring.
- Add a dedicated deployment workflow for the target AWS environment.
- Improve test isolation for database-backed integration tests.
- Add structured metrics and operational dashboards.
