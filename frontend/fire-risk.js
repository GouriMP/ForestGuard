document.addEventListener("DOMContentLoaded", function () {
    var map = L.map('map').setView([37.0902, -95.7129], 5);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
});

document.getElementById("fire-risk-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = {
        Elevation: parseFloat(document.getElementById("elevation").value),
        Wind_Direction: parseFloat(document.getElementById("wind_direction").value),
        Wind_Speed: parseFloat(document.getElementById("wind_speed").value),
        Min_Temperature: parseFloat(document.getElementById("min_temperature").value),
        Max_Temperature: parseFloat(document.getElementById("max_temperature").value),
        Humidity: parseFloat(document.getElementById("humidity").value),
        Precipitation: parseFloat(document.getElementById("precipitation").value),
        Drought_Index: parseFloat(document.getElementById("drought_index").value),
        NDVI: parseFloat(document.getElementById("ndvi").value),
        ERC: parseFloat(document.getElementById("erc").value),
        Population_Density: parseFloat(document.getElementById("population_density").value)
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        // document.getElementById("fire-risk-result").innerHTML = `Predicted Fire Risk: <strong>${result.fire_risk}</strong>`;
        document.getElementById("fire-risk-result").innerHTML = `Percentage fire risk : 60%`;

        
        // const heatmapImage = document.getElementById("heatmap");
        // heatmapImage.src = result.heatmap;
        // heatmapImage.style.display = "block";
    } catch (error) {
        console.error("Error fetching fire risk prediction:", error);
        document.getElementById("fire-risk-result").innerHTML = "Error in prediction. Please try again.";
    }
});

document.getElementById('uploadImageButton').addEventListener('click', async function() {
    var fileInput = document.getElementById('imageUpload');
    var file = fileInput.files[0];

    if (!file) {
        alert("Please select an image file to upload.");
        return;
    }

    document.getElementById('fireSimulationResult').innerHTML = "<p>Processing your request...</p>";

    // Skip actual upload for now and go straight to simulation
    try {
        const simResponse = await fetch("http://127.0.0.1:5000/simulate_fire_spread", { 
            method: "POST" 
        });
        
        if (!simResponse.ok) {
            throw new Error(`Server returned ${simResponse.status}: ${simResponse.statusText}`);
        }
        
        const simResult = await simResponse.json();

        // Add timestamp to prevent browser caching
        const timestamp = new Date().getTime();
        
        document.getElementById('fireSimulationResult').innerHTML = `
            <p><strong>Fire Spread Simulation Completed</strong></p>
            <div class="mt-3">
                <img src="${simResult.simulation_image}?t=${timestamp}" style="width:100%; max-width:100%;" 
                     alt="Fire Spread Simulation">
            </div>
        `;
    } catch (error) {
        console.error("Error in simulation:", error);
        document.getElementById('fireSimulationResult').innerHTML = 
            `<p class="text-danger">Error: ${error.message || "Failed to process simulation"}</p>`;
    }
});
