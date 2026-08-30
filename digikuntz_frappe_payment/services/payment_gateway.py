import frappe

from digikuntz_frappe_payment.services.payment_service import PaymentService


class DigikuntzPaymentGateway:

    def __init__(self):
        pass

    def get_payment_url(self, **kwargs):
        reference_doctype = kwargs.get("reference_doctype")
        reference_docname = kwargs.get("reference_docname")
        company = kwargs.get("company")

        doc = frappe.get_doc(reference_doctype, reference_docname)
        service = PaymentService(company=company or doc.company)

        response = service.create_payment_link(doc, payer_email=kwargs.get("payer_email"))

        return response["data"]["link"]
