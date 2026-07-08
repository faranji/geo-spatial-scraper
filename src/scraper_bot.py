import modal
import time
import re
import random
from bs4 import BeautifulSoup
import uuid
from playwright.sync_api import sync_playwright
from database_manager import DatabaseManager, SpatialGrid, Venue
import config


image = (
    modal.Image.debian_slim()
    .pip_install(
        "playwright",
        "shapely",
        "sqlalchemy",
        "psycopg2-binary",
        "beautifulsoup4"
    )
    .run_commands("playwright install --with-deps chromium")
    .workdir("/root/app")
    .env({"PYTHONPATH": "/root/app:/root/app/src"})
    .add_local_dir(".", remote_path="/root/app", ignore=["__pycache__", ".git"]) 
)

app = modal.App("geo-spatial-scraper")

# --- functions ---

def get_pending_grid(db_session, worker_name: str):
    grid = db_session.query(SpatialGrid).filter(SpatialGrid.status == "Pending").first()

    if grid == None:
        print("Scanning is over.")
        return None

    if grid:
        grid.status = "Processing"
        grid.worker_id = worker_name

    db_session.commit()
    return grid


def scrape_google_maps(grid, keyword: str):
    venues_data = []
    seen_venues = set()

    # selected_proxy = random.choice(config.PROXY_LIST)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            # proxy = selected_proxy
        ) 
        page = browser.new_page()
        
        center_lat = (grid.min_lat + grid.max_lat) / 2
        center_lon = (grid.min_lon + grid.max_lon) / 2

        url = f"https://www.google.com/maps/search/{keyword}/@{center_lat},{center_lon},15z?gl=tr"
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"couldn't load the page, error code: {e}")
            browser.close()
            return None
        
        try:
            page.locator('div[role="feed"]').hover()
        except:
            pass

        try:
            page.wait_for_selector('div[role="article"]', timeout=15000)
        except Exception as e:
            print(f"couldn't load the cards: {e}")
            browser.close()
            return None

        try:  
            for _ in range(10):
                page.mouse.wheel(0, 1000)
                time.sleep(random.uniform(1.5, 3.5))
            
            html_stuff = page.content()
            browser.close()
        
        except Exception as e:
            print(f"error code: {e}")
            try:
                browser.close() 
            except:
                pass
            return None 
        
    # === beautiful soup ===
    soup = BeautifulSoup(html_stuff, "html.parser")
    venue_cards = soup.find_all("div", role="article")
    
    for card in venue_cards:
        try:
            name_tag = card.find("div", class_="qBF1Pd") or card.find("h1")
            venue_name = name_tag.text.strip() if name_tag else "Unknown Venue"

            if venue_name in seen_venues or venue_name == "Unknown Venue":
                continue
            
            rating = 0.0
            rating_span = card.select_one('span.ZkP5Je[aria-label]')
            if rating_span:
                rating_match = re.search(r"(\d+[.,]\d+)", rating_span["aria-label"])
                if rating_match:
                    rating = float(rating_match.group(1).replace(",", "."))

            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag['href']
                coord_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
                if coord_match:
                    exact_lat = float(coord_match.group(1))
                    exact_lng = float(coord_match.group(2))
            
                    unique_key = f"{venue_name}_{exact_lat}_{exact_lng}"

                    if unique_key in seen_venues:
                        continue
                    seen_venues.add(unique_key)

                    venue_dict = {
                        "id": f"place_{uuid.uuid4().hex[:12]}",
                        "name": venue_name,
                        "lat": exact_lat,
                        "lng": exact_lng,
                        "rating": rating,
                        "review_count": None, 
                        "category": keyword,
                        "address": ""
                    }
                    venues_data.append(venue_dict)
                else:
                    continue
            else:
                continue
        except Exception as e:
            continue
    return venues_data

def save_venues_and_complete(db_session, grid, venues_data):
    lat_diff = grid.max_lat - grid.min_lat
    if len(venues_data) >= 120 and lat_diff > 0.0015:
        print(f"limit exceeded ({len(venues_data)} venues). {grid.id} dividing to 4")
        
        mid_lat = (grid.min_lat + grid.max_lat) / 2.0
        mid_lon = (grid.min_lon + grid.max_lon) / 2.0

        tl_grid = SpatialGrid(id=str(uuid.uuid4()), min_lat=mid_lat, max_lat=grid.max_lat, min_lon=grid.min_lon, max_lon=mid_lon, status="Pending")
        tr_grid = SpatialGrid(id=str(uuid.uuid4()),min_lat=mid_lat, max_lat=grid.max_lat, min_lon=mid_lon, max_lon=grid.max_lon, status="Pending")
        bl_grid = SpatialGrid(id=str(uuid.uuid4()),min_lat=grid.min_lat, max_lat=mid_lat, min_lon=grid.min_lon, max_lon=mid_lon, status="Pending")
        br_grid = SpatialGrid(id=str(uuid.uuid4()),min_lat=grid.min_lat, max_lat=mid_lat, min_lon=mid_lon, max_lon=grid.max_lon, status="Pending")

        db_session.add_all([tl_grid, tr_grid, bl_grid, br_grid])
        grid.status = "Subdivided"
        db_session.commit()
        return

    # EĞER LİMİTE ULAŞILMADIYSA (Normal Kayıt İşlemi)
    for place in venues_data:
        new_venue = Venue(
            id=place["id"],
            name=place["name"],
            latitude=place["lat"],
            longitude=place["lng"],
            rating=place["rating"],
            review_count=place.get("review_count"), # KeyError almamak için .get() kullanmak daha güvenlidir
            category=place["category"],
            address=place["address"]
        )
        db_session.add(new_venue)

    grid.status = "Completed"
    db_session.commit()

# --- 3. ANA DÖNGÜ ---

@app.function(image=image, secrets=[modal.Secret.from_name("supabase-secret")], timeout=28800, memory=2048) # RAM for each worker!
def run_worker():
    unique_id = uuid.uuid4().hex[:8]
    worker_name = f"Modal_Worker_{unique_id}"
    
    print(f"{worker_name} started its duty!")
    
    target_keywords = ["cafe", "restaurant"]
    
    db = DatabaseManager()
    while True:
        grid = get_pending_grid(db.db, worker_name=worker_name)
        if not grid:
            print(f"Scanning over. {worker_name} accomplished its duty.")
            break
        
        all_venues_for_this_grid = []
        grid_failed = False
        
        for kw in target_keywords:
            print(f"Searching region {grid.id} for more '{kw}'...")
            data = scrape_google_maps(grid, keyword=kw)
            
            if data is None:
                print(f"CAUTION: {grid.id} had an error, it will be pending again.")
                
                grid.status = "Pending"  
                grid.worker_id = None   
                
                db.db.commit()
                grid_failed = True
                break
                
            all_venues_for_this_grid.extend(data) 
        
        if not grid_failed:
            save_venues_and_complete(db.db, grid, all_venues_for_this_grid)


@app.local_entrypoint()
def main():
    import config 
    worker_count = config.MAX_CONCURRENT_TASKS 
    
    print(f"CAUTION: {worker_count} worker is ready.")
    
    active_tasks = []
    
    for i in range(worker_count):
        task = run_worker.spawn()
        active_tasks.append(task)
        
    for task in active_tasks:
        task.get()
        
    print("All workers completed their tasks!")
