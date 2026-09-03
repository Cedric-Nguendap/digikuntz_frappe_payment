import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


def get_context(context):
    context.no_cache = 1

    tx_ref = frappe.form_dict.get("tx_ref") or ""
    transaction_id = frappe.form_dict.get("transaction_id") or frappe.form_dict.get("depositId") or ""

    print("transaction_id ", transaction_id)
    # Si pas de tx_ref, essayer de le retrouver depuis le depositId (retour PawaPay)
    if not tx_ref and transaction_id:
        tx_ref = _get_tx_ref_from_deposit_id(transaction_id) or ""

    company = _get_company_from_tx_ref(tx_ref)
    if not company or not transaction_id:
        context.status = "error"
        context.tx_ref = tx_ref
        context.transaction_id = transaction_id
        return context

    service = PaymentWebhookService(company=company)
    status = service.handle_transaction_status(transaction_id, tx_ref=tx_ref)
    
    context.status = status
    context.tx_ref = tx_ref
    context.transaction_id = transaction_id
    return context


def _get_company_from_tx_ref(tx_ref):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if pr_name and frappe.db.exists("Payment Request", pr_name):
            return frappe.db.get_value("Payment Request", pr_name, "company")
    except Exception:
        pass
    return None


def _get_tx_ref_from_deposit_id(deposit_id):
    """Retrouve le tx_ref en cherchant le PR dont payment_url contient le depositId."""
    try:
        pr_name = frappe.db.get_value(
            "Payment Request",
            {"payment_url": ["like", f"%{deposit_id}%"]},
            "name"
        )
        if pr_name:
            return f"PR-{pr_name}"
    except Exception:
        pass
    return None
