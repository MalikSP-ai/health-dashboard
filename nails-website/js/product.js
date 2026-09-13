(function () {
  const id = new URLSearchParams(location.search).get('id');
  const p = id ? window.getProduct(id) : null;
  const root = document.querySelector('[data-product-detail]');

  if (!p) {
    root.innerHTML = `<div class="container"><h1>Produktet blev ikke fundet</h1>
      <p><a href="shop.html" class="link-arrow">← Tilbage til shoppen</a></p></div>`;
    return;
  }

  document.title = `${p.name} — Rosé Nails & Style`;
  document.querySelector('[data-crumb-name]').textContent = p.name;

  const oldPrice = p.oldPrice ? `<span class="old-price">${window.formatPrice(p.oldPrice)}</span>` : '';
  const sizeBtns = p.sizes.map((s,i) => `<button data-size="${s}"${i===0?' class="active"':''}>${s}</button>`).join('');
  const colorBtns = p.colors.map(c => `<span class="chip">${c}</span>`).join(' ');

  root.innerHTML = `
    <div class="container">
      <div class="pdp-gallery">
        <div class="pdp-thumbs">
          <button class="active" style="background:${p.gradient}"></button>
          <button style="background:${p.gradient};filter:hue-rotate(30deg)"></button>
          <button style="background:${p.gradient};filter:brightness(0.85)"></button>
        </div>
        <div class="pdp-main" style="background:${p.gradient}"></div>
      </div>
      <div class="pdp-info">
        <span class="brand-line">${p.brand}</span>
        <h1>${p.name}</h1>
        <div class="price-row">
          <span class="price">${window.formatPrice(p.price)}</span>
          ${oldPrice}
        </div>
        <p class="tax-note">Inkl. moms. Fri fragt over 499 kr.</p>

        <div class="pdp-block">
          <h4>Farve — <span data-color-label>${p.colors[0]}</span></h4>
          <div class="chip-row">
            ${p.colors.map((c,i) => `<button data-color="${c}"${i===0?' class="active"':''}>${c}</button>`).join('')}
          </div>
        </div>

        <div class="pdp-block">
          <h4>Størrelse</h4>
          <div class="size-picker">${sizeBtns}</div>
        </div>

        <div class="qty-row">
          <div class="qty-stepper" data-qty>
            <button data-step="-1">–</button>
            <span data-qty-value>1</span>
            <button data-step="1">+</button>
          </div>
        </div>

        <button class="btn btn-primary btn-block" data-add>Læg i kurv</button>

        <div class="pdp-block pdp-desc">
          <h4>Beskrivelse</h4>
          <p>${p.description}</p>
          <ul class="pdp-features">
            <li><span>Materiale</span><span>${p.material}</span></li>
            <li><span>Pasform</span><span>${p.fit}</span></li>
            <li><span>Levering</span><span>1–3 hverdage</span></li>
            <li><span>Retur</span><span>30 dage</span></li>
          </ul>
        </div>
      </div>
    </div>`;

  let qty = 1;
  let selectedSize = p.sizes[0];

  root.querySelectorAll('.size-picker button').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('.size-picker button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedSize = btn.dataset.size;
    });
  });

  root.querySelectorAll('[data-color]').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('[data-color]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      root.querySelector('[data-color-label]').textContent = btn.dataset.color;
    });
  });

  root.querySelectorAll('[data-qty] button').forEach(btn => {
    btn.addEventListener('click', () => {
      qty = Math.max(1, qty + Number(btn.dataset.step));
      root.querySelector('[data-qty-value]').textContent = qty;
    });
  });

  root.querySelectorAll('.pdp-thumbs button').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('.pdp-thumbs button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      root.querySelector('.pdp-main').style.background = btn.style.background;
    });
  });

  root.querySelector('[data-add]').addEventListener('click', () => {
    window.Cart.add(p.id, selectedSize, qty);
    window.showToast(`${p.name} lagt i kurv (str. ${selectedSize})`);
  });

  const related = window.getRelated(p.id, 4);
  const relatedEl = document.querySelector('[data-related-products]');
  if (relatedEl && related.length) {
    relatedEl.innerHTML = related.map(window.productCardHTML).join('');
  }
})();
