import json
import frappe
from digikuntz_frappe_payment.integrations.payment_client_factory import PaymentClientFactory
from digikuntz_frappe_payment.integrations.gateway_registry import resolve_gateway_from_pr


class PaymentWebhookService:

    def __init__(self, company=None, gateway=None):
        self.payment_mode = PaymentClientFactory.get_payment_client(company=company, gateway=gateway)
        self.mode_name = self.payment_mode["mode"]
        self.client = self.payment_mode["client"]

    def handle_webhook(self, payload, signature):
        try:
            if not self.client.verify_webhook_signature(payload, signature):
                frappe.logger().warning("Webhook signature mismatch")
                return {"status": "error", "message": "Invalid signature"}

            transaction = json.loads(payload)
            tx_ref = self.client.extract_tx_ref_from_webhook(transaction)
            if tx_ref:
                self._process_successful_payment(tx_ref)
                return {"status": "success"}

            return {"status": "ignored"}

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Webhook processing error")
            return {"status": "error", "message": str(e)}

    def handle_transaction_status(self, transaction_id, is_web_payment=True, tx_ref=None, gateway=None):
        # Logique de vérification selon la gateway :
        # - PawaPay (web + MoMo) : transaction_id = deposit_id UUID → verify_transaction
        # - Flutterwave web      : transaction_id = ID numérique OU tx_ref → verify_transaction si numérique, sinon by_reference
        # - Flutterwave MoMo     : transaction_id = tx_ref → verify_transaction_by_reference
        effective_gateway = gateway or self.mode_name

        if effective_gateway == "PawaPay":
            response = self.client.verify_transaction(transaction_id)
        elif effective_gateway == "Flutterwave":
            # Si transaction_id est numérique (retour URL Flutterwave) → verify directe
            # Sinon (MoMo ou polling sans ID numérique) → by_reference via tx_ref
            if transaction_id and str(transaction_id).isdigit():
                response = self.client.verify_transaction(transaction_id)
            else:
                ref = tx_ref or transaction_id
                response = self.client.verify_transaction_by_reference(ref)
        else:
            response = self.client.verify_transaction(transaction_id)

        if not response.get("ok"):
            frappe.logger().error(
                f"Transaction verification failed for {transaction_id}: {response.get('error')}"
            )
            return "error"

        data = response.get("data", {})
        status = data.get("status")
        if status == "successful":
            # Priorité au tx_ref passé en paramètre (web payment), sinon celui retourné par l'API
            resolved_tx_ref = tx_ref or data.get("tx_ref", "")
            self._process_successful_payment(resolved_tx_ref)
        return status

    def _process_successful_payment(self, tx_ref):
        pr_name = tx_ref.replace("PR-", "", 1)
        if not pr_name or not frappe.db.exists("Payment Request", pr_name):
            frappe.logger().warning(f"Payment Request introuvable pour tx_ref: {tx_ref}")
            return
        pr = frappe.get_doc("Payment Request", pr_name)
        if pr.status != "Paid":
            pr.set_as_paid()
            frappe.db.commit()


def get_company_and_gateway(pr_name):
    """Retourne (company, gateway_key) depuis un Payment Request."""
    if not pr_name or not frappe.db.exists("Payment Request", pr_name):
        return None, None
    company, payment_gateway = frappe.db.get_value(
        "Payment Request", pr_name, ["company", "payment_gateway"]
    )
    return company, resolve_gateway_from_pr(payment_gateway)
