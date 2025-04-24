# from flask import Flask, request, jsonify
# import os
# import laspy
# import numpy as np
# import rasterio
# from rasterio.transform import from_origin
# import matplotlib.pyplot as plt
# from flask_cors import CORS
# app = Flask(__name__)

# CORS(app)


# # Define paths
# POINT_CLOUD_DIR = "point-cloud"
# OUTPUT_DIR = "output"
# os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure output directory exists

# @app.route('/generate-chm', methods=['POST'])
# def generate_chm():
#     """Process .laz files to generate Canopy Height Model (CHM)."""
#     try:
#         laz_files = [f for f in os.listdir(POINT_CLOUD_DIR) if f.endswith('.laz')]
        
#         if not laz_files:
#             return jsonify({"error": "No .laz files found in point-cloud directory"}), 400

#         file_path = os.path.join(POINT_CLOUD_DIR, laz_files[0])  # Process the first found .laz file

#         # Load LiDAR Data
#         las = laspy.read(file_path, laz_backend=laspy.LazBackend.Lazrs)
#         x, y, z = las.x, las.y, las.z
#         classification = las.classification

#         # Create Digital Terrain Model (DTM)
#         ground_mask = classification == 2
#         ground_x, ground_y, ground_z = x[ground_mask], y[ground_mask], z[ground_mask]

#         resolution = 1
#         xmin, ymin, xmax, ymax = min(x), min(y), max(x), max(y)
#         grid_x = np.arange(xmin, xmax, resolution)
#         grid_y = np.arange(ymin, ymax, resolution)
#         dtm_grid = np.full((len(grid_y), len(grid_x)), np.nan)

#         for i in range(len(ground_x)):
#             col = int((ground_x[i] - xmin) / resolution)
#             row = int((ground_y[i] - ymin) / resolution)
#             row, col = min(max(row, 0), dtm_grid.shape[0] - 1), min(max(col, 0), dtm_grid.shape[1] - 1)

#             if np.isnan(dtm_grid[row, col]) or ground_z[i] < dtm_grid[row, col]:
#                 dtm_grid[row, col] = ground_z[i]

#         # Create Digital Surface Model (DSM)
#         first_return_mask = las.return_number == 1
#         first_x, first_y, first_z = x[first_return_mask], y[first_return_mask], z[first_return_mask]
#         dsm_grid = np.full((len(grid_y), len(grid_x)), np.nan)

#         for i in range(len(first_x)):
#             col = int((first_x[i] - xmin) / resolution)
#             row = int((first_y[i] - ymin) / resolution)
#             row, col = min(max(row, 0), dsm_grid.shape[0] - 1), min(max(col, 0), dsm_grid.shape[1] - 1)

#             if np.isnan(dsm_grid[row, col]) or first_z[i] > dsm_grid[row, col]:
#                 dsm_grid[row, col] = first_z[i]

#         # Compute CHM
#         chm_grid = dsm_grid - dtm_grid
#         chm_grid[np.isnan(chm_grid)] = 0  # Replace NaN with 0

#         # Save CHM as GeoTIFF
#         chm_path = os.path.join(OUTPUT_DIR, "CHM.tif")
#         transform = from_origin(xmin, ymax, resolution, resolution)
#         with rasterio.open(
#             chm_path, "w",
#             driver="GTiff",
#             height=chm_grid.shape[0],
#             width=chm_grid.shape[1],
#             count=1,
#             dtype=rasterio.float32,
#             crs="EPSG:4326",
#             transform=transform
#         ) as dst:
#             dst.write(chm_grid, 1)

#         return jsonify({"message": "CHM generated successfully!", "chm_file": chm_path})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# if __name__ == '__main__':
#     app.run(debug=True)
from flask import Flask, jsonify, request
import torch
import os
import json
import laspy
import numpy as np
from glob import glob
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2

model = joblib.load(r"C:\Users\WORK-HOME\Documents\GitHub\ForestGuard\fire_spread_predictor.pkl")
scaler = joblib.load(r"C:\Users\WORK-HOME\Documents\GitHub\ForestGuard\scaler.pkl")

def generate_fire_risk_map():
    grid_size = 50
    fire_risk_map = np.zeros((grid_size, grid_size))
    
    for i in range(grid_size):
        for j in range(grid_size):
            env_features = pd.DataFrame({
                "Elevation": [np.random.uniform(100, 3000)],
                "Wind_Direction": [np.random.uniform(0, 360)],
                "Wind_Speed": [np.random.uniform(0, 30)],
                "Min_Temperature": [np.random.uniform(-5, 25)],
                "Max_Temperature": [np.random.uniform(15, 45)],
                "Humidity": [np.random.uniform(5, 90)],
                "Precipitation": [np.random.uniform(0, 50)],
                "Drought_Index": [np.random.uniform(0, 1)],
                "NDVI": [np.random.uniform(-1, 1)],
                "ERC": [np.random.uniform(0, 100)],
                "Population_Density": [np.random.uniform(1, 500)]
            })

            env_features_scaled = scaler.transform(env_features)
            fire_risk_map[i, j] = model.predict(env_features_scaled)[0]
    
    return fire_risk_map

def simulate_fire_spread(fire_risk_map, start_x, start_y, steps=10):
    spread_map = np.zeros_like(fire_risk_map)
    spread_map[start_x, start_y] = 255
    
    for step in range(steps):
        temp_map = spread_map.copy()
        for i in range(1, fire_risk_map.shape[0]-1):
            for j in range(1, fire_risk_map.shape[1]-1):
                if spread_map[i, j] == 255:
                    for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                        ni, nj = i + di, j + dj
                        if fire_risk_map[ni, nj] > 100 and spread_map[ni, nj] == 0:
                            temp_map[ni, nj] = 255
        spread_map = temp_map.copy()
    
    return spread_map

@app.route("/predict", methods=["POST"])
def predict_fire_risk():
    data = request.json
    input_data = pd.DataFrame(data)
    input_data_scaled = scaler.transform(input_data)
    prediction = model.predict(input_data_scaled)[0]
    
    fire_risk_map = generate_fire_risk_map()
    fire_spread_simulation = simulate_fire_spread(fire_risk_map, 25, 25, steps=10)
    
    plt.imshow(fire_spread_simulation, cmap="Reds")
    plt.title("🔥 Simulated Fire Spread Over Time")
    plt.axis("off")
    output_path = "static/fire_spread.png"
    plt.savefig(output_path)
    plt.close()
    
    return jsonify({
        "fire_risk": f"{prediction:.2f}%",
        "heatmap": output_path
    })

if __name__ == '__main__':
    app.run(debug=True)