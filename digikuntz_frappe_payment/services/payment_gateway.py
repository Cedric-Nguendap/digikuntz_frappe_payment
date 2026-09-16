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
        gateway_key = resolve_gateway_from_pr(doc.get("payment_gateway")) or None
        service = PaymentService(company=company or doc.company, gateway=gateway_key)

        payment_mode = _get_payment_mode(gateway_key, company or doc.company)

        if payment_mode == "prompt":
            # Pas d'appel API ici — la page checkout gère tout
            return frappe.utils.get_url(f"/checkout?pr={reference_docname}")

        # Mode web : appel API gateway, stocke le redirect, retourne /pay
        response = service.create_payment_link(doc, payer_email=kwargs.get("payer_email"))
        data = response.get("data") or {}

        gateway_redirect = data.get("redirect_url") or ""
        deposit_id = data.get("transaction_id") or ""

        if gateway_redirect:
            _store_redirect(reference_docname, gateway_redirect, deposit_id)

        return frappe.utils.get_url(f"/pay?pr={reference_docname}")


def _get_payment_mode(gateway_key, company):
    """Lit custom_payment_mode sur la Company — source de verite unique."""
    try:
        if company:
            company_name = company if isinstance(company, str) else company.name
            mode = frappe.db.get_value("Company", company_name, "custom_payment_mode")
            return mode or "web"
    except Exception:
        pass
    return "web"


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
