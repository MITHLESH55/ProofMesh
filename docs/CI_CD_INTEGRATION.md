# CI/CD Gate & GitHub Integration Guide

## Overview

ProofMesh provides both an API endpoint and a dedicated command-line tool (`proofmesh check` / `python -m app.cli.check`) for seamless integration with GitHub Actions, GitLab CI, and other continuous integration pipelines.

## Command-Line Interface (CLI)

### Syntax
```bash
python -m app.cli.check <change_id> [--commit-sha <sha>] [--fail-on-warn] [--json] [--base-url <url>]
```

### Exit Codes
- `0`: **PASS** (Policy passed cleanly, or decision is WARN when `--fail-on-warn` is disabled).
- `1`: **BLOCK** (Policy blocked due to critical risk, breaking contract, or security violation).
- `2`: **WARN** (When `--fail-on-warn` flag is set and policy returned WARN).
- `3`: **INSUFFICIENT_EVIDENCE** or unhandled execution error.

### GitHub Actions Workflow Example

```yaml
name: ProofMesh Change Assurance Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  assurance-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run ProofMesh CI Assurance Gate
        env:
          PROOFMESH_API_URL: ${{ secrets.PROOFMESH_API_URL }}
        run: |
          python -m app.cli.check ${{ github.event.pull_request.id }} \
            --commit-sha ${{ github.sha }} \
            --base-url "https://app.proofmesh.io"
```

## GitHub Check Run & Commit Status Payload

When evaluated, ProofMesh publishes an auditable markdown summary back to the pull request:

```markdown
### ProofMesh Assurance — ✅ PASS

| Metric | Assessment |
| :--- | :--- |
| **Risk Level** | `LOW` |
| **Impact Blast Radius** | `3 services / files` |
| **Critical Security Findings** | `0` |
| **Contract Compatibility** | `COMPATIBLE` |
| **Test Coverage Gaps** | `0` |
| **Gate Decision** | **`PASS`** |

🔗 [View Formal Change Proof & Evidence in ProofMesh](http://localhost:3000/changes/123/assurance)
```
