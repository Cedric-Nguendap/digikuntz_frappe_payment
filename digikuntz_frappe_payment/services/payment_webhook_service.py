import json
import hmac
import hashlib
import frappe

from digikuntz_frappe_payment.integrations.payment_client_factory import (
    PaymentClientFactory
)

from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry


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
            event = transaction.get("event", "")

            if event == "charge.completed":
                self.process_successful_payment(transaction)
                return {"status": "success"}

            return {"status": "ignored", "event": event}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Webhook processing error")
            return {"status": "error", "message": str(e)}

    def process_successful_payment(self, transaction):

        data = transaction.get("data", {})

        tx_ref = data.get("tx_ref")

        pr_name = frappe.db.get_value( "Payment Request", {"name": tx_ref.replace("PR-", "",1)}, "name")
        pr = frappe.get_doc("Payment Request", pr_name)
        pr.set_as_paid() 
            
        # 3. Validation explicite de la transaction dans la BDD
        frappe.db.commit()
        
    
    def process_success_by_transaction_id(self, transaction_id):
        transaction = self.client.verify_transaction(transaction_id)
        return self.process_successful_payment(transaction)

    def handle_transaction_status(self, transaction_id, is_web_payment = True):

        if is_web_payment:
            transaction = self.client.verify_transaction(transaction_id)
        else:
            transaction = self.client.verify_transaction_by_reference(transaction_id)

        if transaction.get("status_code") == "success" and transaction.get("status") != "error":            
            status = transaction.get("data", {}).get("status")

            if status == "successful":
                self.process_successful_payment(transaction)
            else:
                frappe.logger().warning(f"Transaction {transaction_id} has status {status}")
        else:
            frappe.logger().error(f"Transaction verification failed for ID {transaction_id}: {transaction.get('message')}")
            status = "error"

        return status