/**
 * create_product.js
 * Page-specific logic for the "Add product" form.
 * Requires product_form_shared.js to be loaded first (window.ProductForm).
 */
document.addEventListener('DOMContentLoaded', () => {
  const {
    FILE_CONFIG, showToast, removeToast, showToastList,
    validateFile, sanitizeText, getPluralForm, getCookie,
    applyFormFieldClasses, renderGallery, setupDropArea,
    setupCountryAutocomplete, setupCityAutocomplete,
  } = window.ProductForm;

  // ========== ELEMENTS ==========
  const form      = document.getElementById('product-form');
  const gallery   = document.getElementById('gallery');
  const dropArea  = document.getElementById('drop-area');
  const fileInput = document.getElementById('fileElem');
  let files = [];

  if (form) applyFormFieldClasses(form);

  // ========== GALLERY ==========
  function refreshGallery() {
    renderGallery(gallery, files, (index) => {
      const filename = files[index].name;
      files.splice(index, 1);
      refreshGallery();
      showToast(`Видалено: ${filename}`, 'info', 2500);
    });
  }

  // ========== FILE UPLOAD ==========
  async function addFiles(selectedFiles) {
    const newFiles = Array.from(selectedFiles || []);
    if (!newFiles.length) return;

    const loadingToast = showToast('Перевірка файлів...', 'loading');
    newFiles.sort((a, b) => a.lastModified - b.lastModified);

    let addedCount = 0;
    const errors = [];

    for (const f of newFiles) {
      if (files.length >= FILE_CONFIG.MAX_FILES) {
        errors.push(`Ліміт ${FILE_CONFIG.MAX_FILES} фото`);
        break;
      }
      const isDuplicate = files.some(ex => ex.name === f.name && ex.size === f.size && ex.lastModified === f.lastModified);
      if (isDuplicate) { errors.push(`"${sanitizeText(f.name)}" вже додано`); continue; }

      const validation = await validateFile(f);
      if (!validation.valid) { errors.push(`${sanitizeText(f.name)}: ${validation.error}`); continue; }

      files.push(f);
      addedCount++;
    }

    removeToast(loadingToast);
    if (addedCount > 0) {
      refreshGallery();
      showToast(`✓ Додано ${addedCount} ${getPluralForm(addedCount, 'файл', 'файли', 'файлів')}`, 'success', 3500);
    }
    if (errors.length > 0) showToastList('Помилки завантаження', errors, 'error', 12000);
    if (fileInput) fileInput.value = '';
  }

  setupDropArea(dropArea, fileInput, addFiles);

  // ========== COUNTRY / CITY AUTOCOMPLETE ==========
  const countryInput    = document.getElementById('country-input');
  const countryList     = document.getElementById('country-list');
  const countryId       = document.getElementById('country-id');
  const currencyDisplay = document.querySelector('#country-currency, [data-country-currency]');

  const { ensureCountrySelected } = setupCountryAutocomplete({
    countryInput,
    countryList,
    countryId,
    currencyDisplay,
    onCountryChange: () => {
      // Reset all city fields when country changes
      document.querySelectorAll('.city-autocomplete').forEach(el => {
        el.value = '';
        const cid = el.dataset.cityId ? document.getElementById(el.dataset.cityId) : null;
        if (cid) cid.value = '';
      });
    },
  });

  setupCityAutocomplete({
    form,
    getCountryId: () => countryId ? countryId.value : '',
    cityApiParam: 'country_id',
  });

  // ========== SUBMIT ==========
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (files.length === 0) {
        showToast('Додайте хоча б одне фото', 'error', 5000);
        if (dropArea) {
          dropArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
          dropArea.animate([
            { transform: 'scale(1)', borderColor: '#d1d5db' },
            { transform: 'scale(1.02)', borderColor: '#ef4444' },
            { transform: 'scale(1)', borderColor: '#d1d5db' },
          ], { duration: 500 });
        }
        return;
      }

      const firstCity   = form.querySelector('.city-autocomplete');
      const firstCityId = firstCity?.dataset.cityId ? document.getElementById(firstCity.dataset.cityId) : null;
      if (!firstCity || !firstCityId || !firstCityId.value) {
        showToast('Оберіть місто зі списку підказок', 'error', 5000);
        if (firstCity) { firstCity.focus(); firstCity.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
        return;
      }

      if (!await ensureCountrySelected()) {
        showToast('Оберіть країну зі списку підказок', 'error', 5000);
        if (countryInput) {
          countryInput.focus();
          countryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
          countryInput.animate(
            [{ transform: 'translateX(0)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(0)' }],
            { duration: 300 }
          );
        }
        return;
      }

      const validatingToast = showToast('Фінальна перевірка файлів...', 'loading');
      for (const file of files) {
        const validation = await validateFile(file);
        if (!validation.valid) {
          removeToast(validatingToast);
          showToast(`Помилка у файлі "${sanitizeText(file.name)}": ${validation.error}`, 'error', 8000);
          return;
        }
      }
      removeToast(validatingToast);

      const formData = new FormData();
      for (const [key, value] of new FormData(form).entries()) {
        if (key !== 'images') formData.append(key, value);
      }
      files.forEach(file => formData.append('images', file));

      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
      const uploadingToast = showToast('Відправка на сервер...', 'loading');

      try {
        const resp = await fetch(form.action || window.location.href, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: csrftoken ? { 'X-CSRFToken': csrftoken } : {},
        });
        removeToast(uploadingToast);
        if (resp.ok) {
          showToast('✓ Товар успішно додано!', 'success', 3000);
          setTimeout(() => { window.location.href = '/shop/'; }, 1500);
        } else {
          let text = ''; try { text = await resp.text(); } catch {}
          console.error('Server error:', resp.status, text);
          showToast('Помилка сервера. Перевірте дані та спробуйте ще раз.', 'error', 8000);
        }
      } catch (err) {
        removeToast(uploadingToast);
        console.error('Network error:', err);
        showToast("Помилка з'єднання. Перевірте інтернет та спробуйте ще раз.", 'error', 8000);
      }
    });
  }
});
