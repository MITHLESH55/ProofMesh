# ProofMesh — REST API Documentation (Phase 1)

All endpoints reside under the `/api/v1` prefix.

---

## 1. Response Envelope Format

### Success Response
```json
{
  "data": { ... },
  "request_id": "req_a1b2c3d4e5f6"
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "request_id": "req_a1b2c3d4e5f6",
    "details": {}
  }
}
```

---

## 2. Authentication

### `POST /api/v1/auth/register`
Creates a new user and optional organization.

- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!",
    "full_name": "Jane Doe",
    "organization_name": "Acme Corp"
  }
  ```
- **Response**: `201 Created` with JWT access token.

### `POST /api/v1/auth/login`
Authenticates an existing user.

- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!"
  }
  ```
- **Response**: `200 OK` with JWT access token.

### `GET /api/v1/auth/me`
Retrieves the currently authenticated user's profile and memberships.

- **Headers**: `Authorization: Bearer <JWT>`
- **Response**: `200 OK` with user details.

---

## 3. Repositories

### `GET /api/v1/repositories`
Lists all connected repositories for the workspace.

- **Headers**: `Authorization: Bearer <JWT>`
- **Query Params**: `organization_id` (optional)
- **Response**: `200 OK` array of repository objects.

### `GET /api/v1/repositories/{id}`
Retrieves a specific repository by ID.

- **Headers**: `Authorization: Bearer <JWT>`
- **Response**: `200 OK` repository object.

### `POST /api/v1/repositories`
Connects a new repository (Requires `ADMIN` role).

- **Headers**: `Authorization: Bearer <JWT>`
- **Request Body**:
  ```json
  {
    "github_repository_id": "123456789",
    "owner": "acme",
    "name": "core-backend",
    "default_branch": "main"
  }
  ```
- **Response**: `201 Created`

---

## 4. Changes & Analyses

### `GET /api/v1/changes`
Lists ingested changes with filtering and pagination.

- **Headers**: `Authorization: Bearer <JWT>`
- **Query Params**:
  - `repository_id`: UUID
  - `status`: `QUEUED` | `RUNNING` | `COMPLETED` | `FAILED`
  - `limit`: int (default 50, max 100)
  - `offset`: int (default 0)
- **Response**: `200 OK` array of change items.

### `GET /api/v1/changes/{id}`
Retrieves full change details including PR metadata, commit SHA, analysis runs, and audit history.

- **Headers**: `Authorization: Bearer <JWT>`
- **Response**: `200 OK` change detail object.

### `GET /api/v1/changes/{id}/status`
Lightweight polling endpoint returning the latest status of a change and its analysis run.

- **Headers**: `Authorization: Bearer <JWT>`
- **Response**: `200 OK`
  ```json
  {
    "data": {
      "change_id": "3b5f8965-746c-489d-8ec6-a738d81641e9",
      "status": "COMPLETED",
      "latest_analysis_run": {
        "id": "02060e8b-7025-43ad-832a-9911c94c9ef5",
        "status": "COMPLETED",
        "stage": "INGESTION_VALIDATION"
      },
      "updated_at": "2026-10-05T00:00:00Z"
    },
    "request_id": "req_123"
  }
  ```

### `POST /api/v1/changes/{id}/reanalyze`
Re-enqueues an analysis run for the change (Requires `ENGINEER` or `ADMIN`).

- **Headers**: `Authorization: Bearer <JWT>`
- **Request Body**:
  ```json
  {
    "reason": "Manual re-trigger from dashboard"
  }
  ```
- **Response**: `200 OK` updated change detail.

---

## 5. Webhooks

### `POST /api/v1/webhooks/github`
Ingests GitHub webhook events.

- **Headers**:
  - `X-Hub-Signature-256`: `sha256=<hmac_hex_digest>`
  - `X-GitHub-Event`: `pull_request` | `ping`
  - `X-GitHub-Delivery`: `<unique_delivery_uuid>`
- **Supported Events**:
  - `pull_request.opened`
  - `pull_request.synchronize`
  - `pull_request.reopened`
  - `pull_request.closed`
- **Response**: `200 OK`

---

## 6. Health & Readiness

### `GET /api/v1/health`
Basic liveness probe.
- **Response**: `200 OK` `{"status": "ok", "service": "proofmesh-api", "version": "0.1.0"}`

### `GET /api/v1/ready`
Readiness probe inspecting PostgreSQL and Redis connectivity.
- **Response**: `200 OK` / `503 Service Unavailable`
  ```json
  {
    "status": "ready",
    "dependencies": {
      "postgres": "ok",
      "redis": "ok"
    }
  }
  ```
