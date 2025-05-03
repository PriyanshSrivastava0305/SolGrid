/**
 * map_utils.js - Map utility functions for Solar Detective Dashboard
 * Handles map initialization, markers, popups, and interactions
 */

// Map instance variable
let map;
// Layer groups for different project types
let utilityLayerGroup, rooftopLayerGroup, floatingLayerGroup, hybridLayerGroup;
// Current visible markers
let visibleMarkers = [];
// Marker clusters
let markerCluster;

/**
 * Initialize the map with base layers
 * @param {string} containerId - ID of the HTML element to contain the map
 * @param {Object} options - Map configuration options
 * @returns {Object} - The initialized map object
 */
function initializeMap(containerId, options = {}) {
  // Default options
  const defaultOptions = {
    center: [78.9629, 20.5937], // Center of India
    zoom: 5,
    minZoom: 4,
    maxZoom: 18,
    mapStyle: 'mapbox://styles/mapbox/light-v10'
  };
  
  // Merge default options with user options
  const mapOptions = { ...defaultOptions, ...options };
  
  // Initialize Mapbox map
  mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN'; // Replace with your Mapbox token
  map = new mapboxgl.Map({
    container: containerId,
    style: mapOptions.mapStyle,
    center: mapOptions.center,
    zoom: mapOptions.zoom,
    minZoom: mapOptions.minZoom,
    maxZoom: mapOptions.maxZoom
  });
  
  // Add navigation controls
  map.addControl(new mapboxgl.NavigationControl(), 'top-right');
  map.addControl(new mapboxgl.GeolocateControl({
    positionOptions: {
      enableHighAccuracy: true
    },
    trackUserLocation: true
  }), 'top-right');
  
  // Add scale control
  map.addControl(new mapboxgl.ScaleControl({
    maxWidth: 200,
    unit: 'metric'
  }), 'bottom-left');
  
  // Initialize layer groups
  initializeLayerGroups();
  
  // Add event listeners
  addMapEventListeners();
  
  return map;
}

/**
 * Initialize layer groups for different project types
 */
function initializeLayerGroups() {
  // Create layer groups once the map is loaded
  map.on('load', () => {
    // Add source for India states
    map.addSource('india-states', {
      type: 'geojson',
      data: '../assets/geojson/india_states.geojson'
    });
    
    // Add India states layer
    map.addLayer({
      id: 'states-layer',
      type: 'fill',
      source: 'india-states',
      paint: {
        'fill-color': 'rgba(200, 200, 200, 0.2)',
        'fill-outline-color': 'rgba(100, 100, 100, 0.5)'
      }
    });
    
    // Add source for power grid
    map.addSource('power-grid', {
      type: 'geojson',
      data: '../assets/geojson/power_grid.geojson'
    });
    
    // Add power grid layer
    map.addLayer({
      id: 'grid-layer',
      type: 'line',
      source: 'power-grid',
      layout: {
        'visibility': 'none', // Hidden by default
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': '#888',
        'line-width': 2,
        'line-opacity': 0.7
      }
    });
  });
}

/**
 * Add event listeners to the map
 */
function addMapEventListeners() {
  // Handle layer toggle events
  document.querySelectorAll('.layer-control-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const layerId = e.target.value;
      const visibility = e.target.checked ? 'visible' : 'none';
      
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', visibility);
      }
    });
  });
}

/**
 * Load and display solar projects on the map
 * @param {Array} projects - Array of project objects
 */
function loadSolarProjects(projects) {
  // Clear existing markers
  clearMarkers();
  
  // Create markers for each project and add to appropriate layer
  projects.forEach(project => {
    const marker = createProjectMarker(project);
    visibleMarkers.push(marker);
    
    // Add marker to appropriate layer based on project type
    switch(project.type.toLowerCase()) {
      case 'utility-scale':
        marker.addTo(utilityLayerGroup);
        break;
      case 'rooftop':
        marker.addTo(rooftopLayerGroup);
        break;
      case 'floating':
        marker.addTo(floatingLayerGroup);
        break;
      case 'hybrid':
        marker.addTo(hybridLayerGroup);
        break;
      default:
        marker.addTo(utilityLayerGroup);
    }
  });
  
  // Create marker clusters
  markerCluster = L.markerClusterGroup({
    iconCreateFunction: createCustomClusterIcon
  });
  
  markerCluster.addLayer(utilityLayerGroup);
  markerCluster.addLayer(rooftopLayerGroup);
  markerCluster.addLayer(floatingLayerGroup);
  markerCluster.addLayer(hybridLayerGroup);
  
  map.addLayer(markerCluster);
  
  // Fit map bounds to show all markers
  if (visibleMarkers.length > 0) {
    const bounds = new mapboxgl.LngLatBounds();
    visibleMarkers.forEach(marker => {
      bounds.extend(marker.getLngLat());
    });
    map.fitBounds(bounds, { padding: 50 });
  }
}

/**
 * Create a marker for a solar project
 * @param {Object} project - Project object with location and details
 * @returns {Object} - Marker object
 */
function createProjectMarker(project) {
  // Determine marker color based on project type
  let markerClass = 'marker-utility';
  
  switch(project.type.toLowerCase()) {
    case 'utility-scale':
      markerClass = 'marker-utility';
      break;
    case 'rooftop':
      markerClass = 'marker-rooftop';
      break;
    case 'floating':
      markerClass = 'marker-floating';
      break;
    case 'hybrid':
      markerClass = 'marker-hybrid';
      break;
  }
  
  // Create marker element
  const el = document.createElement('div');
  el.className = `marker ${markerClass}`;
  
  // Size marker based on capacity (MW)
  const size = calculateMarkerSize(project.capacity);
  el.style.width = `${size}px`;
  el.style.height = `${size}px`;
  
  // Create and return Mapbox marker
  const marker = new mapboxgl.Marker(el)
    .setLngLat([project.longitude, project.latitude]);
  
  // Add popup
  marker.setPopup(createProjectPopup(project));
  
  return marker;
}

/**
 * Calculate marker size based on project capacity
 * @param {number} capacity - Project capacity in MW
 * @returns {number} - Marker size in pixels
 */
function calculateMarkerSize(capacity) {
  // Base size
  const baseSize = 12;
  
  // Scale based on capacity ranges
  if (capacity < 1) {
    return baseSize;
  } else if (capacity < 10) {
    return baseSize + 4;
  } else if (capacity < 50) {
    return baseSize + 8;
  } else if (capacity < 100) {
    return baseSize + 12;
  } else if (capacity < 500) {
    return baseSize + 16;
  } else {
    return baseSize + 20;
  }
}

/**
 * Create a popup for a solar project
 * @param {Object} project - Project object with details
 * @returns {Object} - Popup object
 */
function createProjectPopup(project) {
  // Fetch popup template
  const template = getPopupTemplate(project);
  
  // Replace template variables with project data
  const popupContent = template
    .replace('{{project_name}}', project.name)
    .replace('{{project_type}}', project.type)
    .replace('{{capacity}}', `${project.capacity} MW`)
    .replace('{{developer}}', project.developer)
    .replace('{{commissioned}}', project.commissioningYear)
    .replace('{{technology}}', project.cellTechnology || 'Not specified')
    .replace('{{location}}', `${project.location}, ${project.state}`);
  
  // Create and return Mapbox popup
  return new mapboxgl.Popup({
    offset: 25,
    closeButton: true,
    closeOnClick: true,
    className: 'custom-popup'
  }).setHTML(popupContent);
}

/**
 * Get popup template based on project type
 * @param {Object} project - Project object
 * @returns {string} - HTML template for popup
 */
function getPopupTemplate(project) {
  // This would normally fetch the template from assets/templates/popups/project_popup.html
  // For now, return a simple template
  return `
    <div class="popup-header">
      <h3 class="popup-title">{{project_name}}</h3>
      <p class="popup-subtitle">{{project_type}}</p>
    </div>
    <div class="popup-body">
      <div class="popup-content">
        <div class="popup-stat">
          <span class="popup-stat-label">Capacity:</span>
          <span>{{capacity}}</span>
        </div>
        <div class="popup-stat">
          <span class="popup-stat-label">Developer:</span>
          <span>{{developer}}</span>
        </div>
        <div class="popup-stat">
          <span class="popup-stat-label">Commissioned:</span>
          <span>{{commissioned}}</span>
        </div>
        <div class="popup-stat">
          <span class="popup-stat-label">Technology:</span>
          <span>{{technology}}</span>
        </div>
        <div class="popup-stat">
          <span class="popup-stat-label">Location:</span>
          <span>{{location}}</span>
        </div>
      </div>
    </div>
    <div class="popup-footer">
      <button class="btn btn-secondary btn-sm" onclick="showProjectDetails('${project.id}')">View Details</button>
    </div>
  `;
}

/**
 * Clear all markers from the map
 */
function clearMarkers() {
  visibleMarkers.forEach(marker => marker.remove());
  visibleMarkers = [];
  
  if (markerCluster) {
    map.removeLayer(markerCluster);
  }
}

/**
 * Filter visible projects based on criteria
 * @param {Object} filters - Filter criteria
 */
function filterProjects(filters) {
  // This function would be called when filter controls are changed
  // It would fetch filtered projects from the API and update the map
  fetch(`/api/projects/filter?${new URLSearchParams(filters).toString()}`)
    .then(response => response.json())
    .then(data => {
      loadSolarProjects(data.projects);
    })
    .catch(error => {
      console.error('Error filtering projects:', error);
    });
}

/**
 * Toggle heatmap visualization
 * @param {boolean} show - Whether to show or hide the heatmap
 */
function toggleHeatmap(show) {
  if (show) {
    // Create heatmap data from project capacities
    const heatmapData = visibleMarkers.map(marker => {
      const project = marker.project;
      return {
        coordinates: [project.longitude, project.latitude],
        weight: project.capacity
      };
    });
    
    // Add heatmap layer if it doesn't exist
    if (!map.getSource('heatmap-source')) {
      map.addSource('heatmap-source', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: heatmapData.map(point => ({
            type: 'Feature',
            properties: {
              weight: point.weight
            },
            geometry: {
              type: 'Point',
              coordinates: point.coordinates
            }
          }))
        }
      });
      
      map.addLayer({
        id: 'heatmap-layer',
        type: 'heatmap',
        source: 'heatmap-source',
        paint: {
          'heatmap-weight': [
            'interpolate',
            ['linear'],
            ['get', 'weight'],
            0, 0,
            1000, 1
          ],
          'heatmap-intensity': 1,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(0, 0, 255, 0)',
            0.2, 'rgba(0, 255, 255, 0.6)',
            0.4, 'rgba(0, 255, 0, 0.6)',
            0.6, 'rgba(255, 255, 0, 0.6)',
            0.8, 'rgba(255, 0, 0, 0.6)',
            1, 'rgba(255, 0, 0, 0.8)'
          ],
          'heatmap-radius': 30,
          'heatmap-opacity': 0.8
        }
      });
    } else {
      // Update existing heatmap data
      map.getSource('heatmap-source').setData({
        type: 'FeatureCollection',
        features: heatmapData.map(point => ({
          type: 'Feature',
          properties: {
            weight: point.weight
          },
          geometry: {
            type: 'Point',
            coordinates: point.coordinates
          }
        }))
      });
      
      // Show the heatmap layer
      map.setLayoutProperty('heatmap-layer', 'visibility', 'visible');
    }
  } else if (map.getLayer('heatmap-layer')) {
    // Hide the heatmap layer
    map.setLayoutProperty('heatmap-layer', 'visibility', 'none');
  }
}

/**
 * Export the map as an image
 */
function exportMapImage() {
  // Generate a PNG from the map canvas
  const mapCanvas = map.getCanvas();
  const mapImage = mapCanvas.toDataURL('image/png');
  
  // Create a temporary link element and trigger download
  const downloadLink = document.createElement('a');
  downloadLink.href = mapImage;
  downloadLink.download = 'solar_detective_map.png';
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
}

/**
 * Show detailed view for a specific project
 * @param {string} projectId - ID of the project to show details for
 */
function showProjectDetails(projectId) {
  // Fetch project details from API
  fetch(`/api/projects/${projectId}`)
    .then(response => response.json())
    .then(project => {
      // Display project details in a modal or side panel
      const detailsContainer = document.getElementById('project-details-container');
      if (detailsContainer) {
        detailsContainer.innerHTML = createProjectDetailsHTML(project);
        
        // Show the container
        detailsContainer.classList.remove('hidden');
        
        // Load charts and additional information
        loadProjectCharts(project);
      }
    })
    .catch(error => {
      console.error('Error fetching project details:', error);
    });
}

/**
 * Create HTML for project details
 * @param {Object} project - Full project details
 * @returns {string} - HTML for project details panel
 */
function createProjectDetailsHTML(project) {
  return `
    <div class="details-header">
      <h2>${project.name}</h2>
      <span class="details-close" onclick="closeProjectDetails()">&times;</span>
    </div>
    <div class="details-body">
      <div class="details-section">
        <h3>Project Overview</h3>
        <div class="details-grid">
          <div class="details-item">
            <span class="details-label">Type</span>
            <span class="details-value">${project.type}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Capacity</span>
            <span class="details-value">${project.capacity} MW</span>
          </div>
          <div class="details-item">
            <span class="details-label">Developer</span>
            <span class="details-value">${project.developer}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Owner</span>
            <span class="details-value">${project.owner || 'Same as developer'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Operator</span>
            <span class="details-value">${project.operator || 'Same as owner'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Commissioned</span>
            <span class="details-value">${project.commissioningYear}</span>
          </div>
        </div>
      </div>
      
      <div class="details-section">
        <h3>Technical Information</h3>
        <div class="details-grid">
          <div class="details-item">
            <span class="details-label">Cell Technology</span>
            <span class="details-value">${project.cellTechnology || 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Panel Type</span>
            <span class="details-value">${project.panelType || 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Grid Connection</span>
            <span class="details-value">${project.gridConnection || 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Land Area</span>
            <span class="details-value">${project.landArea ? `${project.landArea} acres` : 'Not specified'}</span>
          </div>
        </div>
      </div>
      
      <div class="details-section">
        <h3>Business Information</h3>
        <div class="details-grid">
          <div class="details-item">
            <span class="details-label">PPA Type</span>
            <span class="details-value">${project.ppaType || 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Offtaker</span>
            <span class="details-value">${project.offtaker || 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">PPA Rate</span>
            <span class="details-value">${project.ppaRate ? `₹${project.ppaRate}/kWh` : 'Not specified'}</span>
          </div>
          <div class="details-item">
            <span class="details-label">Investment</span>
            <span class="details-value">${project.investment ? `₹${project.investment} Cr` : 'Not specified'}</span>
          </div>
        </div>
      </div>
      
      <div class="details-section">
        <h3>Performance Metrics</h3>
        <div id="performance-chart" class="chart-container"></div>
      </div>
      
      <div class="details-section">
        <h3>Images</h3>
        <div class="image-gallery">
          ${project.images ? project.images.map(img => 
            `<div class="gallery-item">
              <img src="${img}" alt="${project.name}">
            </div>`
          ).join('') : 'No images available'}
        </div>
      </div>
    </div>
    <div class="details-footer">
      <button class="btn btn-secondary" onclick="downloadProjectReport('${project.id}')">Download Report</button>
    </div>
  `;
}

/**
 * Close the project details panel
 */
function closeProjectDetails() {
  const detailsContainer = document.getElementById('project-details-container');
  if (detailsContainer) {
    detailsContainer.classList.add('hidden');
  }
}

/**
 * Load and display charts for project performance
 * @param {Object} project - Project with performance data
 */
function loadProjectCharts(project) {
  // Check if performance data exists
  if (!project.performanceData || project.performanceData.length === 0) {
    document.getElementById('performance-chart').innerHTML = 'No performance data available';
    return;
  }
  
  // Create performance chart using Chart.js
  const ctx = document.createElement('canvas');
  document.getElementById('performance-chart').appendChild(ctx);
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: project.performanceData.map(d => d.month),
      datasets: [{
        label: 'Generation (MWh)',
        data: project.performanceData.map(d => d.generation),
        borderColor: 'rgba(33, 158, 188, 1)',
        backgroundColor: 'rgba(33, 158, 188, 0.2)',
        borderWidth: 2,
        tension: 0.1
      }, {
        label: 'Expected (MWh)',
        data: project.performanceData.map(d => d.expected),
        borderColor: 'rgba(251, 133, 0, 1)',
        backgroundColor: 'rgba(251, 133, 0, 0.2)',
        borderWidth: 2,
        tension: 0.1,
        borderDash: [5, 5]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Energy (MWh)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Month'
          }
        }
      }
    }
  });
}

/**
 * Download a detailed project report
 * @param {string} projectId - ID of the project
 */
function downloadProjectReport(projectId) {
  // Request report generation from API
  fetch(`/api/projects/${projectId}/report`, {
    method: 'POST'
  })
    .then(response => response.blob())
    .then(blob => {
      // Create a temporary link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `solar_project_${projectId}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    })
    .catch(error => {
      console.error('Error downloading report:', error);
      alert('Failed to download report. Please try again later.');
    });
}

// Export functions to make them available globally
window.showProjectDetails = showProjectDetails;
window.closeProjectDetails = closeProjectDetails;
window.downloadProjectReport = downloadProjectReport;
window.exportMapImage = exportMapImage;
window.toggleHeatmap = toggleHeatmap;