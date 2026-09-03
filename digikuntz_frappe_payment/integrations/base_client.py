from abc import ABC, abstractmethod


def ok(data=None):
    """Réponse standard succès."""
    return {"ok": True, "data": data or {}}


def err(message):
    """Réponse standard erreur."""
    return {"ok": False, "error": str(message)}


class BasePaymentClient(ABC):
    """
    Contrat commun à toutes les passerelles de paiement.

    Toutes les méthodes DOIVENT retourner soit ok(...) soit err(...).

    ok(data) — succès :
        data pour initialize_web_payment      : {"redirect_url": str, "transaction_id": str}
        data pour initialize_mobile_money_*   : {"transaction_id": str}
        data pour verify_transaction*         : {"status": "successful|failed|pending", "tx_ref": str}
        data pour get_banks                   : {"banks": [{"name": str, "code": str}]}
        data pour get_all_subaccount          : {"subaccounts": [...]}
        data pour get_subaccount_infos        : {"subaccount": {...}}

    err(message) — erreur :
        {"ok": False, "error": str}
    """

    @abstractmethod
    def validate(self):
        """Vérifie que la configuration (clés API, activation) est valide."""

    @abstractmethod
    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency, company, customer_name, callback_url=None):
        """
        Initialise un paiement web (checkout).
        Retourne ok({"redirect_url": str, "transaction_id": str}) ou err(...)
        """

    @abstractmethod
    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country, currency, company, customer_name, callback_url=None):
        """
        Initialise un paiement Mobile Money (push USSD).
        Retourne ok({"transaction_id": str}) ou err(...)
        """

    @abstractmethod
    def verify_transaction(self, transaction_id):
        """
        Vérifie le statut d'une transaction par son ID natif.
        Retourne ok({"status": "successful|failed|pending", "tx_ref": str}) ou err(...)
        """

    @abstractmethod
    def verify_transaction_by_reference(self, tx_ref):
        """
        Vérifie le statut d'une transaction par le tx_ref ERPNext (ex: PR-0001).
        Retourne ok({"status": "successful|failed|pending", "tx_ref": str}) ou err(...)
        """

    @abstractmethod
    def verify_webhook_signature(self, payload, signature):
        """Vérifie l'authenticité d'un webhook. Retourne True/False."""

    @abstractmethod
    def extract_tx_ref_from_webhook(self, transaction):
        """
        Extrait le tx_ref depuis le payload webhook déjà parsé (dict).
        Retourne le tx_ref (str) si paiement réussi, None sinon.
        """

    @abstractmethod
    def get_banks(self, country):
        """
        Retourne la liste des banques/opérateurs disponibles pour un pays.
        Retourne ok({"banks": [{"name": str, "code": str}]}) ou err(...)
        """

    def get_all_subaccount(self):
        """Retourne ok({"subaccounts": []}) si non supporté."""
        return ok({"subaccounts": []})

    def get_subaccount_infos(self, subaccount_id):
        """Retourne ok({"subaccount": {}}) si non supporté."""
        return ok({"subaccount": {}})

    def create_subaccount(self, company, account_bank, account_number, business_email):
        """Lève une exception si non supporté."""
        import frappe
        frappe.throw(f"{self.__class__.__name__} ne supporte pas la création de sous-comptes.")
