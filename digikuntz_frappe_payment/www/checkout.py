import frappe


def get_context(context):
    context.no_cache = 1

    pr_name = frappe.form_dict.get("pr") or ""
    if not pr_name or not frappe.db.exists("Payment Request", pr_name):
        frappe.throw("Payment Request introuvable.", frappe.DoesNotExistError)

    context.pr_name = pr_name
    pr = frappe.db.get_value(
        "Payment Request",
        pr_name,
        ["name", "grand_total", "currency", "party", "party_name", "status", "payment_gateway", "company"],
        as_dict=True,
    )

    if pr.status == "Paid":
        context.redirect_to_success = True
        context.success_url = frappe.utils.get_url(f"/payment-success?pr={pr_name}")
        return

    if pr.status not in ("Requested", "Initiated"):
        frappe.throw("Ce lien de paiement n'est plus actif.")

    # Charger les opérateurs MoMo disponibles
    operators = []
    try:
        from digikuntz_frappe_payment.integrations.payment_client_factory import PaymentClientFactory
        from digikuntz_frappe_payment.integrations.gateway_registry import resolve_gateway_from_pr
        gateway = resolve_gateway_from_pr(pr.payment_gateway)
        payment_mode = PaymentClientFactory.get_payment_client(company=pr.company, gateway=gateway)
        client = payment_mode["client"]
        # country ISO alpha-2 pour Flutterwave, alpha-3 pour PawaPay
        # get_momo_operators accepte les deux formats
        country = getattr(client, "default_country", None) or "CM"
        # Pour Flutterwave, convertir alpha-3 → alpha-2 si nécessaire
        if len(country) == 3:
            country = _alpha3_to_alpha2(country) or country
        ops_resp = client.get_momo_operators(country)
        operators = (ops_resp.get("data") or {}).get("banks") or []
    except Exception:
        pass

    # CSRF token pour les appels POST depuis la page publique
    csrf_token = "Guest"
    try:
        csrf_token = frappe.session.data.csrf_token or "Guest"
    except Exception:
        pass

    context.redirect_to_success = False
    context.pr = pr
    context.pr_name = pr_name
    context.operators = operators
    context.csrf_token = csrf_token


def _alpha3_to_alpha2(code):
    mapping = {
        "CMR": "CM", "SEN": "SN", "CIV": "CI", "GHA": "GH",
        "ZMB": "ZM", "KEN": "KE", "TZA": "TZ", "UGA": "UG",
        "NGA": "NG", "ZAF": "ZA", "MWI": "MW", "MOZ": "MZ",
        "RWA": "RW", "BDI": "BI", "SLE": "SL", "GMB": "GM",
    }
    return mapping.get(code.upper())
