const btn =document.getElementById('menu-btn');
const menu = document.getElementById('mobale-menu');

btn.addEventListener('click',()=>{
    //Перемикаємо клас 'hidden' (приховати/показати)
    menu.classList.toggle('hidden');    
})