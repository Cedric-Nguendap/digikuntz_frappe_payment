import frappe

from frappe_digikuntz_flutterwave.services.flutterwave_service import (
    FlutterwaveService
)

@frappe.whitelist()
def sync_flutterwave_banks(country="CM"):

    service = FlutterwaveService()

    response = service.get_banks(country)

    banks = response.get("data", [])

    for bank in banks:
        exists = frappe.db.exists(
            "Flutterwave Bank",
            {
                "bank_code": bank.get("code")
            }
        )

        if exists:
            continue

        doc = frappe.get_doc({
            "doctype": "Flutterwave Bank",
            "bank_name": bank.get("name"),
            "bank_code": bank.get("code"),
            "country": country,
            "enabled": 1
        })

        doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "status": "success"
    }