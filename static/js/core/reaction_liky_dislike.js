// Функція для отримання CSRF токена з cookies
function getCookie(name) {
    let cookieValue = null; // початково значення відсутнє
    document.cookie.split(';').forEach(cookie => {
        cookie = cookie.trim(); // видаляємо пробіли
        if (cookie.startsWith(name + '=')) { // якщо cookie починається з 'csrftoken='
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1)); 
            // беремо значення токена
        }
    });
    return cookieValue; // повертаємо токен
}

// Знаходимо всі блоки з класом .reaction
document.querySelectorAll('.reaction').forEach((block) => {

    // Для кожного блоку знаходимо кнопки like/dislike
    block.querySelectorAll('.reaction-btn').forEach((btn) => {

        // Коли користувач клікає на кнопку
        btn.onclick = () => {

            // Отримуємо ID об'єкта (article, comment, і т.д.)
            const objectId = block.dataset.objectId;
            // Отримуємо ContentType ID (для визначення типу моделі)
            const contentType = block.dataset.contentType;
            // Беремо CSRF токен для POST запиту
            const csrftoken = getCookie('csrftoken');

            // Відправляємо POST запит на сервер
            fetch('/reaction/toggle/', {
                method: 'POST', // метод POST
                headers: {
                    'X-CSRFToken': csrftoken, // CSRF токен
                    'Content-Type': 'application/x-www-form-urlencoded', // формат даних
                },
                // Тіло запиту: id об'єкта, тип, та реакція
                body: new URLSearchParams({
                    object_id: objectId,
                    content_type: contentType,
                    reaction: btn.dataset.reaction, // "like" або "dislike"
                }),
            })
            // Отримуємо відповідь сервера у форматі JSON
            .then((res) => res.json())
            .then((data) => {
                // Перевіряємо, чи є дані likes/dislikes
                if (typeof data.likes === 'number') {
                    // Оновлюємо елементи на сторінці
                    block.querySelector('.like-count').innerText = data.likes;
                    block.querySelector('.dislike-count').innerText = data.dislikes;

                    // оновлюємо таблицю
                    document.querySelectorAll(`.like-count-cell[data-object-id="${objectId}"]`).forEach(cell=>{
                        cell.textContent = data.likes;
                    });
                    document.querySelectorAll(`.dislike-count-cell[data-object-id="${objectId}"]`).forEach(cell=>{
                        cell.textContent = data.dislikes;
                    });
                }
            });
        };
    });
});
