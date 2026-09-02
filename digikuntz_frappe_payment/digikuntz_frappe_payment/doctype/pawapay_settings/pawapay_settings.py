import frappe
from frappe.model.document import Document


class PawapaySettings(Document):
    supported_currencies = ["XAF", "XOF", "GHS", "KES", "TZS", "UGX", "ZMW", "MWK", "RWF", "MZN", "BIF", "SLL", "GMD"]

    def validate(self):
        if self.enable_pawapay:
            if not self.secret_key:
                frappe.throw("PawaPay API Token est requis.")
            if not self.base_url:
                self.base_url = "https://api.pawapay.io"

    def get_configuration_issues(self):
        """Retourne la liste des problèmes de configuration. [] = tout est OK."""
        issues = []
        if not self.enable_pawapay:
            issues.append("PawaPay est désactivé dans Pawapay Settings.")
        if not self.secret_key:
            issues.append("API Token manquant dans Pawapay Settings.")
        return issues

    def get_payment_url(self, **kwargs):
        from digikuntz_frappe_payment.services.payment_gateway import DigikuntzPaymentGateway
        return DigikuntzPaymentGateway().get_payment_url(**kwargs)

    def validate_transaction_currency(self, currency):
        if currency not in self.supported_currencies:
            frappe.throw(f"PawaPay ne supporte pas la devise '{currency}'.")
