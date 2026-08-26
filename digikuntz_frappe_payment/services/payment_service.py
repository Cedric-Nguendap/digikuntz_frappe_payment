import frappe


import frappe_digikuntz_payment.services.utils as utils_func

class PaymentService:

    def __init__(self):
        self.client = self.get_payment_client(None)
        self.payment_mode = "Flutterwave" #"PawaPay"

    

    def create_payment_link( self, reference_doc, payer_email=None):
        if reference_doc.outstanding_amount <= 0:
        # if reference_doc.grand_total <= 0:
            frappe.throw(f"{reference_doc.reference_doctype} is already paid")

        tx_ref = f"PR-{reference_doc.name}"

        redirect_url = (
            frappe.utils.get_url()
            + "/payment-payment-success"
        )
        
        email = payer_email or reference_doc.email_to or reference_doc.contact_email or reference_doc.owner
        customer = reference_doc.party or reference_doc.customer_name
        company = frappe.get_doc("Company",reference_doc.company)

        if not email or "@" not in email:
            frappe.throw(
                f"Customer email is required for {self.payment_mode} payment"
            )

        response = self.client.initialize_web_payment(
            # amount=reference_doc.grand_total,
            amount=reference_doc.outstanding_amount,
            email=email,
            tx_ref=tx_ref,
            redirect_url=redirect_url,
            customer_name=customer,
            company=company,
            currency=reference_doc.currency
        )

        if response.get("status_code") != "success":

            frappe.throw(
                response.get("message")
                or f"{self.payment_mode} payment initialization failed"
            )
        return response
    
    def mobile_money_charge( self, reference_doc,phone_number, network):
        ##MEttre un if, elle pour le setting en fonction des moyens de paiements
        settings = frappe.get_single(f"{self.payment_mode} Settings")

        email = reference_doc.email_to or reference_doc.contact_email or reference_doc.owner
        customer = reference_doc.party or reference_doc.customer_name
        company = frappe.get_doc("Company",reference_doc.company)

        redirect_url = (
            frappe.utils.get_url()+ "/payment-payment-success"
        )

        tx_ref = f"PR-{reference_doc.name}"        

        response_data = self.client.initialize_mobile_money_payment(
            amount=reference_doc.outstanding_amount,
            email=email,
            tx_ref=tx_ref,
            phone_number=phone_number,
            network=network,
            customer_name=customer,
            company=company,
            redirect_url=redirect_url,
            currency=reference_doc.currency
        )

        frappe.logger().info(response_data)

        return response_data

    def sync_subaccount(self):
        return self.client.get_all_subaccount()

    def create_subaccount(self, company,account_bank,account_number):
        business_email = utils_func.get_current_user_email()
        return self.client.create_subaccount(company,account_bank,account_number,business_email)

    def load_subaccount_infos(self,subaccount_id):
        return self.client.get_subaccount_infos(subaccount_id)

    def get_banks(self, country="CM"):
        return self.client.get_banks(country)