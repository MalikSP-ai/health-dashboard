// Produktkatalog. Billeder er CSS-gradienter, så alt fungerer uden eksterne assets.
window.PRODUCTS = [
  {
    id: "kjole-rose-satin",
    name: "Rose Satin Slip Dress",
    brand: "Maison Rosé",
    category: "kjoler",
    price: 1299, oldPrice: 1599, isNew: true, onSale: true,
    colors: ["Rosa", "Beige", "Sort"],
    sizes: ["XS", "S", "M", "L"],
    gradient: "linear-gradient(160deg, #f2c1c8, #c26b73)",
    description: "En sofistikeret satin-kjole med bias-cut og justerbare stropper. Perfekt til fest og fine middage.",
    material: "100% viscose satin. Kan renses.",
    fit: "Følger kroppen. Vi anbefaler din normale størrelse."
  },
  {
    id: "kjole-linen-midi",
    name: "Linen Midi Kjole",
    brand: "Nord & Sol",
    category: "kjoler",
    price: 899, isNew: true,
    colors: ["Beige", "Hvid"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #f4ebe6, #b48a55)",
    description: "Luftig og let hør-kjole med volang forneden. Sommerens vigtigste kjole.",
    material: "100% europæisk hør.",
    fit: "Løs pasform, tag din normale størrelse."
  },
  {
    id: "kjole-black-wrap",
    name: "Klassisk Wrap Dress",
    brand: "Studio Nord",
    category: "kjoler",
    price: 1099,
    colors: ["Sort"],
    sizes: ["XS", "S", "M", "L"],
    gradient: "linear-gradient(160deg, #333, #111)",
    description: "Den evigt-klassiske wrap-kjole i blødt jersey-stof.",
    material: "92% viscose, 8% elastan.",
    fit: "Følger kroppen. Justerbar med bindebånd."
  },
  {
    id: "top-silke-blouse",
    name: "Silke Bluse",
    brand: "Maison Rosé",
    category: "toppe",
    price: 799,
    colors: ["Hvid", "Rosa"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #ffffff, #f2c1c8)",
    description: "Blød silkebluse med v-udskæring og knappelukning.",
    material: "100% silke.",
    fit: "Regular. Tag din normale størrelse."
  },
  {
    id: "top-strik-crop",
    name: "Rib Strik Top",
    brand: "Copenhagen Basics",
    category: "toppe",
    price: 449, oldPrice: 599, onSale: true,
    colors: ["Beige", "Sort", "Grøn"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #e5d3b3, #b48a55)",
    description: "Rib-strikket top med korte ærmer. En hverdagsfavorit.",
    material: "80% bomuld, 20% viscose.",
    fit: "Tætsiddende. Går til over bæltet."
  },
  {
    id: "top-tshirt-white",
    name: "Perfekt Hvid T-shirt",
    brand: "Copenhagen Basics",
    category: "toppe",
    price: 249,
    colors: ["Hvid", "Sort", "Beige"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #ffffff, #f4ebe6)",
    description: "Den tykke, blødt-faldende t-shirt du bruger igen og igen.",
    material: "100% bomuld i tung kvalitet (220 gsm).",
    fit: "Regular. Runder let over skuldrene."
  },
  {
    id: "bukser-wide-linen",
    name: "Højtaljede Linen Bukser",
    brand: "Nord & Sol",
    category: "bukser",
    price: 899, isNew: true,
    colors: ["Beige", "Hvid"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #f4ebe6, #e5d3b3)",
    description: "Vidde bukser i hør med paperbag-talje.",
    material: "100% hør.",
    fit: "Løs, høj talje."
  },
  {
    id: "bukser-tailored",
    name: "Tailored Bukser",
    brand: "Studio Nord",
    category: "bukser",
    price: 1199,
    colors: ["Sort", "Beige"],
    sizes: ["XS", "S", "M", "L"],
    gradient: "linear-gradient(160deg, #2a2a2a, #111)",
    description: "Klassiske tailored bukser med presfold. Fra kontoret til fredag aften.",
    material: "70% uld, 30% polyester.",
    fit: "Slim gennem hoften, straight ben."
  },
  {
    id: "bukser-mom-jeans",
    name: "Mom Jeans i Vintage Blue",
    brand: "Copenhagen Basics",
    category: "bukser",
    price: 699, oldPrice: 899, onSale: true,
    colors: ["Blå"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #6a8cc0, #3d5a8a)",
    description: "Højtaljede mom jeans i klassisk vasket denim.",
    material: "100% bomuld.",
    fit: "Højtaljet, løs i låret, konisk forneden."
  },
  {
    id: "overtoej-trench",
    name: "Klassisk Trenchcoat",
    brand: "Maison Rosé",
    category: "overtoej",
    price: 1899, isNew: true,
    colors: ["Beige"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #e5d3b3, #a67f4a)",
    description: "Tidløs trenchcoat med bælte og skulderklapper.",
    material: "Ydre 60% bomuld, 40% polyester. For 100% viscose.",
    fit: "Regular. Rummelig så du kan bære over strik."
  },
  {
    id: "overtoej-uld-frakke",
    name: "Uld Overfrakke",
    brand: "Studio Nord",
    category: "overtoej",
    price: 2299,
    colors: ["Sort", "Beige"],
    sizes: ["S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #444, #111)",
    description: "Lang overfrakke i tykt uld — varmen du mangler til vinteren.",
    material: "70% uld, 30% polyester.",
    fit: "Oversize. Tag din normale størrelse for løs pasform."
  },
  {
    id: "overtoej-blazer",
    name: "Oversize Blazer",
    brand: "Studio Nord",
    category: "overtoej",
    price: 1299,
    colors: ["Sort", "Beige", "Rosa"],
    sizes: ["XS", "S", "M", "L"],
    gradient: "linear-gradient(160deg, #f2c1c8, #a86169)",
    description: "Løst siddende blazer med struktur i skuldrene.",
    material: "65% polyester, 30% viscose, 5% elastan.",
    fit: "Oversize. Går ned over hoften."
  },
  {
    id: "acc-lædertaske",
    name: "Læder Skuldertaske",
    brand: "Maison Rosé",
    category: "accessories",
    price: 1499,
    colors: ["Sort", "Beige"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #7a5a3a, #3a2a15)",
    description: "Håndlavet skuldertaske i italiensk læder.",
    material: "100% læder. Foer i bomuld.",
    fit: "Rummer let A4 og laptop."
  },
  {
    id: "acc-silketorklaede",
    name: "Silketørklæde",
    brand: "Maison Rosé",
    category: "accessories",
    price: 349,
    colors: ["Rosa", "Grøn", "Blå"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #f2c1c8, #b48a55)",
    description: "90 x 90 cm silketørklæde — bær det i håret, om halsen eller på tasken.",
    material: "100% silke twill.",
    fit: "One size."
  },
  {
    id: "acc-solbriller",
    name: "Retro Solbriller",
    brand: "Copenhagen Basics",
    category: "accessories",
    price: 449, isNew: true,
    colors: ["Sort", "Beige"],
    sizes: ["ONESIZE"],
    gradient: "linear-gradient(160deg, #222, #000)",
    description: "Overdimensionerede solbriller med UV400-beskyttelse.",
    material: "Acetat-stel, glas med UV400.",
    fit: "One size."
  },
  {
    id: "sko-loafer",
    name: "Læder Loafers",
    brand: "Maison Rosé",
    category: "sko",
    price: 1199,
    colors: ["Sort", "Beige"],
    sizes: ["XS", "S", "M", "L"],
    gradient: "linear-gradient(160deg, #3a2a15, #1a1408)",
    description: "Klassiske penny-loafers i blødt læder.",
    material: "Ægte læder, læder-sål.",
    fit: "Passer normal størrelse. Tag én ned hvis mellem størrelser."
  },
  {
    id: "sko-heels",
    name: "Slingback Heels",
    brand: "Studio Nord",
    category: "sko",
    price: 1399, isNew: true,
    colors: ["Sort", "Rosa"],
    sizes: ["S", "M", "L"],
    gradient: "linear-gradient(160deg, #f2c1c8, #9c4b53)",
    description: "Elegante slingback pumps med 6 cm hæl.",
    material: "Ægte læder.",
    fit: "Passer normal størrelse."
  },
  {
    id: "sko-sneakers",
    name: "Hvide Sneakers",
    brand: "Copenhagen Basics",
    category: "sko",
    price: 799, oldPrice: 999, onSale: true,
    colors: ["Hvid"],
    sizes: ["XS", "S", "M", "L", "XL"],
    gradient: "linear-gradient(160deg, #ffffff, #ecdfd7)",
    description: "Minimalistiske hvide sneakers til hverdag.",
    material: "Overdel i læder, gummi-sål.",
    fit: "Regular. Passer normal størrelse."
  }
];

window.getProduct = (id) => window.PRODUCTS.find(p => p.id === id);
window.getRelated = (id, limit=4) => {
  const p = window.getProduct(id);
  if (!p) return [];
  return window.PRODUCTS.filter(x => x.id !== id && x.category === p.category).slice(0, limit);
};

window.formatPrice = (n) => new Intl.NumberFormat('da-DK').format(n) + ' kr.';

window.productCardHTML = (p) => {
  const badge = p.onSale ? '<span class="badge sale">Tilbud</span>'
              : p.isNew  ? '<span class="badge">Nyhed</span>' : '';
  const oldPrice = p.oldPrice ? `<span class="old-price">${window.formatPrice(p.oldPrice)}</span>` : '';
  return `
    <a class="product-card" href="product.html?id=${p.id}">
      <div class="thumb" style="background:${p.gradient}">${badge}</div>
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
