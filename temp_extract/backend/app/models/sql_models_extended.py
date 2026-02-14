
# --- GAME CONFIG & ASSET MODELS ---
# These are merged into sql_models.py but kept here if imported directly.
# To avoid duplicate table error, we only define if not already defined, or we rely on sql_models.py
# But best practice: remove duplicate definitions if they exist in main sql_models.py

# Empty file or just helper Pydantic models if needed.
# Since we moved everything to sql_models.py, this file should probably be empty or removed to avoid confusion/errors.
# Or if it's imported, it should import FROM sql_models.py

# Re-exporting them allows existing imports to work without breaking.
