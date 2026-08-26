import frappe

from erpnext.accounts.doctype.payment_request.payment_request import (
    make_payment_request
)


@frappe.whitelist()
def create_pawapay_payment_request(sales_invoice):

    invoice = frappe.get_doc("Sales Invoice", sales_invoice)

    payment_request = make_payment_request(
        dt="Sales Invoice",
        dn=invoice.name,
        recipient_id=invoice.contact_email or frappe.session.user,
        submit_doc=1,
        return_doc=1
    )

    return {
        "payment_request": payment_request.name,
        "payment_url": payment_request.payment_url
    }