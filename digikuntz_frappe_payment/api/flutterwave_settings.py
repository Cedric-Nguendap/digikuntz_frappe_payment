import frappe

@frappe.whitelist()
def is_flutterwave_configured():
    frappe_digikuntz_flutterwave = frappe.get_single("Flutterwave Settings")
    return bool(frappe_digikuntz_flutterwave.secret_key and frappe_digikuntz_flutterwave.public_key)