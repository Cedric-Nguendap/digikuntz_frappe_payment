app_name = "digikuntz_frappe_payment"
app_title = "Digikuntz Frappe Payment"
app_publisher = "Digikuntz"
app_description = "Module de paiement multi-gateway pour ERPNext (Flutterwave, PawaPay, ...)"
app_email = "choudja@gic.cm"
app_license = "mit"

required_apps = ["frappe", "erpnext", "payments"]

# Gateways déclarées auprès du module payments de Frappe
payment_gateway_enabled = [
    "Flutterwave Gateway",
    "PawaPay Gateway",
]

# JS injecté dans le desk pour tous les utilisateurs
app_include_js = [
    "/assets/digikuntz_frappe_payment/js/payment_request.js",
    "/assets/digikuntz_frappe_payment/js/sales_invoice.js",
]

# JS injecté sur des doctypes spécifiques
doctype_js = {
    "Company": "public/js/company.js",
}

# Nettoyage automatique des Payment Redirect de plus de 30 jours
scheduler_events = {
    "weekly": [
        "digikuntz_frappe_payment.services.cleanup.delete_old_payment_redirects",
    ]
}

# Hooks d'installation
before_install = "digikuntz_frappe_payment.setup.install.before_install"
after_install = "digikuntz_frappe_payment.setup.install.after_install"
after_uninstall = "digikuntz_frappe_payment.setup.install.after_uninstall"
