from frappe.integrations.utils import create_request_log
import frappe
from digikuntz_frappe_payment.services.flutterwave_service import (
    FlutterwaveService
)

from frappe_digikuntz_flutterwave.integrations.payment_client_factory import (
    PaymentClientFactory
)

from digikuntz_frappe_payment.services.pawapay_service import (
    PawaPayService
)

class FlutterwavePaymentGateway:

    def __init__(self):
        self.payment_mode = PaymentClientFactory.get_payment_client()
        self.client = self.payment_mode["client"]
        self.settings = frappe.get_single(f"{self.payment_mode['mode']} Settings")

    def get_payment_url(self, **kwargs):
        reference_doctype = kwargs.get("reference_doctype")
        reference_docname = kwargs.get("reference_docname")

        doc = frappe.get_doc(reference_doctype, reference_docname)
        service = FlutterwaveService()

        response  = service.create_payment_link(doc, payer_email=kwargs.get("payer_email"))
        
        # return payment_link
        return response["data"]["link"]


class PawaPayPaymentGateway:

    def __init__(self):

        self.settings = frappe.get_single("PawaPay Settings")

    def get_payment_url(self, **kwargs):
        reference_doctype = kwargs.get("reference_doctype")
        reference_docname = kwargs.get("reference_docname")

        doc = frappe.get_doc(reference_doctype, reference_docname)
        service = PawaPayService()

        response  = service.create_payment_link(doc, payer_email=kwargs.get("payer_email"))
        
        # return payment_link
        return response["data"]["link"]

class PaymentGatewayFactory:
    @staticmethod
    def get_payment_gateway(payment_mode):
        if payment_mode == "Flutterwave":
            return FlutterwavePaymentGateway()
        elif payment_mode == "PawaPay":
            return PawaPayPaymentGateway()
        else:
            raise ValueError(f"Unsupported payment mode: {payment_mode}")