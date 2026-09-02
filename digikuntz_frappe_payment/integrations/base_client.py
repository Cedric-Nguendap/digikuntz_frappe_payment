from abc import ABC, abstractmethod


class BasePaymentClient(ABC):
    """
    Contrat commun à toutes les passerelles de paiement.
    Pour ajouter une nouvelle gateway, créer une classe qui hérite de BasePaymentClient
    et implémenter toutes les méthodes abstraites.
    """

    @abstractmethod
    def validate(self):
        """Vérifie que la configuration (clés API, activation) est valide."""

    @abstractmethod
    def initialize_web_payment(self, amount, email, tx_ref, redirect_url, currency, company, customer_name):
        """Initialise un paiement web (checkout). Lever une exception si non supporté."""

    @abstractmethod
    def initialize_mobile_money_payment(self, amount, email, tx_ref, redirect_url, phone_number, network, country, currency, company, customer_name):
        """Initialise un paiement Mobile Money (push USSD)."""

    @abstractmethod
    def verify_transaction(self, transaction_id):
        """Vérifie le statut d'une transaction par son ID natif.
        Doit retourner : {"status_code": "success", "data": {"status": "successful|failed|pending", "tx_ref": "..."}}
        """

    @abstractmethod
    def verify_transaction_by_reference(self, tx_ref):
        """Vérifie le statut d'une transaction par le tx_ref ERPNext (ex: PR-0001)."""

    @abstractmethod
    def verify_webhook_signature(self, payload, signature):
        """Vérifie l'authenticité d'un webhook. Retourne True/False."""

    @abstractmethod
    def extract_tx_ref_from_webhook(self, transaction):
        """
        Extrait le tx_ref depuis le payload webhook déjà parsé (dict).
        Retourne le tx_ref si c'est un événement de paiement réussi, None sinon.
        C'est le client qui connaît le format de son propre webhook.
        """

    @abstractmethod
    def get_banks(self, country):
        """Retourne la liste des banques/opérateurs disponibles pour un pays.
        Doit retourner : {"status_code": "success", "data": [{"name": ..., "code": ...}]}
        """

    def get_all_subaccount(self):
        """Retourne tous les sous-comptes. Retourner {"status": "success", "data": []} si non supporté."""
        return {"status": "success", "data": []}

    def get_subaccount_infos(self, subaccount_id):
        """Retourne les infos d'un sous-compte. Retourner {"status": "success", "data": {}} si non supporté."""
        return {"status": "success", "data": {}}

    def create_subaccount(self, company, account_bank, account_number, business_email):
        """Crée un sous-compte. Lever une exception si non supporté."""
        import frappe
        frappe.throw(f"{self.__class__.__name__} ne supporte pas la création de sous-comptes.")
