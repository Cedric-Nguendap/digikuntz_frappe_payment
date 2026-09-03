import requests
import frappe
import digikuntz_frappe_payment.services.utils as utils_func
from digikuntz_frappe_payment.integrations.base_client import BasePaymentClient, ok, err


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
            return r.json()
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def _get(self, endpoint, params=None):
        try:
            r = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self._headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency="XAF", company=None, customer_name=None, callback_url=None):
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

        result = self._post("/payments", payload)
        if isinstance(result, tuple):
            return err(result[1])
        link = (result.get("data") or {}).get("link")
        if not link:
            return err(result.get("message") or "Flutterwave n'a pas retourné de lien de paiement")
        return ok({"redirect_url": link, "transaction_id": tx_ref})

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CM", currency="XAF", company=None, customer_name=None, callback_url=None):
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

        result = self._post("/charges?type=mobile_money_franco", payload)
        if isinstance(result, tuple):
            return err(result[1])
        if result.get("status") != "success":
            return err(result.get("message") or "Flutterwave mobile money initialization failed")
        return ok({"transaction_id": (result.get("data") or {}).get("id") or tx_ref})

    def verify_transaction(self, transaction_id):
        result = self._get(f"/transactions/{transaction_id}/verify")
        if isinstance(result, tuple):
            return err(result[1])
        data = result.get("data") or {}
        return ok({
            "status": "successful" if data.get("status") == "successful" else data.get("status", "pending"),
            "tx_ref": data.get("tx_ref", "")
        })

    def verify_transaction_by_reference(self, tx_ref):
        result = self._get("/transactions/verify_by_reference", params={"tx_ref": tx_ref})
        if isinstance(result, tuple):
            return err(result[1])
        data = result.get("data") or {}
        return ok({
            "status": "successful" if data.get("status") == "successful" else data.get("status", "pending"),
            "tx_ref": data.get("tx_ref", tx_ref)
        })

    def verify_webhook_signature(self, payload, signature):
        secret_hash = self.settings.get_password("webhook_secret") or ""
        if secret_hash and signature != secret_hash:
            return False
        return True

    def extract_tx_ref_from_webhook(self, transaction):
        if transaction.get("event") == "charge.completed":
            return transaction.get("data", {}).get("tx_ref")
        return None

    def get_banks(self, country):
        result = self._get(f"/banks/{country}")
        if isinstance(result, tuple):
            return err(result[1])
        banks = [{"name": b.get("name"), "code": b.get("code")} for b in (result.get("data") or [])]
        return ok({"banks": banks})

    def get_all_subaccount(self):
        result = self._get("/subaccounts")
        if isinstance(result, tuple):
            return err(result[1])
        return ok({"subaccounts": result.get("data") or []})

    def get_subaccount_infos(self, subaccount_id):
        result = self._get(f"/subaccounts/{subaccount_id}")
        if isinstance(result, tuple):
            return err(result[1])
        return ok({"subaccount": result.get("data") or {}})

    def create_subaccount(self, company, account_bank, account_number, business_email):
        payload = {
            "account_bank": account_bank,
            "account_number": account_number,
            "business_name": company.company_name,
            "business_email": business_email,
            "split_type": "percentage",
            "split_value": 0
        }
        result = self._post("/subaccounts", payload)
        if isinstance(result, tuple):
            return err(result[1])
        if result.get("status") != "success":
            return err(result.get("message") or "Subaccount creation failed")
        return ok({"subaccount": result.get("data") or {}})
