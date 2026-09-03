import frappe
from digikuntz_frappe_payment.integrations.gateway_registry import GATEWAY_REGISTRY, get_gateway_config


def before_install():
    pass


def after_install():
    _extend_payment_url_field()
    for gateway in GATEWAY_REGISTRY:
        ensure_gateway_setup(gateway)
    print("Digikuntz Frappe Payment installé avec succès.")


def _extend_payment_url_field():
    """Étend payment_url en Small Text via Property Setter."""
    frappe.db.delete("Property Setter", {
        "doc_type": "Payment Request",
        "field_name": "payment_url",
        "property": "fieldtype"
    })
    frappe.get_doc({
        "doctype": "Property Setter",
        "doc_type": "Payment Request",
        "field_name": "payment_url",
        "property": "fieldtype",
        "value": "Small Text",
        "property_type": "Select",
        "doctype_or_field": "DocField"
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def after_uninstall():
    for gateway, config in GATEWAY_REGISTRY.items():
        for doctype, name in [
            ("Payment Gateway Account", {"payment_gateway": config["gateway_name"]}),
            ("Payment Gateway", config["gateway_name"]),
            ("Mode of Payment", config["mop_name"]),
        ]:
            try:
                if isinstance(name, dict):
                    existing = frappe.db.get_value(doctype, name, "name")
                    if existing:
                        frappe.delete_doc(doctype, existing, ignore_permissions=True)
                elif frappe.db.exists(doctype, name):
                    frappe.delete_doc(doctype, name, ignore_permissions=True)
            except Exception:
                pass
    frappe.db.commit()
    print("Digikuntz Frappe Payment désinstallé.")


def ensure_gateway_setup(gateway):
    """
    Crée si nécessaire : Payment Gateway, Mode of Payment, Account, Payment Gateway Account.
    Appelé à l'installation ET lors de la sélection d'une passerelle sur la Company.
    """
    company = frappe.defaults.get_global_default("company")
    if not company:
        return

    config = get_gateway_config(gateway)
    controller = "digikuntz_frappe_payment.services.payment_gateway.DigikuntzPaymentGateway"

    account = _get_or_create_account(config["account_name"], company)
    _create_payment_gateway(config["gateway_name"], config["settings_doctype"], controller)
    _create_mode_of_payment(config["mop_name"], company, account)
    _create_payment_gateway_account(config["gateway_name"], account, company)


def _get_or_create_account(account_name, company):
    existing = frappe.db.get_value("Account", {"account_name": account_name, "company": company}, "name")
    if existing:
        return existing

    parent = (
        frappe.db.get_value("Account", {"account_name": "Current Assets", "company": company}, "name")
        or frappe.db.get_value("Account", {"is_group": 1, "root_type": "Asset", "company": company}, "name")
    )
    if not parent:
        frappe.throw(f"Impossible de trouver un compte parent pour '{account_name}'")

    account = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "parent_account": parent,
        "account_type": "Bank",
        "company": company,
        "is_group": 0
    })
    account.insert(ignore_permissions=True)
    frappe.db.commit()
    return account.name


def _create_payment_gateway(gateway_name, settings_doctype, controller):
    if frappe.db.exists("Payment Gateway", gateway_name):
        return
    frappe.get_doc({
        "doctype": "Payment Gateway",
        "gateway": gateway_name,
        "gateway_settings": settings_doctype,
        "gateway_controller": controller
    }).insert(ignore_permissions=True, ignore_links=True)
    frappe.db.commit()


def _create_mode_of_payment(mop_name, company, account):
    if frappe.db.exists("Mode of Payment", mop_name):
        return
    frappe.get_doc({
        "doctype": "Mode of Payment",
        "mode_of_payment": mop_name,
        "type": "General",
        "enabled": 1,
        "accounts": [{"company": company, "default_account": account}]
    }).insert(ignore_permissions=True, ignore_links=True)
    frappe.db.commit()


def _create_payment_gateway_account(gateway_name, account, company):
    if frappe.db.exists("Payment Gateway Account", {"payment_gateway": gateway_name, "company": company}):
        return
    currency = frappe.db.get_value("Company", company, "default_currency") or "XAF"
    frappe.get_doc({
        "doctype": "Payment Gateway Account",
        "payment_gateway": gateway_name,
        "payment_account": account,
        "currency": currency,
        "is_default": 0,
        "company": company
    }).insert(ignore_permissions=True, ignore_links=True)
    frappe.db.commit()
