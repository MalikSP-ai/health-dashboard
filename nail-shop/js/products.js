// Nails webshop — mest tøj, lidt sneakers og accessories.
// Billeder er CSS-gradienter, så alt kører uden eksterne assets.
window.PRODUCTS = [
  {
    id: "hoodie-lime-logo",
    name: "Signature Hoodie — Acid Lime",
    brand: "NAIL 001",
    category: "hoodies",
    price: 599, oldPrice: 749, isNew: true, onSale: true,
    colors: ["Lime", "Sort", "Grå"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #D8FF3D 0%, #A6C82F 70%, #6B8020 100%)",
    description: "Tung 400 gsm hoodie med drop shoulder og broderet NAIL-logo på brystet. Lavet til at holde længere end en sæson.",
    material: "400 gsm børstet bomuld, økologisk dyrket i Portugal.",
    fit: "Oversize. Tag din normale størrelse — én ned hvis du vil have en cleaner fit."
  },
  {
    id: "hoodie-black-basic",
    name: "Everyday Hoodie",
    brand: "NAIL 002",
    category: "hoodies",
    price: 449,
    colors: ["Sort", "Grå", "Beige"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #2a2a2a, #0e0e10)",
    description: "Den blank hoodie du bruger tre gange om ugen. Uden logoer, uden bullshit.",
    material: "320 gsm bomuld/polyester.",
    fit: "Regular. Passer normal størrelse."
  },
  {
    id: "hoodie-zip-orange",
    name: "Zip Hoodie — Safety Orange",
    brand: "NAIL 003",
    category: "hoodies",
    price: 649, isNew: true,
    colors: ["Orange", "Sort"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #FF4A1C, #B22F0F)",
    description: "Fuld zip med YKK-lynlås og kænguru-lommer. High-vis når du vil ses.",
    material: "380 gsm børstet bomuld.",
    fit: "Regular. Ærmerne er lange med tommelfingerhuller."
  },
  {
    id: "tee-graphic-white",
    name: "Graphic Tee — Signature",
    brand: "NAIL 001",
    category: "tees",
    price: 249, oldPrice: 299, onSale: true,
    colors: ["Hvid", "Sort"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #F5F3EE, #C6BFAE)",
    description: "Tung boxy tee med screenprint. Vasket for at føles brugt fra dag ét.",
    material: "220 gsm bomuld, garvet.",
    fit: "Boxy. Kort til bæltet, bredt over skuldrene."
  },
  {
    id: "tee-black-basic",
    name: "Blank Tee",
    brand: "NAIL 002",
    category: "tees",
    price: 179,
    colors: ["Sort", "Hvid", "Beige"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #1a1a1a, #0e0e10)",
    description: "Tung blank tee. Sælges også i pakker á tre — spørg mig.",
    material: "240 gsm ringspun bomuld.",
    fit: "Regular. Passer normal størrelse."
  },
  {
    id: "tee-long-sleeve",
    name: "Long Sleeve — Nail Print",
    brand: "NAIL 001",
    category: "tees",
    price: 299, isNew: true,
    colors: ["Hvid", "Sort"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #ffffff, #e0e0e0)",
    description: "Layer alene eller under en hoodie. Print på ryg og ærmer.",
    material: "200 gsm bomuld.",
    fit: "Regular. Lang i kroppen."
  },
  {
    id: "bukser-cargo-black",
    name: "Cargo Pants — Wide Leg",
    brand: "NAIL 004",
    category: "bukser",
    price: 799, isNew: true,
    colors: ["Sort", "Grøn", "Beige"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #2a2a2a, #0e0e10)",
    description: "Wide leg cargos med seks lommer og elastik i taljen. Streetwear-basic.",
    material: "100% bomuldstwill.",
    fit: "Wide leg. Baggy over hoften."
  },
  {
    id: "bukser-jeans-baggy",
    name: "Baggy Jeans — Washed Blue",
    brand: "NAIL 004",
    category: "bukser",
    price: 649, oldPrice: 799, onSale: true,
    colors: ["Blå"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #7C9EFF, #2C5DBF)",
    description: "Vintage-vasket baggy jeans med raw hem.",
    material: "100% bomuldsdenim, 14 oz.",
    fit: "Højtaljet, løs i låret."
  },
  {
    id: "bukser-joggers-grey",
    name: "Sweatpants — Grey Melange",
    brand: "NAIL 002",
    category: "bukser",
    price: 449,
    colors: ["Grå", "Sort"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #999999, #555555)",
    description: "Matcher hoodien. Elastik i talje og ben.",
    material: "400 gsm bomuld/polyester.",
    fit: "Regular. Ret smal fra knæet og ned."
  },
  {
    id: "jakke-puffer",
    name: "Puffer Jakke — Sort",
    brand: "NAIL 005",
    category: "jakker",
    price: 1499, isNew: true,
    colors: ["Sort", "Beige"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #333, #0e0e10)",
    description: "Overdimensioneret puffer med YKK-lynlås. Genanvendt fyld.",
    material: "100% genanvendt polyester ydre, genanvendt fyld.",
    fit: "Oversize. Går ned til hoften."
  },
  {
    id: "jakke-varsity",
    name: "Varsity Jakke",
    brand: "NAIL 005",
    category: "jakker",
    price: 1299,
    colors: ["Sort", "Grøn"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #0e0e10 60%, #D8FF3D 60%)",
    description: "Klassisk letterman med uld-krop og læder-ærmer. Broderet NAIL på brystet.",
    material: "Uld-blend, PU-læder ærmer.",
    fit: "Regular. Passer normal størrelse."
  },
  {
    id: "jakke-workwear",
    name: "Workwear Jakke",
    brand: "NAIL 005",
    category: "jakker",
    price: 999, oldPrice: 1249, onSale: true,
    colors: ["Beige", "Sort"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #C6BFAE, #6E6A63)",
    description: "Chore coat-inspireret jakke i canvas med fire store lommer.",
    material: "100% bomuldscanvas.",
    fit: "Regular. Plads til en hoodie under."
  },
  {
    id: "cap-trucker",
    name: "Trucker Cap — Lime Panel",
    brand: "NAIL 006",
    category: "caps",
    price: 249, isNew: true,
    colors: ["Lime", "Sort", "Orange"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #D8FF3D, #6B8020)",
    description: "Mesh-back trucker med broderet logo på front.",
    material: "Bomuldsfront, polyester-mesh bagpå.",
    fit: "Snapback. One size."
  },
  {
    id: "cap-beanie",
    name: "Ribbed Beanie",
    brand: "NAIL 006",
    category: "caps",
    price: 199,
    colors: ["Sort", "Grå", "Beige"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #2a2a2a, #0e0e10)",
    description: "Rib-strikket beanie med kanvas-tag på siden.",
    material: "100% akryl.",
    fit: "One size."
  },
  {
    id: "acc-taske",
    name: "Cross Body Bag",
    brand: "NAIL 007",
    category: "caps",
    price: 349,
    colors: ["Sort", "Orange"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #FF4A1C, #B22F0F)",
    description: "Kompakt crossbody med hovedrum og forlomme. Justerbar rem.",
    material: "Genanvendt nylon.",
    fit: "One size. Rummer telefon, nøgler, pung."
  },
  {
    id: "sko-runner",
    name: "Runner Sneakers",
    brand: "NAIL 008",
    category: "sko",
    price: 899, isNew: true,
    colors: ["Sort", "Hvid"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #E1B8FF, #7C4CB0)",
    description: "Chunky runner med mesh-overdel og EVA-sål. Bygget til daglig brug.",
    material: "Mesh, syntetisk overdel, EVA-sål.",
    fit: "Passer normal størrelse."
  },
  {
    id: "sko-court",
    name: "Court Sneakers — Hvid",
    brand: "NAIL 008",
    category: "sko",
    price: 699, oldPrice: 899, onSale: true,
    colors: ["Hvid"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #ffffff, #d6d2c7)",
    description: "Rene lave court sneakers. Klassisk silhouette.",
    material: "Læder overdel, gummisål.",
    fit: "Passer normal størrelse."
  },
  {
    id: "shirt-flannel",
    name: "Flannel Overshirt",
    brand: "NAIL 003",
    category: "hoodies",
    price: 549,
    colors: ["Rød", "Grøn", "Blå"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #7fa07a, #3e5c3a)",
    description: "Ternet flannel med brystlommer. Sidder som en let jakke.",
    material: "Børstet bomuldsflannel.",
    fit: "Oversize. Plads til at layere."
  }
];

window.getProduct = (id) => window.PRODUCTS.find(p => p.id === id);
window.getRelated = (id, limit=4) => {
  const p = window.getProduct(id);
  if (!p) return [];
  return window.PRODUCTS.filter(x => x.id !== id && x.category === p.category).slice(0, limit);
};

window.formatPrice = (n) => new Intl.NumberFormat('da-DK').format(n) + ' kr.';

// Kort SKU-agtig kode fra id — pynt der antyder produktion/serie
window.productSKU = (p) => (p.brand.replace(/\D/g,'') || '00') + '-' + p.id.slice(0,3).toUpperCase();

window.productCardHTML = (p) => {
  const badge = p.onSale ? '<span class="badge sale">Sale</span>'
              : p.isNew  ? '<span class="badge new">New</span>' : '';
  const oldPrice = p.oldPrice ? `<span class="old-price">${window.formatPrice(p.oldPrice)}</span>` : '';
  return `
    <a class="product-card" href="product.html?id=${p.id}">
      <div class="thumb" style="background:${p.gradient}">
        ${badge}
        <span class="sku">${window.productSKU(p)}</span>
      </div>
      <div class="info">
        <span class="brand-line">${p.brand}</span>
        <h3>${p.name}</h3>
        <div class="price-row">
          <span class="price">${window.formatPrice(p.price)}</span>
          ${oldPrice}
        </div>
      </div>
    </a>`;
};
