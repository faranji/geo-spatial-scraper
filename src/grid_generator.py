import json
import os
from shapely.geometry import shape, Polygon, box
from database_manager import DatabaseManager

def load_city_polygon(geojson_path: str):
    """
    GÖREV 1: GeoJSON dosyasını okuyup, içindeki koordinatları 
    Shapely kütüphanesinin anlayacağı bir 'Polygon' objesine dönüştürür.
    """
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f) #json.load() metni okur ve dictionary'e çevirir.
    
    geometry_data = data["features"][0]["geometry"] 
    polygon = shape(geometry_data) # mesela load_city_polygon("data/istanbul_europe.geojson").bounds poligonun sınırlarını verir.
                                # bounds birleşince kocaman bir dikdörtgen olur.
    return polygon

def subdivide_quadtree(city_polygon, min_lon, min_lat, max_lon, max_lat, valid_grids):
    """
    GÖREV 2: Kendi kendini çağıran (Recursive) Quadtree Algoritması. 1x1 Boyutuna ulaşana kadar böleriz.
    """
    # İPUCU 1: Gelen 4 koordinat (min_lon, min_lat, max_lon, max_lat) ile 
    # shapely kütüphanesinden 'box()' kullanarak 'current_box' objesi oluştur.
    current_box = box(min_lon, min_lat, max_lon, max_lat)

    # İPUCU 2: FİLTRELEME (Base Case 1 - Kesişim Kontrolü)
    # Eğer bu 'current_box', 'city_polygon' ile KESİŞMİYORSA (intersects),
    # bu kare tamamen denizde veya alan dışındadır. Hiçbir listeye eklemeden
    # doğrudan 'return' yazıp işlemi sonlandır.

    if not current_box.intersects(city_polygon):
        return
    
    # İPUCU 3: BOYUT KONTROLÜ (Base Case 2 - Yeterince Küçük Mü?)
    # Karenin fiziksel genişliğini (max_lon - min_lon) ve 
    # yüksekliğini (max_lat - min_lat) hesapla.
    # Eğer genişlik <= 0.011 VE yükseklik <= 0.009 ise:
    # Hedef 1x1 km boyutuna ulaştık demektir! 'valid_grids.append(current_box)'
    # ile listeye ekle ve 'return' ile çık.
    if (max_lon - min_lon <= 0.011) and (max_lat - min_lat <= 0.009) :
        valid_grids.append(current_box)
        return
    
    # İPUCU 4: BÖLME (Divide)
    # Kutu şehirle kesişiyor ama hala 1 km'den büyük. Onu 4'e bölmeliyiz.
    # Tam merkez noktasını bulmak için 'mid_lon' ve 'mid_lat' değerlerini hesapla.
    mid_lon = (max_lon + min_lon)/2
    mid_lat = (max_lat + min_lat)/2

    ## İPUCU 5: 4 Çeyrek için kendini tekrar çağır!
    
    # 1. SOL ALT Çeyrek (Batı - Güney)
    # Başlangıç: min_lon, min_lat -> Bitiş: mid_lon, mid_lat
    subdivide_quadtree(city_polygon, min_lon, min_lat, mid_lon, mid_lat, valid_grids)
    
    # 2. SAĞ ALT Çeyrek (Doğu - Güney)
    # Başlangıç: mid_lon, min_lat -> Bitiş: max_lon, mid_lat
    subdivide_quadtree(city_polygon, mid_lon, min_lat, max_lon, mid_lat, valid_grids)
    
    # 3. SOL ÜST Çeyrek (Batı - Kuzey)
    # Başlangıç: min_lon, mid_lat -> Bitiş: mid_lon, max_lat
    subdivide_quadtree(city_polygon, min_lon, mid_lat, mid_lon, max_lat, valid_grids)
    
    # 4. SAĞ ÜST Çeyrek (Doğu - Kuzey)
    # Başlangıç: mid_lon, mid_lat -> Bitiş: max_lon, max_lat
    subdivide_quadtree(city_polygon, mid_lon, mid_lat, max_lon, max_lat, valid_grids)

    pass


def generate_grids(city_name: str, polygon):
    """
    GÖREV 3: Quadtree sürecini başlatan ana fonksiyon.
    """
    # İPUCU 1: Kareleri toplayacağımız boş bir 'valid_grids = []' listesi oluştur.
    valid_grids = []
    # İPUCU 2: 'polygon.bounds' üzerinden en dış çerçevenin 4 sınır noktasını al.
    min_lon, min_lat, max_lon, max_lat = polygon.bounds()
    # İPUCU 3: Motoru ilk kez ateşlemek için 'subdivide_quadtree()' fonksiyonunu çağır.
    # İçine ana poligonu, en dış sınırları ve boş listeyi gönder.
    subdivide_quadtree(polygon, min_lon, min_lat, max_lon, max_lat, valid_grids)
    # İPUCU 4: Fonksiyon işini bitirdiğinde dolmuş olan 'valid_grids' listesini return et.
    return valid_grids
    pass

def save_grids_to_supabase(city_name: str, grids: list):
    """
    GÖREV 4: Oluşan temiz kareleri veritabanına kaydeder.
    """
    # 1. Sınıfı çağırmak (Veritabanı yöneticisi objesi oluşturmak)
    db = DatabaseManager()
    
    # 2. Elimizdeki her bir kareyi (Polygon) tek tek dön
    for index, poly in enumerate(grids):
        # Poligonun sınır noktalarını al
        min_lon, min_lat, max_lon, max_lat = poly.bounds
        
        # 3. Veritabanı tablomuz (SpatialGrid) için yeni bir satır verisi oluştur
        new_grid = SpatialGrid(
            id=f"{city_name}_grid_{index + 1}",  # Örn: istanbul_europe_grid_1
            city=city_name,                      # Örn: istanbul_europe
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            status="Pending"  # Botların taraması için sıraya alıyoruz
        )
        
        # 4. Oluşturduğumuz bu satırı veritabanı oturumuna (session) ekle
        # (Eğer DatabaseManager içinde oturum adı farklıysa (örn: db.session), ona göre düzeltmelisin)
        db.db.add(new_grid)  
    
    # 5. Tüm eklenen verileri tek seferde kalıcı olarak kaydet (Commit)
    db.db.commit()

    pass

if __name__ == "__main__":
    
    target_cities = ["istanbul_europe", "izmir"]
    for city_name in target_cities:

        geojson_path = f"data/{city_name}.geojson"

        # 1. Poligonu Yükle
        poly = load_city_polygon(geojson_path)
    
        # 2. Quadtree ile karelere böl
        grids = generate_grids(city_name, poly)
    
        # 3. Veritabanına kaydet
        save_grids_to_supabase(city_name, grids)


