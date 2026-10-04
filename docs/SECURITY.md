# ProofMesh — Security Architecture & Threat Model (Phase 1)

## 1. Security Overview

ProofMesh implements a defense-in-depth model safeguarding user credentials, webhook ingestion endpoints, internal messaging queues, and database records.

---

## 2. Threat Model & Security Controls

### Threat 1: Forged or Tampered GitHub Webhooks
- **Attack Vector**: Attacker sends unauthorized POST requests to `/api/v1/webhooks/github` attempting to fabricate pull requests or fake change records.
- **Mitigating Control**: Strict HMAC-SHA256 signature verification (`X-Hub-Signature-256`) using `hmac.compare_digest` (timing-safe comparison). Requests without valid signatures are rejected immediately with `400 Bad Request`.

### Threat 2: Unauthorized Tenant / Organization Access
- **Attack Vector**: Authenticated user attempts to modify or view data outside their organization.
- **Mitigating Control**: JWT authentication with cryptographic verification and centralized Role-Based Access Control (`ADMIN`, `ENGINEER`, `VIEWER`). Critical mutations (e.g. connecting repositories) are restricted to `ADMIN` roles.

### Threat 3: Replay Attacks & Duplicate Webhook Processing
- **Attack Vector**: Network glitches or malicious replays send identical webhook payloads multiple times.
- **Mitigating Control**: Webhook delivery ledger (`processed_webhook_events` table). Each `X-GitHub-Delivery` ID is tracked uniquely. Duplicate deliveries return early with `duplicate_ignored` without modifying logical state.

### Threat 4: Malicious Code Execution via Repository Changes
- **Attack Vector**: PR contains malicious scripts attempting to exploit the analysis worker runtime.
- **Mitigating Control**: In Phase 1, workers **NEVER** execute repository code. Analysis workers only inspect metadata, verify SHA integrity, and manage asynchronous pipeline status.

### Threat 5: Secret Exposure in Logs or API Responses
- **Attack Vector**: Accidental logging of passwords, tokens, or webhook secrets.
- **Mitigating Control**: Structured JSON loggers explicitly omit authentication tokens and passwords. Passwords are encrypted with bcrypt (12 rounds) and never stored or returned in plaintext.
