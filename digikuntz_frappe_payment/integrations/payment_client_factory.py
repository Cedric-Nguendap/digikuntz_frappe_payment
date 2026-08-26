import frappe
from frappe_digikuntz_flutterwave.integrations.flutterwave_client import (
    FlutterwaveClient
)

from frappe_digikuntz_pawapay.integrations.pawapay_client import (
    PawaPayClient
)

class PaymentClientFactory:
     @staticmethod
     def get_payment_client():
        company = frappe.form_dict.get("company")
        payment_mode = frappe.get_cached_value("Company", company, "payment_gateway") if company else None
        
        if payment_mode == "Flutterwave":
            return {"client": FlutterwaveClient(), "mode": "Flutterwave"}
        elif payment_mode == "PawaPay":
            return {"client": PawaPayClient(), "mode": "PawaPay"}
        else:
            frappe.throw(
                msg="Aucun mode de paiement n'est configuré pour cette entreprise.<br><br>Veuillez contacter l'administrateur pour plus de détails.",
                title="Mode de paiement non configuré",
                exc=frappe.ValidationError
            )