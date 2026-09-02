import uuid
import hmac
import hashlib
import requests
import frappe
from digikuntz_frappe_payment.integrations.base_client import BasePaymentClient


class PawaPayClient(BasePaymentClient):

    def __init__(self):
        self.settings = frappe.get_single("Pawapay Settings")
        self.base_url = (self.settings.base_url or "https://api.pawapay.io").rstrip("/")
        self.secret_key = self.settings.get_password("secret_key")

    def validate(self):
        if not self.settings.enable_pawapay:
            frappe.throw(
                msg="PawaPay est désactivé. Veuillez l'activer dans Pawapay Settings.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        if not self.secret_key:
            frappe.throw(
                msg="PawaPay API Token est requis. Veuillez le configurer dans Pawapay Settings.",
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

    def _get(self, endpoint):
        try:
            r = requests.get(f"{self.base_url}{endpoint}", headers=self._headers, timeout=30)
            r.raise_for_status()
            return {**r.json(), "status_code": "success"}
        except requests.exceptions.RequestException as e:
            return {"status_code": "error", "message": str(e)}

    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency="XAF", company=None, customer_name=None):
        frappe.throw(
            msg="PawaPay ne supporte pas les paiements web. Utilisez le paiement Mobile Money.",
            title="Mode non supporté",
            exc=frappe.ValidationError
        )

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CM", currency="XAF", company=None, customer_name=None):
        deposit_id = str(uuid.uuid4())
        _store_deposit_id(tx_ref, deposit_id)

        payload = {
            "depositId": deposit_id,
            "amount": str(int(amount)),
            "currency": currency,
            "correspondent": network,
            "payer": {"type": "MSISDN", "address": {"value": phone_number}},
            "customerTimestamp": frappe.utils.now_datetime().isoformat() + "Z",
            "statementDescription": f"Payment {tx_ref}"
        }
        result = self._post("/deposits", payload)
        if result.get("status_code") == "success":
            result["deposit_id"] = deposit_id
        return result

    def verify_transaction(self, deposit_id):
        result = self._get(f"/deposits/{deposit_id}")
        if result.get("status_code") == "success":
            result["data"] = {
                "status": _normalize_pawapay_status(result.get("status", "")),
                "tx_ref": result.get("statementDescription", "").replace("Payment ", "")
            }
        return result

    def verify_transaction_by_reference(self, tx_ref):
        deposit_id = _get_deposit_id(tx_ref)
        if not deposit_id:
            return {"status_code": "error", "message": f"Aucun depositId trouvé pour {tx_ref}"}
        return self.verify_transaction(deposit_id)

    def verify_webhook_signature(self, payload, signature):
        secret = self.settings.get_password("webhook_secret") or ""
        if not secret:
            return True
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def extract_tx_ref_from_webhook(self, transaction):
        """PawaPay: status=COMPLETED à la racine, tx_ref dans statementDescription"""
        if transaction.get("status") == "COMPLETED":
            statement = transaction.get("statementDescription", "")
            return statement.replace("Payment ", "") if statement else None
        return None

    def get_banks(self, country):
        result = self._get("/active-conf")
        if result.get("status_code") == "success":
            correspondents = result.get("correspondents", [])
            result["data"] = [
                {"name": c.get("correspondent"), "code": c.get("correspondent")}
                for c in correspondents
                if c.get("country") == country
            ]
        return result


# --- Helpers privés au module (pas de méthodes d'instance car pas d'état) ---

def _normalize_pawapay_status(status):
    return {
        "COMPLETED": "successful",
        "FAILED": "failed",
        "PENDING": "pending",
        "DUPLICATE_IGNORED": "failed",
        "REJECTED": "failed",
        "TIMED_OUT": "failed",
    }.get(status.upper() if status else "", "pending")


def _store_deposit_id(tx_ref, deposit_id):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if not frappe.db.exists("Payment Request", pr_name):
            return
        existing = frappe.db.get_value("Payment Request", pr_name, "remarks") or ""
        marker = f"pawapay_deposit_id:{deposit_id}"
        if "pawapay_deposit_id" not in existing:
            new_remarks = f"{existing}\n{marker}".strip()
            frappe.db.set_value("Payment Request", pr_name, "remarks", new_remarks, update_modified=False)
            frappe.db.commit()
    except Exception:
        pass


def _get_deposit_id(tx_ref):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        remarks = frappe.db.get_value("Payment Request", pr_name, "remarks") or ""
        for line in remarks.split("\n"):
            if line.startswith("pawapay_deposit_id:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None
