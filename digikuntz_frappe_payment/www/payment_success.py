import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


def get_context(context):
    context.no_cache = 1

    # PawaPay retourne ?depositId=uuid
    # Flutterwave retourne ?tx_ref=PR-...&transaction_id=...
    pr_name = frappe.form_dict.get("pr") or ""
    tx_ref = frappe.form_dict.get("tx_ref") or ""
    transaction_id = frappe.form_dict.get("transaction_id") or frappe.form_dict.get("depositId") or ""

    # Résoudre pr_name depuis depositId via Payment Redirect (cas PawaPay)
    if not pr_name and transaction_id:
        pr_name = frappe.db.get_value(
            "Payment Redirect", {"deposit_id": transaction_id}, "payment_request"
        ) or ""

    # Résoudre pr_name/tx_ref mutuellement
    if pr_name and not tx_ref:
        tx_ref = f"PR-{pr_name}"
    elif tx_ref and not pr_name:
        pr_name = tx_ref.replace("PR-", "", 1)

    # Résoudre transaction_id depuis Payment Redirect si toujours absent
    if not transaction_id and pr_name:
        transaction_id = frappe.db.get_value(
            "Payment Redirect", {"payment_request": pr_name}, "deposit_id"
        ) or ""

    company = _get_company(pr_name)

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


def _get_company(pr_name):
    try:
        if pr_name and frappe.db.exists("Payment Request", pr_name):
            return frappe.db.get_value("Payment Request", pr_name, "company")
    except Exception:
        pass
    return None
