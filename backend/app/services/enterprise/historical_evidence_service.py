"""
Historical Evidence Service.

Stores and retrieves historical change proofs, incidents, regressions, and
remediation records with lightweight TF-IDF-based semantic search capability.
Enables continuous learning from past outcomes to improve future assurance accuracy.
"""
import math
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.enterprise import HistoricalEvidence
from app.schemas.enterprise import (
    HistoricalEvidenceCreate,
    HistoricalEvidenceResponse,
    EvidenceSearchRequest,
    EvidenceSearchResult,
)


class HistoricalEvidenceService:
    """Manages historical evidence records and provides semantic search for knowledge retrieval."""

    # --- CRUD Operations ---

    @staticmethod
    def store_evidence(db: Session, data: HistoricalEvidenceCreate) -> HistoricalEvidence:
        """Persist a new historical evidence record with optional embedding."""
        embedding = data.embedding
        if not embedding:
            embedding = HistoricalEvidenceService._compute_tfidf_vector(data.content)

        record = HistoricalEvidence(
            organization_id=data.organization_id,
            repository_id=data.repository_id,
            evidence_type=data.evidence_type.upper(),
            title=data.title,
            content=data.content,
            embedding=embedding,
            provenance=data.provenance,
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_evidence(db: Session, evidence_id: str) -> Optional[HistoricalEvidence]:
        """Retrieve a single evidence record by ID."""
        return db.query(HistoricalEvidence).filter(HistoricalEvidence.id == evidence_id).first()

    @staticmethod
    def list_evidence(
        db: Session,
        organization_id: Optional[str] = None,
        repository_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[HistoricalEvidence]:
        """List evidence records with optional filtering."""
        query = db.query(HistoricalEvidence)
        if organization_id:
            query = query.filter(HistoricalEvidence.organization_id == organization_id)
        if repository_id:
            query = query.filter(HistoricalEvidence.repository_id == repository_id)
        if evidence_type:
            query = query.filter(HistoricalEvidence.evidence_type == evidence_type.upper())
        return query.order_by(HistoricalEvidence.created_at.desc()).limit(limit).all()

    # --- Semantic Search ---

    @staticmethod
    def search(db: Session, request: EvidenceSearchRequest) -> List[EvidenceSearchResult]:
        """
        Perform semantic search over historical evidence using TF-IDF cosine similarity.

        This is a lightweight, dependency-free implementation suitable for moderate corpus sizes.
        For production-scale deployments, this can be swapped to pgvector or an external embedding service.
        """
        query = db.query(HistoricalEvidence)
        if request.organization_id:
            query = query.filter(HistoricalEvidence.organization_id == request.organization_id)
        if request.repository_id:
            query = query.filter(HistoricalEvidence.repository_id == request.repository_id)
        if request.evidence_type:
            query = query.filter(HistoricalEvidence.evidence_type == request.evidence_type.upper())

        candidates = query.all()
        if not candidates:
            return []

        query_vector = HistoricalEvidenceService._compute_tfidf_vector(request.query)

        scored: List[tuple] = []
        for record in candidates:
            doc_vector = record.embedding
            if not doc_vector or not isinstance(doc_vector, dict):
                doc_vector = HistoricalEvidenceService._compute_tfidf_vector(record.content)
            similarity = HistoricalEvidenceService._cosine_similarity(query_vector, doc_vector)
            if similarity > 0.0:
                scored.append((record, similarity))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for record, score in scored[: request.limit]:
            results.append(
                EvidenceSearchResult(
                    id=record.id,
                    evidence_type=record.evidence_type,
                    title=record.title,
                    content=record.content[:500],  # Truncate for search results
                    similarity_score=round(score, 4),
                    provenance=record.provenance or {},
                    created_at=record.created_at,
                )
            )
        return results

    # --- Automated Evidence Ingestion ---

    @staticmethod
    def ingest_from_change_proof(
        db: Session,
        organization_id: str,
        repository_id: str,
        change_id: str,
        proof_summary: str,
        risk_level: str,
        verdict: str,
    ) -> HistoricalEvidence:
        """Automatically create a historical evidence record from a completed Change Proof."""
        content = (
            f"Change Proof for change {change_id}. "
            f"Risk level: {risk_level}. Verdict: {verdict}. "
            f"Summary: {proof_summary}"
        )
        data = HistoricalEvidenceCreate(
            organization_id=organization_id,
            repository_id=repository_id,
            evidence_type="PROOF_SUMMARY",
            title=f"Change Proof: {verdict} ({risk_level})",
            content=content,
            provenance={
                "source": "change_proof_pipeline",
                "change_id": change_id,
                "risk_level": risk_level,
                "verdict": verdict,
            },
        )
        return HistoricalEvidenceService.store_evidence(db, data)

    @staticmethod
    def ingest_from_incident(
        db: Session,
        organization_id: str,
        incident_id: str,
        summary: str,
        root_cause: str,
        severity: str,
        repository_id: Optional[str] = None,
    ) -> HistoricalEvidence:
        """Automatically create a historical evidence record from an incident."""
        content = (
            f"Incident [{severity}]: {summary}. "
            f"Root cause: {root_cause}"
        )
        data = HistoricalEvidenceCreate(
            organization_id=organization_id,
            repository_id=repository_id,
            evidence_type="INCIDENT",
            title=f"Incident: {summary[:100]}",
            content=content,
            provenance={
                "source": "incident_record",
                "incident_id": incident_id,
                "severity": severity,
            },
        )
        return HistoricalEvidenceService.store_evidence(db, data)

    # --- TF-IDF Internals ---

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase terms, stripping punctuation and common stop words."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
            "and", "or", "not", "this", "that", "it", "its", "but", "so", "if",
        }
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    @staticmethod
    def _compute_tfidf_vector(text: str) -> Dict[str, float]:
        """
        Compute a lightweight TF (term frequency) vector for a document.

        Uses log-normalized TF. In a full implementation, IDF would be computed
        across the corpus; here we use TF alone which is sufficient for cosine
        similarity ranking in moderate-size knowledge bases.
        """
        tokens = HistoricalEvidenceService._tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        max_freq = max(counts.values())
        return {
            term: round(0.5 + 0.5 * (count / max_freq), 4)
            for term, count in counts.items()
        }

    @staticmethod
    def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse term-frequency vectors."""
        if not vec_a or not vec_b:
            return 0.0

        common_terms = set(vec_a.keys()) & set(vec_b.keys())
        if not common_terms:
            return 0.0

        dot_product = sum(vec_a[t] * vec_b[t] for t in common_terms)
        magnitude_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        magnitude_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
