import modal
import time
import re
import random
from bs4 import BeautifulSoup # SOUP BURAYA GELDİ
import uuid
from playwright.sync_api import sync_playwright
from database_manager import DatabaseManager, SpatialGrid, Venue

# --- 1. MODAL BULUT KURULUMU ---
image = modal.Image.debian_slim().pip_install(
    "playwright",
    "shapely",
    "sqlalchemy",
    "psycopg2-binary",
    "beautifulsoup4"  # SOUP MODAL'A EKLENDİ
).run_commands("playwright install --with-deps chromium")

app = modal.App("geo-spatial-scraper")


# --- 2. FONKSİYONLARIN (Aynen Kalıyor) ---

def get_pending_grid(db_session, worker_name: str):
    """
    GÖREV 1: Veritabanından 'Pending' olan ilk kareyi bul ve sahiplen.
    """
    # İPUCU 1: SQLAlchemy ile SpatialGrid tablosundan status'ü "Pending" olan 
    # ilk kaydı (.first()) getir.
    # Örnek: grid = db_session.query(SpatialGrid).filter(...).first()
    grid = db_session.query(SpatialGrid).filter(SpatialGrid.status == "Pending").first()

    # İPUCU 2: Eğer grid bulunamazsa (yani dönecek değer None ise) 
    # doğrudan None döndür (return None). Bu, taramanın bittiği anlamına gelir.
    if grid == None:
        return None
        print("scanning is over.")

    # İPUCU 3: Grid bulunduysa! Başka botların bunu almaması için:
    # grid.status değerini "Processing" yap.
    # grid.worker_id değerini fonksiyon parametresi olan worker_name yap.
    if grid:
        SpatialGrid.status == "Processing"
        SpatialGrid.worker_id == worker_name

    # İPUCU 4: Değişiklikleri veritabanına kalıcı olarak kaydetmek için
    # db_session.commit() yapmayı unutma.
    db_session.commit()

    # İPUCU 5: Üzerine aldığın bu 'grid' objesini return et.
    return grid
    pass

def scrape_google_maps(grid, keyword: str):
    """
    GÖREV 2: Playwright ile sayfayı yükler, Beautiful Soup ile verileri ışık hızında ayıklar.
    """
    venues_data = []
    
    # === AŞAMA 1: PLAYWRIGHT İLE HAMALLIK (Sayfa Yükleme) ===
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        center_lat = (grid.min_lat + grid.max_lat) / 2
        center_lon = (grid.min_lon + grid.max_lon) / 2

        url = f"https://www.google.com/maps/search/{keyword}/@{center_lat},{center_lon},15z"
        page.goto(url)
        
        page.wait_for_load_state("networkidle")
        
        try:
            page.locator('div[role="feed"]').hover()
        except:
            print("Sol panel bulunamadı, ana sayfada kaydırma denenecek.")
            
        # 5 kez aşağı kaydırarak yeni mekanları yüklet
        for _ in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(random.uniform(1.5, 3.5))
            
        # KRİTİK NOKTA: Sayfanın o anki tüm HTML kodunu bir değişkene kopyalıyoruz
        html_stuff = page.content()
        
        # HTML'i aldık, tarayıcıyla işimiz bitti. Hemen kapatıp RAM'i boşaltıyoruz!
        browser.close()
        
    # Elimizdeki HTML metnini Soup objesine dönüştürüyoruz
    soup = BeautifulSoup(html_stuff, "html.parser")
    
    # Tüm mekan kartlarını div etiketinden ve role="article" niteliğinden buluyoruz
    venue_cards = soup.find_all("div", role="article")
    
    for card in venue_cards:
        try:
            # 1. Name Extraction (İsim Çıkarma)
            name_tag = card.find("h1") or card.find("div", class_="fontHeadlineSmall")
            venue_name = name_tag.text.strip() if name_tag else "Unknown Venue"
            
            # 2. Rating & Review Extraction (Puan ve Yorum Çıkarma)
            aria_label_text = card.get("aria-label", "") 
            
            # Başlangıçta varsayılan değerleri atıyoruz
            rating = 0.0
            review_count = 0
            
            # Puanı bulmak için Regex: İçinde rakam, nokta/virgül ve tekrar rakam olan yapıyı arar (Örn: 4.5 veya 4,5)
            rating_match = re.search(r"(\d+[.,]\d+)", aria_label_text)
            if rating_match:
                # "4,5" gibi Türkçe formatlı gelirse diye virgülü noktaya çevirip float yapıyoruz
                rating = float(rating_match.group(1).replace(",", "."))
                
            # Yorum sayısını bulmak için Regex: "1.234 yorum" veya "120 reviews" formatını yakalar
            review_match = re.search(r"([\d.,]+)\s*(?:yorum|review)", aria_label_text.lower())
            if review_match:
                # "1.234" veya "1,234" gibi binlik ayraçları temizleyip tam sayıya (int) çeviriyoruz
                clean_review_text = re.sub(r"[.,]", "", review_match.group(1))
                review_count = int(clean_review_text)
            
            # 3. Dictionary Creation (Sözlük Oluşturma)
            venue_dict = {
                "id": f"place_{random.randint(10000, 99999)}",
                "name": venue_name,
                "lat": center_lat,
                "lng": center_lon,
                "rating": rating,
                "review_count": review_count,
                "category": keyword,
                "address": "Unknown"
            }
            
            venues_data.append(venue_dict)
            
        except Exception as e:
            # Bir mekanda HTML yapısı bozuksa çökmesin, sonrakine geçsin
            continue
            
    return venues_data

def save_venues_and_complete(db_session, grid, venues_data):
    """
    GÖREV 3: Kazınan mekanları kaydeder ve kareyi 'Completed' olarak işaretler.
    """
    # İPUCU 1: venues_data listesinde bir 'for' döngüsü kur. Döngüdeki her bir mekan için 'Venue' tablosu formatında yeni bir obje oluştur.
    for place in venues_data:
        new_venue = Venue(
            id=place["id"],
            name=place["name"],
            latitude=place["lat"],
            longitude=place["lng"],
            rating=place["rating"],
            review_count=place["reviews"],
            category=place["category"],
            address=place["address"],
            grid_id=grid.id  # ÇOK KRİTİK: Bu mekanın hangi kareye ait olduğunu bağlamak için veritabanındaki grid id'sini veriyoruz
        )
        
        # İPUCU 2: Her bir mekanı döngünün İÇİNDE sepete ekle
        db_session.add(new_venue)

    # İPUCU 3: Olay bittiğine göre 'grid' objesinin status değerini "Completed" yap.
    grid.status = "Completed"

    # İPUCU 4: Sepetteki mekanları ve grid'in yeni durumunu tek seferde 
    # Supabase'e yazmak için db_session.commit() komutunu çalıştır.
    db_session.commit()
    pass

# --- 3. ANA DÖNGÜ (Artık Modal Tarafından Yönetiliyor) ---

@app.function(image=image, secrets=[modal.Secret.from_name("supabase-secret")])
def run_worker():
    """
    ANA DÖNGÜ: Bulutta bağımsız bir konteyner olarak uyanır.
    """
    # Her ayağa kalkan konteyner için benzersiz 8 haneli kısa bir ID üretiyoruz
    unique_id = uuid.uuid4().hex[:8]
    worker_name = f"Modal_Worker_{unique_id}"
    
    print(f"🛰️ Bulut üzerinde {worker_name} başarıyla başlatıldı!")
    
    db = DatabaseManager()
    while True:
        # Artık veritabanına o an çalışan gerçek botun adını kaydediyoruz!
        grid = get_pending_grid(db.db, worker_name=worker_name)
        if not grid:
            print(f" Tarama bitti. {worker_name} görevini tamamladı ve kapanıyor.")
            break
        
        data = scrape_google_maps(grid)
        save_venues_and_complete(db.db, grid, data)