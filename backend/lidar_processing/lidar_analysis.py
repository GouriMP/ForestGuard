import laspy
import numpy as np
import rasterio
from rasterio.transform import from_origin
import json
import os

# Configuration
LIDAR_FILE = r"C:\Users\wonde\OneDrive\Desktop\ForestGuard-1\USGS_LPC_WI_AshlandIronFlorence_2019_D19_04950147.copc.laz"  # Change to actual upload path
POWERLINE_HEIGHT = 10  # Example: Stable powerline height (meters)
HIGH_RISK_OUTPUT = "../high_risk/high_risk_locations.json"

# Load LiDAR Data
def load_lidar(file_path):
    las = laspy.read(file_path, laz_backend=laspy.LazBackend.Lazrs)
    return las.x, las.y, las.z, las.classification, las.return_number

# Generate Canopy Height Model (CHM)
def generate_chm(x, y, z, classification, return_number, resolution=1):
    ground_mask = classification == 2  # Ground points
    ground_x, ground_y, ground_z = x[ground_mask], y[ground_mask], z[ground_mask]

    first_return_mask = return_number == 1  # First returns (surface)
    first_x, first_y, first_z = x[first_return_mask], y[first_return_mask], z[first_return_mask]

    xmin, ymin, xmax, ymax = min(x), min(y), max(x), max(y)
    grid_x = np.arange(xmin, xmax, resolution)
    grid_y = np.arange(ymin, ymax, resolution)

    dtm_grid = np.full((len(grid_y), len(grid_x)), np.nan)
    dsm_grid = np.full((len(grid_y), len(grid_x)), np.nan)

    for i in range(len(ground_x)):
        # Ensure row and col indices are within valid bounds
        row = min(max(int((ground_y[i] - ymin) / resolution), 0), dtm_grid.shape[0] - 1)
        col = min(max(int((ground_x[i] - xmin) / resolution), 0), dtm_grid.shape[1] - 1)

        if 0 <= row < dtm_grid.shape[0] and 0 <= col < dtm_grid.shape[1]:  # Ensure valid index
            if np.isnan(dtm_grid[row, col]) or ground_z[i] < dtm_grid[row, col]:
                dtm_grid[row, col] = ground_z[i]



    for i in range(len(first_x)):
        # Ensure row and col indices are within valid bounds
        row = min(max(int((first_y[i] - ymin) / resolution), 0), dsm_grid.shape[0] - 1)
        col = min(max(int((first_x[i] - xmin) / resolution), 0), dsm_grid.shape[1] - 1)

        if 0 <= row < dsm_grid.shape[0] and 0 <= col < dsm_grid.shape[1]:  # Ensure valid index
            if np.isnan(dsm_grid[row, col]) or first_z[i] > dsm_grid[row, col]:
                dsm_grid[row, col] = first_z[i] 


    chm_grid = dsm_grid - dtm_grid
    chm_grid[np.isnan(chm_grid)] = 0
    return chm_grid, xmin, ymax, resolution

# Identify High-Risk Trees
def find_high_risk_trees(chm_grid, xmin, ymax, resolution, threshold=POWERLINE_HEIGHT):
    high_risk_coords = []
    rows, cols = chm_grid.shape
    for row in range(rows):
        for col in range(cols):
            if chm_grid[row, col] > threshold:
                lat = ymax - row * resolution
                lon = xmin + col * resolution
                high_risk_coords.append({"lat": lat, "lon": lon, "height": chm_grid[row, col]})
    return high_risk_coords

# Save High-Risk Locations
def save_high_risk_locations(locations, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(locations, f, indent=4)

# Main Execution
if __name__ == "__main__":
    print("🔄 Processing LiDAR data...")
    x, y, z, classification, return_number = load_lidar(LIDAR_FILE)
    chm_grid, xmin, ymax, resolution = generate_chm(x, y, z, classification, return_number)
    high_risk_trees = find_high_risk_trees(chm_grid, xmin, ymax, resolution)
    save_high_risk_locations(high_risk_trees, HIGH_RISK_OUTPUT)
    print(f"✅ High-risk locations saved in {HIGH_RISK_OUTPUT}")
