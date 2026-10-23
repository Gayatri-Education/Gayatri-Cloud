"""Test configuration loading, validation, and secret masking."""

from app.core.config import Settings


def test_default_settings_instantiation():
    """Verify default settings instantiation and environment properties."""
    cfg = Settings(ENVIRONMENT="testing", DEBUG=True)
    assert cfg.is_testing is True
    assert cfg.is_production is False
    assert cfg.APP_NAME == "Gayatri Cloud API"


def test_cors_origins_parsing():
    """Verify CORS origins parsing from list, json string, and comma-separated string."""
    # List
    cfg1 = Settings(CORS_ORIGINS=["http://localhost:3000", "http://example.com"])
    assert len(cfg1.CORS_ORIGINS) == 2
    assert "http://example.com" in cfg1.CORS_ORIGINS

    # JSON String
    cfg2 = Settings(CORS_ORIGINS='["http://localhost:3000", "http://app.gayatri.internal"]')
    assert len(cfg2.CORS_ORIGINS) == 2
    assert "http://app.gayatri.internal" in cfg2.CORS_ORIGINS

    # Comma-separated string
    cfg3 = Settings(CORS_ORIGINS="http://localhost:3000, http://test.com")
    assert len(cfg3.CORS_ORIGINS) == 2
    assert "http://test.com" in cfg3.CORS_ORIGINS


def test_public_metadata_excludes_secrets():
    """Verify get_public_metadata exposes only safe metadata."""
    cfg = Settings(
        SECRET_KEY="super-secret-key-12345", DATABASE_URL="postgresql://user:pass@host/db"
    )
    meta = cfg.get_public_metadata()
    assert "app_name" in meta
    assert "version" in meta
    assert "environment" in meta
    assert "super-secret-key-12345" not in str(meta)
    assert "pass@" not in str(meta)
