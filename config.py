import os

# Supabase Credentials (Get these from Supabase Dashboard)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Database Connection String for SQLAlchemy / Psycopg2
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db-address:5432/postgres")

# Scraping Settings
MAX_CONCURRENT_TASKS = 4
DEFAULT_GRID_SIZE_KM = 1.0  # Initial bounding box size