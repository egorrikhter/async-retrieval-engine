# Project Roadmap & Issues Tracker

---

## Issue #1: [Setup] Bootstrap project infrastructure and CI/CD pipeline

### Objective
Set up the foundational infrastructure, continuous integration pipeline, and database migrations to start active development.

### Acceptance Criteria
- [x] Initialize GitHub repository with Branch Protection rules for `main`.
- [ ] Set up GitHub Actions CI pipeline (`.github/workflows/ci.yml`) with Ruff, Mypy (strict), and Pytest.
- [ ] Create `docker-compose.yml` including API, PostgreSQL (with pgvector), Redis, and MinIO services.
- [x] Initialize FastAPI application with a basic healthcheck router.
- [ ] Configure database connection using SQLAlchemy 2.0 (asyncpg).
- [ ] Setup Alembic and generate the initial empty migration.

---

## Issue #2: [Data Layer] Implement relational schema and vector indices

### Objective
Design and implement the PostgreSQL database schema using SQLAlchemy 2.0, including pgvector integration and partial indices for soft deletion.

### Acceptance Criteria
- [ ] Create `Document` model (file metadata, status enum, `deleted_at`).
- [ ] Create `Chunk` model with `halfvec(1536)` for embeddings.
- [ ] Configure unique constraint on `(document_id, chunk_index)` to ensure idempotency.
- [ ] Generate Alembic migration creating tables and types.
- [ ] Generate Alembic migration creating partial B-Tree and HNSW indices (`WHERE is_deleted = false`).

---

## Issue #3: [Ingestion] Implement document upload API and MinIO integration

### Objective
Create the asynchronous HTTP endpoint to receive files from clients, store them in object storage, and initialize the state machine.

### Acceptance Criteria
- [ ] Implement async S3/MinIO client (e.g., using `aioboto3` or `httpx`) for file uploads.
- [ ] Create `POST /api/v1/documents` endpoint accepting `multipart/form-data`.
- [ ] Upload the received file to MinIO bucket.
- [ ] Insert a new `Document` record into the database with `status = 'pending'`.
- [ ] Enqueue a background task in Arq (stub implementation).
- [ ] Return `202 Accepted` HTTP status with `document_id` and initial status.

---

## Issue #4: [Worker] Implement asynchronous processing pipeline (Arq)

### Objective
Set up the background worker to handle I/O-bound tasks: downloading files, chunking text, and fetching embeddings from an external LLM API.

### Acceptance Criteria
- [ ] Bootstrap Arq worker process in a separate Docker container.
- [ ] Implement task to download the source file from MinIO using `document_id`.
- [ ] Implement text extraction and chunking logic.
- [ ] Integrate external Embeddings API via `httpx` with exponential backoff for `429 Too Many Requests`.
- [ ] Upsert calculated vectors into the `Chunk` table (`ON CONFLICT DO NOTHING`).
- [ ] Update `Document` status to `completed` (or `failed` with error logging).

---

## Issue #5: [Retrieval] Implement hybrid search API and status polling

### Objective
Create the endpoints for querying the vector database and checking the ingestion status of uploaded documents.

### Acceptance Criteria
- [ ] Create `GET /api/v1/documents/{document_id}` endpoint for clients to poll processing status.
- [ ] Create `POST /api/v1/search` endpoint accepting a JSON payload (search query and optional metadata filters like `tenant_id`).
- [ ] Implement SQLAlchemy query executing vector similarity search (cosine distance) with Pre-filtering via B-Tree indices.
- [ ] Format the API response to include the source text chunk, document metadata, and MinIO download URL.
