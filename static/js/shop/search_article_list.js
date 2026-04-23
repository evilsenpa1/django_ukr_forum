// ==========================================
// 1. ІНІЦІАЛІЗАЦІЯ ТЕГІВ ТА ПАРАМЕТРІВ З URL
// ==========================================
const urlParams = new URLSearchParams(window.location.search);
const tagsFromUrl = urlParams.get('tags');
let selectedTags = tagsFromUrl ? tagsFromUrl.split(',').filter(t => t !== "") : [];

// ==========================================
// 2. ГЕО-ЛОГІКА (КРАЇНА, РЕГІОН, МІСТО)
// ==========================================

// Функція для завантаження при КЛІКУ (з перезавантаженням сторінки)
async function loadGeoData(target) {
    const countrySelect = document.getElementById('country-select');
    const regionSelect = document.getElementById('region-select');
    const citySelect = document.getElementById('city-select');

    // КЛЮЧОВИЙ МОМЕНТ: Якщо ми змінили вищий рівень, 
    // ми ОБНУЛЯЄМО значення в елементах нижчого рівня
    if (target === 'region') { // target='region' означає, що змінили КРАЇНУ
        if (regionSelect) regionSelect.value = "";
        if (citySelect) citySelect.value = "";
    } 
    else if (target === 'city') { // target='city' означає, що змінили РЕГІОН
        if (citySelect) citySelect.value = "";
    }

    // Тепер applyFilters зчитає вже порожні значення для непотрібних параметрів
    applyFilters();
}

// Функція "тихого" завантаження при СТАРТІ (без перезавантаження)
async function initGeoData(target, parentId, currentChildId) {
    if (!parentId) return;
    
    let url = '';
    if (target === 'region') url = `/geo/api/locations/?country_id=${parentId}`;
    if (target === 'city') url = `/geo/api/locations/?region_id=${parentId}`;

    if (url) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            const select = document.getElementById(`${target}-select`);
            
            if (select) {
                select.innerHTML = `<option value="">Оберіть ${target === 'region' ? 'регіон' : 'місто'}</option>`;
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = item.name;
                    if (item.id.toString() === currentChildId) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
                select.disabled = false;

                if (target === 'region' && currentChildId) {
                    const cityId = urlParams.get('city');
                    initGeoData('city', currentChildId, cityId);
                }
            }
        } catch (e) {
            console.error("❌ Помилка завантаження API:", e);
        }
    }
}

// ==========================================
// 3. ФУНКЦІЇ ТЕГІВ ТА ПОШУКУ
// ==========================================

function renderActiveTags() {
    const container = document.getElementById('active-tags-container');
    if (!container) return;
    container.innerHTML = '';
    selectedTags.forEach(tag => {
        const span = document.createElement('span');
        span.className = 'flex items-center bg-amber-200 text-amber-900 text-[10px] font-bold px-2 py-1 rounded-md border border-amber-300 shadow-sm';
        span.appendChild(document.createTextNode(tag + ' '));

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'ml-2 hover:text-red-600 transition-colors';
        btn.textContent = '✕';
        btn.addEventListener('click', () => removeTag(tag));

        span.appendChild(btn);
        container.appendChild(span);
    });
}

function addTagToFilter(tagName) {
    const cleanTagName = tagName.replace('#', '').trim();
    if (!selectedTags.includes(cleanTagName)) {
        if (selectedTags.length < 7) {
            selectedTags.push(cleanTagName);
            applyFilters();
        } else {
            alert("Максимум 7 тегів!");
        }
    }
}

function removeTag(tagToRemove) {
    selectedTags = selectedTags.filter(t => t !== tagToRemove);
    applyFilters();
}

// ==========================================
// 4. ГОЛОВНА ФУНКЦІЯ: ЗАСТОСУВАННЯ ФІЛЬТРІВ (URL)
// ==========================================

function applyFilters() {
    // Створюємо URL на основі поточного шляху без параметрів
    const url = new URL(window.location.origin + window.location.pathname);
    
    // 1. ТЕГИ
    if (selectedTags.length > 0) url.searchParams.set('tags', selectedTags.join(','));

    // 2. ПОШУК
    const searchInput = document.querySelector('input[placeholder="Пошук"]');
    if (searchInput && searchInput.value.trim() !== "") {
        url.searchParams.set('search', searchInput.value.trim());
    }

    // 3. ЛОКАЦІЯ (Ієрархічна побудова)
    const country = document.getElementById('country-select')?.value;
    const region = document.getElementById('region-select')?.value;
    const city = document.getElementById('city-select')?.value;
    
    if (country) {
        
        url.searchParams.set('country', country);
        
        // Додаємо регіон, ТІЛЬКИ якщо він вибраний
        if (region) {
            url.searchParams.set('region', region);
            
            // Додаємо місто, ТІЛЬКИ якщо вибрано регіон
            if (city) {
                url.searchParams.set('city', city);
            }
        }
    }

    url.searchParams.delete('page');
    window.location.href = url.toString();
}

// ==========================================
// 5. ЗАПУСК ПРИ ЗАВАНТАЖЕННІ
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    renderActiveTags();
    
    const countryId = urlParams.get('country');
    const regionId = urlParams.get('region');

    if (countryId) {
        initGeoData('region', countryId, regionId);
    }

    const searchInput = document.querySelector('input[placeholder="Пошук"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') applyFilters();
        });
        const sParam = urlParams.get('search');
        if (sParam) searchInput.value = sParam;
    }
});