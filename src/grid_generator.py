import json
import os
from shapely.geometry import shape, Polygon
from database_manager import DatabaseManager

def load_city_polygon(geojson_path: str):
    """
    GÖREV 1: GeoJSON dosyasını okuyup, içindeki koordinatları 
    Shapely kütüphanesinin anlayacağı bir 'Polygon' objesine dönüştürür.
    """
    # İPUCU: Önce open() ile json dosyasını yükle.
    # Sonra 'shape(data["features"][0]["geometry"])' kullanarak poligon objesini return et.
    pass

def generate_grids(city_name: str, polygon):
    """
    GÖREV 2 & 3: Poligonun sınırlarını (bounds) bulur.
    Sol alttan sağ üste doğru 0.009 ve 0.011 adımlarla döngü kurar.
    Her kareyi shapely objesi yapıp şehir poligonuyla kesişiyor mu (intersects) diye bakar.
    Kesişen kareleri bir liste olarak toplar.
    """
    min_lon, min_lat, max_lon, max_lat = polygon.bounds
    
    # Adım büyüklükleri (1 km için derece karşılıkları)
    lat_step = 0.009
    lon_step = 0.011
    
    valid_grids = []
    grid_counter = 1

    # İPUCU: Burada iç içe iki döngü kurmalısın.
    # lat = min_lat durumundan başlayıp max_lat olana kadar lat_step kadar artmalı.
    # lon = min_lon durumundan başlayıp max_lon olana kadar lon_step kadar artmalı.
    # Her adımda bir kare (Polygon) tanımlayıp 'polygon.intersects(kare)' kontrolü yapmalısın.

    return valid_grids

def save_grids_to_supabase(grids):
    """
    GÖREV 4: Oluşan temiz kareleri veritabanına kaydeder.
    """
    # İPUCU: DatabaseManager sınıfından bir instance oluşturup, 
    # gelen kareleri session.add() ile veritabanına basacağız.
    pass

if __name__ == "__main__":
    # Test etmek için burayı kullanacağız
    print("Grid Generator starting.")
    # geojson_path = "data/istanbul_europe.geojson"
    # poly = load_city_polygon(geojson_path)
    # grids = generate_grids("istanbul", poly)