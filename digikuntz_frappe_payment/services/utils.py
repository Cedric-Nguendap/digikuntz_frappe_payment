import frappe


def get_current_user_email():
    current_user = frappe.session.user
    if current_user == "Administrator":
        return "choudja@gic.cm"
    return current_user


def can_use_flutterwave():
    settings = frappe.get_single("Flutterwave Settings")
    return bool(settings.enable_flutterwave and settings.secret_key and settings.public_key)


def can_use_pawapay():
    settings = frappe.get_single("Pawapay Settings")
    return bool(settings.enable_pawapay and settings.secret_key)


def should_use_subaccount(company):
    if not company.custom_activer:
        return False
    gateway = company.custom_payment_gateway
    if gateway == "Flutterwave":
        return bool(company.custom_sous_compte_par_defaut)
    elif gateway == "PawaPay":
        return bool(company.custom_sous_compte_pawapay)
    return False


def get_subaccount_id(company):
    """Retourne le subaccount_id selon la gateway active."""
    gateway = company.custom_payment_gateway
    if gateway == "Flutterwave":
        return frappe.db.get_value(
            "Flutterwave SubAccount", company.custom_sous_compte_par_defaut, "subaccount_id"
        )
    elif gateway == "PawaPay":
        return frappe.db.get_value(
            "Pawapay SubAccount", company.custom_sous_compte_pawapay, "subaccount_id"
        )
    return None
