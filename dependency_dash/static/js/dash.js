
// The top-of-page navbar
const navbar = document.querySelector('.navbar.fixed-top')
// The main "brand" button
const navbarBrand = document.querySelector('.navbar.fixed-top .navbar-brand:not(navbar-page-title)')
// The page title button
const navbarPageTitle = document.querySelector('.navbar.fixed-top .navbar-page-title')

window.onscroll = () => {
  // Change the navbar label to the page title
  if (window.scrollY > 200) {
    navbar.classList.add('nav-scrolled')
    navbarBrand.tabIndex = -1
    navbarPageTitle.removeAttribute('tabindex')
  } else {
    navbar.classList.remove('nav-scrolled')
    navbarPageTitle.tabIndex = -1
    navbarBrand.removeAttribute('tabindex')
  }
}
