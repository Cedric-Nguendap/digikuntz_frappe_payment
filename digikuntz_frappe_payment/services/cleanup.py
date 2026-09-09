import frappe


def delete_old_payment_redirects():
    """Supprime les Payment Redirect de plus de 30 jours. Lance via scheduler."""
    frappe.db.delete(
        'Payment Redirect',
        {'creation': ('<', frappe.utils.add_days(frappe.utils.now_datetime(), -30))}
    )
    frappe.db.commit()
