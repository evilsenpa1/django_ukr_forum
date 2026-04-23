/**
 * product_form_shared.js
 * Shared utilities for create_product.js and update_product.js.
 * Exposes window.ProductForm namespace — must be loaded BEFORE page scripts.
 */
(function (global) {
  'use strict';

  // ========== FILE SECURITY CONFIG ==========
  const FILE_CONFIG = {
    MAX_FILES: 10,
    MAX_SIZE_MB: 10,
    MAX_SIZE_BYTES: 10 * 1024 * 1024,
    MIN_SIZE_BYTES: 100,
    ALLOWED_MIME_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'],
    ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp', '.gif'],
    MAX_WIDTH: 8000,
    MAX_HEIGHT: 8000,
    MIN_WIDTH: 100,
    MIN_HEIGHT: 100,
    DANGEROUS_PATTERNS: [
      '.php', '.exe', '.sh', '.bat', '.cmd', '.com',
      '.pif', '.scr', '.vbs', '.js', '.jar', '.zip',
      '.rar', '.7z', '.svg', '.html', '.htm',
    ],
  };

  // ========== UTILITIES ==========
  const debounce = (fn, wait = 250) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(null, args), wait);
    };
  };

  const hide = el => el && el.classList.add('hidden');
  const show = el => el && el.classList.remove('hidden');

  function sanitizeText(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function getPluralForm(num, form1, form2, form5) {
    const n = Math.abs(num) % 100;
    const n1 = n % 10;
    if (n > 10 && n < 20) return form5;
    if (n1 > 1 && n1 < 5) return form2;
    if (n1 === 1) return form1;
    return form5;
  }

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  // ========== TOAST SYSTEM ==========
  const TOAST_CONFIG = {
    success: { bg: 'bg-green-500', icon: '✓', duration: 4000 },
    error:   { bg: 'bg-red-500',   icon: '✕', duration: 8000 },
    warning: { bg: 'bg-yellow-500', icon: '⚠', duration: 6000 },
    info:    { bg: 'bg-blue-500',  icon: 'ℹ', duration: 4000 },
    loading: { bg: 'bg-gray-700', icon: '⟳', duration: 0 },
  };

  let _toastContainer = null;

  function getToastContainer() {
    if (!_toastContainer) {
      _toastContainer = document.createElement('div');
      _toastContainer.className = 'toast-container';
      document.body.appendChild(_toastContainer);
    }
    return _toastContainer;
  }

  function showToast(message, type = 'info', customDuration = null) {
    const container = getToastContainer();
    const config = TOAST_CONFIG[type] || TOAST_CONFIG.info;
    const duration = customDuration !== null ? customDuration : config.duration;

    const toast = document.createElement('div');
    toast.className = [
      'toast', config.bg, 'text-white', 'px-5', 'py-4', 'relative', 'overflow-hidden',
      ...(type !== 'loading' ? ['toast-clickable'] : []),
    ].join(' ');

    const content = document.createElement('div');
    content.className = 'flex items-start gap-3';

    const icon = document.createElement('span');
    icon.className = 'text-2xl flex-shrink-0' + (type === 'loading' ? ' spinner' : '');
    icon.textContent = config.icon;

    const text = document.createElement('div');
    text.className = 'flex-1 text-sm leading-relaxed';
    text.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'text-white hover:text-gray-200 text-2xl leading-none flex-shrink-0 ml-2 focus:outline-none';
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => removeToast(toast));

    content.appendChild(icon);
    content.appendChild(text);
    content.appendChild(closeBtn);
    toast.appendChild(content);

    if (duration > 0) {
      const progress = document.createElement('div');
      progress.className = `toast-progress dur-${duration}`;
      toast.appendChild(progress);
      setTimeout(() => removeToast(toast), duration);
    }

    container.appendChild(toast);

    if (type !== 'loading') {
      toast.addEventListener('click', (e) => {
        if (e.target === toast || e.target === content || e.target === text) {
          removeToast(toast);
        }
      });
    }

    return toast;
  }

  function removeToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add('removing');
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 300);
  }

  function showToastList(title, items, type = 'error', duration = 10000) {
    const container = getToastContainer();
    const config = TOAST_CONFIG[type] || TOAST_CONFIG.error;

    const toast = document.createElement('div');
    toast.className = `toast toast-list ${config.bg} text-white px-5 py-4 relative overflow-hidden`;

    const content = document.createElement('div');
    const header = document.createElement('div');
    header.className = 'flex items-center justify-between mb-3';

    const titleEl = document.createElement('div');
    titleEl.className = 'font-bold flex items-center gap-2';

    const iconSpan = document.createElement('span');
    iconSpan.className = 'text-xl';
    iconSpan.textContent = config.icon;

    const titleSpan = document.createElement('span');
    titleSpan.textContent = title;

    titleEl.appendChild(iconSpan);
    titleEl.appendChild(titleSpan);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'text-white hover:text-gray-200 text-2xl leading-none focus:outline-none';
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => removeToast(toast));

    header.appendChild(titleEl);
    header.appendChild(closeBtn);
    content.appendChild(header);

    const list = document.createElement('ul');
    list.className = 'text-sm space-y-1.5 max-h-60 overflow-y-auto pr-2';

    items.slice(0, 8).forEach(item => {
      const li = document.createElement('li');
      li.className = 'leading-relaxed pl-1';
      li.textContent = '• ' + item;
      list.appendChild(li);
    });

    if (items.length > 8) {
      const more = document.createElement('li');
      more.className = 'text-white/70 italic pl-1';
      more.textContent = `... та ще ${items.length - 8} помилок`;
      list.appendChild(more);
    }

    content.appendChild(list);
    toast.appendChild(content);

    if (duration > 0) {
      const progress = document.createElement('div');
      progress.className = `toast-progress dur-${duration}`;
      toast.appendChild(progress);
      setTimeout(() => removeToast(toast), duration);
    }

    container.appendChild(toast);
    return toast;
  }

  // ========== FILE VALIDATION ==========
  function validateExtension(filename) {
    const lower = filename.toLowerCase();
    for (const pat of FILE_CONFIG.DANGEROUS_PATTERNS) {
      if (lower.includes(pat)) return { valid: false, error: `Заборонене розширення: ${pat}` };
    }
    if (!FILE_CONFIG.ALLOWED_EXTENSIONS.some(ext => lower.endsWith(ext))) {
      return { valid: false, error: `Дозволені: ${FILE_CONFIG.ALLOWED_EXTENSIONS.join(', ')}` };
    }
    return { valid: true };
  }

  function validateMimeType(file) {
    if (!file.type) return { valid: false, error: 'Неможливо визначити тип файлу' };
    if (!FILE_CONFIG.ALLOWED_MIME_TYPES.includes(file.type)) {
      return { valid: false, error: `Недозволений тип: ${file.type}` };
    }
    return { valid: true };
  }

  function validateFileSize(file) {
    if (file.size === 0) return { valid: false, error: 'Файл порожній' };
    if (file.size < FILE_CONFIG.MIN_SIZE_BYTES) {
      return { valid: false, error: `Файл занадто малий (мін. ${FILE_CONFIG.MIN_SIZE_BYTES} байт)` };
    }
    if (file.size > FILE_CONFIG.MAX_SIZE_BYTES) {
      return { valid: false, error: `Розмір ${(file.size / 1024 / 1024).toFixed(2)} MB (макс. ${FILE_CONFIG.MAX_SIZE_MB} MB)` };
    }
    return { valid: true };
  }

  function validateFileName(filename) {
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      return { valid: false, error: 'Заборонені символи в імені' };
    }
    if (/[\x00-\x1F\x7F]/.test(filename)) return { valid: false, error: 'Керуючі символи в імені' };
    if (filename.length > 255) return { valid: false, error: "Ім'я занадто довге" };
    return { valid: true };
  }

  function validateImageContent(file) {
    return new Promise(resolve => {
      const reader = new FileReader();
      reader.onerror = () => resolve({ valid: false, error: 'Помилка читання' });
      reader.onload = e => {
        const img = new Image();
        img.onerror = () => resolve({ valid: false, error: 'Не є зображенням' });
        img.onload = () => {
          if (img.width > FILE_CONFIG.MAX_WIDTH || img.height > FILE_CONFIG.MAX_HEIGHT) {
            return resolve({ valid: false, error: `${img.width}x${img.height}px (макс. ${FILE_CONFIG.MAX_WIDTH}x${FILE_CONFIG.MAX_HEIGHT})` });
          }
          if (img.width < FILE_CONFIG.MIN_WIDTH || img.height < FILE_CONFIG.MIN_HEIGHT) {
            return resolve({ valid: false, error: `${img.width}x${img.height}px (мін. ${FILE_CONFIG.MIN_WIDTH}x${FILE_CONFIG.MIN_HEIGHT})` });
          }
          if (Math.max(img.width, img.height) / Math.min(img.width, img.height) > 20) {
            return resolve({ valid: false, error: 'Некоректні пропорції' });
          }
          resolve({ valid: true });
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  async function validateFile(file) {
    const nameCheck = validateFileName(file.name); if (!nameCheck.valid) return nameCheck;
    const extCheck  = validateExtension(file.name); if (!extCheck.valid)  return extCheck;
    const mimeCheck = validateMimeType(file);        if (!mimeCheck.valid) return mimeCheck;
    const sizeCheck = validateFileSize(file);        if (!sizeCheck.valid) return sizeCheck;
    return await validateImageContent(file);
  }

  // ========== API HELPERS ==========
  const API = {
    countries: '/geo/api/get-countries/',
    cities: '/geo/api/get-cities/',
  };

  async function safeJsonFetch(url) {
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  }

  function makeItem(innerHTML, meta = {}) {
    const li = document.createElement('li');
    li.className = 'px-3 py-2 cursor-pointer hover:bg-blue-50 hover:text-blue-700 text-gray-800 text-sm';
    li.tabIndex = 0;
    li.innerHTML = innerHTML; // nosemgrep: dangerous-innerhtml -- callers sanitize user data via sanitizeText()
    li.dataset.meta = JSON.stringify(meta);
    return li;
  }

  // ========== FORM FIELD CLASSES ==========
  function applyFormFieldClasses(form) {
    form.querySelectorAll('input:not([type=file]):not([type=hidden]), textarea, select').forEach(field => {
      field.classList.add(
        'w-full', 'border-2', 'border-gray-300', 'rounded-xl', 'px-4', 'py-3', 'text-gray-800',
        'transition', 'focus:outline-none', 'focus:border-blue-500', 'focus:ring-2', 'focus:ring-blue-200'
      );
    });
  }

  // ========== GALLERY ==========
  /**
   * Re-renders gallery thumbnails from the files array.
   * @param {HTMLElement} gallery - Container element
   * @param {File[]} files - Current file list (shared reference)
   * @param {Function} onRemove - Called with index when remove button is clicked
   */
  function renderGallery(gallery, files, onRemove) {
    if (!gallery) return;
    gallery.innerHTML = '';
    files.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = e => {
        const container = document.createElement('div');
        container.className = 'relative w-24 h-24 m-1 group';

        const img = document.createElement('img');
        img.src = e.target.result;
        img.className = 'w-full h-full object-cover rounded-lg shadow-md border-2 border-gray-200';
        img.alt = sanitizeText(file.name);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = '×';
        removeBtn.className = [
          'absolute', 'top-1/2', 'left-1/2', 'transform', '-translate-x-1/2', '-translate-y-1/2',
          'bg-red-600', 'text-white', 'rounded-full', 'w-10', 'h-10', 'flex', 'items-center',
          'justify-center', 'text-2xl', 'font-bold', 'opacity-0', 'group-hover:opacity-100',
          'transition-opacity', 'duration-200', 'hover:bg-red-700', 'focus:outline-none',
          'focus:ring-2', 'focus:ring-red-500',
        ].join(' ');
        removeBtn.addEventListener('click', () => onRemove(index));

        container.appendChild(img);
        container.appendChild(removeBtn);
        gallery.appendChild(container);
      };
      reader.readAsDataURL(file);
    });
  }

  // ========== DROP AREA ==========
  /**
   * Wires up drag-and-drop and file input for a drop zone.
   * @param {HTMLElement} dropArea
   * @param {HTMLInputElement} fileInput
   * @param {Function} onFilesAdded - Called with FileList when files are selected/dropped
   */
  function setupDropArea(dropArea, fileInput, onFilesAdded) {
    if (dropArea) {
      const info = document.createElement('div');
      info.className = 'text-xs text-gray-500 mt-3';
      info.textContent = `Формати: JPG, PNG, WEBP, GIF | Макс. ${FILE_CONFIG.MAX_SIZE_MB} MB | До ${FILE_CONFIG.MAX_FILES} фото`;
      dropArea.appendChild(info);

      dropArea.addEventListener('dragover', e => {
        e.preventDefault();
        dropArea.classList.add('border-blue-500', 'bg-blue-50');
      });
      dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('border-blue-500', 'bg-blue-50');
      });
      dropArea.addEventListener('drop', e => {
        e.preventDefault();
        dropArea.classList.remove('border-blue-500', 'bg-blue-50');
        onFilesAdded(e.dataTransfer.files);
      });
    }

    if (fileInput) {
      fileInput.setAttribute('accept', FILE_CONFIG.ALLOWED_EXTENSIONS.join(','));
      fileInput.addEventListener('change', () => onFilesAdded(fileInput.files));
    }

    const uploadTrigger = document.getElementById('upload-trigger');
    if (uploadTrigger && fileInput) {
      uploadTrigger.addEventListener('click', () => fileInput.click());
    }
  }

  // ========== COUNTRY AUTOCOMPLETE ==========
  /**
   * Sets up country autocomplete with currency display.
   * @param {Object} opts
   * @param {HTMLInputElement} opts.countryInput
   * @param {HTMLUListElement} opts.countryList
   * @param {HTMLInputElement} opts.countryId
   * @param {HTMLElement}      opts.currencyDisplay
   * @param {Function}         opts.onCountryChange - Called after a country is selected (to reset city)
   * @returns {{ fetchCountries, ensureCountrySelected }}
   */
  function setupCountryAutocomplete({ countryInput, countryList, countryId, currencyDisplay, onCountryChange }) {
    function setCurrencyDisplay(value) {
      if (!currencyDisplay) return;
      currencyDisplay.textContent = value ? String(value) : '—';
      currencyDisplay.title = value ? `Currency: ${value}` : '';
    }

    async function fetchCountries(q = '', byId = '') {
      const url = new URL(API.countries, window.location.origin);
      if (q)    url.searchParams.set('q', q);
      if (byId) url.searchParams.set('country', byId);
      const data = await safeJsonFetch(url.toString());
      if (data === null) return [];
      return Array.isArray(data) ? data : [data];
    }

    function renderCountries(arr) {
      if (!countryList) return;
      countryList.innerHTML = '';
      if (!arr.length) { hide(countryList); return; }
      arr.forEach(c => {
        const text = `${sanitizeText(c.name || '')}${c.code ? ` <span class="text-gray-400 text-xs">(${sanitizeText(c.code)})</span>` : ''}`;
        const li = makeItem(text, { id: c.id, name: c.name, currency: c.currency });
        li.addEventListener('click', () => {
          if (countryInput) countryInput.value = c.name;
          if (countryId)    countryId.value = c.id || '';
          setCurrencyDisplay(c.currency || '');
          if (onCountryChange) onCountryChange();
          hide(countryList);
        });
        countryList.appendChild(li);
      });
      show(countryList);
    }

    const countrySearch = debounce(async () => {
      const q = countryInput ? countryInput.value.trim() : '';
      renderCountries(await fetchCountries(q, ''));
    }, 250);

    if (countryInput) {
      countryInput.addEventListener('focus', async () => {
        if (!countryList.childElementCount) renderCountries(await fetchCountries('', ''));
        else show(countryList);
      });
      countryInput.addEventListener('input', () => {
        if (countryId) countryId.value = '';
        countrySearch();
      });
    }

    document.addEventListener('click', e => {
      if (countryList && countryInput && !countryInput.contains(e.target) && !countryList.contains(e.target)) {
        hide(countryList);
      }
    });
    if (countryList) countryList.addEventListener('click', e => e.stopPropagation());

    // Pre-fill country if default values exist in the DOM
    (async function initPrefilledCountry() {
      try {
        const hidVal  = countryId    ? (countryId.value    || '').trim() : '';
        const defAttr = countryInput ? (countryInput.getAttribute('data-default-id') || '').trim() : '';
        const nameVal = countryInput ? (countryInput.value || '').trim() : '';
        const idToUse = hidVal || defAttr || '';

        function findMatching(arr, idOrName) {
          if (!Array.isArray(arr) || !arr.length) return null;
          return arr.find(x => String(x.id) === String(idOrName))
              || arr.find(x => x.code && x.code.toLowerCase() === idOrName.toLowerCase())
              || arr.find(x => x.name && x.name.toLowerCase() === idOrName.toLowerCase())
              || arr[0];
        }

        if (idToUse) {
          const arr = await fetchCountries('', idToUse);
          const matched = findMatching(arr, idToUse);
          if (matched) {
            if (countryId && !countryId.value) countryId.value = matched.id || idToUse;
            if (countryInput && !countryInput.value.trim()) countryInput.value = matched.name || '';
            setCurrencyDisplay(matched.currency || '');
            return;
          }
        }
        if (nameVal) {
          const arr2 = await fetchCountries(nameVal, '');
          const matched2 = findMatching(arr2, nameVal);
          if (matched2) {
            if (countryId && !countryId.value) countryId.value = matched2.id || '';
            if (!countryInput.value) countryInput.value = matched2.name || '';
            setCurrencyDisplay(matched2.currency || '');
            return;
          }
        }
        setCurrencyDisplay('');
      } catch { setCurrencyDisplay(''); }
    })();

    async function ensureCountrySelected() {
      if (countryId && countryId.value.trim()) return true;
      const name = countryInput ? countryInput.value : '';
      if (!name.trim()) return false;
      const arr = await fetchCountries(name.trim(), '');
      if (!arr || !arr.length) return false;
      if (countryId) countryId.value = arr[0].id || '';
      if (arr[0].currency) setCurrencyDisplay(arr[0].currency);
      return true;
    }

    return { fetchCountries, ensureCountrySelected };
  }

  // ========== CITY AUTOCOMPLETE ==========
  /**
   * Sets up city autocomplete for all .city-autocomplete inputs in a form.
   * @param {Object} opts
   * @param {HTMLFormElement} opts.form
   * @param {Function} opts.getCountryId - Returns current country id string
   * @param {string}   opts.cityApiParam  - Query param name for country ('country_id' or 'country')
   */
  function setupCityAutocomplete({ form, getCountryId, cityApiParam = 'country_id' }) {
    if (!form) return;
    const cityInputEls = Array.from(form.querySelectorAll('.city-autocomplete'));

    cityInputEls.forEach(cityInput => {
      const cityList = document.createElement('ul');
      cityList.className = 'city-dropdown absolute bg-white border border-gray-200 shadow-lg rounded-md mt-1 max-h-60 overflow-y-auto z-50 hidden';
      cityInput.parentNode.insertBefore(cityList, cityInput.nextSibling);

      const cityIdInput = cityInput.dataset.cityId ? document.getElementById(cityInput.dataset.cityId) : null;

      async function fetchCities(q = '', countryVal = '') {
        const url = new URL(API.cities, window.location.origin);
        if (q)          url.searchParams.set('q', q);
        if (countryVal) url.searchParams.set(cityApiParam, countryVal);
        const data = await safeJsonFetch(url.toString());
        return Array.isArray(data) ? data : [];
      }

      function renderCities(arr) {
        cityList.innerHTML = '';
        if (!arr.length) { hide(cityList); return; }
        arr.forEach(c => {
          const txt = `${sanitizeText(c.city)}${c.region ? ` <span class="text-gray-400 text-xs">(${sanitizeText(c.region)})</span>` : ''}`;
          const li = makeItem(txt, { id: c.id, city: c.city });
          li.addEventListener('click', () => {
            cityInput.value = c.city;
            if (cityIdInput) cityIdInput.value = c.id || '';
            hide(cityList);
          });
          cityList.appendChild(li);
        });
        show(cityList);
      }

      const doSearch = debounce(async () => {
        const q = cityInput.value.trim();
        const countryVal = getCountryId();
        if (q.length < 1) { hide(cityList); return; }
        if (!countryVal) {
          cityInput.animate(
            [{ transform: 'translateX(0)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(0)' }],
            { duration: 200 }
          );
          showToast('Спочатку оберіть країну', 'warning', 3000);
          return;
        }
        renderCities(await fetchCities(q, countryVal));
      }, 250);

      cityInput.addEventListener('focus', () => { if (cityList.childElementCount) show(cityList); });
      cityInput.addEventListener('input', () => {
        if (cityIdInput) cityIdInput.value = '';
        doSearch();
      });
      document.addEventListener('click', e => {
        if (!cityInput.contains(e.target) && !cityList.contains(e.target)) hide(cityList);
      });
      cityList.addEventListener('click', e => e.stopPropagation());
    });
  }

  // ========== EXPORT ==========
  global.ProductForm = {
    FILE_CONFIG,
    debounce,
    hide,
    show,
    showToast,
    removeToast,
    showToastList,
    validateFile,
    sanitizeText,
    getPluralForm,
    getCookie,
    safeJsonFetch,
    makeItem,
    applyFormFieldClasses,
    renderGallery,
    setupDropArea,
    setupCountryAutocomplete,
    setupCityAutocomplete,
  };
})(window);
