import uuid
import hmac
import hashlib
import requests
import frappe
from digikuntz_frappe_payment.integrations.base_client import BasePaymentClient, ok, err


class PawaPayClient(BasePaymentClient):

    def __init__(self, company=None):
        self.company = company
        self._load_config()

    def _load_config(self):
        if self.company:
            doc = frappe.get_cached_doc("Company", self.company)
            self.enabled = bool(doc.custom_pp_enable)
            self.secret_key = doc.custom_pp_secret_key or ""
            self.webhook_secret_val = doc.get_password("custom_pp_webhook_secret") if doc.custom_pp_webhook_secret else ""
            self.base_url = (doc.custom_pp_base_url or "https://api.pawapay.io").rstrip("/")
            self.default_country = doc.custom_pp_default_country or ""
        else:
            self.enabled = False
            self.secret_key = ""
            self.webhook_secret_val = ""
            self.base_url = "https://api.pawapay.io"
            self.default_country = ""

    def validate(self):
        if not self.enabled:
            frappe.throw(
                msg="PawaPay est desactive pour cette société.",
                title="PawaPay Inactif",
                exc=frappe.ValidationError
            )
        if not self.secret_key:
            frappe.throw(
                msg="PawaPay API Token est requis. Veuillez le configurer dans les paramètres de la société.",
                title="Configuration manquante",
                exc=frappe.ValidationError
            )

    def get_configuration_issues(self):
        issues = []
        if not self.enabled:
            issues.append("PawaPay est désactivé.")
        if not self.secret_key:
            issues.append("API Token manquant.")
        if not self.default_country:
            issues.append("Pays par défaut (ISO alpha-3) manquant.")
        return issues

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

    def _get(self, endpoint):
        try:
            r = requests.get(f"{self.base_url}{endpoint}", headers=self._headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency="XAF", company=None, customer_name=None, callback_url=None):
        """Payment Page PawaPay v2 — POST /v2/paymentpage"""
        country = self.default_country
        if not country:
            frappe.throw(
                msg="Le pays par défaut (ISO alpha-3) est requis dans les paramètres de la société.",
                title="Configuration manquante",
                exc=frappe.ValidationError
            )

        deposit_id = str(uuid.uuid4())

        payload = {
            "depositId": deposit_id,
            "returnUrl": redirect_url,
            "amountDetails": {"amount": str(int(amount)), "currency": currency},
            "country": country,
            "reason": tx_ref,
            "language": "FR"
        }
        # if callback_url:
        #     payload["notificationUrl"] = callback_url

        result = self._post("/v2/paymentpage", payload)
        # raise Exception()
        if isinstance(result, tuple):
            return err(result[1])
        pawapay_redirect = result.get("redirectUrl")
        if not pawapay_redirect:
            return err(result.get("errorMessage") or "PawaPay n'a pas retourné de redirectUrl")
        return ok({"redirect_url": pawapay_redirect, "transaction_id": deposit_id})

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CMR", currency="XAF", company=None, customer_name=None, callback_url=None):
        """Direct deposit PawaPay v2 — POST /v2/deposits"""
        deposit_id = str(uuid.uuid4())
        _store_pawapay_data(tx_ref, deposit_id)

        payload = {
            "depositId": deposit_id,
            "amount": str(int(amount)),
            "currency": currency,
            "payer": {
                "type": "MMO",
                "accountDetails": {"provider": f"{network}_{country}", "phoneNumber": phone_number}
            },
            "customerMessage": f"Payment {tx_ref}"
        }
        if callback_url:
            payload["notificationUrl"] = callback_url

        result = self._post("/v2/deposits", payload)
        print("Result",payload, result)

        if isinstance(result, tuple):
            return err(result[1])
        if result.get("status") not in ("ACCEPTED", None) and result.get("errorCode"):
            return err(result.get("errorMessage") or "PawaPay deposit initialization failed")
        return ok({"transaction_id": deposit_id})

    def verify_transaction(self, deposit_id):
        """GET /v2/deposits/:depositId — retourne une liste"""
        result = self._get(f"/v2/deposits/{deposit_id}")
        if isinstance(result, tuple):
            return err(result[1])
        frappe.logger().info(f"PawaPay verify_transaction raw: {result}")
        data = result[0] if isinstance(result, list) and result else result
        if not data:
            return err(f"Deposit {deposit_id} not found")
        status_val = data.get("status", "")
        if status_val == "NOT_FOUND":
            return err(f"Deposit {deposit_id} not found")
        data  = data.get("data") or {}
        return ok({
            "status": _normalize_pawapay_status(data.get("status")),
            "tx_ref": _extract_tx_ref_from_message(data.get("customerMessage", ""))
        })

    def verify_transaction_by_reference(self, tx_ref):
        deposit_id = _get_deposit_id(tx_ref)
        if not deposit_id:
            return err(f"Aucun depositId trouvé pour {tx_ref}")
        return self.verify_transaction(deposit_id)

    def verify_webhook_signature(self, payload, signature):
        secret = self.webhook_secret_val or ""
        if not secret:
            return True
        expected = hmac.new(secret.encode(), payload.encode() if isinstance(payload, str) else payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def extract_tx_ref_from_webhook(self, transaction):
        if transaction.get("status") == "COMPLETED":
            return _extract_tx_ref_from_message(transaction.get("customerMessage", ""))
        return None

    def get_banks(self, country):
        result = self._get(f"/v2/active-conf?country={country}&operationType=DEPOSIT")
        if isinstance(result, tuple):
            return err(result[1])
        banks = []
        for c in result.get("countries", []):
            for p in c.get("providers", []):
                banks.append({"name": p.get("provider"), "code": p.get("provider")})
        return ok({"banks": banks})


# --- Helpers privés au module ---

def _normalize_pawapay_status(status):
    return {
        "COMPLETED": "successful",
        "FAILED": "failed",
        "ACCEPTED": "pending",
        "PROCESSING": "pending",
        "IN_RECONCILIATION": "pending",
        "DUPLICATE_IGNORED": "failed",
        "REJECTED": "failed",
        "TIMED_OUT": "failed",
    }.get(status.upper() if status else "", "pending")


def _extract_tx_ref_from_message(message):
    if message and message.startswith("Payment "):
        return message.replace("Payment ", "", 1).strip()
    return message or None


def _store_pawapay_data(tx_ref, deposit_id):
    """Stocke le deposit_id dans Payment Redirect pour le suivi MoMo."""
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if not frappe.db.exists("Payment Request", pr_name):
            return
        existing = frappe.db.get_value("Payment Redirect", {"payment_request": pr_name}, "name")
        if existing:
            frappe.db.set_value("Payment Redirect", existing, "deposit_id", deposit_id)
        else:
            frappe.get_doc({
                "doctype": "Payment Redirect",
                "payment_request": pr_name,
                "redirect_url": "/payment-success",
                "deposit_id": deposit_id,
            }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass


def _get_deposit_id(tx_ref):
    return _get_pawapay_field(tx_ref, "pawapay_deposit_id")


def _get_redirect_url(tx_ref):
    return _get_pawapay_field(tx_ref, "pawapay_redirect_url")


def _get_pawapay_field(tx_ref, key):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if key == "pawapay_deposit_id":
            return frappe.db.get_value("Payment Redirect", {"payment_request": pr_name}, "deposit_id") or None
    except Exception:
        pass
    return None
