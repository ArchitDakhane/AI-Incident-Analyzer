"""Application settings safety tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(ENVIRONMENT="production",
                 SECRET_KEY="dev-secret-key-not-for-production-change-me")


def test_production_accepts_long_generated_jwt_secret() -> None:
    settings = Settings(ENVIRONMENT="production", SECRET_KEY="a" * 48)

    assert settings.SECRET_KEY == "a" * 48
