(function () {
  // Mobil-menu toggle
  const btn = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  if (btn && nav) {
    btn.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open);
    });
  }

  // Featured products på forsiden (viser 4 nyheder)
  const featured = document.querySelector('[data-featured-products]');
  if (featured && window.PRODUCTS) {
    const items = window.PRODUCTS.filter(p => p.isNew).slice(0, 4);
    featured.innerHTML = items.map(window.productCardHTML).join('');
  }
})();
