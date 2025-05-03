/**
 * Solar Detective - Dashboard Filter Functionality
 * 
 * This file contains functions for filtering data displayed in the
 * Solar Detective dashboard.
 */

/**
 * Object to store active filters
 */
const activeFilters = {
    states: [],
    developers: [],
    projectTypes: [],
    capacityRange: [0, Infinity],
    yearRange: [2000, new Date().getFullYear()],
    technologies: []
};

/**
 * Initialize filter widgets with available options
 * @param {Array} data - Array of project data
 */
function initializeFilters(data) {
    // Extract unique values for each filter type
    const states = new Set();
    const developers = new Set();
    const projectTypes = new Set();
    const technologies = new Set();
    let minCapacity = Infinity;
    let maxCapacity = 0;
    let minYear = Infinity;
    let maxYear = 0;
    
    data.forEach(project => {
        // State filter
        if (project.state) {
            states.add(project.state);
        }
        
        // Developer filter
        if (project.developer) {
            developers.add(project.developer);
        }
        
        // Project type filter
        if (project.project_type) {
            projectTypes.add(project.project_type);
        }
        
        // Technology filter
        if (project.cell_technology) {
            technologies.add(project.cell_technology);
        }
        
        // Capacity range
        if (project.capacity_mw) {
            const capacity = parseFloat(project.capacity_mw);
            if (!isNaN(capacity)) {
                minCapacity = Math.min(minCapacity, capacity);
                maxCapacity = Math.max(maxCapacity, capacity);
            }
        }
        
        // Year range
        if (project.commissioning_year) {
            const year = parseInt(project.commissioning_year);
            if (!isNaN(year)) {
                minYear = Math.min(minYear, year);
                maxYear = Math.max(maxYear, year);
            }
        }
    });
    
    // Update filter widget options
    
    // State filter
    const stateFilter = document.getElementById('stateFilter');
    if (stateFilter) {
        fillSelectOptions(stateFilter, Array.from(states).sort());
    }
    
    // Developer filter
    const developerFilter = document.getElementById('developerFilter');
    if (developerFilter) {
        fillSelectOptions(developerFilter, Array.from(developers).sort());
    }
    
    // Project type filter
    const typeFilter = document.getElementById('projectTypeFilter');
    if (typeFilter) {
        fillSelectOptions(typeFilter, Array.from(projectTypes).sort());
    }
    
    // Technology filter
    const technologyFilter = document.getElementById('technologyFilter');
    if (technologyFilter) {
        fillSelectOptions(technologyFilter, Array.from(technologies).sort());
    }
    
    // Capacity slider
    const capacitySlider = document.getElementById('capacityRangeSlider');
    if (capacitySlider) {
        initializeRangeSlider(
            capacitySlider, 
            Math.floor(minCapacity), 
            Math.ceil(maxCapacity),
            (values) => {
                activeFilters.capacityRange = values;
                document.getElementById('minCapacityLabel').textContent = values[0].toLocaleString();
                document.getElementById('maxCapacityLabel').textContent = values[1].toLocaleString();
                applyFilters();
            }
        );
    }
    
    // Year slider
    const yearSlider = document.getElementById('yearRangeSlider');
    if (yearSlider) {
        initializeRangeSlider(
            yearSlider, 
            minYear, 
            maxYear,
            (values) => {
                activeFilters.yearRange = values;
                document.getElementById('minYearLabel').textContent = values[0];
                document.getElementById('maxYearLabel').textContent = values[1];
                applyFilters();
            }
        );
    }
    
    // Reset activeFilters to initial state
    activeFilters.states = [];
    activeFilters.developers = [];
    activeFilters.projectTypes = [];
    activeFilters.capacityRange = [minCapacity, maxCapacity];
    activeFilters.yearRange = [minYear, maxYear];
    activeFilters.technologies = [];
    
    // Setup filter listeners
    setupFilterListeners();
}

/**
 * Helper function to fill select element with options
 * @param {HTMLElement} selectElement - The select element to fill
 * @param {Array} options - Array of option values
 */
function fillSelectOptions(selectElement, options) {
    // Clear existing options
    selectElement.innerHTML = '';
    
    // Add default "All" option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'All';
    defaultOption.selected = true;
    selectElement.appendChild(defaultOption);
    
    // Add options from the data
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        selectElement.appendChild(optionElement);
    });
    
    // Initialize select2 if available
    if ($.fn.select2) {
        $(selectElement).select2({
            placeholder: "Select options",
            allowClear: true
        });
    }
}

/**
 * Initialize a range slider
 * @param {HTMLElement} element - The slider element
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {Function} callback - Callback function when values change
 */
function initializeRangeSlider(element, min, max, callback) {
    // Use noUiSlider if available
    if (window.noUiSlider) {
        noUiSlider.create(element, {
            start: [min, max],
            connect: true,
            range: {
                'min': min,
                'max': max
            },
            step: 1,
            format: {
                to: value => Math.round(value),
                from: value => Math.round(value)
            }
        });
        
        element.noUiSlider.on('update', callback);
    } else {
        // Fallback to simple HTML range inputs
        element.innerHTML = `
            <input type="range" min="${min}" max="${max}" value="${min}" class="range-min" />
            <input type="range" min="${min}" max="${max}" value="${max}" class="range-max" />
        `;
        
        const minInput = element.querySelector('.range-min');
        const maxInput = element.querySelector('.range-max');
        
        minInput.addEventListener('input', () => {
            callback([parseInt(minInput.value), parseInt(maxInput.value)]);
        });
        
        maxInput.addEventListener('input', () => {
            callback([parseInt(minInput.value), parseInt(maxInput.value)]);
        });
    }
}

/**
 * Set up event listeners for filter controls
 */
function setupFilterListeners() {
    // State filter
    const stateFilter = document.getElementById('stateFilter');
    if (stateFilter) {
        stateFilter.addEventListener('change', () => {
            activeFilters.states = Array.from(stateFilter.selectedOptions).map(option => option.value);
            applyFilters();
        });
    }
    
    // Developer filter
    const developerFilter = document.getElementById('developerFilter');
    if (developerFilter) {
        developerFilter.addEventListener('change', () => {
            activeFilters.developers = Array.from(developerFilter.selectedOptions).map(option => option.value);
            applyFilters();
        });
    }
    
    // Project type filter
    const typeFilter = document.getElementById('projectTypeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', () => {
            activeFilters.projectTypes = Array.from(typeFilter.selectedOptions).map(option => option.value);
            applyFilters();
        });
    }
    
    // Technology filter
    const technologyFilter = document.getElementById('technologyFilter');
    if (technologyFilter) {
        technologyFilter.addEventListener('change', () => {
            activeFilters.technologies = Array.from(technologyFilter.selectedOptions).map(option => option.value);
            applyFilters();
        });
    }
    
    // Reset filters button
    const resetButton = document.getElementById('resetFilters');
    if (resetButton) {
        resetButton.addEventListener('click', resetFilters);
    }
}

/**
 * Reset all filters to their default state
 */
function resetFilters() {
    // Reset select elements
    const selectElements = document.querySelectorAll('select[id$="Filter"]');
    selectElements.forEach(select => {
        // Reset selected options
        Array.from(select.options).forEach(option => {
            option.selected = option.value === '';
        });
        
        // Update Select2 if available
        if ($.fn.select2 && $(select).data('select2')) {
            $(select).val('').trigger('change');
        }
    });
    
    // Reset range sliders
    const capacitySlider = document.getElementById('capacityRangeSlider');
    if (capacitySlider && capacitySlider.noUiSlider) {
        const [min, max] = capacitySlider.noUiSlider.options.range;
        capacitySlider.noUiSlider.set([min.min, max.max]);
    }
    
    const yearSlider = document.getElementById('yearRangeSlider');
    if (yearSlider && yearSlider.noUiSlider) {
        const [min, max] = yearSlider.noUiSlider.options.range;
        yearSlider.noUiSlider.set([min.min, max.max]);
    }
    
    // Reset activeFilters object
    Object.keys(activeFilters).forEach(key => {
        if (Array.isArray(activeFilters[key])) {
            if (key === 'capacityRange' || key === 'yearRange') {
                // For range filters, we need to reset to their min and max values
                // This will be handled by the slider reset above
            } else {
                // For select filters, reset to empty array
                activeFilters[key] = [];
            }
        }
    });
    
    // Apply filters (which with reset values will show all data)
    applyFilters();
}

/**
 * Apply filters to the dataset and update visualizations
 */
function applyFilters() {
    // Get the original dataset
    const originalData = window.solarData || [];
    
    // Apply filters
    const filteredData = originalData.filter(project => {
        // State filter
        if (activeFilters.states.length > 0 && project.state) {
            if (!activeFilters.states.includes(project.state)) {
                return false;
            }
        }
        
        // Developer filter
        if (activeFilters.developers.length > 0 && project.developer) {
            if (!activeFilters.developers.includes(project.developer)) {
                return false;
            }
        }
        
        // Project type filter
        if (activeFilters.projectTypes.length > 0 && project.project_type) {
            if (!activeFilters.projectTypes.includes(project.project_type)) {
                return false;
            }
        }
        
        // Technology filter
        if (activeFilters.technologies.length > 0 && project.cell_technology) {
            if (!activeFilters.technologies.includes(project.cell_technology)) {
                return false;
            }
        }
        
        // Capacity range filter
        if (project.capacity_mw) {
            const capacity = parseFloat(project.capacity_mw);
            if (capacity < activeFilters.capacityRange[0] || capacity > activeFilters.capacityRange[1]) {
                return false;
            }
        }
        
        // Year range filter
        if (project.commissioning_year) {
            const year = parseInt(project.commissioning_year);
            if (year < activeFilters.yearRange[0] || year > activeFilters.yearRange[1]) {
                return false;
            }
        }
        
        // Project passed all filters
        return true;
    });
    
    // Update the map
    if (window.updateMap) {
        window.updateMap(filteredData);
    }
    
    // Update charts
    if (window.solarCharts && window.solarCharts.updateAllCharts) {
        window.solarCharts.updateAllCharts(filteredData);
    }
    
    // Update filter counts
    updateFilterCounts(filteredData);
    
    // Update URL to make filtered view shareable
    updateUrlWithFilters();
}

/**
 * Update the displayed counts on filter widgets
 * @param {Array} filteredData - The filtered dataset
 */
function updateFilterCounts(filteredData) {
    // Get counts by state
    const stateCounts = {};
    filteredData.forEach(project => {
        if (project.state) {
            stateCounts[project.state] = (stateCounts[project.state] || 0) + 1;
        }
    });
    
    // Update state filter counts
    const stateFilter = document.getElementById('stateFilter');
    if (stateFilter) {
        Array.from(stateFilter.options).forEach(option => {
            if (option.value) {
                const count = stateCounts[option.value] || 0;
                option.textContent = `${option.value} (${count})`;
            }
        });
    }
    
    // Similar counts can be added for other filter types
    // Developer counts, project type counts, etc.
    
    // Update total filtered count
    const countDisplay = document.getElementById('filteredCount');
    if (countDisplay) {
        countDisplay.textContent = `${filteredData.length} projects found`;
    }
}

/**
 * Update URL parameters to make filtered view shareable
 */
function updateUrlWithFilters() {
    const params = new URLSearchParams();
    
    // Add states
    if (activeFilters.states.length > 0) {
        params.set('states', activeFilters.states.join(','));
    }
    
    // Add developers
    if (activeFilters.developers.length > 0) {
        params.set('developers', activeFilters.developers.join(','));
    }
    
    // Add project types
    if (activeFilters.projectTypes.length > 0) {
        params.set('types', activeFilters.projectTypes.join(','));
    }
    
    // Add technologies
    if (activeFilters.technologies.length > 0) {
        params.set('techs', activeFilters.technologies.join(','));
    }
    
    // Add capacity range
    if (activeFilters.capacityRange[0] > 0 || activeFilters.capacityRange[1] < Infinity) {
        params.set('capacity', `${activeFilters.capacityRange[0]},${activeFilters.capacityRange[1]}`);
    }
    
    // Add year range
    if (activeFilters.yearRange[0] > 2000 || activeFilters.yearRange[1] < new Date().getFullYear()) {
        params.set('years', `${activeFilters.yearRange[0]},${activeFilters.yearRange[1]}`);
    }
    
    // Update URL without reloading the page
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({ path: newUrl }, '', newUrl);
}

/**
 * Load filters from URL parameters
 */
function loadFiltersFromUrl() {
    const params = new URLSearchParams(window.location.search);
    
    // Load states
    if (params.has('states')) {
        activeFilters.states = params.get('states').split(',');
        setSelectValues('stateFilter', activeFilters.states);
    }
    
    // Load developers
    if (params.has('developers')) {
        activeFilters.developers = params.get('developers').split(',');
        setSelectValues('developerFilter', activeFilters.developers);
    }
    
    // Load project types
    if (params.has('types')) {
        activeFilters.projectTypes = params.get('types').split(',');
        setSelectValues('projectTypeFilter', activeFilters.projectTypes);
    }
    
    // Load technologies
    if (params.has('techs')) {
        activeFilters.technologies = params.get('techs').split(',');
        setSelectValues('technologyFilter', activeFilters.technologies);
    }
    
    // Load capacity range
    if (params.has('capacity')) {
        const [min, max] = params.get('capacity').split(',').map(Number);
        activeFilters.capacityRange = [min, max];
        
        const capacitySlider = document.getElementById('capacityRangeSlider');
        if (capacitySlider && capacitySlider.noUiSlider) {
            capacitySlider.noUiSlider.set([min, max]);
        }
    }
    
    // Load year range
    if (params.has('years')) {
        const [min, max] = params.get('years').split(',').map(Number);
        activeFilters.yearRange = [min, max];
        
        const yearSlider = document.getElementById('yearRangeSlider');
        if (yearSlider && yearSlider.noUiSlider) {
            yearSlider.noUiSlider.set([min, max]);
        }
    }
    
    // Apply the loaded filters
    if (window.solarData) {
        applyFilters();
    }
}

/**
 * Helper function to set values in select elements
 * @param {string} elementId - The ID of the select element
 * @param {Array} values - Array of values to select
 */
function setSelectValues(elementId, values) {
    const selectElement = document.getElementById(elementId);
    if (!selectElement) return;
    
    // Update selected options
    Array.from(selectElement.options).forEach(option => {
        option.selected = values.includes(option.value);
    });
    
    // Update Select2 if available
    if ($.fn.select2 && $(selectElement).data('select2')) {
        $(selectElement).val(values).trigger('change');
    }
}

// Export functions
window.solarFilters = {
    initializeFilters,
    applyFilters,
    resetFilters,
    loadFiltersFromUrl
};

// Initialize filters from URL when the page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.solarData) {
        initializeFilters(window.solarData);
        loadFiltersFromUrl();
    }
});