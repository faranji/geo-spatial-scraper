""" Processes raw city GeoJSON files and subdivides them into coordinate grids. """
import argparse

class GridGenerator:
    def __init__(self, geojson_path: str):
        self.geojson_path = geojson_path

    def generate_mesh(self, grid_size_km: float):
        """ Cuts the GeoJSON polygon into a grid mesh of bounding boxes. """
        pass

    def push_grids_to_db(self):
        """ Saves generated coordinates into 'spatial_grids' table as 'Pending'. """
        pass

if __name__ == "__main__":
    # Command line arguments to run: python src/grid_generator.py --region izmir
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True, help="Target region: izmir or istanbul")
    args = parser.parse_args()
    print(f"Initializing grid generation for: {args.region}")