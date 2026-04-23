// Логіка видалення фото з можливістю скасування
window.markMediaForDelete = function (mediaId) {
    const deleteInput = document.getElementById('deleteMediaInput');
    const mediaBlock = document.getElementById(`media-item-${mediaId}`);
    if (!deleteInput || !mediaBlock) return;

    let currentIds = deleteInput.value ? deleteInput.value.split(',') : [];

    if (!currentIds.includes(mediaId.toString())) {
        // ДОДАЄМО ДО СПИСКУ НА ВИДАЛЕННЯ
        currentIds.push(mediaId.toString());
        
        mediaBlock.style.opacity = '0.5';
        mediaBlock.classList.add('border-red-500', 'border-2');
        
        const btn = mediaBlock.querySelector('button');
        btn.innerHTML = '↺'; // Символ повернення
        btn.title = "Скасувати видалення";
    } else {
        // ВИДАЛЯЄМО ЗІ СПИСКУ (СКАСУВАННЯ)
        currentIds = currentIds.filter(id => id !== mediaId.toString());
        
        mediaBlock.style.opacity = '1';
        mediaBlock.classList.remove('border-red-500', 'border-2');
        
        const btn = mediaBlock.querySelector('button');
        btn.innerHTML = '×';
        btn.title = "Видалити";
    }

    deleteInput.value = currentIds.join(',');
};

