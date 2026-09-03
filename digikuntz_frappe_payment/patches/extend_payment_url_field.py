import frappe


def execute():
    # Modifier le type du champ dans Frappe
    frappe.make_property_setter(
        "Payment Request",
        "payment_url",
        "fieldtype",
        "Text",
        "Text",
    )

    # S'assurer que la colonne SQL correspond au nouveau type
    frappe.db.sql("""
        ALTER TABLE `tabPayment Request`
        MODIFY COLUMN `payment_url` TEXT
    """)

    frappe.db.commit()
