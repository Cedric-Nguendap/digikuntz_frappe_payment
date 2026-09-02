import frappe


def execute():
    """
    Supprime les anciens custom fields de Company issus des modules satellites
    (frappe_digikuntz_flutterwave) qui ont été fusionnés dans digikuntz_frappe_payment.
    """
    obsolete_fields = [
        "Company-custom_payment_tab",
        "Company-custom_flutterwave",
    ]

    for field_name in obsolete_fields:
        if frappe.db.exists("Custom Field", field_name):
            frappe.delete_doc("Custom Field", field_name, ignore_permissions=True)

    frappe.db.commit()
