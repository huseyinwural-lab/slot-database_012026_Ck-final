import pytest
from sqlalchemy import text
from app.db import get_db

def test_backfill_verification():
    """Verify no users have NULL segment_type after migration."""
    db = next(get_db())
    
    # Check for NULLs
    result = db.execute(text("SELECT count(*) FROM users WHERE segment_type IS NULL")).scalar()
    assert result == 0, "Found users with NULL segment_type!"
    
    # Check for Default Value correctness
    result_individual = db.execute(text("SELECT count(*) FROM users WHERE segment_type = 'INDIVIDUAL'")).scalar()
    total_users = db.execute(text("SELECT count(*) FROM users")).scalar()
    
    # Assuming this runs immediately after migration on existing data where all were null
    assert result_individual == total_users, "Not all users were backfilled to INDIVIDUAL"
