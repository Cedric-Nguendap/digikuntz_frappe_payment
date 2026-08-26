import frappe

from frappe_digikuntz_flutterwave.services.flutterwave_webhook_service import (
    FlutterwaveWebhookService
)


@frappe.whitelist(allow_guest=True)
def flutterwave_webhook():

    payload = frappe.request.get_data(as_text=True)

    signature = frappe.get_request_header("verif-hash")

    service = FlutterwaveWebhookService()

    return service.handle_webhook(
        payload=payload,
        signature=signature
    )