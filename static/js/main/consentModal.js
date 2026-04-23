function toggleModal() {
    const modal = document.getElementById('consentModal');
    // .classList.toggle дозволяє або додати клас 'hidden', або прибрати його
    // Якщо він є — вікно зникне, якщо немає — з'явиться
    modal.classList.toggle('hidden');
}