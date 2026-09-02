import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService


@frappe.whitelist()
def sync_gateway_company(company):
    """Synchronise les sous-comptes de la passerelle configurée sur la company."""
    service = PaymentService(company=company)
    response = service.sync_subaccount()

    if response.get("status") != "success":
        return {"status": "error", "message": response.get("message")}

    data = response.get("data", [])
    mode = service.mode_name

    company_doc = frappe.get_doc("Company", company)
    company_doc.custom_sous_compte_par_defaut = None
    company_doc.custom_sous_compte_pawapay = None
    company_doc.save(ignore_permissions=True)

    doctype = f"{mode} SubAccount"
    frappe.db.delete(doctype)

    for d in data:
        new_doc = frappe.get_doc({
            "doctype": doctype,
            "subaccount_id": d.get("subaccount_id"),
            "bank_name": d.get("bank_name"),
            "pourcentance": d.get("split_value", 0),
            "business_name": d.get("business_name"),
            "country": d.get("country"),
            "account_number": d.get("account_number"),
        })
        new_doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success"}


@frappe.whitelist()
def get_subaccount_infos(company, subaccount_name):
    """Retourne les infos d'un sous-compte selon la passerelle configurée."""
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    doctype = "Flutterwave SubAccount" if gateway == "Flutterwave" else "Pawapay SubAccount"
    subaccount = frappe.get_doc(doctype, subaccount_name)
    return {
        "bank_name": subaccount.bank_name,
        "account_number": subaccount.account_number
    }


@frappe.whitelist()
def check_gateway_config(company):
    """
    Vérifie que la passerelle configurée sur la company est correctement
    paramétrée (clés API, gateway ERPNext, mode de paiement, compte).
    Retourne la liste des éléments manquants.
    """
    gateway = frappe.get_cached_value("Company", company, "custom_payment_gateway")
    if not gateway:
        return {"status": "error", "message": "Aucune passerelle sélectionnée."}

    issues = []

    if gateway == "Flutterwave":
        settings = frappe.get_single("Flutterwave Settings")
        if not settings.enable_flutterwave:
            issues.append("Flutterwave est désactivé dans Flutterwave Settings.")
        if not settings.secret_key:
            issues.append("Secret Key manquante dans Flutterwave Settings.")
        if not settings.public_key:
            issues.append("Public Key manquante dans Flutterwave Settings.")
        gateway_name = "Flutterwave Gateway"
        mop_name = "Flutterwave"

    elif gateway == "PawaPay":
        settings = frappe.get_single("Pawapay Settings")
        if not settings.enable_pawapay:
            issues.append("PawaPay est désactivé dans Pawapay Settings.")
        if not settings.secret_key:
            issues.append("API Token manquant dans Pawapay Settings.")
        gateway_name = "PawaPay Gateway"
        mop_name = "PawaPay"

    else:
        return {"status": "error", "message": f"Passerelle inconnue : {gateway}"}

    if not frappe.db.exists("Payment Gateway", gateway_name):
        issues.append(f"Payment Gateway '{gateway_name}' non créée. Relancez l'installation.")

    if not frappe.db.exists("Mode of Payment", mop_name):
        issues.append(f"Mode de paiement '{mop_name}' non créé. Relancez l'installation.")

    if issues:
        return {"status": "warning", "issues": issues}

    return {"status": "success", "gateway": gateway}
