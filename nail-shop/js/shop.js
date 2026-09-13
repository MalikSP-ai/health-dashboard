(function () {
  const state = {
    category: 'all',
    sizes: new Set(),
    colors: new Set(),
    price: 2000,
    sort: 'new'
  };

  const params = new URLSearchParams(location.search);
  if (params.get('category')) state.category = params.get('category');

  const grid = document.querySelector('[data-product-grid]');
  const empty = document.querySelector('[data-empty]');
  const count = document.querySelector('[data-result-count]');
  const priceOut = document.querySelector('[data-price-out]');

  function applyFilters() {
    let list = window.PRODUCTS.filter(p => {
      if (state.category !== 'all' && p.category !== state.category) return false;
      if (state.sizes.size && !p.sizes.some(s => state.sizes.has(s))) return false;
      if (state.colors.size && !p.colors.some(c => state.colors.has(c))) return false;
      if (p.price > state.price) return false;
      return true;
    });

    switch (state.sort) {
      case 'price-asc': list.sort((a,b) => a.price - b.price); break;
      case 'price-desc': list.sort((a,b) => b.price - a.price); break;
      case 'name': list.sort((a,b) => a.name.localeCompare(b.name, 'da')); break;
      default: list.sort((a,b) => (b.isNew?1:0) - (a.isNew?1:0));
    }

    grid.innerHTML = list.map(window.productCardHTML).join('');
    count.textContent = list.length + (list.length === 1 ? ' produkt' : ' produkter');
    empty.hidden = list.length !== 0;
    grid.hidden = list.length === 0;
  }

  // Category filter
  document.querySelectorAll('[data-filter="category"] button').forEach(btn => {
    if (btn.dataset.value === state.category) {
      document.querySelectorAll('[data-filter="category"] button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-filter="category"] button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.category = btn.dataset.value;
      applyFilters();
    });
  });

  // Size + color chip filters
  ['size', 'color'].forEach(kind => {
    document.querySelectorAll(`[data-filter="${kind}"] button`).forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('active');
        const set = kind === 'size' ? state.sizes : state.colors;
        if (btn.classList.contains('active')) set.add(btn.dataset.value);
        else set.delete(btn.dataset.value);
        applyFilters();
      });
    });
  });

  // Price
  const priceInput = document.querySelector('[data-filter="price"]');
  if (priceInput) {
    priceInput.addEventListener('input', () => {
      state.price = +priceInput.value;
      priceOut.textContent = priceInput.value;
      applyFilters();
    });
  }

  // Sort
  document.querySelector('[data-sort]').addEventListener('change', (e) => {
    state.sort = e.target.value;
    applyFilters();
  });

  // Reset
  document.querySelector('[data-reset-filters]').addEventListener('click', () => {
    state.category = 'all'; state.sizes.clear(); state.colors.clear(); state.price = 2000; state.sort = 'new';
    document.querySelectorAll('.shop-filters button.active').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-filter="category"] button[data-value="all"]').classList.add('active');
    priceInput.value = 2000; priceOut.textContent = '2000';
    document.querySelector('[data-sort]').value = 'new';
    applyFilters();
  });

  applyFilters();
})();
