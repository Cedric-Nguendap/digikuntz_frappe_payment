import frappe


def get_context(context):
    context.no_cache = 1

    pr_name = frappe.form_dict.get("pr") or ""
    if not pr_name or not frappe.db.exists("Payment Request", pr_name):
        context.error = "Payment Request introuvable."
        context.redirect_url = ""
        return

    redirect_url = frappe.db.get_value(
        "Payment Redirect", {"payment_request": pr_name}, "redirect_url"
    ) or ""

    if not redirect_url:
        context.error = "Lien de paiement introuvable ou expiré."
        context.redirect_url = ""
        return

    context.redirect_url = redirect_url
    context.error = ""
