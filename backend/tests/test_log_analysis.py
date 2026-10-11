"""Log selection, redaction, bounds, and AI prompt integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database.base import Base
from app.database.session import get_db
from app.incidents.log_analysis import extract_relevant_log_content
from app.models.log_file import LogFile
from main import create_app


@pytest.fixture
def client_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = testing_session()

    def override_get_db():
        yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield {"client": test_client, "db": db}
    app.dependency_overrides.clear()
    db.close()


def test_excerpt_keeps_error_context_and_redacts_common_secrets() -> None:
    text = "\n".join(
        [
            "startup complete",
            "connecting to database",
            'database connection timeout password="hunter2" email=alice@example.com',
            "retry scheduled",
            "normal heartbeat",
            "AWS access key AKIAABCDEFGHIJKLMNOP",
            "Bearer abc.def.ghi",
        ]
    )

    excerpt = extract_relevant_log_content(text, max_chars=500)

    assert "connecting to database" in excerpt
    assert "database connection timeout" in excerpt
    assert "retry scheduled" in excerpt
    assert "hunter2" not in excerpt
    assert "alice@example.com" not in excerpt
    assert "AKIAABCDEFGHIJKLMNOP" not in excerpt
    assert "abc.def.ghi" not in excerpt
    assert "normal heartbeat" not in excerpt


def test_excerpt_is_bounded_even_for_a_long_matching_line() -> None:
    excerpt = extract_relevant_log_content(
        "ERROR " + ("x" * 200), max_chars=40)

    assert len(excerpt) <= 40
    assert "ERROR" in excerpt


def _register_and_incident(client: TestClient, email: str, username: str) -> tuple[dict, dict]:
    session = client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "secret123"},
    ).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    incident = client.post(
        "/api/incidents",
        json={"title": f"{username} incident",
              "description": "service incident"},
        headers=headers,
    ).json()
    return session, {**headers, "incident": incident}


def test_ai_prompt_uses_only_selected_incident_log_and_redacts_values(
    client_and_db,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client = client_and_db["client"]
    db: Session = client_and_db["db"]
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))
    prompts: list[str] = []

    def fake_gemini(prompt: str, api_key: str) -> str:
        prompts.append(prompt)
        return (
            '{"summary":"Database connection timed out","findings":["pool timeout"],'
            '"recommended_actions":["check pool"],"confidence_score":0.9}'
        )

    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api", fake_gemini)
    monkeypatch.setattr(
        "app.incidents.ai_service.index_ai_report_embedding", lambda *args, **kwargs: None)

    owner, owner_info = _register_and_incident(
        client, "logs-owner@example.com", "logsowner")
    other, other_info = _register_and_incident(
        client, "logs-other@example.com", "logsother")
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    selected_upload = client.post(
        f"/api/incidents/{owner_info['incident']['id']}/upload",
        files={
            "file": (
                "prod.txt",
                b"service startup\n"
                b"database connection timeout password=super-secret\n"
                b"retrying request\n",
                "text/plain",
            )
        },
        headers=owner_headers,
    )
    unrelated_upload = client.post(
        f"/api/incidents/{other_info['incident']['id']}/upload",
        files={
            "file": ("other.txt", b"OTHER TENANT PRIVATE LOG MARKER", "text/plain")},
        headers=other_headers,
    )
    selected_id = selected_upload.json()["id"]

    listed = client.get(
        f"/api/incidents/{owner_info['incident']['id']}/logs", headers=owner_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == selected_id
    assert "file_path" not in listed.json()[0]

    generated = client.post(
        f"/api/incidents/{owner_info['incident']['id']}/ai-report",
        params={"log_file_id": selected_id},
        headers=owner_headers,
    )
    assert generated.status_code == 200
    assert "database connection timeout" in prompts[0]
    assert "retrying request" in prompts[0]
    assert "super-secret" not in prompts[0]
    assert "OTHER TENANT PRIVATE LOG MARKER" not in prompts[0]

    cross_owner_list = client.get(
        f"/api/incidents/{other_info['incident']['id']}/logs",
        headers=owner_headers,
    )
    cross_owner_analysis = client.post(
        f"/api/incidents/{owner_info['incident']['id']}/ai-report",
        params={"log_file_id": unrelated_upload.json()["id"]},
        headers=owner_headers,
    )
    assert cross_owner_list.status_code == 404
    assert cross_owner_analysis.status_code == 404
    assert owner["user"]["id"] != other["user"]["id"]
    assert db.query(LogFile).count() == 2


def test_log_analysis_handles_empty_invalid_missing_and_oversized_files(
    client_and_db,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client = client_and_db["client"]
    db: Session = client_and_db["db"]
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    monkeypatch.setattr(
        "app.incidents.ai_service.call_gemini_api",
        lambda *args, **kwargs: pytest.fail(
            "Gemini must not be called for invalid logs"),
    )
    monkeypatch.setattr(
        "app.incidents.ai_service.index_ai_report_embedding", lambda *args, **kwargs: None)

    session, info = _register_and_incident(
        client, "log-validation@example.com", "logvalidation"
    )
    incident_id = info["incident"]["id"]
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    def upload(name: str, content: bytes) -> int:
        response = client.post(
            f"/api/incidents/{incident_id}/upload",
            files={"file": (name, content, "text/plain")},
            headers=headers,
        )
        assert response.status_code == 200
        return response.json()["id"]

    empty_id = upload("empty.txt", b"")
    invalid_encoding_id = upload("invalid.txt", b"\xff\xfe\xfa")
    missing_id = upload("missing.txt", b"valid log line")
    oversized_id = upload("oversized.txt", b"valid log line")

    missing_row = db.query(LogFile).filter(LogFile.id == missing_id).one()
    Path(missing_row.file_path).unlink()
    oversized_row = db.query(LogFile).filter(LogFile.id == oversized_id).one()
    Path(oversized_row.file_path).write_bytes(
        b"x" * (settings.max_upload_size_bytes + 1))

    for file_id in (empty_id, invalid_encoding_id, missing_id, oversized_id):
        response = client.post(
            f"/api/incidents/{incident_id}/ai-report",
            params={"log_file_id": file_id},
            headers=headers,
        )
        assert response.status_code == 422
