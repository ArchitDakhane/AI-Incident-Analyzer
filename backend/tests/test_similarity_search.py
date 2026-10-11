"""Similar incident search tests."""

from __future__ import annotations

import math
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.incidents.vector_service import VectorSearchHit, generate_embedding
from app.models.ai_report import AIReport
from main import create_app


class InMemoryVectorClient:
    """Tiny Qdrant stand-in used by similarity tests."""

    def __init__(self) -> None:
        self.points: dict[str, dict[str, Any]] = {}

    def upsert_embedding(
        self,
        *,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        self.points[point_id] = {"vector": vector, "payload": payload}

    def search_similar(
        self,
        *,
        vector: list[float],
        limit: int,
        owner_id: int,
    ) -> list[VectorSearchHit]:
        hits = [
            VectorSearchHit(
                point_id=point_id,
                score=self._cosine_similarity(vector, point["vector"]),
                payload=point["payload"],
            )
            for point_id, point in self.points.items()
            if point["payload"].get("owner_id") == owner_id
        ]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        dot_product = sum(left_value * right_value for left_value,
                          right_value in zip(left, right))
        left_length = math.sqrt(sum(value * value for value in left))
        right_length = math.sqrt(sum(value * value for value in right))
        if left_length == 0 or right_length == 0:
            return 0.0
        return dot_product / (left_length * right_length)


@pytest.fixture()
def client_and_db():
    """Create a FastAPI test client with a shared in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield {"client": test_client, "db": db}

    app.dependency_overrides.clear()
    db.close()


def create_user_token(client: TestClient) -> str:
    """Create a user and return an access token."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "similar@example.com",
            "username": "similaruser",
            "password": "secret123",
        },
    )
    return register_response.json()["access_token"]


def fake_ai_response(prompt: str, api_key: str) -> str:
    """Return deterministic AI reports from incident titles in the prompt."""
    if "Database timeout" in prompt:
        return (
            '{"summary": "Database connection pool timeout", '
            '"findings": ["Database connection pool exhausted"], '
            '"recommended_actions": ["Increase pool size"], '
            '"confidence_score": 0.93}'
        )
    if "Database lock" in prompt:
        return (
            '{"summary": "Database row lock contention", '
            '"findings": ["Long transaction held locks"], '
            '"recommended_actions": ["Tune transaction boundaries"], '
            '"confidence_score": 0.89}'
        )
    if "Network timeout" in prompt:
        return (
            '{"summary": "Network timeout between services", '
            '"findings": ["Upstream network latency"], '
            '"recommended_actions": ["Add retries and circuit breaker"], '
            '"confidence_score": 0.81}'
        )
    return (
        '{"summary": "Authentication token failure", '
        '"findings": ["Expired JWT tokens"], '
        '"recommended_actions": ["Refresh tokens earlier"], '
        '"confidence_score": 0.77}'
    )


def fake_embedding(text: str) -> list[float]:
    """Return deterministic embeddings from report text."""
    lowered = text.lower()
    if "connection pool timeout" in lowered:
        return [1.0, 0.0, 0.0]
    if "row lock contention" in lowered:
        return [0.92, 0.1, 0.0]
    if "network timeout" in lowered:
        return [0.75, 0.2, 0.0]
    if "authentication token" in lowered:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def test_generate_embedding_parses_gemini_response(monkeypatch) -> None:
    """Gemini embedding responses should parse into float vectors."""

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"embedding": {"values": [0.1, "0.2", 0.3]}}

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "app.incidents.vector_service.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.incidents.vector_service.httpx.post", fake_post)

    assert generate_embedding("incident text") == [0.1, 0.2, 0.3]


def test_analyzed_incidents_are_indexed_and_searchable(client_and_db, monkeypatch) -> None:
    """Analyzed incidents should be stored in Qdrant and returned by similarity search."""
    client = client_and_db["client"]
    db = client_and_db["db"]
    vector_client = InMemoryVectorClient()
    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_ai_response)
    monkeypatch.setattr(
        "app.incidents.vector_service.generate_embedding", fake_embedding)
    monkeypatch.setattr(
        "app.incidents.vector_service.get_vector_client", lambda: vector_client)

    token = create_user_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    incident_ids: dict[str, int] = {}

    for title, description in [
        ("Database timeout", "Primary database requests are timing out"),
        ("Database lock", "Database writes are stuck behind locks"),
        ("Network timeout", "Service calls time out over the network"),
        ("Authentication failure", "Users are seeing invalid token errors"),
    ]:
        incident_response = client.post(
            "/api/incidents",
            json={"title": title, "description": description, "severity": "high"},
            headers=headers,
        )
        assert incident_response.status_code == 201
        incident_id = incident_response.json()["id"]
        incident_ids[title] = incident_id

        report_response = client.post(
            f"/api/incidents/{incident_id}/ai-report",
            headers=headers,
        )
        assert report_response.status_code == 200
        assert report_response.json()["embedding_id"] is not None

    assert len(vector_client.points) == 4
    assert db.query(AIReport).filter(
        AIReport.embedding_id.is_not(None)).count() == 4

    similar_response = client.get(
        f"/api/incidents/{incident_ids['Database timeout']}/similar",
        headers=headers,
    )

    assert similar_response.status_code == 200
    items = similar_response.json()["items"]
    assert len(items) == 3
    assert items[0]["title"] == "Database lock"
    assert items[0]["similarity_score"] > items[1]["similarity_score"]
    assert "Database connection pool" not in items[0]["root_cause"]
    assert {item["title"] for item in items} == {
        "Database lock",
        "Network timeout",
        "Authentication failure",
    }


def test_similar_incidents_do_not_cross_user_boundaries(client_and_db, monkeypatch) -> None:
    client = client_and_db["client"]
    vector_client = InMemoryVectorClient()
    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_ai_response)
    monkeypatch.setattr(
        "app.incidents.vector_service.generate_embedding", fake_embedding)
    monkeypatch.setattr(
        "app.incidents.vector_service.get_vector_client", lambda: vector_client)

    owner_token = create_user_token(client)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    owner_incident = client.post(
        "/api/incidents",
        json={"title": "Database timeout",
              "description": "Connection pool timed out"},
        headers=owner_headers,
    ).json()
    client.post(
        f"/api/incidents/{owner_incident['id']}/ai-report", headers=owner_headers)

    other_user = client.post(
        "/api/auth/register",
        json={"email": "similar-other@example.com",
              "username": "similarother", "password": "secret123"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other_user['access_token']}"}
    other_incident = client.post(
        "/api/incidents",
        json={"title": "Database lock",
              "description": "Private other-owner incident"},
        headers=other_headers,
    ).json()
    client.post(
        f"/api/incidents/{other_incident['id']}/ai-report", headers=other_headers)

    response = client.get(
        f"/api/incidents/{owner_incident['id']}/similar",
        headers=owner_headers,
    )
    assert response.status_code == 200
    assert response.json()["items"] == []

    other_response = client.get(
        f"/api/incidents/{other_incident['id']}/similar",
        headers=owner_headers,
    )
    assert other_response.status_code == 404
