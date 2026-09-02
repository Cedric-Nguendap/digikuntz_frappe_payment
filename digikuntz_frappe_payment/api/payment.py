import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


@frappe.whitelist()
def initiate_momo_push(payment_request_name, phone_number, network):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentService(company=pr.company)
    return service.mobile_money_charge(pr, phone_number, network)


@frappe.whitelist()
def check_momo_push(payment_request_name):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentWebhookService(company=pr.company)
    return service.handle_transaction_status(f"PR-{payment_request_name}", is_web_payment=False)
