"""Safe extraction and redaction of uploaded text logs for AI analysis."""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.models.incident import Incident
from app.models.log_file import LogFile

_RELEVANT_LINE = re.compile(
    r"\b(error|fatal|critical|exception|traceback|stack trace|failed|failure|"
    r"timeout|timed out|database|sql|postgres|mysql|mongodb|redis|connection refused|"
    r"network|dns|socket|tls|ssl|unauthorized|forbidden|authentication|authorization|"
    r"invalid token|permission denied)\b",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)([\"']?\b(?:password|passwd|pwd|secret|client_secret|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|auth[_-]?token|session[_-]?id|cookie|set-cookie|token|private[_-]?key)"
    r"\b[\"']?\s*[:=]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^,\s;]+)"
)
_AUTH_HEADER = re.compile(
    r"(?i)(\b(?:proxy-)?authorization\s*[:=]\s*)(?:(?:bearer|basic)\s+)?[^\s,;]+"
)
_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_URL_PASSWORD = re.compile(
    r"(?i)(?:https?|postgres(?:ql)?|mysql|rediss?)://[^\s/@:]+:[^\s/@]+@"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_sensitive_values(text: str) -> str:
    """Redact common credentials, bearer tokens, email addresses, and key blocks."""
    redacted = _PRIVATE_KEY.sub("[REDACTED PRIVATE KEY]", text)
    redacted = _URL_PASSWORD.sub("[REDACTED CREDENTIALS]@", redacted)
    redacted = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", redacted)
    redacted = _AUTH_HEADER.sub(r"\1[REDACTED]", redacted)
    redacted = _BEARER_TOKEN.sub("Bearer [REDACTED]", redacted)
    redacted = _JWT.sub("[REDACTED JWT]", redacted)
    redacted = _AWS_ACCESS_KEY.sub("[REDACTED AWS KEY]", redacted)
    return _EMAIL.sub("[REDACTED EMAIL]", redacted)


def extract_relevant_log_content(
    text: str,
    *,
    max_chars: int | None = None,
    context_lines: int = 1,
) -> str:
    """Select error-relevant lines with nearby context, redact, and bound output."""
    limit = max(
        1, max_chars if max_chars is not None else settings.MAX_ANALYSIS_LOG_CHARS)

    def truncate(value: str) -> str:
        marker = "\n... excerpt truncated at the analysis limit ..."
        if len(value) <= limit:
            return value
        if limit <= len(marker):
            return value[:limit]
        return value[: limit - len(marker)] + marker

    redacted_lines = redact_sensitive_values(text).splitlines()
    if not redacted_lines:
        return ""

    matches = [index for index, line in enumerate(
        redacted_lines) if _RELEVANT_LINE.search(line)]
    if not matches:
        excerpt = "\n".join(redacted_lines)
        return truncate(excerpt)

    selected: set[int] = set()
    for index in matches:
        selected.update(
            range(max(index - context_lines, 0),
                  min(index + context_lines + 1, len(redacted_lines)))
        )

    chunks: list[str] = []
    previous: int | None = None
    for index in sorted(selected):
        if previous is not None and index > previous + 1:
            chunks.append("... unrelated log lines omitted ...")
        chunks.append(redacted_lines[index])
        previous = index

    excerpt = "\n".join(chunks)
    return truncate(excerpt)


def get_log_excerpt(
    db: Session,
    *,
    incident: Incident,
    log_file_id: int | None = None,
) -> str:
    """Read one incident-owned TXT log and return a bounded, redacted excerpt.

    If the incident has no TXT upload, an empty excerpt is returned so metadata-only
    analysis remains available. A requested file must belong to this incident.
    """
    query = db.query(LogFile).filter(
        LogFile.incident_id == incident.id,
        LogFile.file_type == "txt",
    )
    if log_file_id is not None:
        query = query.filter(LogFile.id == log_file_id)
        log_file = query.first()
        if log_file is None:
            raise ResourceNotFoundException("log file", log_file_id)
    else:
        log_file = query.order_by(
            LogFile.uploaded_at.desc(), LogFile.id.desc()).first()
        if log_file is None:
            return ""

    if log_file.size_bytes is not None and log_file.size_bytes > settings.max_upload_size_bytes:
        raise ValidationException(
            "Uploaded log file exceeds the analysis size limit")

    upload_root = Path(settings.UPLOAD_DIRECTORY).resolve()
    try:
        log_path = Path(log_file.file_path).resolve(strict=True)
        log_path.relative_to(upload_root)
    except FileNotFoundError as exc:
        raise ValidationException("Uploaded log file is missing") from exc
    except ValueError as exc:
        raise ValidationException("Uploaded log file path is invalid") from exc
    except OSError as exc:
        raise ValidationException("Uploaded log file cannot be read") from exc

    try:
        if not log_path.is_file():
            raise ValidationException("Uploaded log file is unavailable")
        file_size = log_path.stat().st_size
    except OSError as exc:
        raise ValidationException("Uploaded log file cannot be read") from exc
    if file_size > settings.max_upload_size_bytes:
        raise ValidationException(
            "Uploaded log file exceeds the analysis size limit")

    try:
        with log_path.open("rb") as log_file:
            raw_content = log_file.read(settings.max_upload_size_bytes + 1)
    except OSError as exc:
        raise ValidationException("Uploaded log file cannot be read") from exc
    if len(raw_content) > settings.max_upload_size_bytes:
        raise ValidationException(
            "Uploaded log file exceeds the analysis size limit")
    try:
        content = raw_content.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationException(
            "Uploaded log file must use UTF-8 encoding") from exc
    if not content.strip():
        raise ValidationException("Uploaded log file is empty")

    return extract_relevant_log_content(content)
