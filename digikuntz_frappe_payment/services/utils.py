import frappe
from digikuntz_frappe_payment.integrations.gateway_registry import get_gateway_config


def get_current_user_email():
    user = frappe.session.user
    return user if user != "Administrator" else "choudja@gic.cm"


def can_use_flutterwave():
    settings = frappe.get_single("Flutterwave Settings")
    return bool(settings.enable_flutterwave and settings.secret_key and settings.public_key)


def can_use_pawapay():
    settings = frappe.get_single("Pawapay Settings")
    return bool(settings.enable_pawapay and settings.secret_key)


def should_use_subaccount(company):
    if not company or not company.custom_activer:
        return False
    config = get_gateway_config(company.custom_payment_gateway)
    return bool(company.get(config["subaccount_field"]))


def get_subaccount_id(company):
    """Retourne le subaccount_id du sous-compte par défaut selon la gateway active."""
    config = get_gateway_config(company.custom_payment_gateway)
    subaccount_name = company.get(config["subaccount_field"])
    if not subaccount_name:
        return None
    return frappe.db.get_value(config["subaccount_doctype"], subaccount_name, "subaccount_id")
