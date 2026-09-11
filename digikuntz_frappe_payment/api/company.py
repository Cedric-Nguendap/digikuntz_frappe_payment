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
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        return {"status": "error", "message": "Aucune passerelle sélectionnée."}
    if gateway not in GATEWAY_REGISTRY:
        return {"status": "error", "message": f"Passerelle inconnue : {gateway}"}

    config = get_gateway_config(gateway)
    ClientClass = frappe.get_attr(config["client_class"])
    client = ClientClass(company=company)
    issues = client.get_configuration_issues()

    if issues:
        return {"status": "warning", "issues": issues, "gateway": gateway}
    return {"status": "success", "gateway": gateway}
