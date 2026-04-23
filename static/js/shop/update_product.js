/**
 * update_product.js
 * Page-specific logic for the "Edit product" form.
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
  const form                    = document.getElementById('product-form');
  const gallery                 = document.getElementById('gallery');
  const dropArea                = document.getElementById('drop-area');
  const fileInput               = document.getElementById('fileElem');
  const existingImagesContainer = document.getElementById('existing-images');
  let files = [];
  let deletedImageIds = [];

  if (form) applyFormFieldClasses(form);

  // ========== CONFIRM MODAL ==========
  function showConfirmModal(message, onConfirm, onCancel) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    const modal = document.createElement('div');
    modal.className = 'bg-white rounded-lg shadow-2xl p-6 max-w-md mx-4';

    const text = document.createElement('div');
    text.className = 'text-gray-800 mb-6 text-lg';
    text.textContent = message;

    const buttons = document.createElement('div');
    buttons.className = 'flex gap-3 justify-end';

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Скасувати';
    cancelBtn.className = 'px-5 py-2.5 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition';
    cancelBtn.addEventListener('click', () => {
      document.body.removeChild(overlay);
      if (onCancel) onCancel();
    });

    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Видалити';
    confirmBtn.className = 'px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition';
    confirmBtn.addEventListener('click', () => {
      document.body.removeChild(overlay);
      if (onConfirm) onConfirm();
    });

    buttons.appendChild(cancelBtn);
    buttons.appendChild(confirmBtn);
    modal.appendChild(text);
    modal.appendChild(buttons);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    overlay.addEventListener('click', e => {
      if (e.target === overlay) {
        document.body.removeChild(overlay);
        if (onCancel) onCancel();
      }
    });
  }

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

    const existingCount = existingImagesContainer
      ? existingImagesContainer.querySelectorAll('[data-image-id]').length
      : 0;
    const totalAllowed = FILE_CONFIG.MAX_FILES - existingCount;

    const loadingToast = showToast('Перевірка файлів...', 'loading');
    newFiles.sort((a, b) => a.lastModified - b.lastModified);

    let addedCount = 0;
    const errors = [];

    for (const f of newFiles) {
      if (files.length >= totalAllowed) {
        errors.push(`Ліміт ${FILE_CONFIG.MAX_FILES} фото загалом. Є ${existingCount} існуючих.`);
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

  // ========== EXISTING IMAGE DELETION ==========
  if (existingImagesContainer) {
    existingImagesContainer.addEventListener('click', e => {
      const btn = e.target.closest('[data-delete-id]');
      if (!btn) return;
      const imageId = btn.dataset.deleteId;
      showConfirmModal('Видалити це фото?', () => {
        const imageDiv = existingImagesContainer.querySelector(`[data-image-id="${imageId}"]`);
        if (imageDiv) {
          imageDiv.remove();
          deletedImageIds.push(imageId);
          showToast('Фото буде видалено після збереження', 'info', 3500);
        }
      });
    });
  }

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

      const existingCount = existingImagesContainer
        ? existingImagesContainer.querySelectorAll('[data-image-id]').length
        : 0;

      if (existingCount === 0 && files.length === 0) {
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
      if (deletedImageIds.length > 0) {
        formData.append('deleted_images', JSON.stringify(deletedImageIds));
      }

      const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
      const uploadingToast = showToast('Збереження змін...', 'loading');

      try {
        const resp = await fetch(form.action || window.location.href, {
          method: 'POST',
          body: formData,
          credentials: 'same-origin',
          headers: csrftoken ? { 'X-CSRFToken': csrftoken } : {},
        });
        removeToast(uploadingToast);
        if (resp.ok) {
          showToast('✓ Зміни успішно збережено!', 'success', 3000);
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
