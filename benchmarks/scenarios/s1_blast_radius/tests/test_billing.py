import pytest
from benchmarks.scenarios.s1_blast_radius.src.services.billing import generate_invoice_link


def test_generate_invoice_link_multiple_invoices():
    link = generate_invoice_link("cust_12345", ["inv_001", "inv_002", "inv_003"])
    expected = "https://billing.example.com/portal/invoices?customer_id=cust_12345&invoice_id=inv_001&invoice_id=inv_002&invoice_id=inv_003"
    assert link == expected


def test_generate_invoice_link_single_invoice():
    link = generate_invoice_link("cust_999", ["inv_alpha"])
    expected = "https://billing.example.com/portal/invoices?customer_id=cust_999&invoice_id=inv_alpha"
    assert link == expected
