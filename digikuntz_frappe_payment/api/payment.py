import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


@frappe.whitelist()
def initiate_momo_push(payment_request_name, phone_number, network):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentService(company=pr.company)
    return service.mobile_money_charge(pr, phone_number, network)


@frappe.whitelist(allow_guest=True)
def check_payment_status(transaction_id, tx_ref=None):
    """Endpoint JSON pour le polling de statut depuis payment-success.html"""
    if not transaction_id:
        return {"status": "error"}

    # Retrouver tx_ref depuis depositId si non fourni (cas PawaPay)
    if not tx_ref:
        pr_name = frappe.db.get_value(
            "Payment Request",
            {"payment_url": ["like", f"%{transaction_id}%"]},
            "name"
        )
        tx_ref = f"PR-{pr_name}" if pr_name else ""

    company = None
    if tx_ref:
        pr_name = tx_ref.replace("PR-", "", 1)
        if frappe.db.exists("Payment Request", pr_name):
            company = frappe.db.get_value("Payment Request", pr_name, "company")

    if not company:
        return {"status": "error"}

    service = PaymentWebhookService(company=company)
    status = service.handle_transaction_status(transaction_id, tx_ref=tx_ref)
    return {"status": status}


@frappe.whitelist()
def check_momo_push(payment_request_name):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentWebhookService(company=pr.company)
    return service.handle_transaction_status(f"PR-{payment_request_name}", is_web_payment=False)
