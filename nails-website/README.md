# Rosé Nails & Style

Statisk hjemmeside til en neglesalon med indbygget tøjbutik (Zalando-lignende oplevelse).

## Kør lokalt

Åbn `index.html` direkte i browseren, eller start en simpel server:

```bash
cd nails-website
python3 -m http.server 8000
# åbn http://localhost:8000
```

## Struktur

- `index.html` — Forside med hero, kategorier, nyheder og salon-preview
- `shop.html` — Produktkatalog med filtre (kategori, størrelse, farve, pris) og sortering
- `product.html?id=…` — Produktside med farve/størrelse-valg og "Læg i kurv"
- `cart.html` — Kurv med mængde-justering og ordreoversigt
- `services.html` — Neglebehandlinger med priser
- `booking.html` — Bookingformular
- `about.html` — Om salonen og teamet
- `css/styles.css` — Design system (roséfarver, Playfair + Inter)
- `js/products.js` — Produktkatalog (18 varer på tværs af 6 kategorier)
- `js/cart.js` — Kurv-logik (localStorage)
- `js/shop.js` — Filtre og sortering
- `js/product.js` — Produktside
- `js/cart-page.js` — Kurv-side
- `js/main.js` — Fælles UI (mobil-menu, nyheder på forsiden)

## Funktioner

- Fuldt responsivt design (desktop, tablet, mobil)
- Kurv persisterer via `localStorage`
- Filtrering på kategori, størrelse, farve, pris + 4 sorteringer
- Deep-linking til kategorier via `?category=`
- Fri fragt beregnes automatisk over 499 kr.
