/**
 * data_loader.js - Data loading functions for Solar Detective Dashboard
 * Handles fetching and processing data from the API
 */

// Cache for loaded data
const dataCache = {
    projects: null,
    filters: null,
    statistics: null,
    timestamp: null
  };
  
  // Cache expiration time in milliseconds (15 minutes)
  const CACHE_EXPIRATION = 15 * 60 * 1000;
  
  /**
   * Load solar project data from the API with optional filters
   * @param {Object} filters - Filter criteria (optional)
   * @returns {Promise} - Promise resolving to array of project objects
   */
  async function loadProjects(filters = {}) {
    try {
      // Check if we have cached data and it's still valid
      if (
        dataCache.projects && 
        dataCache.timestamp && 
        Date.now() - dataCache.timestamp < CACHE_EXPIRATION &&
        !filters  // Only use cache for unfiltered data
      ) {
        console.log('Using cached project data');
        return dataCache.projects;
      }
      
      // Build query string from filters
      const queryString = filters ? `?${new URLSearchParams(filters).toString()}` : '';
      
      // Fetch data from API
      const response = await fetch(`/api/projects${queryString}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Cache the data if it's an unfiltered request
      if (!filters || Object.keys(filters).length === 0) {
        dataCache.projects = data.projects;
        dataCache.timestamp = Date.now();
      }
      
      return data.projects;
    } catch (error) {
      console.error('Error loading projects:', error);
      
      // Return cached data if available, otherwise empty array
      return dataCache.projects || [];
    }
  }
  
  /**
   * Load available filter options from the API
   * @returns {Promise} - Promise resolving to filter options object
   */
  async function loadFilterOptions() {
    try {
      // Check if we have cached filter options and they're still valid
      if (
        dataCache.filters && 
        dataCache.timestamp && 
        Date.now() - dataCache.timestamp < CACHE_EXPIRATION
      ) {
        console.log('Using cached filter options');
        return dataCache.filters;
      }
      
      // Fetch filter options from API
      const response = await fetch('/api/filters');
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const filterOptions = await response.json();
      
      // Cache the filter options
      dataCache.filters = filterOptions;
      
      return filterOptions;
    } catch (error) {
      console.error('Error loading filter options:', error);
      
      // Return cached options if available, otherwise empty object
      return dataCache.filters || {
        types: [],
        developers: [],
        states: [],
        years: [],
        technologies: []
      };
    }
  }
  
  /**
   * Load summary statistics for dashboard
   * @returns {Promise} - Promise resolving to statistics object
   */
  async function loadStatistics() {
    try {
      // Check if we have cached statistics and they're still valid
      if (
        dataCache.statistics && 
        dataCache.timestamp && 
        Date.now() - dataCache.timestamp < CACHE_EXPIRATION
      ) {
        console.log('Using cached statistics');
        return dataCache.statistics;
      }
      
      // Fetch statistics from API
      const response = await fetch('/api/statistics');
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const statistics = await response.json();
      
      // Cache the statistics
      dataCache.statistics = statistics;
      
      return statistics;
    } catch (error) {
      console.error('Error loading statistics:', error);
      
      // Return cached statistics if available, otherwise null
      return dataCache.statistics || null;
    }
  }
  
  /**
   * Load detailed data for a specific project
   * @param {string} projectId - ID of the project to load
   * @returns {Promise} - Promise resolving to project object with full details
   */
  async function loadProjectDetails(projectId) {
    try {
      // This is always fetched fresh (no caching)
      const response = await fetch(`/api/projects/${projectId}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error loading project ${projectId} details:`, error);
      return null;
    }
  }
  
  /**
   * Load performance data for a specific project
   * @param {string} projectId - ID of the project
   * @param {string} timeframe - Timeframe for data (daily, monthly, yearly)
   * @returns {Promise} - Promise resolving to array of performance data points
   */
  async function loadProjectPerformance(projectId, timeframe = 'monthly') {
    try {
      const response = await fetch(`/api/projects/${projectId}/performance?timeframe=${timeframe}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error loading performance data for project ${projectId}:`, error);
      return [];
    }
  }
  
  /**
   * Load comparison data for multiple projects
   * @param {Array} projectIds - Array of project IDs to compare
   * @returns {Promise} - Promise resolving to comparison data object
   */
  async function loadProjectComparison(projectIds) {
    try {
      const response = await fetch('/api/projects/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ projectIds })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading project comparison data:', error);
      return null;
    }
  }
  
  /**
   * Load GeoJSON data for India states
   * @returns {Promise} - Promise resolving to GeoJSON object
   */
  async function loadIndiaStatesGeoJSON() {
    try {
      const response = await fetch('/assets/geojson/india_states.geojson');
      
      if (!response.ok) {
        throw new Error(`Error loading GeoJSON: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading India states GeoJSON:', error);
      return null;
    }
  }
  
  /**
   * Load GeoJSON data for power grid network
   * @returns {Promise} - Promise resolving to GeoJSON object
   */
  async function loadPowerGridGeoJSON() {
    try {
      const response = await fetch('/assets/geojson/power_grid.geojson');
      
      if (!response.ok) {
        throw new Error(`Error loading GeoJSON: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading power grid GeoJSON:', error);
      return null;
    }
  }
  
  /**
   * Load capacity timeline data (capacity added by year)
   * @returns {Promise} - Promise resolving to timeline data object
   */
  async function loadCapacityTimeline() {
    try {
      const response = await fetch('/api/timeline/capacity');
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading capacity timeline data:', error);
      return [];
    }
  }
  
  /**
   * Export CSV data for all projects or filtered results
   * @param {Object} filters - Filter criteria (optional)
   * @returns {Promise} - Promise resolving to CSV data as string
   */
  async function exportProjectsCSV(filters = {}) {
    try {
      // Build query string from filters
      const queryString = filters ? `?${new URLSearchParams(filters).toString()}` : '';
      
      // Fetch CSV data from API
      const response = await fetch(`/api/projects/export/csv${queryString}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      return await response.text();
    } catch (error) {
      console.error('Error exporting CSV data:', error);
      return null;
    }
  }
  
  /**
   * Clear the data cache
   */
  function clearCache() {
    dataCache.projects = null;
    dataCache.filters = null;
    dataCache.statistics = null;
    dataCache.timestamp = null;
    console.log('Data cache cleared');
  }
  
  // Export functions to make them available globally
  window.loadProjects = loadProjects;
  window.loadFilterOptions = loadFilterOptions;
  window.loadStatistics = loadStatistics;
  window.loadProjectDetails = loadProjectDetails;
  window.loadProjectPerformance = loadProjectPerformance;
  window.loadProjectComparison = loadProjectComparison;
  window.loadIndiaStatesGeoJSON = loadIndiaStatesGeoJSON;
  window.loadPowerGridGeoJSON = loadPowerGridGeoJSON;
  window.loadCapacityTimeline = loadCapacityTimeline;
  window.exportProjectsCSV = exportProjectsCSV;
  window.clearCache = clearCache;