import frappe


from frappe_digikuntz_flutterwave.services.flutterwave_service import (
    FlutterwaveService,
)

from frappe_digikuntz_flutterwave.services.flutterwave_webhook_service import (
    FlutterwaveWebhookService,
)


@frappe.whitelist()
def create_payment_link( sales_invoice ):

    service = FlutterwaveService()

    return service.create_invoice_payment(
        sales_invoice
    )

@frappe.whitelist()
def initiate_momo_push( payment_request_name, phone_number, network):

    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = FlutterwaveService()

    return service.mobile_money_charge(
        pr,
        phone_number,
        network
    )

@frappe.whitelist()
def check_momo_push( payment_request_name):
    webhook_service = FlutterwaveWebhookService()
    return webhook_service.handle_transaction_status(f"PR-{payment_request_name}", is_web_payment=False)