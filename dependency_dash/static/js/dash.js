// Change the navbar label to the page title
const navbar = document.querySelector('.navbar.fixed-top');
window.onscroll = () => {
    if (window.scrollY > 200) {
        navbar.classList.add('nav-scrolled');
    } else {
        navbar.classList.remove('nav-scrolled');
    }
};
