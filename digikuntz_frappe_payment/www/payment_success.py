import frappe

from digikuntz_frappe_payment.services.payment_webhook_service import (
    PaymentWebhookService
)


def get_context(context):

    context.no_cache = 1

    tx_ref = frappe.form_dict.get("tx_ref")
    transaction_id = frappe.form_dict.get("transaction_id")
    
    service = PaymentWebhookService()
    status = service.handle_transaction_status(transaction_id)
    context.status = status
    context.tx_ref = tx_ref
    return context