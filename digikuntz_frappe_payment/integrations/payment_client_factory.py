import frappe
from digikuntz_frappe_payment.integrations.flutterwave_client import (
    FlutterwaveClient
)
from digikuntz_frappe_payment.integrations.pawapay_client import (
    PawaPayClient
)

class PaymentClientFactory:
    @staticmethod
    def get_payment_client(company=None):
        if not company:
            company = frappe.form_dict.get("company")
        payment_mode = frappe.get_cached_value("Company", company, "custom_payment_gateway") if company else None

        if payment_mode == "Flutterwave":
            client = FlutterwaveClient()
            client.validate()
            return {"client": client, "mode": "Flutterwave"}
        elif payment_mode == "PawaPay":
            client = PawaPayClient()
            client.validate()
            return {"client": client, "mode": "PawaPay"}
        else:
            frappe.throw(
                msg="Aucun mode de paiement n'est configuré pour cette entreprise.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="Mode de paiement non configuré",
                exc=frappe.ValidationError
            )