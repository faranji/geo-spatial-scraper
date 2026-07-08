# Geo-Spatial Distributed Scraper & Interactive Visualization Dashboard

[![Live Application](https://img.shields.io/badge/Live-Streamlit_Dashboard-FF4B4B?style=for-the-badge&logo=streamlit)](https://geo-spatial-scraper-ed5nufscmb4ghgkiqyvuml.streamlit.app/)

![Dashboard Preview](assets/dashboard.png)

A high-performance, distributed data engineering and geospatial analysis pipeline designed to extract, store, and visualize every cafe and restaurant across **Istanbul (European Side)** and **Izmir** without relying on expensive official APIs.

The core mission of this project is to achieve **100% coverage**—ensuring that even the most obscure, hidden local spots are successfully mapped. By leveraging a dynamic **QuadTree spatial grid algorithm** and exact coordinate extraction, the system bypasses standard keyword search limits and maps venues to their literal street coordinates.

## Architecture & Data Flow

The system is built on a modular, distributed architecture designed to run on scalable infrastructure while preventing IP rate-limiting.

* **Dynamic Spatial Partitioning (QuadTree Algorithm):** Uses `geopandas` and `shapely` to load official GeoJSON boundaries. If a grid contains too many venues (hitting the API rendering limit of ~120), the algorithm dynamically subdivides the bounding box into 4 smaller quadrants, zooming closer to extract every hidden element in ultra-dense zones.
* **Distributed Scraping Engine:** An asynchronous `Playwright` browser automation framework orchestrated via **Modal Serverless Cloud**. Workers pull "Pending" grid coordinates from the queue dynamically. 
* **Exact Coordinate Extraction:** Instead of defaulting to grid centroids, the engine utilizes Regex to parse encrypted Google Maps URLs within the DOM, extracting the exact latitude and longitude (`!3d... !4d...`) for absolute precision.
* **Residential Proxy Network:** Integrated with **Webshare Proxies** to rotate IPs, masking the automated traffic as organic residential users to completely bypass bot-detection algorithms and rate limits.
* **Centralized Storage:** A multi-worker transactional pipeline streaming scraped data into a remote **PostgreSQL (Supabase)** instance utilizing connection pooling and transactional states (Pending, Processing, Subdivided, Completed) to prevent race conditions.
* **Analytics & Frontend Panel:** A high-performance dashboard built with `Streamlit` that queries the database in real-time, rendering thousands of custom mapping pins instantly via WebGL-powered `PyDeck` (IconLayer) visualization.

## Tech Stack

* **Core Language:** Python 3.10+
* **Geospatial Processing:** Geopandas, Shapely, PyProj
* **Web Scraping / Automation:** Playwright, BeautifulSoup4, Regex
* **Database / Storage:** PostgreSQL (Supabase Client, SQLAlchemy)
* **Frontend & Mapping:** Streamlit, PyDeck (WebGL IconLayer Rendering)
* **Orchestration & Infrastructure:** Modal Serverless Cloud, Webshare Proxies

## 🚀 Getting Started

### 1. Prerequisites & Installation

Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/faranji/geo-spatial-scraper.git](https://github.com/faranji/geo-spatial-scraper.git)
cd geo-spatial-scraper
pip install -r requirements.txt
playwright install chromium
```

### 2. Database Configuration
```bash
SUPABASE_URL = "[https://your-project-id.supabase.co](https://your-project-id.supabase.co)"
SUPABASE_KEY = "your-anon-or-service-role-key"
DATABASE_URL = "postgresql://postgres:password@db-address:5432/postgres"

Scraping Settings
MAX_CONCURRENT_TASKS = 4  # Adjust based on your cloud infrastructure capacity

Proxy Configuration (Residential Proxies recommended for production)
Example: "http://username:password@proxy-address:port"
WEBSHARE_PROXY = "your_webshare_proxy_string"
```

### 3. Execution Pipeline
The project follows a three-stage automated pipeline to ensure data consistency and full coverage.

Step A: Generate the Spatial Grids
Before scraping, we process the target region boundaries (GeoJSON) and populate the database with a pool of grid coordinates. This prepares the "task list" for our workers:

```bash
python src/grid_generator.py --region izmir
```
* You can switch between --region istanbul or --region izmir

Step B: Spin up the Modal Scraper Fleet
Launch the distributed scraper. Workers will automatically fetch "Pending" grid units, apply the rotating proxy network to bypass restrictions, and run the QuadTree subdivision logic autonomously:

```bash
modal deploy src/scraper_bot.py
```
* Note: The workers will continue running until all grid units are marked as "Completed".

Step C: Launch the Visual Dashboard
Once data starts flowing, launch the real-time analytics dashboard to filter, analyze, and visualize the findings:

```bash
streamlit run app/dashboard.py
```