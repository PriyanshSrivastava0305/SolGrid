/**
 * Solar Detective - Dashboard Charting Utilities
 * 
 * This file contains functions for creating and updating various charts
 * used throughout the Solar Detective dashboard.
 */

// Import Chart.js library - included via CDN in the main HTML file
// Make sure to add: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script> to your HTML

/**
 * Creates a capacity by state bar chart
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of project data
 */
function createCapacityByStateChart(elementId, data) {
    // Group data by state and sum capacity
    const stateCapacities = {};
    
    data.forEach(project => {
        if (project.state && project.capacity_mw) {
            if (stateCapacities[project.state]) {
                stateCapacities[project.state] += parseFloat(project.capacity_mw);
            } else {
                stateCapacities[project.state] = parseFloat(project.capacity_mw);
            }
        }
    });
    
    // Convert to arrays for Chart.js
    const states = Object.keys(stateCapacities);
    const capacities = states.map(state => stateCapacities[state]);
    
    // Sort by capacity (descending)
    const sortedIndices = capacities.map((_, i) => i)
        .sort((a, b) => capacities[b] - capacities[a]);
    
    const sortedStates = sortedIndices.map(i => states[i]);
    const sortedCapacities = sortedIndices.map(i => capacities[i]);
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedStates,
            datasets: [{
                label: 'Installed Capacity (MW)',
                data: sortedCapacities,
                backgroundColor: 'rgba(255, 193, 7, 0.8)',
                borderColor: 'rgba(255, 193, 7, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solar Capacity by State (MW)',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toLocaleString()} MW`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Capacity (MW)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'State'
                    }
                }
            }
        }
    });
}

/**
 * Creates a doughnut chart showing project distribution by type
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of project data
 */
function createProjectTypeChart(elementId, data) {
    // Count projects by type
    const typeCounts = {};
    
    data.forEach(project => {
        if (project.project_type) {
            if (typeCounts[project.project_type]) {
                typeCounts[project.project_type]++;
            } else {
                typeCounts[project.project_type] = 1;
            }
        }
    });
    
    // Convert to arrays for Chart.js
    const types = Object.keys(typeCounts);
    const counts = types.map(type => typeCounts[type]);
    
    // Colors for different project types
    const typeColors = {
        'Utility-scale': 'rgba(255, 193, 7, 0.8)', // Yellow
        'Rooftop': 'rgba(33, 150, 243, 0.8)',      // Blue
        'Floating': 'rgba(0, 150, 136, 0.8)',      // Teal
        'Hybrid': 'rgba(156, 39, 176, 0.8)',       // Purple
        'Other': 'rgba(96, 125, 139, 0.8)'         // Blue Grey
    };
    
    // Assign colors
    const backgroundColors = types.map(type => typeColors[type] || 'rgba(189, 189, 189, 0.8)');
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: types,
            datasets: [{
                data: counts,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Projects by Type',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} projects (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a line chart showing growth over time
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of project data
 */
function createGrowthTimelineChart(elementId, data) {
    // Group by commissioning year
    const yearCapacities = {};
    const currentYear = new Date().getFullYear();
    
    // Initialize all years to 0
    for (let year = 2010; year <= currentYear; year++) {
        yearCapacities[year] = 0;
    }
    
    // Sum capacity by year
    data.forEach(project => {
        if (project.commissioning_year && project.capacity_mw) {
            const year = parseInt(project.commissioning_year);
            if (year >= 2010 && year <= currentYear) {
                yearCapacities[year] += parseFloat(project.capacity_mw);
            }
        }
    });
    
    // Convert to arrays for Chart.js
    const years = Object.keys(yearCapacities).map(Number).sort();
    const capacities = years.map(year => yearCapacities[year]);
    
    // Calculate cumulative capacity
    const cumulativeCapacity = [];
    let totalCapacity = 0;
    
    capacities.forEach(capacity => {
        totalCapacity += capacity;
        cumulativeCapacity.push(totalCapacity);
    });
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Annual Addition (MW)',
                    data: capacities,
                    backgroundColor: 'rgba(255, 193, 7, 0.4)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 2,
                    type: 'bar',
                    yAxisID: 'y'
                },
                {
                    label: 'Cumulative Capacity (MW)',
                    data: cumulativeCapacity,
                    backgroundColor: 'rgba(33, 150, 243, 0.0)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: 'rgba(33, 150, 243, 1)',
                    type: 'line',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solar Capacity Growth Timeline',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw.toLocaleString();
                            if (context.datasetIndex === 0) {
                                return `Annual: ${value} MW`;
                            } else {
                                return `Cumulative: ${value} MW`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Annual Addition (MW)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Cumulative Capacity (MW)'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a horizontal bar chart for top developers by capacity
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of project data
 * @param {number} limit - Number of top developers to display
 */
function createTopDevelopersChart(elementId, data, limit = 10) {
    // Group data by developer and sum capacity
    const developerCapacities = {};
    
    data.forEach(project => {
        if (project.developer && project.capacity_mw) {
            if (developerCapacities[project.developer]) {
                developerCapacities[project.developer] += parseFloat(project.capacity_mw);
            } else {
                developerCapacities[project.developer] = parseFloat(project.capacity_mw);
            }
        }
    });
    
    // Convert to arrays and sort
    let developers = Object.keys(developerCapacities);
    let capacities = developers.map(dev => developerCapacities[dev]);
    
    // Sort by capacity (descending)
    const sortedIndices = capacities.map((_, i) => i)
        .sort((a, b) => capacities[b] - capacities[a]);
    
    // Take only the top N developers
    const topDevelopers = sortedIndices.slice(0, limit).map(i => developers[i]);
    const topCapacities = sortedIndices.slice(0, limit).map(i => capacities[i]);
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topDevelopers,
            datasets: [{
                label: 'Total Capacity (MW)',
                data: topCapacities,
                backgroundColor: 'rgba(33, 150, 243, 0.8)',
                borderColor: 'rgba(33, 150, 243, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Top ${limit} Developers by Capacity`,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toLocaleString()} MW`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Capacity (MW)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a stacked bar chart showing technology distribution
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of project data
 */
function createTechnologyDistributionChart(elementId, data) {
    // Group projects by cell technology and then by year
    const techYearCapacity = {};
    const technologies = new Set();
    const allYears = new Set();
    
    data.forEach(project => {
        if (project.cell_technology && project.commissioning_year && project.capacity_mw) {
            const tech = project.cell_technology;
            const year = parseInt(project.commissioning_year);
            const capacity = parseFloat(project.capacity_mw);
            
            technologies.add(tech);
            allYears.add(year);
            
            if (!techYearCapacity[tech]) {
                techYearCapacity[tech] = {};
            }
            
            if (!techYearCapacity[tech][year]) {
                techYearCapacity[tech][year] = 0;
            }
            
            techYearCapacity[tech][year] += capacity;
        }
    });
    
    // Convert to arrays sorted by year
    const years = Array.from(allYears).sort();
    const techsArray = Array.from(technologies);
    
    // Create datasets for Chart.js
    const datasets = techsArray.map((tech, index) => {
        // Create a different color for each technology
        const hue = (index * 137) % 360; // Use golden ratio to space colors
        const color = `hsla(${hue}, 70%, 50%, 0.8)`;
        const borderColor = `hsla(${hue}, 70%, 40%, 1)`;
        
        return {
            label: tech,
            data: years.map(year => techYearCapacity[tech][year] || 0),
            backgroundColor: color,
            borderColor: borderColor,
            borderWidth: 1
        };
    });
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solar Technology Distribution by Year',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw.toLocaleString();
                            return `${context.dataset.label}: ${value} MW`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Capacity (MW)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a gauge chart showing progress toward a target
 * @param {string} elementId - The ID of the canvas element
 * @param {number} currentValue - Current installed capacity
 * @param {number} targetValue - Target capacity
 * @param {string} title - Chart title
 */
function createTargetProgressGauge(elementId, currentValue, targetValue, title = "Progress Toward 2030 Target") {
    const percentage = Math.min(100, (currentValue / targetValue) * 100);
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Achieved', 'Remaining'],
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [
                    'rgba(76, 175, 80, 0.8)',  // Green for achieved
                    'rgba(224, 224, 224, 0.8)' // Light gray for remaining
                ],
                borderColor: [
                    'rgba(76, 175, 80, 1)',
                    'rgba(224, 224, 224, 1)'
                ],
                borderWidth: 1,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 16
                    }
                },
                subtitle: {
                    display: true,
                    text: `${currentValue.toLocaleString()} / ${targetValue.toLocaleString()} MW (${percentage.toFixed(1)}%)`,
                    font: {
                        size: 14
                    },
                    padding: {
                        bottom: 10
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataIndex === 0) {
                                return `Achieved: ${currentValue.toLocaleString()} MW (${percentage.toFixed(1)}%)`;
                            } else {
                                return `Remaining: ${(targetValue - currentValue).toLocaleString()} MW (${(100 - percentage).toFixed(1)}%)`;
                            }
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * Creates a performance comparison chart comparing actual vs expected generation
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of performance data with expected and actual generation
 */
function createPerformanceComparisonChart(elementId, data) {
    // Extract labels, expected, and actual values
    const labels = data.map(item => item.period);
    const expectedValues = data.map(item => item.expected_generation);
    const actualValues = data.map(item => item.actual_generation);
    
    // Calculate performance ratio
    const performanceRatios = data.map((item, index) => {
        if (item.expected_generation > 0) {
            return (item.actual_generation / item.expected_generation) * 100;
        }
        return 0;
    });
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Expected Generation (MWh)',
                    data: expectedValues,
                    backgroundColor: 'rgba(255, 193, 7, 0.5)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1,
                    order: 2
                },
                {
                    label: 'Actual Generation (MWh)',
                    data: actualValues,
                    backgroundColor: 'rgba(76, 175, 80, 0.5)',
                    borderColor: 'rgba(76, 175, 80, 1)',
                    borderWidth: 1,
                    order: 1
                },
                {
                    label: 'Performance Ratio (%)',
                    data: performanceRatios,
                    backgroundColor: 'rgba(33, 150, 243, 0)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    borderWidth: 2,
                    type: 'line',
                    yAxisID: 'y1',
                    order: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Generation Performance Comparison',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Generation (MWh)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Performance Ratio (%)'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    min: 0,
                    max: 120,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a heat map visualization for irradiance data
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} data - Array of irradiance data by state
 */
function createIrradianceHeatmap(elementId, data) {
    // For the heatmap, we'll use a custom Chart.js plugin
    // This is a simplified version - a real implementation would use more complex geospatial visualization
    
    // Sort states by irradiance value (descending)
    data.sort((a, b) => b.irradiance - a.irradiance);
    
    // Extract labels and values
    const labels = data.map(item => item.state);
    const values = data.map(item => item.irradiance);
    
    // Create a color gradient based on irradiance values
    const getColor = (value) => {
        // Map value to a color (yellow-orange-red gradient)
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const normalizedValue = (value - minVal) / (maxVal - minVal);
        
        // HSL gradient from yellow (60) to red (0)
        const hue = 60 - normalizedValue * 60;
        return `hsla(${hue}, 100%, 50%, 0.8)`;
    };
    
    const colors = values.map(val => getColor(val));
    
    // Create chart
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Annual Solar Irradiance (kWh/m²)',
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solar Irradiance by State',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toLocaleString()} kWh/m²/year`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Annual Irradiance (kWh/m²)'
                    }
                }
            }
        }
    });
}

/**
 * Updates all charts when data or filters change
 * @param {Object} filteredData - The filtered dataset
 */
function updateAllCharts(filteredData) {
    // Get the current total capacity
    const totalCapacity = filteredData.reduce((sum, project) => {
        return sum + (parseFloat(project.capacity_mw) || 0);
    }, 0);
    
    // Example of updating charts with new data
    if (window.charts) {
        if (window.charts.capacityByState) {
            window.charts.capacityByState.destroy();
        }
        
        if (window.charts.projectType) {
            window.charts.projectType.destroy();
        }
        
        if (window.charts.growthTimeline) {
            window.charts.growthTimeline.destroy();
        }
        
        if (window.charts.topDevelopers) {
            window.charts.topDevelopers.destroy();
        }
    }
    
    // Initialize charts object if it doesn't exist
    window.charts = window.charts || {};
    
    // Create new charts with filtered data
    window.charts.capacityByState = createCapacityByStateChart('capacityByStateChart', filteredData);
    window.charts.projectType = createProjectTypeChart('projectTypeChart', filteredData);
    window.charts.growthTimeline = createGrowthTimelineChart('growthTimelineChart', filteredData);
    window.charts.topDevelopers = createTopDevelopersChart('topDevelopersChart', filteredData);
    
    // Update summary statistics
    document.getElementById('totalCapacity').textContent = totalCapacity.toLocaleString();
    document.getElementById('projectCount').textContent = filteredData.length.toLocaleString();
    
    // Calculate additional stats
    const uniqueDevelopers = new Set(filteredData.map(project => project.developer)).size;
    document.getElementById('developerCount').textContent = uniqueDevelopers.toLocaleString();
    
    // Calculate target progress if applicable (assuming 500 GW by 2030 as per India's target)
    const targetCapacity = 500000; // 500 GW in MW
    if (document.getElementById('targetProgressChart')) {
        if (window.charts.targetProgress) {
            window.charts.targetProgress.destroy();
        }
        window.charts.targetProgress = createTargetProgressGauge('targetProgressChart', totalCapacity, targetCapacity);
    }
}

// Export functions
window.solarCharts = {
    createCapacityByStateChart,
    createProjectTypeChart,
    createGrowthTimelineChart,
    createTopDevelopersChart,
    createTechnologyDistributionChart,
    createTargetProgressGauge,
    createPerformanceComparisonChart,
    createIrradianceHeatmap,
    updateAllCharts
};