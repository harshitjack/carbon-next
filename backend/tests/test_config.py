import logging

from app.core.config import Settings, validate_config


def test_validate_config_all_present(caplog):
    settings = Settings(
        USE_OPENROUTER=True,
        USE_GEMINI=True,
        OPENROUTER_API_KEY="test",
        USE_SUPABASE=True,
        USE_FIRESTORE=True,
        SUPABASE_DB_URL="test"
    )
    with caplog.at_level(logging.INFO):
        validate_config(settings)
    assert "configuration validated successfully" in caplog.text

def test_validate_config_missing_vars(caplog):
    settings = Settings(
        USE_OPENROUTER=True,
        USE_GEMINI=True,
        OPENROUTER_API_KEY="",
        USE_SUPABASE=True,
        USE_FIRESTORE=True,
        SUPABASE_DB_URL=""
    )
    with caplog.at_level(logging.INFO):
        validate_config(settings)
    assert "OPENROUTER_API_KEY is not set" in caplog.text
    assert "SUPABASE_DB_URL is not set" in caplog.text
    assert "2 config warning(s)" in caplog.text

def test_dsn_sanitization():
    settings = Settings(
        SUPABASE_DB_URL="postgresql://postgres:Harshit#123@123@db.mnvdxrpkhroslxjzuxni.supabase.co:5432/postgres"
    )
    assert settings.SUPABASE_DB_URL == "postgresql://postgres:Harshit%23123%40123@db.mnvdxrpkhroslxjzuxni.supabase.co:5432/postgres"
