import json
import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService, get_company_and_gateway


@frappe.whitelist(allow_guest=True)
def payment_webhook():
    payload = frappe.request.get_data(as_text=True)
    signature = frappe.get_request_header("verif-hash") or frappe.get_request_header("x-pawapay-signature") or ""

    pr_name = _extract_pr_name_from_payload(payload)
    company, gateway = get_company_and_gateway(pr_name)

    service = PaymentWebhookService(company=company, gateway=gateway)
    return service.handle_webhook(payload=payload, signature=signature)


def _extract_pr_name_from_payload(payload):
    """Extrait le pr_name depuis le payload webhook."""
    try:
        data = json.loads(payload)
        tx_ref = (data.get("data") or {}).get("tx_ref") or ""
        if not tx_ref:
            tx_ref = data.get("customerMessage") or ""
        tx_ref = tx_ref.replace("Payment ", "", 1)
        return tx_ref.replace("PR-", "", 1)
    except Exception:
        return None
