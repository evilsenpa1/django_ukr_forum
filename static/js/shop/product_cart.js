//=============== ПОЧАТОК модального вікна контактів ===================
function customAlert(message) {
  return new Promise(resolve => {
    const overlay = document.createElement("div");
    overlay.className = "overlay";

    const box = document.createElement("div");
    box.className = "box";

    const title = document.createElement("h3");
    const titleBold = document.createElement("b");
    titleBold.textContent = "Контакти користувача";
    title.append(titleBold);

    box.append(title);

    const fields = [
      "Телефон",
      "Telegram",
      "WhatsApp",
      "Viber",
      "Email",
    ];

    fields.forEach(label => {
      const p = document.createElement("p");
      p.textContent = `${label}: ${message}`;
      box.append(p);
    });

    const button = document.createElement("button");
    button.textContent = "OK";
    button.onclick = () => {
      overlay.remove();
      resolve();
    };

    box.append(button);
    overlay.append(box);
    document.body.append(overlay);

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.remove();
        resolve();
      }
    });
  });
}

// Обробник кнопки "Зв'язок"
document.addEventListener('DOMContentLoaded', function () {
  const contactBtn = document.getElementById('contact');
  if (contactBtn) {
    contactBtn.addEventListener('click', function() {
      // Тут ви можете отримати реальні дані користувача
      customAlert('[дані користувача]');
    });
  }
});
//=============== КІНЕЦЬ модального вікна контактів ===================


//=============== ПОЧАТОК каруселі ===================
document.addEventListener('DOMContentLoaded', function () {
    let currentIndex = 0;
    const images = Array.from(document.querySelectorAll('.carousel-img'));
    const thumbnails = Array.from(document.querySelectorAll('.thumbnail'));
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    // Якщо зображень немає — нічого не робимо
    if (!images.length) return;

    // Функція показу певного зображення
    function showImage(index) {
        if (index < 0) index = images.length - 1;
        if (index >= images.length) index = 0;

        // Оновлюємо відображення зображень
        images.forEach((img, i) => {
            img.classList.remove('opacity-100', 'z-10');
            img.classList.add('opacity-0', 'z-0');
            if (i === index) {
                img.classList.add('opacity-100', 'z-10');
                img.classList.remove('opacity-0', 'z-0');
            }
        });

        // Оновлюємо активну мініатюру
        thumbnails.forEach((thumb, i) => {
            if (i === index) {
                thumb.classList.add('active', 'border-blue-500');
                thumb.classList.remove('border-transparent');
            } else {
                thumb.classList.remove('active', 'border-blue-500');
                thumb.classList.add('border-transparent');
            }
        });

        currentIndex = index;
    }

    // Наступне/попереднє зображення
    function nextImage() {
        showImage((currentIndex + 1) % images.length);
    }

    function prevImage() {
        showImage((currentIndex - 1 + images.length) % images.length);
    }

    // Клік по мініатюрі
    thumbnails.forEach((thumb, index) => {
        thumb.addEventListener('click', () => showImage(index));
    });

    // Клік по кнопках
    if (prevBtn) prevBtn.addEventListener('click', prevImage);
    if (nextBtn) nextBtn.addEventListener('click', nextImage);

    // Початковий стан (показуємо перше зображення)
    showImage(0);
});
//=============== КІНЕЦЬ каруселі ===================