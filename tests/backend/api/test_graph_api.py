from unittest.mock import MagicMock, patch
import pytest
from app.services.impact.impact_analyzer import ImpactAnalysisResult, ImpactedFile, ImpactLevel


def test_graph_health_endpoint(client):
    with patch("app.services.graph.neo4j_connection.Neo4jConnection.health_check") as mock_health:
        mock_health.return_value = {"status": "healthy", "uri": "bolt://localhost:7687"}
        response = client.get("/api/v1/graph/health")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "healthy"


def test_graph_repository_endpoint(client):
    with patch("app.services.graph.graph_service.GraphService.ensure_schema") as mock_schema, \
         patch("app.services.graph.graph_service.GraphService.get_repository_graph") as mock_graph:
        mock_graph.return_value = {
            "repository_id": "repo-test-1",
            "nodes": [
                {"id": "file:1", "label": "app/main.py", "type": "file", "properties": {"language": "python"}},
                {"id": "file:2", "label": "app/utils.py", "type": "file", "properties": {"language": "python"}},
            ],
            "edges": [
                {"source": "file:1", "target": "file:2", "relationship": "IMPORTS"},
            ],
            "total_files": 2,
        }
        response = client.get("/api/v1/graph/repository/repo-test-1")
        assert response.status_code == 200
        res_data = response.json()["data"]
        assert len(res_data["nodes"]) == 2
        assert len(res_data["edges"]) == 1
        assert res_data["edges"][0]["relationship"] == "IMPORTS"


def test_graph_stats_endpoint(client):
    with patch("app.services.graph.graph_service.GraphService.ensure_schema") as mock_schema, \
         patch("app.services.graph.graph_service.GraphService.get_graph_stats") as mock_stats:
        mock_stats.return_value = {
            "repository_id": "repo-test-1",
            "total_files": 12,
            "total_classes": 8,
            "total_functions": 35,
            "total_import_edges": 24,
        }
        response = client.get("/api/v1/graph/stats/repo-test-1")
        assert response.status_code == 200
        res_data = response.json()["data"]
        assert res_data["total_files"] == 12
        assert res_data["total_classes"] == 8
        assert res_data["total_functions"] == 35
        assert res_data["total_import_edges"] == 24


def test_graph_impact_analysis_endpoint(client):
    with patch("app.services.graph.graph_service.GraphService.ensure_schema") as mock_schema, \
         patch("app.services.impact.impact_analyzer.ImpactAnalyzer.analyze_changes") as mock_analyze:
        
        file = ImpactedFile(
            path="app/views.py",
            language="python",
            impact_level=ImpactLevel.FIRST_ORDER,
            impact_chain=["app/models.py"],
            risk_score=0.8,
        )
        mock_analyze.return_value = ImpactAnalysisResult(
            repository_id="repo-test-1",
            changed_files=["app/models.py"],
            directly_impacted=[file],
            transitively_impacted=[],
            total_files_affected=2,
            risk_summary={
                "overall_risk": "high",
                "risk_score": 0.8,
                "high_risk_files": 1,
                "medium_risk_files": 0,
                "low_risk_files": 0,
                "blast_radius": 2,
            },
        )
        response = client.post(
            "/api/v1/graph/impact/repo-test-1",
            json={"changed_files": ["app/models.py"], "max_depth": 3},
        )
        assert response.status_code == 200
        res_data = response.json()["data"]
        assert res_data["repository_id"] == "repo-test-1"
        assert res_data["total_files_affected"] == 2
        assert res_data["risk_summary"]["overall_risk"] == "high"


def test_graph_file_ingestion_endpoint(client):
    with patch("app.services.graph.graph_service.GraphService.ensure_schema") as mock_schema, \
         patch("app.services.graph.graph_service.GraphService.ingest_file_analysis") as mock_ingest:
        
        mock_ingest.return_value = {
            "files": 1,
            "classes": 1,
            "functions": 2,
            "methods": 0,
            "imports": 1,
            "relationships": 3,
        }
        
        payload = {
            "repository_id": "repo-test-1",
            "commit_sha": "abc1234def5678",
            "files": [
                {
                    "path": "app/calculator.py",
                    "content": "import math\n\nclass Calculator:\n    pass\n\ndef add(a, b):\n    return a + b\n",
                }
            ],
        }
        response = client.post("/api/v1/graph/ingest", json=payload)
        assert response.status_code == 200
        res_data = response.json()["data"]
        assert res_data["files_processed"] == 1
        assert res_data["total_classes"] == 1
        assert res_data["total_functions"] == 2
