const mobileNav = document.querySelector("#mobile-nav");
const hamburger = document.querySelector("#hamburger")
const cross = document.querySelector("#cross");

hamburger.addEventListener('click', () => {
    mobileNav.style.display = "block";
    hamburger.style.display = "none";
    cross.style.display = "inline";
});

cross.addEventListener('click', () => {
    mobileNav.style.display = "none";
    hamburger.style.display = "inline";
    cross.style.display = "none";
});

// hide mobile nav on window re-size
window.addEventListener('resize', () => {
    if (window.innerWidth > 1040) {
        hamburger.style.display = "none";
    } else {
        hamburger.style.display = "inline";
    }
    mobileNav.style.display = "none";
    cross.style.display = "none";
});

// hide mobile nav when clicking outside of it
window.addEventListener('click', (e) => {
    if (window.innerWidth < 1040 && e.target != hamburger && e.target != mobileNav && e.target.className != 'nav') {
        mobileNav.style.display = "none";
        cross.style.display = "none";
        hamburger.style.display = "inline";
        console.log(e.target)
    }
});