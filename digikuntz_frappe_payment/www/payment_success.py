import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


def get_context(context):
    context.no_cache = 1

    tx_ref = frappe.form_dict.get("tx_ref") or ""
    transaction_id = frappe.form_dict.get("transaction_id")

    company = _get_company_from_tx_ref(tx_ref)

    service = PaymentWebhookService(company=company)
    status = service.handle_transaction_status(transaction_id)

    context.status = status
    context.tx_ref = tx_ref
    return context


def _get_company_from_tx_ref(tx_ref):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if pr_name and frappe.db.exists("Payment Request", pr_name):
            return frappe.db.get_value("Payment Request", pr_name, "company")
    except Exception:
        pass
    return None
