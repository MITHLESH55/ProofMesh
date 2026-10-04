"""
Phase 3 Assurance Orchestrator.

Executes the complete assurance pipeline for a change:
Code Facts -> Intent -> Impact -> Invariants -> Contracts -> Security -> Tests -> Risk -> Policy -> Change Proof.
Persists all evidence and findings into PostgreSQL.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.entities import Change, AnalysisRun
from app.models.assurance import (
    ChangeIntent,
    BehavioralInvariant,
    SemanticContract,
    SecurityFinding,
    TestRecommendation,
    RiskAssessment,
    EvidenceRecord,
    PolicyDecision,
    ChangeProof,
)
from app.services.assurance.intent_analyzer import IntentAnalyzer
from app.services.assurance.invariant_engine import InvariantEngine
from app.services.assurance.contract_analyzer import ContractAnalyzer
from app.services.assurance.security_analyzer import SecurityAnalyzer
from app.services.assurance.test_recommender import TestRecommender
from app.services.assurance.risk_engine import RiskEngine
from app.services.assurance.policy_engine import PolicyEngine
from app.services.assurance.change_proof_builder import ChangeProofBuilder
from app.services.audit.service import AuditService


class AssuranceOrchestrator:
    """Coordinates execution and persistence of the Phase 3 assurance pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.intent_analyzer = IntentAnalyzer()
        self.invariant_engine = InvariantEngine()
        self.contract_analyzer = ContractAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.test_recommender = TestRecommender()
        self.audit_service = AuditService(db)

    def run_assurance(
        self,
        change: Change,
        analysis_run: AnalysisRun,
        changed_files: Optional[List[str]] = None,
        diff_text: str = "",
        impact_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute end-to-end assurance evaluation and persist all entities."""
        pr = change.pull_request
        repo = pr.repository if pr else None
        org_id = repo.organization_id if repo else None

        title = pr.title if pr else "Software Change"
        description = pr.description if pr and pr.description else ""
        commit_sha = change.commit_sha
        files = changed_files or []

        if not files and pr:
            # Fallback if no files explicitly passed
            files = ["app/main.py"]

        impact = impact_summary or {
            "total_files_affected": len(files),
            "directly_impacted": files,
            "transitively_impacted": [],
        }

        # 1. Intent Analysis
        intent_data = self.intent_analyzer.analyze_intent(
            title=title,
            description=description,
            commit_sha=commit_sha,
            changed_files=files,
            diff_text=diff_text,
        )
        intent_model = ChangeIntent(
            change_id=change.id,
            analysis_run_id=analysis_run.id,
            objective=intent_data["objective"],
            category=intent_data["category"],
            affected_capability=intent_data["affected_capability"],
            expected_behavior=intent_data["expected_behavior"],
            affected_components=intent_data["affected_components"],
            confidence=intent_data["confidence"],
            model_info=intent_data["model_info"],
        )
        self.db.add(intent_model)

        # 2. Behavioral Invariants
        invariants_data = self.invariant_engine.evaluate_invariants(
            changed_files=files,
            diff_text=diff_text,
            impacted_files=impact.get("transitively_impacted", []),
        )
        for inv in invariants_data:
            inv_model = BehavioralInvariant(
                change_id=change.id,
                analysis_run_id=analysis_run.id,
                invariant_type=inv["invariant_type"],
                description=inv["description"],
                affected_component=inv["affected_component"],
                source=inv["source"],
                evidence_refs=inv.get("evidence_refs"),
                confidence=inv.get("confidence", 1.0),
                verification_status=inv.get("verification_status", "UNVERIFIED"),
            )
            self.db.add(inv_model)

        # 3. Semantic Contracts
        contracts_data = self.contract_analyzer.analyze_contracts(
            changed_files=files,
            diff_text=diff_text,
        )
        for c in contracts_data:
            c_model = SemanticContract(
                change_id=change.id,
                analysis_run_id=analysis_run.id,
                endpoint_path=c["endpoint_path"],
                http_method=c["http_method"],
                contract_type=c["contract_type"],
                classification=c["classification"],
                evidence_refs=c.get("evidence_refs"),
                details=c.get("details"),
            )
            self.db.add(c_model)

        # 4. Security Findings
        security_data = self.security_analyzer.analyze_security(
            changed_files=files,
            diff_text=diff_text,
            impacted_files=impact.get("transitively_impacted", []),
        )
        for s in security_data:
            s_model = SecurityFinding(
                change_id=change.id,
                analysis_run_id=analysis_run.id,
                category=s["category"],
                severity=s["severity"],
                affected_component=s["affected_component"],
                evidence_refs=s.get("evidence_refs"),
                reasoning=s["reasoning"],
                remediation_suggestion=s.get("remediation_suggestion"),
                confidence=s.get("confidence", 0.9),
            )
            self.db.add(s_model)

        # 5. Test Recommendations
        test_recs_data = self.test_recommender.generate_recommendations(
            changed_files=files,
            title=title,
            invariants=invariants_data,
            contracts=contracts_data,
            security_findings=security_data,
        )
        for t in test_recs_data:
            t_model = TestRecommendation(
                change_id=change.id,
                analysis_run_id=analysis_run.id,
                target_component=t["target_component"],
                test_title=t["test_title"],
                test_code_scaffold=t.get("test_code_scaffold"),
                reason=t["reason"],
                invariant_covered=t.get("invariant_covered"),
                expected_behavior=t.get("expected_behavior"),
                confidence=t.get("confidence", 0.85),
            )
            self.db.add(t_model)

        # 6. Evidence Records
        evidence_records: List[Dict[str, Any]] = []
        for f in files:
            ev = {
                "source_type": "CODE_DIFF",
                "source_reference": f,
                "confidence": 1.0,
                "explanation": f"Source file {f} modified in commit {commit_sha[:7]}.",
            }
            evidence_records.append(ev)
            self.db.add(EvidenceRecord(
                analysis_run_id=analysis_run.id,
                source_type=ev["source_type"],
                source_reference=ev["source_reference"],
                confidence=ev["confidence"],
                explanation=ev["explanation"],
            ))

        for inv in invariants_data:
            ev = {
                "source_type": "INVARIANT",
                "source_reference": inv.get("affected_component", "system"),
                "confidence": inv.get("confidence", 1.0),
                "explanation": f"Behavioral Invariant: {inv.get('description')}",
            }
            evidence_records.append(ev)
            self.db.add(EvidenceRecord(
                analysis_run_id=analysis_run.id,
                source_type=ev["source_type"],
                source_reference=ev["source_reference"],
                confidence=ev["confidence"],
                explanation=ev["explanation"],
            ))

        # 7. Explainable Risk Assessment
        risk_data = RiskEngine.calculate_risk(
            changed_files=files,
            blast_radius=impact.get("total_files_affected", len(files)),
            security_findings=security_data,
            contracts=contracts_data,
            invariants=invariants_data,
            has_tests_modified=any("test" in f for f in files),
        )
        risk_model = RiskAssessment(
            change_id=change.id,
            analysis_run_id=analysis_run.id,
            overall_risk=risk_data["overall_risk"],
            numerical_score=risk_data["numerical_score"],
            contributing_factors=risk_data["contributing_factors"],
            confidence=risk_data["confidence"],
            uncertainties=risk_data["uncertainties"],
        )
        self.db.add(risk_model)

        # 8. Deterministic Policy Decision
        decision_data = PolicyEngine.evaluate(
            risk_assessment=risk_data,
            security_findings=security_data,
            contracts=contracts_data,
            invariants=invariants_data,
            evidence_count=len(evidence_records),
        )
        policy_model = PolicyDecision(
            change_id=change.id,
            analysis_run_id=analysis_run.id,
            decision=decision_data["decision"],
            rules_evaluated=decision_data["rules_evaluated"],
            blocking_reasons=decision_data["blocking_reasons"],
            warning_reasons=decision_data["warning_reasons"],
        )
        self.db.add(policy_model)

        # 9. Change Proof Compilation
        pr_meta = {
            "number": pr.number if pr else 1,
            "title": title,
            "author": pr.author if pr else "author",
            "repository": repo.full_name if repo else "repo",
        }
        proof_data = ChangeProofBuilder.build_proof(
            change_id=change.id,
            commit_sha=commit_sha,
            analysis_run_id=analysis_run.id,
            intent=intent_data,
            impact_summary=impact,
            invariants=invariants_data,
            contracts=contracts_data,
            security_findings=security_data,
            test_recommendations=test_recs_data,
            risk_assessment=risk_data,
            evidence_records=evidence_records,
            policy_decision=decision_data,
            pr_metadata=pr_meta,
        )
        proof_model = ChangeProof(
            change_id=change.id,
            analysis_run_id=analysis_run.id,
            decision=proof_data["decision"],
            risk_level=proof_data["risk_level"],
            summary=proof_data["summary"],
            full_proof_artifact=proof_data["full_proof_artifact"],
        )
        self.db.add(proof_model)

        # Audit Log
        self.audit_service.log(
            action="CHANGE_PROOF_GENERATED",
            entity_type="ANALYSIS_RUN",
            entity_id=analysis_run.id,
            organization_id=org_id,
            metadata={
                "decision": proof_data["decision"],
                "risk_level": proof_data["risk_level"],
                "risk_score": risk_data["numerical_score"],
                "evidence_count": len(evidence_records),
                "invariants_count": len(invariants_data),
            },
        )

        self.db.commit()

        logger.info(
            f"Assurance analysis complete for run {analysis_run.id}: decision={proof_data['decision']}, risk={proof_data['risk_level']}",
            extra={"analysis_run_id": analysis_run.id, "decision": proof_data["decision"]},
        )

        return proof_data
