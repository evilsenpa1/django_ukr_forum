document.addEventListener('DOMContentLoaded', function() {
    // 1. Елементи форми
    const countrySelect = document.getElementById('id_country');
    const regionSelect = document.getElementById('id_region');
    const citySelect = document.getElementById('id_city');

    // 2. Hidden поля (Додано нові для валюти)
    const countryNameHidden = document.getElementById('country_name_hidden');
    const currencyCodeHidden = document.getElementById('currency_code_hidden'); // Нове
    const currencySymbolHidden = document.getElementById('currency_symbol_hidden'); // Нове
    
    const regionNameHidden = document.getElementById('region_name_hidden');
    const cityNameHidden = document.getElementById('city_name_hidden');
    const cityApiIdHidden = document.getElementById('city_api_id_hidden');
    const latitudeHidden = document.getElementById('latitude_hidden');
    const longitudeHidden = document.getElementById('longitude_hidden');

    const resetSelect = (select, text) => {
        select.innerHTML = '';
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = text;
        select.appendChild(opt);
    };

    function loadCountries() {
        resetSelect(countrySelect, "Завантаження країн...");
        fetch('/geo/ajax/proxy/countries/')
            .then(res => res.json())
            .then(data => {
                resetSelect(countrySelect, "Оберіть країну");
                data.forEach(item => {
                    const option = new Option(item.name, item.iso2);
                    option.dataset.name = item.name;
                    countrySelect.add(option);
                });
            })
            .catch(err => console.error("Помилка країн:", err));
    }
    loadCountries();

    // --- КРОК 2: Вибір країни -> Завантаження деталей (валюти) та регіонів ---
    countrySelect.addEventListener('change', function() {
        const countryIso = this.value;
        const selectedOption = this.options[this.selectedIndex];
        
        // Очищуємо поля, якщо країну скинули
        if (!countryIso) {
                if (countryNameHidden) countryNameHidden.value = '';
                resetSelect(regionSelect, "Оберіть країну");
                resetSelect(citySelect, "Спочатку оберіть регіон");
                return; 
            }
        // 2.1 Отримуємо назву країни
        if (countryNameHidden && selectedOption) {
            countryNameHidden.value = selectedOption.dataset.name;
        }

        // 2.2 НОВЕ: Запит детальної інформації про країну (валюта)
        // Використовуємо твій проксі, щоб отримати деталі конкретної країни
        fetch(`/geo/ajax/proxy/countries/${countryIso}/`) 
            .then(res => res.json())
            .then(data => {
                if (currencyCodeHidden) currencyCodeHidden.value = data.currency || '';
                if (currencySymbolHidden) currencySymbolHidden.value = data.currency_symbol || '';
                console.log(`Валюта: ${data.currency}, Символ: ${data.currency_symbol}`);
            })
            .catch(err => console.error("Помилка деталей країни:", err));

        // 2.3 Завантаження регіонів (залишається без змін)
        resetSelect(regionSelect, "Завантаження регіонів...");
        resetSelect(citySelect, "Спочатку оберіть регіон");

        fetch(`/geo/ajax/load-regions/?country_code=${countryIso}`)
            .then(res => res.json())
            .then(data => {
                resetSelect(regionSelect, "Оберіть регіон");
                data.forEach(item => {
                    const option = new Option(item.name, item.iso2);
                    option.dataset.name = item.name;
                    regionSelect.add(option);
                });
            });
    });

    // --- КРОК 3 та КРОК 4 залишаються без змін ---
    regionSelect.addEventListener('change', function() {
        const stateCode = this.value;
        const countryIso = countrySelect.value;
        const selectedOption = this.options[this.selectedIndex];

        if (regionNameHidden && selectedOption) {
            regionNameHidden.value = selectedOption.dataset.name;
        }

        resetSelect(citySelect, "Завантаження міст...");
        if (!stateCode) return;

        fetch(`/geo/ajax/load-cities/?country_code=${countryIso}&state_code=${stateCode}`)
            .then(res => res.json())
            .then(data => {
                resetSelect(citySelect, "Оберіть місто");
                data.forEach(item => {
                    const option = new Option(item.name, item.name);
                    option.dataset.apiId = item.id;
                    option.dataset.lat = item.latitude;
                    option.dataset.lng = item.longitude;
                    citySelect.add(option);
                });
            });
    });

    citySelect.addEventListener('change', function() {
        const opt = this.options[this.selectedIndex];
        if (opt && cityNameHidden) {
            cityNameHidden.value = opt.value;
            cityApiIdHidden.value = opt.dataset.apiId || '';
            latitudeHidden.value = opt.dataset.lat || '';
            longitudeHidden.value = opt.dataset.lng || '';
        }
    });

    // Автозавантаження, якщо значення вже є (режим редагування)
if (countrySelect && countrySelect.value) {
    countrySelect.dispatchEvent(new Event('change'));
}
});