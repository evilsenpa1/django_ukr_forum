document.addEventListener('DOMContentLoaded', () => {
    console.log('=== JS LOADED AND INITIALIZED ===');

    // ==========================================
    // 1. ЛОГІКА ФАЙЛІВ (Валідація та обмеження)
    // ==========================================
    const fileInput = document.getElementById('id_files') || document.querySelector('input[type="file"]');
    
    if (fileInput) {
        console.log('File input found:', fileInput.id);
        
        // Встановлюємо обмеження у вікні вибору файлів
        fileInput.setAttribute('accept', '.jpg,.jpeg,.png,.webp');

        fileInput.addEventListener('change', function() {
            const validExtensions = ['jpg', 'jpeg', 'png', 'webp'];
            const maxSize = 5 * 1024 * 1024; // 5 МБ
            const files = this.files;

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const fileName = file.name.toLowerCase();
                const fileExt = fileName.split('.').pop();

                console.log(`Checking file: ${fileName}, Ext: ${fileExt}, Size: ${file.size}`);

                // Перевірка розширення
                if (!validExtensions.includes(fileExt)) {
                    alert(`ПОМИЛКА ФОРМАТУ!\nФайл "${file.name}" має розширення .${fileExt}.\nДозволені тільки: ${validExtensions.join(', ')}`);
                    this.value = ''; // Повністю очищуємо вибір
                    return;
                }

                // Перевірка розміру
                if (file.size > maxSize) {
                    alert(`ФАЙЛ ЗАВЕЛИКИЙ!\nФайл "${file.name}" важить більше 5 МБ.\nБудь ласка, стисніть його або виберіть інший.`);
                    this.value = ''; // Повністю очищуємо вибір
                    return;
                }
            }
            console.log('All files passed validation');
        });
    } else {
        console.warn('Warning: File input (id_files) not found on this page.');
    }

    // ==========================================
    // 2. ЛОГІКА ТЕГІВ
    // ==========================================
    let selectedTags = [];
    const openModalBtn = document.getElementById('openModal');
    const closeModalBtn = document.getElementById('closeModal');
    const saveTagsBtn = document.getElementById('saveTags');
    const tagModal = document.getElementById('tagModal');
    const selectedTagsInput = document.getElementById('selectedTags');
    const filterBlocks = document.getElementById('filterBlocks');

    function updateFilterBlocks() {
        if (!filterBlocks) return;
        filterBlocks.innerHTML = '';

        selectedTags.slice(0, 7).forEach((tag) => {
            const block = document.createElement('div');
            block.className = 'p-1 bg-blue-100 border border-blue-300 rounded flex justify-between items-center';

            const span = document.createElement('span');
            span.className = 'mr-2';
            span.textContent = tag;

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'px-1 rounded-xl bg-[#ecda8a] text-red-500 hover:text-red-700 text-xl';
            btn.textContent = '×';
            btn.addEventListener('click', () => window.removeTag(tag));

            block.appendChild(span);
            block.appendChild(btn);
            filterBlocks.appendChild(block);
        });
    }

    window.removeTag = function (tagToRemove) {
        selectedTags = selectedTags.filter((tag) => tag !== tagToRemove);
        selectedTagsInput.value = selectedTags.join(',');
        const checkbox = tagModal.querySelector(`input[value="${tagToRemove}"]`);
        if (checkbox) checkbox.checked = false;
        updateFilterBlocks();
    };

    if (openModalBtn) {
        openModalBtn.addEventListener('click', () => {
            const currentValue = selectedTagsInput.value;
            selectedTags = currentValue ? currentValue.split(',').filter((t) => t.trim()) : [];
            tagModal.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
                cb.checked = selectedTags.includes(cb.value);
            });
            tagModal.classList.remove('hidden');
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => tagModal.classList.add('hidden'));
    }

    if (saveTagsBtn) {
        saveTagsBtn.addEventListener('click', () => {
            const checkboxes = tagModal.querySelectorAll('input[type="checkbox"]:checked');
            const newTags = Array.from(checkboxes).map((cb) => cb.value);
            
            if (newTags.length > 7) {
                alert('Максимум 7 тегів дозволено!');
                return;
            }
            
            selectedTags = [...new Set(newTags)];
            selectedTagsInput.value = selectedTags.join(',');
            updateFilterBlocks();
            tagModal.classList.add('hidden');
        });
    }

    // ==========================================
    // 3. ЛОГІКА ЛОКАЦІЙ (AJAX)
    // ==========================================
    const countrySelect = document.getElementById('id_country');
    const regionSelect = document.getElementById('id_region');
    const citySelect = document.getElementById('id_city');

    function resetSelect(select, placeholder) {
        if (!select) return;
        select.innerHTML = '';
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = placeholder;
        select.appendChild(opt);
        select.disabled = true;
    }

    if (countrySelect) {
        countrySelect.addEventListener('change', function () {
            const countryId = this.value;
            resetSelect(regionSelect, '---------');
            resetSelect(citySelect, '---------');

            if (countryId) {
                fetch(`/geo/api/locations/?country_id=${countryId}`)
                    .then((res) => res.json())
                    .then((data) => {
                        data.forEach((item) => regionSelect.add(new Option(item.name, item.id)));
                        regionSelect.disabled = false;
                    });
            }
        });
    }

    if (regionSelect) {
        regionSelect.addEventListener('change', function () {
            const regionId = this.value;
            resetSelect(citySelect, '---------');

            if (regionId) {
                fetch(`/geo/api/locations/?region_id=${regionId}`)
                    .then((res) => res.json())
                    .then((data) => {
                        data.forEach((item) => citySelect.add(new Option(item.name, item.id)));
                        citySelect.disabled = false;
                    });
            }
        });
    }

    // Ініціалізація тегів при завантаженні сторінки (для режиму редагування)
    if (selectedTagsInput && selectedTagsInput.value) {
        selectedTags = selectedTagsInput.value.split(',').filter(t => t.trim());
        updateFilterBlocks();
    }
});