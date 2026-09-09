import frappe
from digikuntz_frappe_payment.services.payment_service import PaymentService


class DigikuntzPaymentGateway:

    def __init__(self):
        pass

    def get_payment_url(self, **kwargs):
        reference_doctype = kwargs.get('reference_doctype')
        reference_docname = kwargs.get('reference_docname')
        company = kwargs.get('company')

        doc = frappe.get_doc(reference_doctype, reference_docname)
        service = PaymentService(company=company or doc.company)

        response = service.create_payment_link(doc, payer_email=kwargs.get('payer_email'))
        data = response.get('data') or {}

        redirect_url = data.get('redirect_url') or ''
        deposit_id = data.get('transaction_id') or ''

        if redirect_url:
            _store_redirect(reference_docname, redirect_url, deposit_id)

        return frappe.utils.get_url('/pay?pr=' + reference_docname)


def _store_redirect(pr_name, redirect_url, deposit_id=''):
    # Supprimer l'entree existante si elle existe (re-soumission)
    existing = frappe.db.get_value('Payment Redirect', {'payment_request': pr_name}, 'name')
    if existing:
        frappe.delete_doc('Payment Redirect', existing, force=True, ignore_permissions=True)

    doc = frappe.get_doc({
        'doctype': 'Payment Redirect',
        'payment_request': pr_name,
        'redirect_url': redirect_url,
        'deposit_id': deposit_id,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
