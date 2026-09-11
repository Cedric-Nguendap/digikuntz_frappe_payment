import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService, get_company_and_gateway
from digikuntz_frappe_payment.integrations.gateway_registry import resolve_gateway_from_pr


@frappe.whitelist()
def initiate_momo_push(payment_request_name, phone_number, network):
    pr = frappe.get_doc("Payment Request", payment_request_name)
    gateway = resolve_gateway_from_pr(pr.get("payment_gateway")) or None
    service = PaymentService(company=pr.company, gateway=gateway)
    return service.mobile_money_charge(pr, phone_number, network)


@frappe.whitelist(allow_guest=True)
def check_payment_status(transaction_id=None, tx_ref=None, pr=None):
    pr_name = pr or (tx_ref.replace("PR-", "", 1) if tx_ref else "")

    if not pr_name and transaction_id:
        pr_name = frappe.db.get_value(
            "Payment Redirect", {"deposit_id": transaction_id}, "payment_request"
        ) or ""

    if not tx_ref and pr_name:
        tx_ref = f"PR-{pr_name}"

    if not transaction_id and pr_name:
        transaction_id = frappe.db.get_value(
            "Payment Redirect", {"payment_request": pr_name}, "deposit_id"
        ) or ""

    if not transaction_id or not pr_name:
        return {"status": "error"}

    company, gateway = get_company_and_gateway(pr_name)
    if not company:
        return {"status": "error"}

    service = PaymentWebhookService(company=company, gateway=gateway)
    status = service.handle_transaction_status(transaction_id, tx_ref=tx_ref, gateway=gateway)
    return {"status": status}


@frappe.whitelist()
def check_momo_push(payment_request_name):
    company, gateway = get_company_and_gateway(payment_request_name)
    service = PaymentWebhookService(company=company, gateway=gateway)
    return service.handle_transaction_status(f"PR-{payment_request_name}", is_web_payment=False, gateway=gateway)
