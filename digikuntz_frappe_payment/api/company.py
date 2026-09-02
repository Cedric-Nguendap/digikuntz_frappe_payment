import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService
from digikuntz_frappe_payment.integrations.gateway_registry import get_gateway_config, GATEWAY_REGISTRY


@frappe.whitelist()
def sync_gateway_company(company):
    """Synchronise les sous-comptes de la passerelle configurée sur la company."""
    service = PaymentService(company=company)
    response = service.sync_subaccount()

    if response.get("status") != "success":
        return {"status": "error", "message": response.get("message")}

    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    config = get_gateway_config(gateway)
    subaccount_doctype = config["subaccount_doctype"]
    subaccount_field = config["subaccount_field"]

    company_doc = frappe.get_doc("Company", company)
    company_doc.set(subaccount_field, None)
    company_doc.save(ignore_permissions=True)

    frappe.db.delete(subaccount_doctype)

    for d in response.get("data", []):
        frappe.get_doc({
            "doctype": subaccount_doctype,
            "subaccount_id": d.get("subaccount_id"),
            "bank_name": d.get("bank_name"),
            "pourcentance": d.get("split_value", 0),
            "business_name": d.get("business_name"),
            "country": d.get("country"),
            "account_number": d.get("account_number"),
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success"}


@frappe.whitelist()
def get_subaccount_infos(company, subaccount_name):
    """Retourne les infos d'un sous-compte selon la passerelle configurée."""
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    config = get_gateway_config(gateway)
    subaccount = frappe.get_doc(config["subaccount_doctype"], subaccount_name)
    return {
        "bank_name": subaccount.bank_name,
        "account_number": subaccount.account_number
    }


@frappe.whitelist()
def check_gateway_config(company):
    """
    Vérifie que la passerelle configurée sur la company est correctement paramétrée.
    Retourne les éléments manquants sans if/elif par gateway.
    """
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        return {"status": "error", "message": "Aucune passerelle sélectionnée."}

    if gateway not in GATEWAY_REGISTRY:
        return {"status": "error", "message": f"Passerelle inconnue : {gateway}"}

    config = get_gateway_config(gateway)
    issues = []

    # Vérification des clés API via le doctype Settings
    settings = frappe.get_single(config["settings_doctype"])
    issues += settings.get_configuration_issues()

    if not frappe.db.exists("Payment Gateway", config["gateway_name"]):
        issues.append(f"Payment Gateway '{config['gateway_name']}' non créée. Relancez l'installation.")

    if not frappe.db.exists("Mode of Payment", config["mop_name"]):
        issues.append(f"Mode de paiement '{config['mop_name']}' non créé. Relancez l'installation.")

    if issues:
        return {"status": "warning", "issues": issues, "gateway": gateway, "settings_doctype": config["settings_doctype"]}

    return {"status": "success", "gateway": gateway, "settings_doctype": config["settings_doctype"]}
