# ProofMesh — Change Proof Specification

A **Change Proof** is the core verifiable assurance artifact produced by ProofMesh Phase 3. It synthesizes deterministic evidence and AI assurance into a formal dossier that answers the ten fundamental reliability questions:

---

## 1. What Changed?
* **Commit SHA**: Exact commit hash analyzed.
* **Changed Files**: Normalized paths of all added, modified, or removed files.
* **Structural Delta**: Extracted AST symbols (functions, methods, classes, imports) modified.

## 2. Why Did It Change?
* **Objective**: Primary purpose of the change inferred from PR metadata and commit context.
* **Category**: Discrete classification (`FEATURE`, `BUG_FIX`, `REFACTOR`, `SECURITY`, `PERFORMANCE`, etc.).
* **Affected Capability**: High-level domain capability impacted.

## 3. What Can It Affect?
* **Blast Radius**: Count of direct and downstream transitive dependent files computed from the Neo4j dependency graph.
* **Impact Chains**: Traversed dependency paths showing how external components import modified units.

## 4. What Behavior May Change?
* **Behavioral Invariants**: Formal rules that must remain true across modifications.
* **Verification Status**:
  * `VERIFIED`: Concrete code evidence proves the invariant is upheld.
  * `VIOLATED`: Analysis detects evidence breaking the invariant.
  * `UNVERIFIED`: Insufficient evidence to prove invariant preservation.

## 5. What Contracts May Change?
* **Interface & API Contracts**: Monitored REST endpoints, parameters, and payloads.
* **Classifications**:
  * `NO_CHANGE`
  * `COMPATIBLE_CHANGE`
  * `POTENTIALLY_BREAKING`
  * `BREAKING`

## 6. What Security Properties Are Affected?
* **Vulnerability Vectors**: Scanned for authorization bypasses, missing auth guards, injection risks, and secret leaks.
* **Findings**: Category, severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), concrete reasoning, and remediation advice.

## 7. What Tests Cover It?
* **Recommended Scaffolds**: AI-assisted candidate test implementations targeting modified logic, invariant preservation, and contract compatibility.

## 8. What Evidence Supports the Conclusion?
* **Traceable Evidence Ledger**: Every finding is backed by an `EvidenceRecord` citing `CODE_DIFF`, `AST_FACT`, `GRAPH_RELATION`, or `INVARIANT` with confidence ratings.

## 9. What Remains Uncertain?
* **Uncertainties**: Explicit listing of unverified assumptions, missing test assertions, or unresolved transitive dependencies.

## 10. What Policy Decision Was Made?
* **Final Verdict**:
  * `PASS`: Change complies with all governance policies.
  * `WARN`: Non-blocking elevated risk or minor contract drift requiring review.
  * `BLOCK`: Critical security issue, invariant violation, or breaking contract detected.
  * `INSUFFICIENT_EVIDENCE`: Change lacks verifiable diff or facts.
