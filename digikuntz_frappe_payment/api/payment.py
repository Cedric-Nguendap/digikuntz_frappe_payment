import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.services.payment_webhook_service import PaymentWebhookService, get_company_and_gateway
from digikuntz_frappe_payment.integrations.gateway_registry import resolve_gateway_from_pr


@frappe.whitelist(allow_guest=True)
def initiate_prompt_payment(pr_name, phone_number, network):
    """Appelé par checkout.html — initie un paiement prompt MoMo."""
    if not frappe.db.exists("Payment Request", pr_name):
        return {"ok": False, "error": "Payment Request introuvable."}

    pr = frappe.get_doc("Payment Request", pr_name)
    if pr.status not in ("Requested", "Initiated"):
        return {"ok": False, "error": "Ce lien de paiement n'est plus actif."}

    gateway = resolve_gateway_from_pr(pr.get("payment_gateway")) or None
    service = PaymentService(company=pr.company, gateway=gateway)
    response = service.mobile_money_charge(pr, phone_number, network)

    if not response.get("ok"):
        return {"ok": False, "error": response.get("error") or "Échec de l'initialisation."}

    deposit_id = (response.get("data") or {}).get("transaction_id") or ""
    if not deposit_id:
        return {"ok": False, "error": "Aucun depositId retourné par la gateway."}
    existing = frappe.db.get_value("Payment Redirect", {"payment_request": pr_name}, "name")
    if existing:
        frappe.db.set_value("Payment Redirect", existing, "deposit_id", deposit_id)
    else:
        frappe.get_doc({
            "doctype": "Payment Redirect",
            "payment_request": pr_name,
            "deposit_id": deposit_id,
        }).insert(ignore_permissions=True)
    frappe.db.commit()

    return {"ok": True}


@frappe.whitelist(allow_guest=True)
def check_payment_status(pr=None):
    """Polling depuis checkout.html et payment-success."""
    pr_name = pr or ""
    if not pr_name or not frappe.db.exists("Payment Request", pr_name):
        return {"status": "error"}

    tx_ref = f"PR-{pr_name}"
    transaction_id = frappe.db.get_value(
        "Payment Redirect", {"payment_request": pr_name}, "deposit_id"
    ) or ""
    if not transaction_id:
        return {"status": "pending"}

    company, gateway = get_company_and_gateway(pr_name)
    if not company:
        return {"status": "error"}

    service = PaymentWebhookService(company=company, gateway=gateway)
    status = service.handle_transaction_status(transaction_id, tx_ref=tx_ref, gateway=gateway)
    return {"status": status}


@frappe.whitelist()
def initiate_momo_push(payment_request_name, phone_number, network):
    """Appelé depuis le desk ERPNext (bouton MoMo sur Payment Request)."""
    pr = frappe.get_doc("Payment Request", payment_request_name)
    gateway = resolve_gateway_from_pr(pr.get("payment_gateway")) or None
    service = PaymentService(company=pr.company, gateway=gateway)
    return service.mobile_money_charge(pr, phone_number, network)


@frappe.whitelist()
def check_momo_push(payment_request_name):
    """Vérification manuelle depuis le desk."""
    company, gateway = get_company_and_gateway(payment_request_name)
    service = PaymentWebhookService(company=company, gateway=gateway)
    return service.handle_transaction_status(
        f"PR-{payment_request_name}", is_web_payment=False, gateway=gateway
    )
