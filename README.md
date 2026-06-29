# Geo-Spatial Distributed Scraper & Interactive Visualization Dashboard

A high-performance, distributed data engineering and geospatial analysis pipeline designed to extract, store, and visualize every cafe and restaurant across **Istanbul (European Side)** and **Izmir** without relying on official APIs. 

The core mission of this project is to achieve 100% coverage—ensuring that even the most obscure, hidden local spots are successfully mapped by leveraging a dynamic spatial grid algorithm instead of standard keyword search limitations.

---

## Architecture & Data Flow

The system is built on a modular, distributed architecture designed to run entirely on free-tier infrastructure while maximizing throughput and preventing IP rate-limiting.

1. **Spatial Grid Partitioning (`src/grid_generator.py`):** Uses `geopandas` and `shapely` to load official GeoJSON boundaries. It cuts the target regions into localized bounding boxes (starting at 1km² chunks) to bypass viewport limits.
2. **Distributed Scraping Engine (`src/playwright_scraper.py`):** An asynchronous `Playwright` browser automation framework deployed across a hybrid fleet of cloud virtual machines and GitHub Actions runners. Workers pull "Pending" grid coordinates from the queue dynamically.
3. **Centralized Storage (`src/database_manager.py`):** A multi-worker transactional pipeline that streams scraped data directly into a remote cloud **PostgreSQL (Supabase)** instance utilizing connection pooling.
4. **Analytics & Frontend Panel (`app/dashboard.py`):** A high-performance dashboard built with **Streamlit** that queries the database in real-time, rendering tens of thousands of map pins instantly via WebGL-powered **PyDeck** visualization charts.

---

## Tech Stack

- **Core Language:** Python 3.10+
- **Geospatial Processing:** Geopandas, Shapely, PyProj
- **Web Scraping / Automation:** Playwright, BeautifulSoup4
- **Database / Storage:** PostgreSQL (Supabase Client, SQLAlchemy)
- **Frontend & Mapping:** Streamlit, PyDeck (WebGL Rendering)
- **Orchestration / Infrastructure:** Modal Serverless Cloud, Auto-scaling Parallel Workers

---

## Features

- [x] **Zero-API Map Scraper:** Complete web automation that extracts Name, Latitude, Longitude, Rating, Review Count, Phone Number, and Email Address.
- [x] **Dynamic Spatial Indexing:** Quadtree-inspired coordinate subdivision that automatically zooms closer into ultra-dense metropolitan zones (e.g., Alsancak, Beşiktaş Çarşı) to extract hidden elements.
- [x] **Concurrency & Race Condition Safety:** Uses relational locking and transactional states (`Pending`, `Processing`, `Completed`) so multiple VM workers can scrape the same map boundary without duplication.
- [x] **Interactive Dashboard:** Live text filtering by venue name, real-time metric sliders for minimum reviews/ratings, and smooth high-density mapping.

---

## 🚀 Getting Started

### 1. Prerequisites & Installation
Clone the repository and install the required dependencies:

```bash
git clone [https://github.com/faranji/geo-spatial-scraper.git](https://github.com/faranji/geo-spatial-scraper.git)
cd geo-spatial-scraper
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration
Create a `config.py` file in the root directory to store your environment variables safely:

```python
# config.py
SUPABASE_URL = "[https://your-project-id.supabase.co](https://your-project-id.supabase.co)"
SUPABASE_KEY = "your-anon-or-service-role-key"
DATABASE_URL = "postgresql://postgres:password@db-address:5432/postgres"
```

### 3. Execution Pipeline

**Step A: Generate the Spatial Grids**
Process the GeoJSON map boundaries and populate the PostgreSQL coordinates pool:
```bash
python src/grid_generator.py --region izmir
```

**Step B: Spin up the VM Scraper Fleet**
Run the worker script on your distributed machines. Workers will automatically fetch unassigned grid units from the centralized pool:
```bash
python src/playwright_scraper.py
```

**Step C: Launch the Visual Dashboard**
Boot up the user interface locally or host it on platforms like Hugging Face Spaces:
```bash
streamlit run app/dashboard.py
```

---

## 📊 Database Schema Details

The central PostgreSQL database maintains the following structures for integrity:

- **`spatial_grids` Table:** Tracks `grid_id`, `centroid_lat`, `centroid_lon`, `status` (Pending/Processing/Completed), and `worker_id`.
- **`venues` Table:** Stores the ultimate output: `id` (UUID), `name`, `latitude`, `longitude`, `rating`, `review_count`, `phone`, `email`, and `scraped_at`.

---
