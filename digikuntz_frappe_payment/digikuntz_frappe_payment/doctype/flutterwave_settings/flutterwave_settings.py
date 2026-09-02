import frappe
from frappe.model.document import Document


class FlutterwaveSettings(Document):

    def validate(self):
        if self.enable_flutterwave:
            if not self.secret_key:
                frappe.throw("Flutterwave Secret Key est requis.")
            if not self.public_key:
                frappe.throw("Flutterwave Public Key est requis.")

    def get_configuration_issues(self):
        """Retourne la liste des problèmes de configuration. [] = tout est OK."""
        issues = []
        if not self.enable_flutterwave:
            issues.append("Flutterwave est désactivé dans Flutterwave Settings.")
        if not self.secret_key:
            issues.append("Secret Key manquante dans Flutterwave Settings.")
        if not self.public_key:
            issues.append("Public Key manquante dans Flutterwave Settings.")
        return issues

    def get_payment_url(self, **kwargs):
        from digikuntz_frappe_payment.services.payment_gateway import DigikuntzPaymentGateway
        return DigikuntzPaymentGateway().get_payment_url(**kwargs)

    def validate_transaction_currency(self, currency):
        supported = ["XAF", "XOF", "GHS", "KES", "NGN", "UGX", "TZS", "ZAR", "USD", "EUR"]
        if currency not in supported:
            frappe.throw(f"Flutterwave ne supporte pas la devise '{currency}'.")
