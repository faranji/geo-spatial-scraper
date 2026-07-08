import json
import os
from shapely.geometry import shape, Polygon, box
from database_manager import DatabaseManager, SpatialGrid

def load_city_polygon(geojson_path: str):
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f) #json.load() metni okur ve dictionary'e çevirir.
    
    geometry_data = data["features"][0]["geometry"] 
    polygon = shape(geometry_data) # mesela load_city_polygon("data/istanbul_europe.geojson").bounds poligonun sınırlarını verir.
                                # bounds birleşince kocaman bir dikdörtgen olur.
    return polygon

def subdivide_quadtree(city_polygon, min_lon, min_lat, max_lon, max_lat, valid_grids):
    current_box = box(min_lon, min_lat, max_lon, max_lat)

    if not current_box.intersects(city_polygon):
        return
    
    if (max_lon - min_lon <= 0.011) and (max_lat - min_lat <= 0.009) :
        valid_grids.append(current_box)
        return
    
    mid_lon = (max_lon + min_lon)/2
    mid_lat = (max_lat + min_lat)/2

    subdivide_quadtree(city_polygon, min_lon, min_lat, mid_lon, mid_lat, valid_grids)
    subdivide_quadtree(city_polygon, mid_lon, min_lat, max_lon, mid_lat, valid_grids)
    subdivide_quadtree(city_polygon, min_lon, mid_lat, mid_lon, max_lat, valid_grids)
    subdivide_quadtree(city_polygon, mid_lon, mid_lat, max_lon, max_lat, valid_grids)

    pass


def generate_grids(city_name: str, polygon):
    valid_grids = []

    min_lon, min_lat, max_lon, max_lat = polygon.bounds
    subdivide_quadtree(polygon, min_lon, min_lat, max_lon, max_lat, valid_grids)
    return valid_grids
    pass

def save_grids_to_supabase(city_name: str, grids: list):
    # call the class
    simos = DatabaseManager()
    
    # return every square we have as a polygon
    for index, poly in enumerate(grids):
        min_lon, min_lat, max_lon, max_lat = poly.bounds
        
        # new row for our db table
        new_grid = SpatialGrid(
            id=f"{city_name}_grid_{index + 1}",  # Örn: istanbul_europe_grid_1
            city=city_name,                      # Örn: istanbul_europe
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            status="Pending" 
        )
        
        simos.db.add(new_grid)  
    simos.db.commit()

    pass

if __name__ == "__main__":
    
    target_cities = ["istanbul_europe", "izmir"]
    for city_name in target_cities:

        geojson_path = f"data/{city_name}.geojson"

        poly = load_city_polygon(geojson_path)
        grids = generate_grids(city_name, poly)
        save_grids_to_supabase(city_name, grids)


