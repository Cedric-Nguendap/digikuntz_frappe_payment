import frappe
from digikuntz_frappe_payment.setup.install import ensure_gateway_setup


@frappe.whitelist()
def is_flutterwave_configured():
    settings = frappe.get_single("Flutterwave Settings")
    return bool(settings.enable_flutterwave and settings.secret_key and settings.public_key)


@frappe.whitelist()
def is_gateway_configured(company):
    """Vérifie si la passerelle configurée sur la company est opérationnelle."""
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        return False
    if gateway == "Flutterwave":
        settings = frappe.get_single("Flutterwave Settings")
        return bool(settings.enable_flutterwave and settings.secret_key and settings.public_key)
    elif gateway == "PawaPay":
        settings = frappe.get_single("Pawapay Settings")
        return bool(settings.enable_pawapay and settings.secret_key)
    return False


@frappe.whitelist()
def trigger_gateway_setup(company):
    """
    Déclenché lors de la sélection/confirmation d'une passerelle sur la Company.
    Crée les ressources manquantes (Payment Gateway, Mode of Payment, Account).
    """
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        frappe.throw("Aucune passerelle sélectionnée sur cette société.")

    try:
        ensure_gateway_setup(gateway)
        return {
            "status": "success",
            "message": f"Configuration {gateway} vérifiée et complétée."
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Gateway setup error: {gateway}")
        return {"status": "error", "message": str(e)}
