""" Handles all database transactions, connection pooling, and atomic updates. """
import os
import sys
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.pool import NullPool

# for config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    try:
        import config
        DATABASE_URL = config.DATABASE_URL
        
    except ImportError:
        import streamlit as st
        DATABASE_URL = st.secrets["DATABASE_URL"]


# SQLAlchemy Engine
# pool_size: Aynı anda kaç bağlantıya izin verileceğini belirler (for VMs)

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,     
    connect_args={
        "keepalives": 1,       
        "keepalives_idle": 30,  # 30 saniye boşta kalırsa dürtmeye başla
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SCHEMAS ---

class SpatialGrid(Base):
    """Haritadaki 1x1 km'lik taranacak koordinat karelerini tutan tablo."""
    __tablename__ = "spatial_grids"

    id = Column(String, primary_key=True, index=True)       # exp: izmir_grid_1
    city = Column(String, index=True)                       # izmir or istanbul_europe
    min_lat = Column(Float, nullable=False)
    min_lon = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    max_lon = Column(Float, nullable=False)
    status = Column(String, default="Pending", index=True)  # Pending, Processing, Completed, Subdivided
    worker_id = Column(String, nullable=True)               
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Venue(Base):
    __tablename__ = "venues"

    id = Column(String, primary_key=True, index=True)       # unique venue id
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rating = Column(Float)
    review_count = Column(Integer)
    category = Column(String)                               # cafe or restaurant
    address = Column(String)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

# --- DATABASE MANAGEMENT CLASS ---

class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_tables(self):
        try:
            Base.metadata.create_all(bind=engine)
            print("SUCCESS: check the Table Editor!")
        except Exception as e:
            print(f"couldn't connect to server. error code: {e}")

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_tables()