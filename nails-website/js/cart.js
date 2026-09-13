// localStorage-baseret kurv-håndtering
(function () {
  const KEY = 'rose-nails-cart';

  const read = () => {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch { return []; }
  };
  const write = (items) => {
    localStorage.setItem(KEY, JSON.stringify(items));
    updateCartBadge();
    window.dispatchEvent(new CustomEvent('cart:change'));
  };

  const updateCartBadge = () => {
    const count = read().reduce((s, l) => s + l.qty, 0);
    document.querySelectorAll('[data-cart-count]').forEach(el => {
      el.textContent = count;
      el.style.display = count > 0 ? '' : 'none';
    });
  };

  window.Cart = {
    getAll: read,
    add(productId, size, qty = 1) {
      const items = read();
      const key = productId + '|' + (size || '');
      const existing = items.find(l => (l.productId + '|' + (l.size || '')) === key);
      if (existing) existing.qty += qty;
      else items.push({ productId, size: size || null, qty });
      write(items);
    },
    setQty(productId, size, qty) {
      const items = read();
      const line = items.find(l => l.productId === productId && (l.size || null) === (size || null));
      if (!line) return;
      line.qty = Math.max(1, qty);
      write(items);
    },
    remove(productId, size) {
      write(read().filter(l => !(l.productId === productId && (l.size || null) === (size || null))));
    },
    clear() { write([]); },
    subtotal() {
      const items = read();
      return items.reduce((sum, l) => {
        const p = window.getProduct(l.productId);
        return sum + (p ? p.price * l.qty : 0);
      }, 0);
    },
    shipping() {
      return this.subtotal() >= 499 || this.subtotal() === 0 ? 0 : 39;
    },
    total() { return this.subtotal() + this.shipping(); }
  };

  document.addEventListener('DOMContentLoaded', updateCartBadge);
})();

// Toast helper
window.showToast = (msg) => {
  let t = document.querySelector('.toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  requestAnimationFrame(() => t.classList.add('show'));
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => t.classList.remove('show'), 2400);
};
