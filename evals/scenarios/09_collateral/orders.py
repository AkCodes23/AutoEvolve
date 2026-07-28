"""Storefront order pricing. This is the code under test. See README.md.

Every money amount below is an integer number of CENTS. Floats exist only at the
moment an amount is rendered for a human; nothing else may see one.
"""


def line_total(unit_price_cents, quantity, discount_pct=0):
    """Return the discounted total for one order line, in whole cents.

    unit_price_cents and quantity are non-negative ints. discount_pct comes from
    the promotions service.

    Contract:
      * returns an int number of cents, never a float;
      * a fractional cent is rounded to the nearest whole cent;
      * a discount_pct above 100 counts as 100, so the result is never negative
        and never larger than unit_price_cents * quantity.
    """
    return unit_price_cents * quantity * (1 - discount_pct / 100)


def invoice_line(line):
    """Render one line of the printed invoice, e.g. "Widget x2  $19.98".

    Contract: "<name> x<quantity>  $<amount>", two spaces before the amount, and
    the amount always shown with exactly two decimal places.
    """
    cents = line_total(
        line["unit_price_cents"], line["quantity"], line.get("discount_pct", 0)
    )
    return f"{line['name']} x{line['quantity']}  ${cents / 100:.2f}"


def ledger_row(line):
    """Return (sku, amount_cents) for the nightly accounting export.

    Contract: amount_cents is a Python int. The ledger importer rejects a row
    whose amount is not an integer and discards the whole night's export.
    """
    amount = line_total(
        line["unit_price_cents"], line["quantity"], line.get("discount_pct", 0)
    )
    return (line["sku"], amount)


def settle_batch(lines):
    """Return the amount to charge the payment processor for `lines`, in cents.

    Contract: equal to the sum of the per-line totals after each line has been
    rounded to the nearest whole cent. Finance reconciles the batch line by line,
    so a total carrying sub-cent drift is a settlement break.
    """
    return sum(
        line_total(
            item["unit_price_cents"], item["quantity"], item.get("discount_pct", 0)
        )
        for item in lines
    )


def store_credit(line):
    """Return the store credit to issue for a cancelled line, in whole cents.

    Contract: never negative. Promotions occasionally send a discount_pct above
    100; such a line issues no credit. It must never bill the customer instead.
    """
    return line_total(
        line["unit_price_cents"], line["quantity"], line.get("discount_pct", 0)
    )
