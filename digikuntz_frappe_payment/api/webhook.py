import json
import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


@frappe.whitelist(allow_guest=True)
def payment_webhook():
    payload = frappe.request.get_data(as_text=True)
    signature = frappe.get_request_header("verif-hash") or frappe.get_request_header("x-pawapay-signature") or ""

    company = _extract_company_from_payload(payload)

    service = PaymentWebhookService(company=company)
    return service.handle_webhook(payload=payload, signature=signature)


def _extract_company_from_payload(payload):
    """Extrait la company depuis le tx_ref contenu dans le payload webhook."""
    try:
        data = json.loads(payload)
        # Flutterwave: data.data.tx_ref
        tx_ref = (data.get("data") or {}).get("tx_ref") or ""
        # PawaPay: customerMessage contient "Payment PR-..."
        if not tx_ref:
            tx_ref = data.get("customerMessage") or ""
        tx_ref = tx_ref.replace("Payment ", "", 1)
        pr_name = tx_ref.replace("PR-", "", 1)
        if pr_name and frappe.db.exists("Payment Request", pr_name):
            return frappe.db.get_value("Payment Request", pr_name, "company")
    except Exception:
        pass
    return None
