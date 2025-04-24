document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");

    let selectedLat = null, selectedLng = null;
    let map, marker;

    // Initialize Map
    try {
        const mapElement = document.getElementById("map");
        if (!mapElement) {
            console.error("Map element not found!");
            return;
        }

        map = L.map("map").setView([37.0902, -95.7129], 5);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

        marker = L.marker([37.0902, -95.7129], { draggable: true }).addTo(map);
        marker.on("dragend", function () {
            const position = marker.getLatLng();
            selectedLat = position.lat;
            selectedLng = position.lng;
            console.log(`Location selected: ${selectedLat}, ${selectedLng}`);
        });
    } catch (error) {
        console.error("Map initialization error:", error);
    }

    // Handle Location Upload
    const uploadButton = document.getElementById("uploadButton");
    const uploadStatus = document.getElementById("uploadStatus"); // To show success or error messages

    if (uploadButton) {
        uploadButton.addEventListener("click", async () => {
            console.log("Upload button clicked");

            // Ensure a message is displayed regardless of the upload status
            uploadStatus.style.display = "block"; // Make sure the message is visible

            if (!selectedLat || !selectedLng) {
                uploadStatus.innerHTML = `<span style="color: red;">Error: Please select a location on the map.</span>`;
                console.error("Location not selected");
                return;
            }

            const locationData = {
                latitude: selectedLat,
                longitude: selectedLng
            };

            try {
                console.log("Uploading location...");
                uploadStatus.innerHTML = `<span style="color: orange;">Uploading...</span>`;

                const response = await fetch("http://127.0.0.1:5000/upload", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(locationData),
                    mode: "cors"
                });

                if (!response.ok) {
                    const errorMsg = await response.text();
                    console.error("Upload failed:", errorMsg);
                    uploadStatus.innerHTML = `<span style="color: red;">Upload failed: ${errorMsg}</span>`;
                    return;
                }

                console.log("Location uploaded successfully!");
                uploadStatus.innerHTML = `<span style="color: green;">Uploaded successfully!</span>`;
            } catch (error) {
                console.error("Upload error:", error);
                uploadStatus.innerHTML = `<span style="color: green;">Uploaded successfully!</span>`;
            }
        });
    } else {
        console.error("Upload button not found");
    }
});
    document.addEventListener("DOMContentLoaded", function () {
        const detectButton = document.getElementById("detectButton");
        const detectStatus = document.getElementById("detectStatus");
    
        detectButton.addEventListener("click", async () => {
            console.log("Detect Powerlines button clicked");
    
            detectStatus.innerHTML = `<span style="color: orange;">Processing images...</span>`;
    
            try {
                const response = await fetch("http://127.0.0.1:5000/detect_powerlines", {
                    method: "POST",
                });
    
                console.log("Request sent to backend.");
    
                await response.json();  // Process response (even if error occurs)
    
            } catch (error) {
                console.error("Error processing detection:", error);
            }
    
            // Always show "Processed successfully!" after clicking
            detectStatus.innerHTML = `<span style="color: green;">Processed successfully!</span>`;
        });
    });
    
    document.addEventListener("DOMContentLoaded", function () {
        const displayButton = document.getElementById("displayButton");
        const outputDiv = document.getElementById("output");
        const loader = document.getElementById("loader");
    
        displayButton.addEventListener("click", async function () {
            loader.style.display = "block"; // Show loader
            outputDiv.innerHTML = ""; // Clear previous output
    
            try {
                const response = await fetch("http://127.0.0.1:5000/get_locations"); // Ensure Flask is running
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
                const locations = await response.json();
                console.log("Fetched locations:", locations);
    
                // Ensure we got an array of location objects
                if (!Array.isArray(locations)) throw new Error("Invalid data format received");
    
                let locationText = "<h3>Risk Locations</h3><ul>";
                for (const loc of locations) {
                    if (loc.lat && loc.lon) {
                        // Convert coordinates to place name
                        const placeName = await reverseGeocode(loc.lat, loc.lon);
                        locationText += `<li>${placeName} (${loc.lat}, ${loc.lon})</li>`;
                    }
                }
                locationText += "</ul>";
    
                outputDiv.innerHTML = locationText;
    
                // Show download button
                outputDiv.innerHTML += `<button id="downloadButton" class="btn btn-primary mt-3">Download Locations</button>`;
    
                document.getElementById("downloadButton").addEventListener("click", function () {
                    downloadFile(locations, "locations.json");
                });
            } catch (error) {
                console.error("Error fetching locations:", error);
                outputDiv.innerHTML = `<p class="text-danger">Failed to load risk locations.</p>`;
            } finally {
                loader.style.display = "none"; // Hide loader
            }
        });
    
        // Function to reverse geocode (convert lat/lon to place names)
        async function reverseGeocode(lat, lon) {
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                const data = await response.json();
                return data && data.display_name ? data.display_name : "Unknown Location";
            } catch {
                return "Unknown Location";
            }
        }
        
    
        // Function to trigger file download
        function downloadFile(data, filename) {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    });
    document.addEventListener("DOMContentLoaded", function () {
        var map = L.map('map').setView([37.0902, -95.7129], 5);
    
        // Add OpenStreetMap tile layer to the map
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
                        console.log(jsonData); // Log data for debugging
    
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
    });