import frappe
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService, get_company_and_gateway


def get_context(context):
    context.no_cache = 1

    # PawaPay retourne : ?pr=...&status=cancelled&tx_ref=PR-...
    # Flutterwave retourne : ?tx_ref=PR-...&transaction_id=12345&status=successful
    pr_name     = frappe.form_dict.get("pr") or ""
    tx_ref      = frappe.form_dict.get("tx_ref") or ""
    url_status  = frappe.form_dict.get("status") or ""
    # Flutterwave met l'ID numérique dans transaction_id, PawaPay met depositId
    transaction_id = frappe.form_dict.get("transaction_id") or frappe.form_dict.get("depositId") or ""

    # Résoudre pr_name
    if not pr_name:
        if tx_ref:
            pr_name = tx_ref.replace("PR-", "", 1)
        elif transaction_id:
            pr_name = frappe.db.get_value(
                "Payment Redirect", {"deposit_id": transaction_id}, "payment_request"
            ) or ""

    if pr_name and not tx_ref:
        tx_ref = f"PR-{pr_name}"

    company, gateway = get_company_and_gateway(pr_name)

    if not company:
        context.status = "error"
        context.tx_ref = tx_ref
        context.transaction_id = transaction_id
        return context

    # Si la gateway dit explicitement cancelled/failed dans l'URL → pas besoin d'appel API
    if url_status in ("cancelled", "failed", "error"):
        context.status = "failed"
        context.tx_ref = tx_ref
        context.transaction_id = transaction_id
        return context

    # Résoudre transaction_id selon la gateway
    # - Flutterwave : transaction_id numérique déjà dans l'URL
    # - PawaPay     : deposit_id stocké dans Payment Redirect
    if not transaction_id and pr_name:
        transaction_id = frappe.db.get_value(
            "Payment Redirect", {"payment_request": pr_name}, "deposit_id"
        ) or ""

    if not transaction_id:
        context.status = "error"
        context.tx_ref = tx_ref
        context.transaction_id = transaction_id
        return context

    service = PaymentWebhookService(company=company, gateway=gateway)
    status = service.handle_transaction_status(transaction_id, tx_ref=tx_ref, gateway=gateway)

    context.status = status
    context.tx_ref = tx_ref
    context.transaction_id = transaction_id
    return context
