# ProofMesh — Phase 3 Architecture: AI Assurance & Explainable Risk

```text
               Pull Request / Commit Diff
                           │
                           ▼
                 ┌───────────────────┐
                 │  Secret Redactor  │
                 │ (Masks API keys & │
                 │  private tokens)  │
                 └─────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
      ┌────────────┐ ┌────────────┐ ┌────────────┐
      │   Intent   │ │ Invariant  │ │  Semantic  │
      │  Analyzer  │ │   Engine   │ │ Contracts  │
      └──────┬─────┘ └─────┬──────┘ └─────┬──────┘
             │             │              │
             └─────────────┼──────────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
      ┌────────────┐ ┌────────────┐ ┌────────────┐
      │  Security  │ │    Test    │ │  Evidence  │
      │  Analyzer  │ │Recommender │ │   Ledger   │
      └──────┬─────┘ └─────┬──────┘ └─────┬──────┘
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                 ┌───────────────────┐
                 │ Explainable Risk  │
                 │      Engine       │
                 │ (Factor Breakdown)│
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │  Policy Decision  │
                 │      Engine       │
                 │ PASS/WARN/BLOCK/  │
                 │ INSUFFICIENT_EVID │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │   Change Proof    │
                 │  Formal Artifact  │
                 └─────────┬─────────┘
                           ▼
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐
│  FastAPI REST    │               │ PostgreSQL Store │
│  Endpoints       │               │ (9 Schema Tables)│
└────────┬─────────┘               └──────────────────┘
         ▼
┌──────────────────┐
│ React Assurance  │
│ Dashboard View   │
└──────────────────┘
```

## Architectural Tenets

1. **Separation of Evidence and Decision**:
   AI models generate hypotheses, identify semantic intent, and propose tests. Deterministic code evaluates concrete invariant proofs, syntax contracts, and security rules. A deterministic policy layer renders the final governance decision.

2. **Full Provenance & Auditability**:
   Every claim or risk score has an underlying `evidence_ref` stored in `evidence_records`, linking directly to lines of code, AST symbols, or graph relationship paths.

3. **Privacy by Default**:
   All text passed to model providers is sanitized through `SecretRedactor` to strip credentials, bearer tokens, and private keys.
