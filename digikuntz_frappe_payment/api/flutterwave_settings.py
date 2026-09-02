import frappe
from digikuntz_frappe_payment.integrations.gateway_registry import GATEWAY_REGISTRY, get_gateway_config
from digikuntz_frappe_payment.setup.install import ensure_gateway_setup


@frappe.whitelist()
def is_gateway_configured(company):
    """Vérifie si la passerelle configurée sur la company est opérationnelle."""
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway or gateway not in GATEWAY_REGISTRY:
        return False
    config = get_gateway_config(gateway)
    settings = frappe.get_single(config["settings_doctype"])
    return not bool(settings.get_configuration_issues())


@frappe.whitelist()
def trigger_gateway_setup(company):
    """
    Déclenché lors de la sélection d'une passerelle sur la Company.
    Crée les ressources ERPNext manquantes (Payment Gateway, Mode of Payment, Account).
    """
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        frappe.throw("Aucune passerelle sélectionnée sur cette société.")
    try:
        ensure_gateway_setup(gateway)
        return {"status": "success", "message": f"Configuration {gateway} vérifiée et complétée."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Gateway setup error: {gateway}")
        return {"status": "error", "message": str(e)}
