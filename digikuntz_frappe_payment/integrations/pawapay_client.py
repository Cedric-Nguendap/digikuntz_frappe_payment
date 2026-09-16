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
                msg="PawaPay API Token est requis.",
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
            if not r.ok:
                return None, f"{r.status_code}: {r.text[:500]}"
            return r.json()
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def _get(self, endpoint):
        try:
            r = requests.get(f"{self.base_url}{endpoint}", headers=self._headers, timeout=30)
            if not r.ok:
                return None, f"{r.status_code}: {r.text[:500]}"
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
        if isinstance(result, tuple):
            return err(result[1])
        pawapay_redirect = result.get("redirectUrl")
        if not pawapay_redirect:
            return err(result.get("errorMessage") or "PawaPay n'a pas retourné de redirectUrl")
        return ok({"redirect_url": pawapay_redirect, "transaction_id": deposit_id})

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CMR", currency="XAF", company=None, customer_name=None, callback_url=None):
        """Direct deposit PawaPay v2 — POST /v2/deposits"""
        # country doit être ISO alpha-3 (CMR, SEN...) — utiliser default_country si disponible
        effective_country = self.default_country or country
        deposit_id = str(uuid.uuid4())

        payload = {
            "depositId": deposit_id,
            "amount": str(int(amount)),
            "currency": currency,
            "payer": {
                "type": "MMO",
                "accountDetails": {
                    "provider": f"{network}_{effective_country}",
                    "phoneNumber": phone_number
                }
            },
            # "customerMessage": f"Payment {tx_ref}"
        }
        # if callback_url:
        #     payload["notificationUrl"] = callback_url

        result = self._post("/v2/deposits", payload)
        if isinstance(result, tuple):
            return err(result[1])
        if result.get("errorCode"):
            return err(result.get("errorMessage") or "PawaPay deposit initialization failed")
        return ok({"transaction_id": deposit_id})

    def verify_transaction(self, deposit_id):
        """GET /v2/deposits/:depositId"""
        result = self._get(f"/v2/deposits/{deposit_id}")
        if isinstance(result, tuple):
            return err(result[1])
        if result.get("status") == "NOT_FOUND":
            return err(f"Deposit {deposit_id} not found")
        data = result.get("data") or {}
        if not data:
            return err(f"Deposit {deposit_id} returned empty data")
        print("Data data ",data)
        pr_name = frappe.db.get_value("Payment Redirect", {"deposit_id": deposit_id}, "payment_request") or ""
        tx_ref = f"PR-{pr_name}" if pr_name else ""
        return ok({
            "status": _normalize_pawapay_status(data.get("status", "")),
            "tx_ref": tx_ref
        })

    def verify_transaction_by_reference(self, tx_ref):
        pr_name = tx_ref.replace("PR-", "", 1)
        deposit_id = frappe.db.get_value("Payment Redirect", {"payment_request": pr_name}, "deposit_id") or ""
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
        if transaction.get("status") != "COMPLETED":
            return None
        deposit_id = transaction.get("depositId") or ""
        if not deposit_id:
            return None
        pr_name = frappe.db.get_value("Payment Redirect", {"deposit_id": deposit_id}, "payment_request") or ""
        return f"PR-{pr_name}" if pr_name else None

    def get_banks(self, country):
        result = self._get(f"/v2/active-conf?country={country}&operationType=DEPOSIT")
        if isinstance(result, tuple):
            return err(result[1])
        banks = []
        for c in (result.get("countries") or []):
            for p in (c.get("providers") or []):
                banks.append({"name": p.get("provider"), "code": p.get("provider")})
        return ok({"banks": banks})

    def get_momo_operators(self, country="CM"):
        """Retourne les operateurs Mobile Money disponibles pour un pays."""
        # Flutterwave n'a pas d'endpoint dédié pour les opérateurs MoMo franco
        # Liste statique basée sur la doc Flutterwave mobile_money_franco
        operators_by_country = {
            "CM": [
                {"name": "MTN Mobile Money", "code": "MTN"},
                {"name": "Orange Money", "code": "ORANGE"},
            ],
            "SN": [
                {"name": "Orange Money", "code": "ORANGE"},
                {"name": "Free Money", "code": "FREE"},
                {"name": "Wave", "code": "WAVE"},
            ],
            "CI": [
                {"name": "MTN Mobile Money", "code": "MTN"},
                {"name": "Orange Money", "code": "ORANGE"},
                {"name": "Wave", "code": "WAVE"},
            ],
            "GH": [
                {"name": "MTN Mobile Money", "code": "MTN"},
                {"name": "Vodafone Cash", "code": "VODAFONE"},
                {"name": "AirtelTigo Money", "code": "TIGO"},
            ],
            "ZM": [
                {"name": "MTN Mobile Money", "code": "MTN"},
                {"name": "Airtel Money", "code": "AIRTEL"},
                {"name": "Zamtel Money", "code": "ZAMTEL"},
            ],
        }
        ops = operators_by_country.get(country.upper(), [
            {"name": "MTN Mobile Money", "code": "MTN"},
            {"name": "Orange Money", "code": "ORANGE"}
        ])
        return ok({"banks": ops})


# --- Helpers ---

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

