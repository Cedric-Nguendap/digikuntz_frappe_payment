import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService


@frappe.whitelist()
def initiate_momo_push(payment_request_name, phone_number, network):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    service = PaymentService(company=pr.company)
    return service.mobile_money_charge(pr, phone_number, network)


@frappe.whitelist(allow_guest=True)
def check_payment_status(transaction_id=None, tx_ref=None, pr=None):
    """Endpoint JSON pour le polling de statut depuis payment-success.html"""

    # Résoudre pr_name
    pr_name = pr or (tx_ref.replace("PR-", "", 1) if tx_ref else None)

    # Résoudre transaction_id depuis Payment Redirect si non fourni
    if not transaction_id and pr_name:
        transaction_id = frappe.db.get_value(
            "Payment Redirect", {"payment_request": pr_name}, "deposit_id"
        ) or ""

    # Résoudre tx_ref depuis pr_name
    if not tx_ref and pr_name:
        tx_ref = f"PR-{pr_name}"

    if not transaction_id or not pr_name:
        return {"status": "error"}

    if not frappe.db.exists("Payment Request", pr_name):
        return {"status": "error"}

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
