from flask import Flask, jsonify, request
import torch
import os
import json
import laspy
import numpy as np
from glob import glob
from flask_cors import CORS

import sys
# sys.path.append("yolov5")  # path to your YOLOv5 folder
from yolov5.models.experimental import attempt_load
from yolov5.utils.general import non_max_suppression
from yolov5.utils.torch_utils import select_device
from yolov5.models.common import DetectMultiBackend



app = Flask(__name__)
CORS(app)  


MODEL_PATH = "best.pt"
UPLOAD_FOLDER = "uploads"
OUTPUT_DIR = "output"
CHM_OUTPUT = os.path.join(OUTPUT_DIR, "chm.npy")
HIGH_RISK_OUTPUT = os.path.join(OUTPUT_DIR, "high_risk_locations.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)  
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  


# model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH, force_reload=True)




device = select_device('')
model = DetectMultiBackend(MODEL_PATH, device=device)




ALLOWED_EXTENSIONS = {'laz'}
POWERLINE_HEIGHT = 10  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/detect_powerlines', methods=['POST'])
def detect_powerlines():
    try:
        image_paths = glob(os.path.join(UPLOAD_FOLDER, "*.jpg"))  
        if not image_paths:
            return jsonify({"message": "No images found for processing."}), 400

        results = []
        for image_path in image_paths:
            result = model(image_path)
            result.save()  
            results.append(os.path.basename(image_path))

        return jsonify({"message": f"Detection complete for {len(results)} images."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_locations', methods=['GET'])
def get_locations():
    try:
        locations_path = os.path.join(os.getcwd(), "locations.json")
        with open(locations_path, "r") as file:
            locations = json.load(file)
        return jsonify(locations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_locations_1', methods=['GET'])
def get_locations_1():
    try:
        locations_path = os.path.join(os.getcwd(), "risk_locations.json")
        with open(locations_path, "r") as file:
            locations = json.load(file)
        return jsonify(locations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-chm', methods=['POST'])
def generate_chm():
    try:
        # filename = r'C:\Users\wonde\OneDrive\Desktop\ForestGuard-1\USGS_LPC_WI_AshlandIronFlorence_2019_D19_04950147.copc.laz'
        filename='USGS_LPC_WI_AshlandIronFlorence_2019_D19_04950147.copc.laz'

       
        las = laspy.read(filename)
        x, y, z = las.x, las.y, las.z
        classification = las.classification
        return_number = las.return_number

        
        chm_grid, xmin, ymax, resolution = generate_chm_grid(x, y, z, classification, return_number)
        np.save(CHM_OUTPUT, chm_grid)  
       
        high_risk_trees = find_high_risk_trees(chm_grid, xmin, ymax, resolution)
        save_high_risk_locations(high_risk_trees, HIGH_RISK_OUTPUT)

        return jsonify({
            "message": f"High-risk locations saved to {HIGH_RISK_OUTPUT}",
            "high_risk_trees": high_risk_trees
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_chm_grid(x, y, z, classification, return_number, resolution=1):
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
        row = min(max(int((ground_y[i] - ymin) / resolution), 0), dtm_grid.shape[0] - 1)
        col = min(max(int((ground_x[i] - xmin) / resolution), 0), dtm_grid.shape[1] - 1)
        if np.isnan(dtm_grid[row, col]) or ground_z[i] < dtm_grid[row, col]:
            dtm_grid[row, col] = ground_z[i]

    for i in range(len(first_x)):
        row = min(max(int((first_y[i] - ymin) / resolution), 0), dsm_grid.shape[0] - 1)
        col = min(max(int((first_x[i] - xmin) / resolution), 0), dsm_grid.shape[1] - 1)
        if np.isnan(dsm_grid[row, col]) or first_z[i] > dsm_grid[row, col]:
            dsm_grid[row, col] = first_z[i]

    chm_grid = dsm_grid - dtm_grid
    chm_grid[np.isnan(chm_grid)] = 0
    return chm_grid, xmin, ymax, resolution


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


def save_high_risk_locations(locations, output_file):
    with open(output_file, "w") as f:
        json.dump(locations, f, indent=4)

MODEL_PATH = "best.pt"
UPLOAD_FOLDER = "uploads"
OUTPUT_DIR = "output"
CHM_OUTPUT = os.path.join(OUTPUT_DIR, "chm.npy")
HIGH_RISK_OUTPUT = os.path.join(OUTPUT_DIR, "high_risk_locations.json")
# FIRE_SPREAD_MODEL = r"C:\Users\wonde\OneDrive\Desktop\ForestGuard-1\fire_spread_predictor.pkl"
FIRE_SPREAD_MODEL=r"C:\Users\WORK-HOME\Documents\GitHub\ForestGuard\fire_spread_predictor.pkl"
# SCALER_PATH = r"C:\Users\wonde\OneDrive\Desktop\ForestGuard-1\scaler.pkl"
SCALER_PATH=r'C:\Users\WORK-HOME\Documents\GitHub\ForestGuard\scaler.pkl'
IMAGE_PATH = "aereal_view.png"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

import joblib
import matplotlib.pyplot as plt
# model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH, force_reload=True)

# fire_spread_model = joblib.load(FIRE_SPREAD_MODEL)
scaler = joblib.load(SCALER_PATH)

ALLOWED_EXTENSIONS = {'laz'}
POWERLINE_HEIGHT = 10

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/predict', methods=['POST'])
def predict_fire_risk():
    try:
        data = request.json
        input_data = np.array([list(data.values())]).reshape(1, -1)
        input_data_scaled = scaler.transform(input_data)
        prediction = fire_spread_model.predict(input_data_scaled)[0]
        
        return jsonify({
            "fire_risk": f"{prediction:.2f}%",
            "heatmap": "heatmap_placeholder.png"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/simulate_fire_spread', methods=['POST'])
def simulate_fire_spread():
    try:
        # Ensure static directory exists
        os.makedirs('static', exist_ok=True)
        
        # For now, we're just returning the path to the existing static image
        # In a production app, you would generate this dynamically
        
        # Make sure the image exists - if not, create a placeholder
        if not os.path.exists('static/fire_spread.png'):
            # Create a simple colored rectangle as placeholder
            plt.figure(figsize=(8, 6))
            plt.imshow(np.random.uniform(0, 255, (50, 50)), cmap='hot')
            plt.title("Fire Spread Simulation")
            plt.axis('off')
            plt.savefig('static/fire_spread.png')
            plt.close()
        
        # Return the path to the image
        return jsonify({
            "simulation_image": "/static/fire_spread.png",
            "message": "Simulation completed successfully"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to process simulation"
        }), 500



if __name__ == '__main__':
    app.run(debug=True)
