import frappe

def after_install():
    create_payment_gateway()

    create_mode_of_payment()
    create_payment_gateway_account()
    print("End of installation script Flutterwave Integration")


def create_mode_of_payment():
    if not frappe.db.exists("Mode of Payment", "Flutterwave"):
        mop = frappe.get_doc({
            "doctype": "Mode of Payment",
            "mode_of_payment": "Flutterwave",
            "type": "General",
            "enabled": 1,
            "accounts": [
                {
                    "company": frappe.defaults.get_global_default("company"),
                    "default_account": get_or_create_account()
                }
            ]
        })

        mop.insert(ignore_permissions=True)


def get_or_create_account():

    account_name = "Flutterwave Wallet"
    company = frappe.defaults.get_global_default("company")

    if frappe.db.exists("Account", {"account_name":account_name}):
        return frappe.get_doc("Account", {"account_name":account_name}).name

    # récupérer un parent valide dynamiquement
    parent = frappe.db.get_value(
        "Account",
        {
            "account_name": "Current Assets",
            "company": company
        },
        "name"
    )

    if not parent:
        # fallback plus robuste
        parent = frappe.db.get_value(
            "Account",
            {
                "is_group": 1,
                "company": company
            },
            "name"
        )

    if not parent:
        frappe.throw("No valid parent account found for Flutterwave Wallet")

    account = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "parent_account": parent,
        "account_type": "Bank",
        "company": company,
        "is_group": 0
    })

    account.insert(ignore_permissions=True)

    return account.name

    


def create_payment_gateway():
    if frappe.db.exists("Payment Gateway", "Flutterwave Gateway"):
        return

    gateway = frappe.get_doc({
        "doctype": "Payment Gateway",
        "gateway": "Flutterwave Gateway",
        "gateway_settings": "Flutterwave Settings",
        "gateway_controller": "frappe_digikuntz_flutterwave.services.payment_gateway.FlutterwavePaymentGateway"
    })

    gateway.insert(ignore_permissions=True)
    frappe.db.commit()

def create_payment_gateway_account():
    company = frappe.defaults.get_global_default("company")
    # 1. On vérifie si le lien existe déjà
    if frappe.db.exists("Payment Gateway Account", {"payment_gateway": "Flutterwave Gateway", "company": company}):
        return

    # 2. On s'assure que le compte et la gateway existent
    account = get_or_create_account() 
    
    # 3. On crée le lien
    pga = frappe.get_doc({
        "doctype": "Payment Gateway Account",
        "payment_gateway": "Flutterwave Gateway", # Le nom de ta Gateway
        "payment_account": account,       # Le compte que ta fonction a créé
        "is_default": 1,
        "company": frappe.defaults.get_global_default("company")
    })
    
    pga.insert(ignore_permissions=True)
    frappe.db.commit()