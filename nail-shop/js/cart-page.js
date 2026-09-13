(function () {
  const linesEl = document.querySelector('[data-cart-lines]');
  const layout = document.querySelector('[data-cart-layout]');
  const emptyEl = document.querySelector('[data-cart-empty]');

  function render() {
    const items = window.Cart.getAll();
    if (!items.length) {
      layout.hidden = true;
      emptyEl.hidden = false;
      return;
    }
    layout.hidden = false;
    emptyEl.hidden = true;

    linesEl.innerHTML = items.map(line => {
      const p = window.getProduct(line.productId);
      if (!p) return '';
      const total = p.price * line.qty;
      return `
        <article class="cart-line" data-line data-id="${p.id}" data-size="${line.size || ''}">
          <div class="thumb" style="background:${p.gradient}"></div>
          <div>
            <h4>${p.name}</h4>
            <div class="meta">${p.brand} · Str. ${line.size || 'One size'}</div>
            <div class="line-actions">
              <div class="qty-stepper">
                <button data-step="-1">–</button>
                <span data-qty>${line.qty}</span>
                <button data-step="1">+</button>
              </div>
              <button class="remove" data-remove>Fjern</button>
            </div>
          </div>
          <div class="line-total">${window.formatPrice(total)}</div>
        </article>`;
    }).join('');

    document.querySelector('[data-cart-subtotal]').textContent = window.formatPrice(window.Cart.subtotal());
    document.querySelector('[data-cart-shipping]').textContent =
      window.Cart.shipping() === 0 ? 'Gratis' : window.formatPrice(window.Cart.shipping());
    document.querySelector('[data-cart-total]').textContent = window.formatPrice(window.Cart.total());

    linesEl.querySelectorAll('[data-line]').forEach(el => {
      const id = el.dataset.id;
      const size = el.dataset.size || null;
      el.querySelectorAll('[data-step]').forEach(btn => {
        btn.addEventListener('click', () => {
          const current = window.Cart.getAll().find(l => l.productId === id && (l.size || null) === size);
          if (!current) return;
          window.Cart.setQty(id, size, current.qty + Number(btn.dataset.step));
        });
      });
      el.querySelector('[data-remove]').addEventListener('click', () => {
        window.Cart.remove(id, size);
      });
    });
  }

  document.querySelector('[data-checkout]').addEventListener('click', () => {
    if (!window.Cart.getAll().length) return;
    window.showToast('Til betaling — dette er en demo 🌸');
  });

  window.addEventListener('cart:change', render);
  render();
})();
