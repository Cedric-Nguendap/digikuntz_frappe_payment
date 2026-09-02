import frappe
from digikuntz_frappe_payment.integrations.gateway_registry import get_gateway_config


class PaymentClientFactory:

    @staticmethod
    def get_payment_client(company=None):
        if not company:
            company = frappe.form_dict.get("company")

        gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway") if company else None

        if not gateway:
            frappe.throw(
                msg="Aucun mode de paiement n'est configuré pour cette entreprise.<br><br>"
                    "Veuillez contacter l'administrateur pour plus de détails.",
                title="Mode de paiement non configuré",
                exc=frappe.ValidationError
            )

        config = get_gateway_config(gateway)
        ClientClass = frappe.get_attr(config["client_class"])
        client = ClientClass()
        client.validate()
        return {"client": client, "mode": gateway}
