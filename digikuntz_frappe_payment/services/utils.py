import frappe

def get_current_user_email():
    current_user = frappe.session.user
    if current_user == "Administrator":
        return "choudja@gic.cm"
    return current_user


def can_use_flutterwave():
    f_settings = frappe.get_single("Flutterwave Settings")
    return f_settings.enable_flutterwave and f_settings.secret_key and f_settings.public_key


def can_use_pawapay():
    p_settings = frappe.get_single("Pawapay Settings")
    return bool(p_settings.enable_pawapay and p_settings.secret_key)


def should_use_subaccount(company):
    return company.custom_activer and company.custom_sous_compte_par_defaut