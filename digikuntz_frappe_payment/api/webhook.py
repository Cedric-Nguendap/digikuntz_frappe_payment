import frappe

from digikuntz_frappe_payment.services.payment_webhook_service import (
    PaymentWebhookService
)


@frappe.whitelist(allow_guest=True)
def payment_webhook():

    payload = frappe.request.get_data(as_text=True)

    signature = frappe.get_request_header("verif-hash")

    service = PaymentWebhookService()

    return service.handle_webhook(
        payload=payload,
        signature=signature
    )