import uuid
import hmac
import hashlib
import requests
import frappe
import digikuntz_frappe_payment.services.utils as utils_func


class PawaPayClient:

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
    def headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def _post(self, endpoint, payload):
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return {**response.json(), "status_code": "success"}
        except requests.exceptions.RequestException as e:
            return {"status_code": "error", "message": str(e)}

    def _get(self, endpoint):
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return {**response.json(), "status_code": "success"}
        except requests.exceptions.RequestException as e:
            return {"status_code": "error", "message": str(e)}

    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency="XAF", company=None, customer_name=None):
        """
        PawaPay ne supporte pas de checkout web standard.
        Le paiement doit être initié via Mobile Money uniquement.
        """
        frappe.throw(
            msg="PawaPay ne supporte pas les paiements web. Veuillez utiliser le paiement Mobile Money depuis le Payment Request.",
            title="Mode non supporté",
            exc=frappe.ValidationError
        )

    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country="CM", currency="XAF", company=None, customer_name=None):
        """
        PawaPay API: POST /deposits
        Un UUID unique (depositId) est généré et stocké pour permettre la vérification ultérieure.
        """
        deposit_id = str(uuid.uuid4())
        self._store_deposit_id(tx_ref, deposit_id)

        payload = {
            "depositId": deposit_id,
            "amount": str(int(amount)),
            "currency": currency,
            "correspondent": network,
            "payer": {
                "type": "MSISDN",
                "address": {
                    "value": phone_number
                }
            },
            "customerTimestamp": frappe.utils.now_datetime().isoformat() + "Z",
            "statementDescription": f"Payment {tx_ref}"
        }

        result = self._post("/deposits", payload)

        if result.get("status_code") == "success":
            result["deposit_id"] = deposit_id

        return result

    def verify_transaction(self, deposit_id):
        """
        PawaPay API: GET /deposits/{depositId}
        Normalise le statut PawaPay vers le format interne (successful/failed/pending).
        """
        result = self._get(f"/deposits/{deposit_id}")
        if result.get("status_code") == "success":
            pawapay_status = result.get("status", "")
            result["data"] = {
                "status": self._normalize_status(pawapay_status),
                "tx_ref": result.get("statementDescription", "").replace("Payment ", "")
            }
        return result

    def verify_transaction_by_reference(self, tx_ref):
        """
        PawaPay n'a pas de recherche par tx_ref natif.
        On récupère le depositId stocké lors de l'initiation du paiement.
        """
        deposit_id = self._get_deposit_id(tx_ref)
        if not deposit_id:
            return {
                "status_code": "error",
                "message": f"Aucun depositId trouvé pour la référence {tx_ref}"
            }
        return self.verify_transaction(deposit_id)

    def verify_webhook_signature(self, payload, signature):
        """
        PawaPay signe les webhooks avec HMAC-SHA256.
        """
        secret = self.settings.get_password("webhook_secret") or ""
        if not secret:
            return True
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def get_active_correspondents(self):
        """
        PawaPay API: GET /active-conf
        Retourne les opérateurs MNO actifs (équivalent des banques pour Flutterwave).
        """
        return self._get("/active-conf")

    def get_banks(self, country):
        """
        Alias pour compatibilité avec l'interface commune.
        Retourne les correspondants MNO actifs filtrés par pays.
        """
        result = self.get_active_correspondents()
        if result.get("status_code") == "success":
            correspondents = result.get("correspondents", [])
            filtered = [c for c in correspondents if c.get("country") == country]
            result["data"] = [
                {"name": c.get("correspondent"), "code": c.get("correspondent")}
                for c in filtered
            ]
        return result

    def get_all_subaccount(self):
        """PawaPay ne supporte pas les sous-comptes."""
        return {"status": "success", "data": []}

    def get_subaccount_infos(self, subaccount_id):
        """PawaPay ne supporte pas les sous-comptes."""
        return {"status": "success", "data": {}}

    def create_subaccount(self, company, account_bank, account_number, business_email):
        """PawaPay ne supporte pas la création de sous-comptes."""
        frappe.throw("PawaPay ne supporte pas la création de sous-comptes.")

    def _normalize_status(self, pawapay_status):
        """Convertit les statuts PawaPay vers le format interne."""
        mapping = {
            "COMPLETED": "successful",
            "FAILED": "failed",
            "PENDING": "pending",
            "DUPLICATE_IGNORED": "failed",
            "REJECTED": "failed",
            "TIMED_OUT": "failed"
        }
        return mapping.get(pawapay_status.upper() if pawapay_status else "", "pending")

    def _store_deposit_id(self, tx_ref, deposit_id):
        """Stocke la correspondance tx_ref <-> depositId dans le champ remarks du Payment Request."""
        try:
            pr_name = tx_ref.replace("PR-", "", 1)
            if frappe.db.exists("Payment Request", pr_name):
                existing = frappe.db.get_value("Payment Request", pr_name, "remarks") or ""
                new_remarks = f"pawapay_deposit_id:{deposit_id}"
                if existing and "pawapay_deposit_id" not in existing:
                    new_remarks = existing + "\n" + new_remarks
                frappe.db.set_value(
                    "Payment Request", pr_name, "remarks",
                    new_remarks, update_modified=False
                )
                frappe.db.commit()
        except Exception:
            pass

    def _get_deposit_id(self, tx_ref):
        """Récupère le depositId stocké pour un tx_ref donné."""
        try:
            pr_name = tx_ref.replace("PR-", "", 1)
            remarks = frappe.db.get_value("Payment Request", pr_name, "remarks") or ""
            for part in remarks.split("\n"):
                if part.startswith("pawapay_deposit_id:"):
                    return part.split(":", 1)[1].strip()
        except Exception:
            pass
        return None
