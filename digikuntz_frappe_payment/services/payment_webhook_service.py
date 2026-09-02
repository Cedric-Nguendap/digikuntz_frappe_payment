import json
import frappe
from digikuntz_frappe_payment.integrations.payment_client_factory import PaymentClientFactory


class PaymentWebhookService:

    def __init__(self, company=None):
        self.payment_mode = PaymentClientFactory.get_payment_client(company=company)
        self.mode_name = self.payment_mode["mode"]
        self.client = self.payment_mode["client"]

    def handle_webhook(self, payload, signature):
        try:
            if not self.client.verify_webhook_signature(payload, signature):
                frappe.logger().warning("Webhook signature mismatch")
                return {"status": "error", "message": "Invalid signature"}

            transaction = json.loads(payload)

            # Chaque client sait reconnaître son propre format de webhook
            tx_ref = self.client.extract_tx_ref_from_webhook(transaction)
            if tx_ref:
                self._process_successful_payment(tx_ref)
                return {"status": "success"}

            return {"status": "ignored"}

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Webhook processing error")
            return {"status": "error", "message": str(e)}

    def handle_transaction_status(self, transaction_id, is_web_payment=True):
        if is_web_payment:
            transaction = self.client.verify_transaction(transaction_id)
        else:
            transaction = self.client.verify_transaction_by_reference(transaction_id)

        if transaction.get("status_code") == "success":
            status = transaction.get("data", {}).get("status")
            if status == "successful":
                tx_ref = transaction.get("data", {}).get("tx_ref", "")
                self._process_successful_payment(tx_ref)
            return status

        frappe.logger().error(
            f"Transaction verification failed for {transaction_id}: {transaction.get('message')}"
        )
        return "error"

    def _process_successful_payment(self, tx_ref):
        pr_name = tx_ref.replace("PR-", "", 1)
        if not pr_name or not frappe.db.exists("Payment Request", pr_name):
            frappe.logger().warning(f"Payment Request introuvable pour tx_ref: {tx_ref}")
            return
        pr = frappe.get_doc("Payment Request", pr_name)
        if pr.status != "Paid":
            pr.set_as_paid()
            frappe.db.commit()
