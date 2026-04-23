/**
 * Search Form with Location Filters
 * Handles cascading location selection: Country → Region → City → Radius
 * Version: 2.1
 */

document.addEventListener('DOMContentLoaded', () => {
  
  // ==================== UTILITIES ====================
  
  /**
   * Debounce function to limit API calls
   */
  const debounce = (fn, wait = 300) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), wait);
    };
  };

  /**
   * Element visibility helpers
   */
  const hideElem = (el) => el && el.classList.add('hidden');
  const showElem = (el) => el && el.classList.remove('hidden');

  /**
   * Shake animation for UX feedback
   */
  const shakeElement = (el) => {
    el.animate([
      { transform: 'translateX(0)' },
      { transform: 'translateX(6px)' },
      { transform: 'translateX(-6px)' },
      { transform: 'translateX(0)' }
    ], { duration: 300, easing: 'ease-in-out' });
  };

  // ==================== DOM ELEMENTS ====================
  
  const elements = {
    // Country
    countryInput: document.getElementById('country-input'),
    countryList: document.getElementById('country-list'),
    countryId: document.getElementById('country-id'),
    
    // Region
    regionToggle: document.getElementById('region-toggle'),
    regionLabel: document.getElementById('region-label'),
    regionList: document.getElementById('region-list'),
    regionId: document.getElementById('region-id'),
    regionName: document.getElementById('region-name'),
    
    // City
    cityInput: document.getElementById('city-input'),
    cityList: document.getElementById('city-list'),
    cityId: document.getElementById('city-id'),
    
    // Radius
    radiusSelect: document.getElementById('radius-select'),
    
    // Form
    form: document.querySelector('form')
  };

  // ==================== API CONFIGURATION ====================
  
  const API = {
    countries: '/geo/api/get-countries/',
    regions: '/geo/api/get-regions/',
    cities: '/geo/api/get-cities/'
  };

  // ==================== CLEAR FUNCTIONS ====================
  
  /**
   * Clear region selection and related fields
   */
  function clearRegion() {
    if (elements.regionLabel) {
      // Use non-breaking space to maintain height
      elements.regionLabel.innerHTML = '&nbsp;';
    }
    if (elements.regionId) elements.regionId.value = '';
    if (elements.regionName) elements.regionName.value = '';
    if (elements.regionList) {
      elements.regionList.innerHTML = '';
      hideElem(elements.regionList);
    }
  }

  /**
   * Clear city selection and related fields
   */
  function clearCity() {
    if (elements.cityInput) elements.cityInput.value = '';
    if (elements.cityId) elements.cityId.value = '';
    if (elements.cityList) {
      elements.cityList.innerHTML = '';
      hideElem(elements.cityList);
    }
  }

  /**
   * Clear radius selection
   */
  function clearRadius() {
    if (elements.radiusSelect) {
      elements.radiusSelect.value = '';
    }
  }

  // ==================== LIST ITEM BUILDER ====================
  
  /** Escape a string for safe HTML interpolation */
  function esc(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
  }

  /**
   * Create list item element with hover effects.
   * Callers must escape user-supplied values with esc() before interpolating into htmlContent.
   */
  function createListItem(htmlContent, metadata = {}) {
    const li = document.createElement('li');
    li.className = 'px-3 py-2 cursor-pointer hover:bg-blue-50 hover:text-blue-700 text-gray-800 text-sm transition-colors';
    li.tabIndex = 0;
    li.innerHTML = htmlContent; // nosemgrep: dangerous-innerhtml -- inputs sanitized by callers via esc()
    li.dataset.meta = JSON.stringify(metadata);
    return li;
  }

  // ==================== COUNTRY HANDLING ====================
  
  /**
   * Fetch countries from API
   */
  async function fetchCountries(query = '') {
    try {
      const url = new URL(API.countries, window.location.origin);
      if (query) url.searchParams.set('q', query);
      
      const response = await fetch(url.toString());
      if (!response.ok) return [];
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching countries:', error);
      return [];
    }
  }

  /**
   * Render countries list
   */
  function renderCountries(countries) {
    if (!elements.countryList) return;
    
    elements.countryList.innerHTML = '';
    
    if (!countries.length) {
      hideElem(elements.countryList);
      return;
    }

    // Add "Усі" option first
    const allCountriesItem = createListItem('<strong>Усі</strong>', { id: '', name: 'Усі' });
    allCountriesItem.addEventListener('click', () => {
      elements.countryInput.value = 'Усі';
      elements.countryId.value = '';
      
      // Clear dependent fields
      clearRegion();
      clearCity();
      clearRadius();
      
      hideElem(elements.countryList);
    });
    elements.countryList.appendChild(allCountriesItem);

    // Add separator
    const separator = document.createElement('li');
    separator.className = 'border-t border-gray-200 my-1';
    elements.countryList.appendChild(separator);

    countries.forEach(country => {
      const html = `${esc(country.name)}${country.code ? ` <span class="text-gray-400 text-xs">(${esc(country.code)})</span>` : ''}`;
      const listItem = createListItem(html, { id: country.id, name: country.name });
      
      listItem.addEventListener('click', () => {
        // Set new country
        elements.countryInput.value = country.name;
        elements.countryId.value = country.id || '';
        
        // Clear dependent fields
        clearRegion();
        clearCity();
        clearRadius();
        
        hideElem(elements.countryList);
        
        // Preload regions for better UX
        if (country.id) loadRegions(country.id);
      });
      
      elements.countryList.appendChild(listItem);
    });
    
    showElem(elements.countryList);
  }

  /**
   * Debounced country search
   */
  const searchCountries = debounce(async () => {
    const query = elements.countryInput.value.trim();
    const countries = await fetchCountries(query);
    renderCountries(countries);
  }, 250);

  // Country event listeners
  if (elements.countryInput) {
    elements.countryInput.addEventListener('focus', async () => {
      if (!elements.countryList.childElementCount) {
        const countries = await fetchCountries('');
        renderCountries(countries);
      } else {
        showElem(elements.countryList);
      }
    });

    elements.countryInput.addEventListener('input', () => {
      elements.countryId.value = '';
      clearRegion();
      clearCity();
      clearRadius();
      searchCountries();
    });
  }

  // ==================== REGION HANDLING ====================
  
  /**
   * Load regions for selected country
   */
  async function loadRegions(countryId) {
    if (!elements.regionList || !countryId) {
      if (elements.regionList) hideElem(elements.regionList);
      return;
    }

    elements.regionList.innerHTML = '';

    try {
      const url = new URL(API.regions, window.location.origin);
      url.searchParams.set('country_id', countryId);
      
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        elements.regionList.innerHTML = '<li class="px-3 py-2 text-gray-500 text-sm">Помилка завантаження</li>';
        return;
      }

      const regions = await response.json();

      if (!regions.length) {
        elements.regionList.innerHTML = '<li class="px-3 py-2 text-gray-500 text-sm">Регіони не знайдені</li>';
        return;
      }

      // Add "Усі" option first
      const allRegionsItem = createListItem('<strong>Усі</strong>', { id: '', name: 'Усі' });
      allRegionsItem.addEventListener('click', () => {
        if (elements.regionLabel) elements.regionLabel.textContent = 'Усі';
        elements.regionId.value = '';
        if (elements.regionName) elements.regionName.value = 'Усі';
        
        // Clear dependent fields
        clearCity();
        clearRadius();
        
        hideElem(elements.regionList);
      });
      elements.regionList.appendChild(allRegionsItem);

      // Add separator
      const separator = document.createElement('li');
      separator.className = 'border-t border-gray-200 my-1';
      elements.regionList.appendChild(separator);

      regions.forEach(region => {
        const listItem = createListItem(esc(region.name), { id: region.id, name: region.name });
        
        listItem.addEventListener('click', () => {
          // Set new region
          if (elements.regionLabel) elements.regionLabel.textContent = region.name;
          elements.regionId.value = region.id || '';
          if (elements.regionName) elements.regionName.value = region.name;
          
          // Clear dependent fields
          clearCity();
          clearRadius();
          
          hideElem(elements.regionList);
        });
        
        elements.regionList.appendChild(listItem);
      });
    } catch (error) {
      console.error('Error loading regions:', error);
      elements.regionList.innerHTML = '<li class="px-3 py-2 text-gray-500 text-sm">Помилка завантаження</li>';
    }
  }

  // Region toggle event listener
  if (elements.regionToggle) {
    elements.regionToggle.addEventListener('click', async (e) => {
      e.stopPropagation();
      
      const countryId = elements.countryId.value;

      // Check if country is selected
      if (!countryId) {
        shakeElement(elements.regionToggle);
        
        const previousText = elements.regionLabel.textContent;
        elements.regionLabel.textContent = 'Оберіть країну спочатку';

        setTimeout(() => {
          elements.regionLabel.textContent = previousText || '\u00A0';
        }, 1500);
        
        return;
      }

      // Toggle dropdown
      const isHidden = elements.regionList.classList.contains('hidden');
      
      if (isHidden) {
        if (!elements.regionList.childElementCount) {
          await loadRegions(countryId);
        }
        showElem(elements.regionList);
        elements.regionToggle.setAttribute('aria-expanded', 'true');
      } else {
        hideElem(elements.regionList);
        elements.regionToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ==================== CITY HANDLING ====================
  
  /**
   * Fetch cities from API
   */
  async function fetchCities(query = '', countryId = '', regionId = '') {
    try {
      const url = new URL(API.cities, window.location.origin);
      if (query) url.searchParams.set('q', query);
      if (countryId) url.searchParams.set('country_id', countryId);
      if (regionId) url.searchParams.set('region_id', regionId);
      
      const response = await fetch(url.toString());
      if (!response.ok) return [];
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching cities:', error);
      return [];
    }
  }

  /**
   * Render cities list
   */
  function renderCities(cities) {
    if (!elements.cityList) return;
    
    elements.cityList.innerHTML = '';
    
    if (!cities.length) {
      hideElem(elements.cityList);
      return;
    }

    cities.forEach(city => {
      const html = `${esc(city.city)}${city.region ? ` <span class="text-gray-400 text-xs">(${esc(city.region)})</span>` : ''}`;
      const listItem = createListItem(html, { id: city.id, city: city.city });
      
      listItem.addEventListener('click', () => {
        elements.cityInput.value = city.city;
        elements.cityId.value = city.id || '';
        hideElem(elements.cityList);
      });
      
      elements.cityList.appendChild(listItem);
    });
    
    showElem(elements.cityList);
  }

  /**
   * Debounced city search
   */
  const searchCities = debounce(async () => {
    const query = elements.cityInput.value.trim();
    const countryId = elements.countryId.value || '';
    const regionId = elements.regionId.value || '';

    if (query.length < 1) {
      hideElem(elements.cityList);
      return;
    }

    // Require both country and region
    if (!countryId || !regionId) {
      shakeElement(elements.cityInput);
      
      let message = '';
      if (!countryId) {
        message = 'Спочатку оберіть країну';
      } else if (!regionId) {
        message = 'Спочатку оберіть регіон';
      }
      
      elements.cityList.innerHTML = `<li class="px-3 py-2 text-gray-500 text-sm">${message}</li>`;
      showElem(elements.cityList);
      return;
    }

    const cities = await fetchCities(query, countryId, regionId);
    renderCities(cities);
  }, 250);

  // City event listeners
  if (elements.cityInput) {
    elements.cityInput.addEventListener('focus', () => {
      if (elements.cityList.childElementCount && elements.cityInput.value.trim()) {
        showElem(elements.cityList);
      }
    });

    elements.cityInput.addEventListener('input', () => {
      elements.cityId.value = '';
      clearRadius();
      searchCities();
    });
  }

  // ==================== RADIUS HANDLING ====================
  
  if (elements.radiusSelect) {
    elements.radiusSelect.addEventListener('change', () => {
      // Verify city is selected when radius is chosen
      if (elements.radiusSelect.value && !elements.cityId.value) {
        const previousValue = elements.radiusSelect.value;
        elements.radiusSelect.value = '';
        
        alert('Спочатку оберіть місто для пошуку за радіусом');
        
        setTimeout(() => {
          elements.radiusSelect.value = previousValue;
        }, 100);
      }
    });
  }

  // ==================== PAGE LOAD VALIDATION ====================
  
  /**
   * Validate initial state on page load
   */
  function validateInitialState() {
    const initialCountryId = elements.countryId.value;
    const initialRegionId = elements.regionId.value;
    const initialCityId = elements.cityId.value;

    // Validate country-region relationship
    if (initialCountryId) {
      loadRegions(initialCountryId).then(() => {
        if (initialRegionId) {
          const regionItems = elements.regionList.querySelectorAll('li');
          let regionFound = false;

          regionItems.forEach(item => {
            try {
              const meta = JSON.parse(item.dataset.meta || '{}');
              if (meta.id && meta.id.toString() === initialRegionId.toString()) {
                regionFound = true;
              }
            } catch (e) {
              // Ignore parsing errors
            }
          });

          // Clear region if it doesn't match the country
          if (!regionFound && elements.regionList.childElementCount > 0) {
            console.warn('Region ID does not match country, clearing region');
            clearRegion();
            clearCity();
          }
        }
      });
    } else if (initialRegionId) {
      // Clear region if no country is selected
      console.warn('Region without country, clearing region');
      clearRegion();
    }

    // Validate city requires both country and region
    if (initialCityId) {
      if (!initialCountryId) {
        console.warn('City without country, clearing city');
        clearCity();
      } else if (!initialRegionId) {
        console.warn('City without region, clearing city');
        clearCity();
      }
    }
  }

  // Run validation on load
  validateInitialState();

  // ==================== REGION LABEL HEIGHT FIX ====================
  
  /**
   * Ensure region label maintains height even when empty
   */
  if (elements.regionLabel) {
    // Set minimum height to match text line height
    elements.regionLabel.style.minHeight = '1.5rem';
    elements.regionLabel.style.display = 'inline-block';
    
    const currentText = elements.regionLabel.textContent || elements.regionLabel.innerHTML;
    if (!currentText || currentText.trim() === '') {
      elements.regionLabel.innerHTML = '&nbsp;';
    }
  }

  // ==================== FORM SUBMISSION VALIDATION ====================
  
  if (elements.form) {
    elements.form.addEventListener('submit', (e) => {
      // Clean up invalid combinations before submission
      
      if (elements.regionId.value && !elements.countryId.value) {
        clearRegion();
      }

      if (elements.cityId.value) {
        if (!elements.countryId.value || !elements.regionId.value) {
          clearCity();
        }
      }

      if (elements.radiusSelect && elements.radiusSelect.value && !elements.cityId.value) {
        clearRadius();
      }
    });
  }

  // ==================== DROPDOWN CLOSE HANDLERS ====================
  
  /**
   * Close dropdowns when clicking outside
   */
  document.addEventListener('click', (e) => {
    // Close country dropdown
    if (elements.countryInput && elements.countryList) {
      if (!elements.countryInput.contains(e.target) && !elements.countryList.contains(e.target)) {
        hideElem(elements.countryList);
      }
    }

    // Close city dropdown
    if (elements.cityInput && elements.cityList) {
      if (!elements.cityInput.contains(e.target) && !elements.cityList.contains(e.target)) {
        hideElem(elements.cityList);
      }
    }

    // Close region dropdown
    if (elements.regionToggle && elements.regionList) {
      if (!elements.regionToggle.contains(e.target) && !elements.regionList.contains(e.target)) {
        hideElem(elements.regionList);
        elements.regionToggle.setAttribute('aria-expanded', 'false');
      }
    }
  });

  /**
   * Prevent closing when clicking inside dropdown lists
   */
  [elements.countryList, elements.regionList, elements.cityList].forEach(list => {
    if (list) {
      list.addEventListener('click', (e) => e.stopPropagation());
    }
  });

  // ==================== ACCESSIBILITY ====================
  
  /**
   * Keyboard navigation for dropdowns
   */
  [elements.countryInput, elements.cityInput].forEach(input => {
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          const listId = input.id.replace('-input', '-list');
          const list = document.getElementById(listId);
          if (list) hideElem(list);
        }
      });
    }
  });

  console.log('Search form initialized successfully');
});