# NAIL

Nails webshop — statisk hjemmeside til teen-entreprenøren Nail, der sælger streetwear
(hoodies, tees, jeans, sneakers m.m.) med en Zalando-lignende shop-oplevelse.

## Kør lokalt

```bash
cd nail-shop
python3 -m http.server 8000
# åbn http://localhost:8000
```

## Sider

- `index.html` — Forside med hero (Drop 01), kategorier, nyheder og "Om Nail"
- `shop.html` — Produktkatalog med filtre (kategori, størrelse, farve, pris) + sortering
- `product.html?id=…` — Produktside med farve/størrelse-valg og "Læg i kurv"
- `cart.html` — Kurv (mængde, subtotal, fri fragt over 499 kr.), gemmes i `localStorage`
- `about.html` — Nails historie, hjælpere, FAQ

## Design

- Palette: warm paper (#F1EEE7), graphite ink, electric lime (#D8FF3D) accent, safety orange (#FF4A1C) for sale-badges
- Typografi: Archivo Black (display, uppercase), Inter (body), JetBrains Mono (SKU/priser/labels)
- Layout: brutalistisk drop-culture — hårde 2px borders, offset-skygger, prikket paper-ground
- Fuldt responsivt (desktop, tablet, mobil)

## Produkter

18 varer på tværs af 6 kategorier (hoodies, tees, bukser, jakker, caps/bags, sneakers).
Priserne ligger 179-1499 kr. Produktbilleder er CSS-gradienter, så alt kører offline.
