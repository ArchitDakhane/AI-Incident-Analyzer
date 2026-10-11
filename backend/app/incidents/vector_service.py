
"""Gemini embedding and Qdrant similarity search service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ServiceException
from app.core.logger import get_logger
from app.models.ai_report import AIReport
from app.models.incident import Incident

logger = get_logger(__name__)


@dataclass(slots=True)
class VectorSearchHit:
    """A single vector database search result."""

    point_id: str
    score: float
    payload: dict[str, Any]


class QdrantVectorClient:
    """Small Qdrant HTTP client for storing and searching embeddings."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        collection_name: str,
        api_key: str = "",
    ) -> None:
        self.collection_name = collection_name
        self.base_url = self._build_base_url(host, port)
        self.headers = {"api-key": api_key} if api_key else {}

    @staticmethod
    def _build_base_url(host: str, port: int) -> str:
        """Build the Qdrant base URL."""
        normalized_host = host.rstrip("/")

        if normalized_host.startswith(("http://", "https://")):
            return normalized_host

        return f"http://{normalized_host}:{port}"

    def ensure_collection(self, vector_size: int) -> None:
        """Create the Qdrant collection if it does not exist."""
        collection_url = (
            f"{self.base_url}/collections/{self.collection_name}"
        )

        try:
            response = httpx.get(
                collection_url,
                headers=self.headers,
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            logger.exception("Qdrant collection inspection failed")
            raise ServiceException(
                "Unable to inspect Qdrant collection"
            ) from exc

        if response.status_code == 200:
            return

        if response.status_code != 404:
            logger.error(
                "Qdrant collection inspection returned status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise ServiceException(
                "Unable to inspect Qdrant collection"
            )

        logger.info(
            "Qdrant collection '%s' does not exist; creating it",
            self.collection_name,
        )

        try:
            create_response = httpx.put(
                collection_url,
                headers=self.headers,
                json={
                    "vectors": {
                        "size": vector_size,
                        "distance": "Cosine",
                    }
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            logger.exception("Qdrant collection creation failed")
            raise ServiceException(
                "Unable to create Qdrant collection"
            ) from exc

        if create_response.status_code >= 400:
            logger.error(
                "Qdrant collection creation returned status=%s body=%s",
                create_response.status_code,
                create_response.text[:500],
            )
            raise ServiceException(
                "Unable to create Qdrant collection"
            )

        logger.info(
            "Created Qdrant collection '%s' with vector size %s",
            self.collection_name,
            vector_size,
        )

    def upsert_embedding(
        self,
        *,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Store or replace one incident embedding in Qdrant."""
        self.ensure_collection(len(vector))

        try:
            response = httpx.put(
                (
                    f"{self.base_url}/collections/"
                    f"{self.collection_name}/points"
                ),
                headers=self.headers,
                params={"wait": "true"},
                json={
                    "points": [
                        {
                            "id": point_id,
                            "vector": vector,
                            "payload": payload,
                        }
                    ]
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            logger.exception("Qdrant embedding upsert failed")
            raise ServiceException(
                "Unable to store embedding in Qdrant"
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "Qdrant embedding upsert returned status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise ServiceException(
                "Unable to store embedding in Qdrant"
            )

        logger.info(
            "Stored embedding '%s' in Qdrant collection '%s'",
            point_id,
            self.collection_name,
        )

    def search_similar(
        self,
        *,
        vector: list[float],
        limit: int,
        owner_id: int,
    ) -> list[VectorSearchHit]:
        """Search Qdrant for similar incidents belonging to one user."""
        self.ensure_collection(len(vector))

        try:
            response = httpx.post(
                (
                    f"{self.base_url}/collections/"
                    f"{self.collection_name}/points/search"
                ),
                headers=self.headers,
                json={
                    "vector": vector,
                    "limit": limit,
                    "with_payload": True,
                    "filter": {
                        "must": [
                            {
                                "key": "owner_id",
                                "match": {"value": owner_id},
                            }
                        ]
                    },
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            logger.exception("Qdrant similarity search failed")
            raise ServiceException(
                "Unable to search similar incidents"
            ) from exc

        if response.status_code >= 400:
            logger.error(
                "Qdrant similarity search returned status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise ServiceException(
                "Unable to search similar incidents"
            )

        try:
            data = response.json()
            hits = data.get("result", [])
        except (ValueError, AttributeError) as exc:
            logger.exception("Invalid Qdrant search response")
            raise ServiceException(
                "Invalid Qdrant search response"
            ) from exc

        return [
            VectorSearchHit(
                point_id=str(hit.get("id")),
                score=float(hit.get("score", 0.0)),
                payload=hit.get("payload") or {},
            )
            for hit in hits
        ]


def get_vector_client() -> QdrantVectorClient:
    """Build a Qdrant client from application settings."""
    return QdrantVectorClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        api_key=settings.QDRANT_API_KEY,
    )


def generate_embedding(text: str) -> list[float]:
    """Generate a 768-dimensional embedding using Gemini."""
    if (
        not settings.GEMINI_API_KEY
        or settings.GEMINI_API_KEY == "your-gemini-api-key-here"
    ):
        raise ServiceException("Gemini API key is not configured")

    try:
        response = httpx.post(
            (
                "https://generativelanguage.googleapis.com/v1beta/"
                "models/gemini-embedding-001:embedContent"
            ),
            headers={
                "x-goog-api-key": settings.GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": 768,
            },
            timeout=20.0,
        )
        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gemini embedding request failed: status=%s body=%s",
            exc.response.status_code,
            exc.response.text[:500],
        )
        raise ServiceException(
            "Gemini embedding request failed "
            f"(HTTP {exc.response.status_code})"
        ) from exc

    except httpx.HTTPError as exc:
        logger.exception("Unable to connect to Gemini embedding service")
        raise ServiceException(
            "Unable to connect to Gemini embedding service"
        ) from exc

    try:
        values = response.json()["embedding"]["values"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ServiceException(
            "Invalid Gemini embedding response format"
        ) from exc

    if not isinstance(values, list) or len(values) != 768:
        raise ServiceException(
            "Gemini returned an embedding with an unexpected dimension"
        )

    try:
        return [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise ServiceException(
            "Gemini returned invalid embedding values"
        ) from exc


def parse_report_content(
    ai_report: AIReport | None,
) -> dict[str, Any]:
    """Return AI report content as a dictionary."""
    if ai_report is None:
        return {}

    try:
        payload = json.loads(ai_report.content)
    except (json.JSONDecodeError, TypeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def get_latest_ai_report(
    db: Session,
    incident_id: int,
) -> AIReport | None:
    """Return the newest AI report for an incident."""
    return (
        db.query(AIReport)
        .filter(AIReport.incident_id == incident_id)
        .order_by(AIReport.created_at.desc())
        .first()
    )


def build_embedding_text(
    incident: Incident,
    ai_report: AIReport | None,
) -> str:
    """Build the text used for incident embeddings."""
    report_payload = parse_report_content(ai_report)
    description = incident.description or incident.title
    summary = report_payload.get("summary", "")

    return (
        f"Incident description:\n{description}\n\n"
        f"AI summary:\n{summary}"
    ).strip()


def build_vector_payload(
    incident: Incident,
    ai_report: AIReport,
) -> dict[str, Any]:
    """Build Qdrant payload metadata for an incident embedding."""
    report_payload = parse_report_content(ai_report)

    findings = report_payload.get("findings") or []
    recommendations = report_payload.get("recommended_actions") or []

    root_cause = report_payload.get("root_cause")
    if not root_cause and findings:
        root_cause = str(findings[0])
    if not root_cause:
        root_cause = report_payload.get("summary", "")

    resolution_summary = report_payload.get("resolution_summary")
    if not resolution_summary and recommendations:
        resolution_summary = "; ".join(
            str(item) for item in recommendations
        )

    return {
        "incident_id": incident.id,
        "owner_id": incident.created_by_id,
        "ai_report_id": ai_report.id,
        "title": incident.title,
        "root_cause": root_cause or "",
        "resolution_summary": resolution_summary or "",
        "summary": report_payload.get("summary", ""),
    }


def index_ai_report_embedding(
    db: Session,
    *,
    incident: Incident,
    ai_report: AIReport,
) -> str | None:
    """Generate and store an embedding for an AI report.

    Indexing is best-effort so users can still receive an AI report
    when Gemini embeddings or Qdrant are temporarily unavailable.
    """
    try:
        embedding_text = build_embedding_text(incident, ai_report)
        vector = generate_embedding(embedding_text)
        point_id = f"incident-{incident.id}-report-{ai_report.id}"

        get_vector_client().upsert_embedding(
            point_id=point_id,
            vector=vector,
            payload=build_vector_payload(incident, ai_report),
        )

    except (ServiceException, httpx.HTTPError):
        logger.exception(
            "Skipping incident embedding indexing for incident_id=%s "
            "and ai_report_id=%s",
            incident.id,
            ai_report.id,
        )
        return None

    ai_report.embedding_id = point_id
    db.commit()
    db.refresh(ai_report)

    return point_id


def search_similar_incidents(
    db: Session,
    *,
    incident: Incident,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return the top similar incidents for an incident."""
    ai_report = get_latest_ai_report(db, incident.id)
    query_text = build_embedding_text(incident, ai_report)
    query_vector = generate_embedding(query_text)

    if incident.created_by_id is None:
        return []

    hits = get_vector_client().search_similar(
        vector=query_vector,
        limit=top_k + 1,
        owner_id=incident.created_by_id,
    )

    results: list[dict[str, Any]] = []
    seen_incident_ids: set[int] = set()

    for hit in hits:
        incident_id = hit.payload.get("incident_id")

        if incident_id is None:
            continue

        incident_id = int(incident_id)

        # Do not return the current incident as its own match.
        if (
            incident_id == incident.id
            or incident_id in seen_incident_ids
        ):
            continue

        matched_incident = (
            db.query(Incident)
            .filter(
                Incident.id == incident_id,
                Incident.created_by_id == incident.created_by_id,
            )
            .first()
        )

        if matched_incident is None:
            continue

        matched_report = get_latest_ai_report(db, incident_id)

        fallback_payload = (
            build_vector_payload(matched_incident, matched_report)
            if matched_report is not None
            else {}
        )

        results.append(
            {
                "incident_id": incident_id,
                "title": matched_incident.title,
                "similarity_score": hit.score,
                "root_cause": (
                    hit.payload.get("root_cause")
                    or fallback_payload.get("root_cause", "")
                ),
                "resolution_summary": (
                    hit.payload.get("resolution_summary")
                    or fallback_payload.get("resolution_summary", "")
                ),
            }
        )

        seen_incident_ids.add(incident_id)

        if len(results) == top_k:
            break

    return results
