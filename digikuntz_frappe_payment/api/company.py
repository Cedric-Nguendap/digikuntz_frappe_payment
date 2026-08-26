import frappe

from frappe_digikuntz_flutterwave.services.flutterwave_service import (
    FlutterwaveService
)

@frappe.whitelist()
def sync_flutterwave_company(company):


    service = FlutterwaveService()

    response = service.sync_subaccount()

    if response.get("status")!="success":
        return {
            "status":"error",
            "message":response.get("message")
        }
    data = response.get("data", {})

    company_doc = frappe.get_doc("Company",company)
    company_doc.custom_sous_compte_par_defaut = None
    company_doc.save(ignore_permissions=True)

    frappe.db.delete("Flutterwave SubAccount")	
    for d in data:
        new_doc = frappe.get_doc(
            {  "doctype": "Flutterwave SubAccount",                   
                "subaccount_id": d["subaccount_id"],
                "bank_name": d["bank_name"],
                "pourcentance": d["split_value"],
                "business_name":d["business_name"],
                "country":d["country"],
                "account_number":d["account_number"],
            })
        new_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success"
    }

@frappe.whitelist()
def get_subaccount_infos(subaccount_businness_name):
    subaccount = frappe.get_doc("Flutterwave SubAccount", subaccount_businness_name)

    return {
        "bank_name":subaccount.bank_name,
        "account_number": subaccount.account_number
    }