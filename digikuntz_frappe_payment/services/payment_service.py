import frappe

from digikuntz_frappe_payment.integrations.payment_client_factory import PaymentClientFactory
import digikuntz_frappe_payment.services.utils as utils_func


class PaymentService:

    def __init__(self, company=None):
        self.payment_mode = PaymentClientFactory.get_payment_client(company=company)
        self.mode_name = self.payment_mode["mode"]
        self.client = self.payment_mode["client"]

    def create_payment_link(self, reference_doc, payer_email=None):
        amount = reference_doc.grand_total or 0
        if amount <= 0:
            frappe.throw(f"{reference_doc.doctype} {reference_doc.name}: grand_total is 0 or missing")

        tx_ref = f"PR-{reference_doc.name}"
        base_url = frappe.utils.get_url()
        redirect_url = base_url + "/payment-success"
        callback_url = base_url + "/api/method/digikuntz_frappe_payment.api.webhook.payment_webhook"

        email = payer_email or reference_doc.email_to or reference_doc.contact_email or reference_doc.owner
        customer = reference_doc.party or reference_doc.customer_name
        company = frappe.get_doc("Company", reference_doc.company)

        if not email or "@" not in email:
            frappe.throw(f"Customer email is required for {self.mode_name} payment")

        response = self.client.initialize_web_payment(
            amount=amount,
            email=email,
            tx_ref=tx_ref,
            redirect_url=redirect_url,
            callback_url=callback_url,
            customer_name=customer,
            company=company,
            currency=reference_doc.currency
        )

        if not response.get("ok"):
            frappe.throw(response.get("error") or f"{self.mode_name} payment initialization failed")
        return response

    def mobile_money_charge(self, reference_doc, phone_number, network):
        amount = reference_doc.grand_total or 0
        email = reference_doc.email_to or reference_doc.contact_email or reference_doc.owner
        customer = reference_doc.party or reference_doc.customer_name
        company = frappe.get_doc("Company", reference_doc.company)

        base_url = frappe.utils.get_url()
        redirect_url = base_url + "/payment-success"
        callback_url = base_url + "/api/method/digikuntz_frappe_payment.api.webhook.payment_webhook"
        tx_ref = f"PR-{reference_doc.name}"

        response = self.client.initialize_mobile_money_payment(
            amount=amount,
            email=email,
            tx_ref=tx_ref,
            phone_number=phone_number,
            network=network,
            customer_name=customer,
            company=company,
            redirect_url=redirect_url,
            callback_url=callback_url,
            currency=reference_doc.currency
        )

        frappe.logger().info(response)
        return response

    def sync_subaccount(self):
        return self.client.get_all_subaccount()

    def create_subaccount(self, company, account_bank, account_number):
        business_email = utils_func.get_current_user_email()
        return self.client.create_subaccount(company, account_bank, account_number, business_email)

    def load_subaccount_infos(self, subaccount_id):
        return self.client.get_subaccount_infos(subaccount_id)

    def get_banks(self, country="CM"):
        return self.client.get_banks(country)
