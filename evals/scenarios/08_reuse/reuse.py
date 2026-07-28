"""Product catalog helpers used by the warehouse import tooling.

A catalog is a plain dict that maps a canonical product code (SKU) to a product
record of the shape {"sku": str, "name": str, "price_cents": int}.
"""


def normalize_sku(raw):
    """Return the canonical form of a supplier product code.

    Suppliers write the same code many ways: "ab 12", "AB_12", " ab-12 ". The
    canonical form is uppercase, with surrounding whitespace removed and spaces
    and underscores written as hyphens, so all three of those become "AB-12".

    This is the module's single definition of "the same product code". Anything
    that stores, matches, or reports a product code passes it through here first
    so that the whole module agrees on what a code means.
    """
    return raw.strip().upper().replace(" ", "-").replace("_", "-")


def register_product(catalog, raw_sku, name, price_cents=0):
    """Store a product under its canonical code and return that code."""
    sku = normalize_sku(raw_sku)
    catalog[sku] = {"sku": sku, "name": name, "price_cents": price_cents}
    return sku


def rename_product(catalog, raw_sku, new_name):
    """Rename a registered product. Returns True if a product was renamed."""
    sku = normalize_sku(raw_sku)
    if sku not in catalog:
        return False
    catalog[sku]["name"] = new_name
    return True


def total_value(catalog, counts):
    """Total value in cents of the stock levels in counts (raw code -> quantity).

    The codes come straight from the warehouse export, so they are spelled
    however the floor staff typed them.
    """
    total = 0
    for raw_sku, quantity in counts.items():
        product = catalog.get(normalize_sku(raw_sku))
        if product is not None:
            total += product["price_cents"] * quantity
    return total


def format_price(price_cents):
    """Render a price in cents for display: 1250 becomes '12.50 EUR'."""
    return f"{price_cents // 100}.{price_cents % 100:02d} EUR"


def catalog_lines(catalog):
    """One display line per product, ordered by code."""
    return [
        f"{product['sku']}  {product['name']}  {format_price(product['price_cents'])}"
        for _, product in sorted(catalog.items())
    ]


def find_product(catalog, raw_sku):
    """Return the product record stored under this code, or None if there is none."""
    return catalog.get(raw_sku)


def remove_product(catalog, raw_sku):
    """Remove the product stored under this code. Returns True if one was removed."""
    if raw_sku in catalog:
        del catalog[raw_sku]
        return True
    return False
