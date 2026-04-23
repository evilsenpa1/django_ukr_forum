let map;
let marker;
let geocoder;

/**
 * Ініціалізація карти. Викликається автоматично Google Maps SDK.
 */
function initMap() {
    // 1. Об'єкт для перетворення координат у назву адреси (і навпаки)
    geocoder = new google.maps.Geocoder();
    
    // 2. Початкові координати (Центр України або координати з бази, якщо редагуємо)
    const latInput = document.getElementById("id_place_lat");
    const lngInput = document.getElementById("id_place_lng");
    
    const initialPos = { 
        lat: latInput.value ? parseFloat(latInput.value) : 48.3794, 
        lng: lngInput.value ? parseFloat(lngInput.value) : 31.1656 
    };

    // 3. Створення самої карти
    map = new google.maps.Map(document.getElementById("map"), {
        center: initialPos,
        zoom: latInput.value ? 15 : 6, // Якщо точка вже є — зумимо ближче
        mapTypeControl: false, // Прибираємо зайві кнопки для чистоти інтерфейсу
    });

    // 4. Створення маркера
    marker = new google.maps.Marker({
        position: initialPos,
        map: map,
        draggable: true, // Дозволяємо користувачу перетягувати маркер пальцем/мишкою
        visible: latInput.value ? true : false // Ховаємо, якщо точки ще немає
    });

    // --- СЛУХАЧІ ПОДІЙ (Events) ---

    // А. Клік по карті: ставимо маркер там, де натиснули
    map.addListener("click", (e) => {
        updateMarkerAndFields(e.latLng);
    });

    // Б. Закінчення перетягування маркера: оновлюємо координати
    marker.addListener("dragend", () => {
        updateMarkerAndFields(marker.getPosition());
    });

    // В. Автозаповнення назв (Google Places Autocomplete)
    const searchInput = document.getElementById("id_local_place_search");
    if (searchInput) {
        const autocomplete = new google.maps.places.Autocomplete(searchInput);
        
        autocomplete.addListener("place_changed", () => {
            const place = autocomplete.getPlace();
            if (!place.geometry || !place.geometry.location) return;

            map.setCenter(place.geometry.location);
            map.setZoom(17);
            updateMarkerAndFields(place.geometry.location, place);
        });
    }
}

/**
 * Функція для оновлення маркеру та запису даних у приховані поля Django форми
 */
function updateMarkerAndFields(latLng, place = null) {
    // Показуємо і переміщуємо маркер
    marker.setPosition(latLng);
    marker.setVisible(true);
    
    // Записуємо широту та довготу в приховані поля
    document.getElementById("id_place_lat").value = latLng.lat();
    document.getElementById("id_place_lng").value = latLng.lng();

    // Якщо ми вибрали заклад через Пошук (Autocomplete)
    if (place) {
        document.getElementById("id_place_id").value = place.place_id || "";
        document.getElementById("id_place_name").value = place.name || place.formatted_address;
    } else {
        // Якщо просто клікнули на карту — запитуємо у Google адресу цієї точки (Reverse Geocoding)
        geocoder.geocode({ location: latLng }, (results, status) => {
            if (status === "OK" && results[0]) {
                const address = results[0].formatted_address;
                document.getElementById("id_place_id").value = ""; // Очищуємо ID закладу, бо це довільна точка
                document.getElementById("id_place_name").value = address;
                
                // Також вписуємо адресу в поле пошуку для візуального підтвердження
                const searchInput = document.getElementById("id_local_place_search");
                if (searchInput) searchInput.value = address;
            }
        });
    }
}