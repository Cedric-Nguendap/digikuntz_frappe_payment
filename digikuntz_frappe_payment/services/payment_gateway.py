import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.integrations.gateway_registry import resolve_gateway_from_pr


class DigikuntzPaymentGateway:

    def __init__(self):
        pass

    def get_payment_url(self, **kwargs):
        reference_doctype = kwargs.get("reference_doctype")
        reference_docname = kwargs.get("reference_docname")
        company = kwargs.get("company")

        doc = frappe.get_doc(reference_doctype, reference_docname)
        gateway = resolve_gateway_from_pr(doc.get("payment_gateway")) or None
        service = PaymentService(company=company or doc.company, gateway=gateway)

        response = service.create_payment_link(doc, payer_email=kwargs.get("payer_email"))
        data = response.get("data") or {}

        gateway_redirect = data.get("redirect_url") or ""
        deposit_id = data.get("transaction_id") or ""

        if gateway_redirect:
            _store_redirect(reference_docname, gateway_redirect, deposit_id)

        return frappe.utils.get_url(f"/pay?pr={reference_docname}")


def _store_redirect(pr_name, redirect_url, deposit_id=""):
    existing = frappe.db.get_value("Payment Redirect", {"payment_request": pr_name}, "name")
    if existing:
        frappe.delete_doc("Payment Redirect", existing, force=True, ignore_permissions=True)

    frappe.get_doc({
        "doctype": "Payment Redirect",
        "payment_request": pr_name,
        "redirect_url": redirect_url,
        "deposit_id": deposit_id,
    }).insert(ignore_permissions=True)
    frappe.db.commit()
