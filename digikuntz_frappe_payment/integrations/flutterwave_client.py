import requests
import frappe
import digikuntz_frappe_payment.services.utils as utils_func
from digikuntz_frappe_payment.integrations.base_client import BasePaymentClient


class FlutterwaveClient(BasePaymentClient):

    def __init__(self):
        self.settings = frappe.get_single("Flutterwave Settings")
        self.base_url = "https://api.flutterwave.com/v3"
        self.secret_key = self.settings.get_password("secret_key")

    def validate(self):
        if not self.settings.enable_flutterwave:
            frappe.throw(
                msg="Flutterwave est désactivé. Veuillez l'activer dans Flutterwave Settings.",
                title="Flutterwave Inactif",
                exc=frappe.ValidationError
            )
        if not self.secret_key or not self.settings.public_key:
            frappe.throw(
                msg="Flutterwave n'est pas configuré. Secret Key et Public Key sont requis.",
                title="Configuration manquante",
                exc=frappe.ValidationError
            )

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def _post(self, endpoint, payload):
        try:
            r = requests.post(f"{self.base_url}{endpoint}", json=payload, headers=self._headers, timeout=30)
            r.raise_for_status()
            return {**r.json(), "status_code": "success"}
        except requests.exceptions.RequestException as e:
            return {"status_code": "error", "message": str(e)}

    def _get(self, endpoint, params=None):
        try:
            r = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self._headers, timeout=30)
            r.raise_for_status()
            return {**r.json(), "status_code": "success"}
        except requests.exceptions.RequestException as e:
            return {"status_code": "error", "message": str(e)}

    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency="XAF", company=None, customer_name=None):
        payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {"email": email, "name": customer_name or email},
            "customizations": {"title": "ERPNext Payment", "description": "Invoice Payment"}
        }
        if utils_func.should_use_subaccount(company):
            subaccount_id = utils_func.get_subaccount_id(company)
            if subaccount_id:
                payload["subaccounts"] = [{"id": subaccount_id}]
        return self._post("/payments", payload)

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CM", currency="XAF", company=None, customer_name=None):
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
        if utils_func.should_use_subaccount(company):
            subaccount_id = utils_func.get_subaccount_id(company)
            if subaccount_id:
                payload["subaccounts"] = [{"id": subaccount_id}]
        return self._post("/charges?type=mobile_money_franco", payload)

    def verify_transaction(self, transaction_id):
        result = self._get(f"/transactions/{transaction_id}/verify")
        if result.get("status_code") == "success":
            data = result.get("data", {})
            result["data"] = {
                "status": "successful" if data.get("status") == "successful" else data.get("status", "pending"),
                "tx_ref": data.get("tx_ref", "")
            }
        return result

    def verify_transaction_by_reference(self, tx_ref):
        result = self._get("/transactions/verify_by_reference", params={"tx_ref": tx_ref})
        if result.get("status_code") == "success":
            data = result.get("data", {})
            result["data"] = {
                "status": "successful" if data.get("status") == "successful" else data.get("status", "pending"),
                "tx_ref": data.get("tx_ref", tx_ref)
            }
        return result

    def verify_webhook_signature(self, payload, signature):
        secret_hash = self.settings.get_password("webhook_secret") or ""
        if secret_hash and signature != secret_hash:
            return False
        return True

    def extract_tx_ref_from_webhook(self, transaction):
        """Flutterwave: event=charge.completed, tx_ref dans data.tx_ref"""
        if transaction.get("event") == "charge.completed":
            return transaction.get("data", {}).get("tx_ref")
        return None

    def get_banks(self, country):
        return self._get(f"/banks/{country}")

    def get_all_subaccount(self):
        return self._get("/subaccounts")

    def get_subaccount_infos(self, subaccount_id):
        return self._get(f"/subaccounts/{subaccount_id}")

    def create_subaccount(self, company, account_bank, account_number, business_email):
        payload = {
            "account_bank": account_bank,
            "account_number": account_number,
            "business_name": company.company_name,
            "business_email": business_email,
            "split_type": "percentage",
            "split_value": 0
        }
        return self._post("/subaccounts", payload)
