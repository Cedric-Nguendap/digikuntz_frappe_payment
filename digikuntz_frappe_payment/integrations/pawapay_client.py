import uuid
import hmac
import hashlib
import requests
import frappe
from digikuntz_frappe_payment.integrations.base_client import BasePaymentClient, ok, err


class PawaPayClient(BasePaymentClient):

    def __init__(self):
        self.settings = frappe.get_single("Pawapay Settings")
        self.base_url = (self.settings.base_url or "https://api.pawapay.io").rstrip("/")
        self.secret_key = self.settings.get_password("secret_key")

    def validate(self):
        if not self.settings.enable_pawapay:
            frappe.throw(
                msg="PawaPay est desactive. Veuillez l'activer dans Pawapay Settings.",
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
        country = self.settings.default_country or ""
        if not country:
            frappe.throw(
                msg="Le pays par defaut (ISO alpha-3) est requis dans Pawapay Settings pour la Payment Page.",
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
        if isinstance(result, tuple):
            return err(result[1])
        pawapay_redirect = result.get("redirectUrl")
        if not pawapay_redirect:
            return err(result.get("errorMessage") or "PawaPay n'a pas retourné de redirectUrl")
        return ok({"redirect_url": pawapay_redirect, "transaction_id": deposit_id})

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CM", currency="XAF", company=None, customer_name=None, callback_url=None):
        """Direct deposit PawaPay v2 — POST /v2/deposits"""
        deposit_id = str(uuid.uuid4())
        _store_pawapay_data(tx_ref, deposit_id)

        payload = {
            "depositId": deposit_id,
            "amount": str(int(amount)),
            "currency": currency,
            "payer": {
                "type": "MMO",
                "accountDetails": {"provider": network, "phoneNumber": phone_number}
            },
            "customerMessage": f"Payment {tx_ref}"
        }
        if callback_url:
            payload["notificationUrl"] = callback_url

        result = self._post("/v2/deposits", payload)
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
        frappe.logger().info(f"PawaPay verify_transaction raw response: {result}")
        # L'API PawaPay v2 retourne une liste
        data = result[0] if isinstance(result, list) and result else result
        if not data or data.get("status") == "NOT_FOUND":
            return err(f"Deposit {deposit_id} not found")
        return ok({
            "status": _normalize_pawapay_status(data.get("status", "")),
            "tx_ref": _extract_tx_ref_from_message(data.get("customerMessage", ""))
        })

    def verify_transaction_by_reference(self, tx_ref):
        deposit_id = _get_deposit_id(tx_ref)
        if not deposit_id:
            return err(f"Aucun depositId trouvé pour {tx_ref}")
        return self.verify_transaction(deposit_id)

    def verify_webhook_signature(self, payload, signature):
        secret = self.settings.get_password("webhook_secret") or ""
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


def _store_pawapay_data(tx_ref, deposit_id, redirect_url=None):
    try:
        pr_name = tx_ref.replace("PR-", "", 1)
        if not frappe.db.exists("Payment Request", pr_name):
            return
        existing = frappe.db.get_value("Payment Request", pr_name, "message") or ""
        lines = [l for l in existing.split("\n") if not l.startswith("pawapay_")]
        lines.append(f"pawapay_deposit_id:{deposit_id}")
        if redirect_url:
            lines.append(f"pawapay_redirect_url:{redirect_url}")
        frappe.db.set_value("Payment Request", pr_name, "message", "\n".join(lines).strip(), update_modified=False)
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
        data = frappe.db.get_value("Payment Request", pr_name, "message") or ""
        for line in data.split("\n"):
            if line.startswith(f"{key}:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None
