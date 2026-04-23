document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggleActions');
  const actionsMenu = document.getElementById('actionsMenu');
  
  if (toggleBtn && actionsMenu) {
    toggleBtn.addEventListener('click', () => {
      actionsMenu.classList.toggle('show');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!toggleBtn.contains(e.target) && !actionsMenu.contains(e.target)) {
        actionsMenu.classList.remove('show');
      }
    });
  }
});