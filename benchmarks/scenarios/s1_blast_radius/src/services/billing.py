"""Billing service client."""
from ..utils.url_builder import build_query_url


def generate_invoice_link(customer_id: str, invoice_ids: list[str]) -> str:
    """Generate secure portal link for retrieving multiple invoices."""
    params = {
        "customer_id": customer_id,
        "invoice_id": invoice_ids,
    }
    return build_query_url("https://billing.example.com/portal/invoices", params, sort_keys=True)
