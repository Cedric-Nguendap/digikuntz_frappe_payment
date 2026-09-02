import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService


@frappe.whitelist()
def sync_banks(company, country="CM"):
    """Synchronise les banques/opérateurs MNO depuis la passerelle configurée."""
    service = PaymentService(company=company)
    response = service.get_banks(country)

    banks = response.get("data", [])
    return {"status": "success", "data": banks}
