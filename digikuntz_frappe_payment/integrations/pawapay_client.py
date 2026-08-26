import requests
import frappe
import frappe_digikuntz_flutterwave.services.utils as utils_func


class PawaPayClient:

    def __init__(self):
        self.settings = frappe.get_single("PawaPay Settings")
        self.base_url = ""
        self.secret_key = self.settings.get_password("secret_key")


    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_web_payment(
        self,
        amount,
        email,
        tx_ref,
        redirect_url,
        currency="XAF",
        company = None,
        customer_name=None
    ):
    
        payload = {
        }

        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de procéder au paiement car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="Composant Inactif",
                exc=frappe.ValidationError
            )

        if utils_func.should_use_subaccount(company):
            id_sous_compte = frappe.get_doc("PawaPay SubAccount", company.custom_sous_compte_par_defaut).subaccount_id

            payload["subaccounts"]= [
                {
                    "id": id_sous_compte
                }
            ]
        
        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=self.headers
            )            
            data = {**response.json(), "status_code": "success"}
        except requests.exceptions.HTTPError as http_err:
            data = {"status_code": "error", "message": str(http_err)}
        return data

    def initialize_mobile_money_payment(
        self,
        amount,
        email,
        tx_ref,
        redirect_url,
        phone_number,
        network,
        country="CM",
        currency="XAF",
        company = None,
        customer_name=None
    ):
    
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "country": country,
            "email": email,
            "phone_number": phone_number,
            "fullname": customer_name or email,
            "network": network,
            "redirect_url": redirect_url
        }

        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de procéder au paiement car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )

        if utils_func.should_use_subaccount(company):
            id_sous_compte = frappe.get_doc("PawaPay SubAccount", company.custom_sous_compte_par_defaut).subaccount_id
            payload["subaccounts"]= [
                {
                    "id": id_sous_compte
                }
            ]

        try:
            response = requests.post(
                f"{self.base_url}/charges?type=mobile_money_franco",
                json=payload,
                headers=self.headers
            )            
            data = {**response.json(), "status_code": "success"}
        except requests.exceptions.HTTPError as http_err:
            data = {"status_code": "error", "message": str(http_err)}
        return data
    

    def verify_transaction(self,transaction_id):
        try:
            if not utils_func.can_use_pawapay():
                frappe.throw(
                    msg="Impossible de procéder a la vérification du paiement car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                    title="PawaPay Inactif",
                    exc=frappe.ValidationError
                )

            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}/verify",
                headers=self.headers
            )
            data = {**response.json(), "status_code": "success"}
        except requests.exceptions.HTTPError as http_err:
            data = {"status_code": "error", "message": str(http_err)}

        return data
    

    def verify_transaction_by_reference(self,reference):
        try:
            if not utils_func.can_use_pawapay():
                frappe.throw(
                    msg="Impossible de procéder a la vérification du paiement car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                    title="PawaPay Inactif",
                    exc=frappe.ValidationError
                )
            response = requests.get(
                f"{self.base_url}/transactions/verify_by_reference?tx_ref={reference}",
                headers=self.headers
            )
            data = {**response.json(), "status_code": "success"}
        except requests.exceptions.HTTPError as http_err:
            data = {"status_code": "error", "message": str(http_err)}

        return data
    

    def create_subaccount(self, company,account_bank,account_number,business_email):
        payload = {
            "account_bank": account_bank,
            "account_number": account_number,
            "business_name": company.company_name,
            "business_email": business_email,
            "split_type": "percentage",
            "split_value": 0
        }
        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de procéder a la création du sous-compte car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        response = requests.post(
            f"{self.base_url}/subaccounts",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_all_subaccount(self):
        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de procéder a la récupération des sous-comptes car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        response = requests.get(
            f"{self.base_url}/subaccounts",
            headers=self.headers
        )
        return response.json()
    
    def get_subaccount_infos(self,subaccount_id):
        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de récupérer les informations du sous-comptes car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        
        payload = {
            "id": subaccount_id
        }

        response  = requests.get(
             f"{self.base_url}/subaccounts",
            json=payload,
            headers=self.headers
        )
        return response.json()


    def get_banks(self, country):

        if not utils_func.can_use_pawapay():
            frappe.throw(
                msg="Impossible de procéder a la récupération des banques car le composant PawaPay est désactivé.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        response = requests.get(f"{self.base_url}/banks/{country}",headers=self.headers)

        return response.json()
    
