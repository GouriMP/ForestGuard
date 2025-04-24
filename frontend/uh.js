document.addEventListener("DOMContentLoaded", function () {
    var map = L.map('map').setView([37.0902, -95.7129], 5);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Handle JSON file upload
    document.getElementById('uploadJsonButton').addEventListener('click', function () {
        var fileInput = document.getElementById('fileInput');
        var file = fileInput.files[0];

        if (file && file.type === "application/json") {
            var reader = new FileReader();
            reader.onload = function (event) {
                try {
                    var jsonData = JSON.parse(event.target.result);
                    console.log("Uploaded JSON Data:", jsonData);

                    // Ensure JSON data is an array of coordinates
                    if (Array.isArray(jsonData)) {
                        jsonData.forEach(function (coord) {
                            if (coord.lat && coord.lon) {
                                L.marker([coord.lat, coord.lon]).addTo(map)
                                    .bindPopup(`Latitude: ${coord.lat}, Longitude: ${coord.lon}`)
                                    .openPopup();
                            } else {
                                console.warn("Invalid coordinate entry:", coord);
                            }
                        });

                        // Show success message
                        document.getElementById('uploadStatus').innerHTML = 
                            '<p class="text-success mt-2">File uploaded successfully! Markers added to the map.</p>';
                    } else {
                        alert("Invalid JSON structure. Please provide an array of objects with 'lat' and 'lon' fields.");
                    }
                } catch (error) {
                    alert("Error parsing JSON file. Please check the file format.");
                    console.error("JSON Parsing Error:", error);
                }
            };
            reader.readAsText(file);
        } else {
            alert("Please upload a valid JSON file.");
        }
    });

    document.getElementById("getTreeHeightButton").addEventListener("click", async function () {
        const loader = document.getElementById("loader");
        const outputDiv = document.getElementById("treeHeightOutput");
        
        if (loader) loader.style.display = "block"; 
        outputDiv.innerHTML = "";

        try {
            const response = await fetch("http://127.0.0.1:5000/get_locations_1");
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const locations = await response.json();
            console.log("Fetched locations:", locations);

            if (!Array.isArray(locations)) throw new Error("Invalid data format received");

            let locationText = "<h3>Risk Locations</h3><ul>";
            for (const loc of locations) {
                if (loc.lat && loc.lon) {
                    const placeName = await reverseGeocode(loc.lat, loc.lon);
                    locationText += `<li>${placeName} (${loc.lat}, ${loc.lon})</li>`;
                }
            }
            locationText += "</ul>";

            outputDiv.innerHTML = locationText;
            outputDiv.innerHTML += `<button id="downloadButton" class="btn btn-primary mt-3">Download Locations</button>`;

            document.getElementById("downloadButton").addEventListener("click", function () {
                downloadFile(locations, "locations.json");
            });
        } catch (error) {
            console.error("Error fetching locations:", error);
            outputDiv.innerHTML = `<p class="text-danger">Failed to load risk locations.</p>`;
        } finally {
            if (loader) loader.style.display = "none";
        }
    });

    async function reverseGeocode(lat, lon) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
            const data = await response.json();
            return data && data.display_name ? data.display_name : "Unknown Location";
        } catch {
            return "Unknown Location";
        }
    }
});
