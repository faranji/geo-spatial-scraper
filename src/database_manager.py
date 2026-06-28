""" Handles all database transactions, connection pooling, and atomic updates. """
import os
import sys
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Üst klasördeki config.py dosyasına erişebilmek için yolu ekliyoruz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# SQLAlchemy Engine
# pool_size: Aynı anda kaç bağlantıya izin verileceğini belirler (Sanal makinelerimiz için hayati önem taşır)
engine = create_engine(
    config.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SCHEMAS ---

class SpatialGrid(Base):
    """Haritadaki 1x1 km'lik taranacak koordinat karelerini tutan tablo."""
    __tablename__ = "spatial_grids"

    id = Column(String, primary_key=True, index=True)       # Örn: izmir_grid_1
    city = Column(String, index=True)                       # izmir veya istanbul_europe
    min_lat = Column(Float, nullable=False)
    min_lon = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    max_lon = Column(Float, nullable=False)
    status = Column(String, default="Pending", index=True)  # Pending, Processing, Completed
    worker_id = Column(String, nullable=True)               # Görevi alan sanal makinenin adı
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Venue(Base):
    """Google Maps üzerinden kazınan restoran ve kafelerin nihai verilerini tutan tablo."""
    __tablename__ = "venues"

    id = Column(String, primary_key=True, index=True)       # Benzersiz mekan ID'si
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rating = Column(Float)
    review_count = Column(Integer)
    category = Column(String)                               # kafe veya restoran
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