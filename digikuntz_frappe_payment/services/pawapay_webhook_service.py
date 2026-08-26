import json
import frappe

from frappe_digikuntz_flutterwave.integrations.payment_client_factory import (
    PaymentClientFactory
)

from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry


class FlutterwaveWebhookService:

    def __init__(self):
        self.payment_mode = PaymentClientFactory.get_payment_client()
        self.settings = self.payment_mode["mode"]   
        self.client = self.payment_mode["client"]


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