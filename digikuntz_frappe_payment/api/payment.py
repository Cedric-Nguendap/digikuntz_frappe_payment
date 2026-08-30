import frappe


from digikuntz_frappe_payment.services.payment_service import (
    PaymentService,
)

from digikuntz_frappe_payment.services.payment_webhook_service import (
    PaymentWebhookService,
)


@frappe.whitelist()
def create_payment_link( sales_invoice ):

    service = PaymentService()

    return service.create_invoice_payment(
        sales_invoice
    )

@frappe.whitelist()
def initiate_momo_push( payment_request_name, phone_number, network):

    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentService()

    return service.mobile_money_charge(
        pr,
        phone_number,
        network
    )

@frappe.whitelist()
def check_momo_push( payment_request_name):
    webhook_service = PaymentWebhookService()
    return webhook_service.handle_transaction_status(f"PR-{payment_request_name}", is_web_payment=False)