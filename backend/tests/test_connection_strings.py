from app.core.connection_strings import derive_sync_database_url, summarize_database_url, summarize_redis_url


def test_derive_sync_database_url_converts_asyncpg_to_psycopg2():
    url = "postgresql+asyncpg://user:pass@db.example.com:5432/mydb?sslmode=require"
    out = derive_sync_database_url(database_url=url)
    assert out.startswith("postgresql+psycopg2://")
    assert "sslmode=require" in out


def test_derive_sync_database_url_converts_aiosqlite_to_sqlite():
    url = "sqlite+aiosqlite:////tmp/test.db"
    out = derive_sync_database_url(database_url=url)
    assert out.startswith("sqlite:////tmp/test.db")


def test_summarize_database_url_masks_credentials():
    url = "postgresql+asyncpg://user:pass@db.example.com:5432/mydb?sslmode=require"
    s = summarize_database_url(url)
    assert s["host"] == "db.example.com"
    assert s["port"] == 5432
    assert s["dbname"] == "mydb"
    assert s["sslmode"] == "require"


def test_summarize_redis_url():
    s = summarize_redis_url("rediss://:pw@redis.example.com:6380/0")
    assert s["host"] == "redis.example.com"
    assert s["tls"] is True
