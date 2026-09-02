"""
Registre central des passerelles de paiement.

Pour ajouter une nouvelle gateway :
1. Créer le client dans integrations/mon_client.py (hériter de BasePaymentClient)
2. Créer le doctype Settings correspondant
3. Ajouter une entrée dans GATEWAY_REGISTRY ci-dessous
4. Lancer bench migrate

C'est tout. Aucun autre fichier à modifier.
"""

GATEWAY_REGISTRY = {
    "Flutterwave": {
        # Classe client (chemin Python complet)
        "client_class": "digikuntz_frappe_payment.integrations.flutterwave_client.FlutterwaveClient",
        # Doctype Single contenant les clés API
        "settings_doctype": "Flutterwave Settings",
        # Nom du Mode of Payment ERPNext créé à l'installation
        "mop_name": "Flutterwave",
        # Nom du compte comptable créé à l'installation
        "account_name": "Flutterwave Wallet",
        # Nom de la Payment Gateway ERPNext
        "gateway_name": "Flutterwave Gateway",
        # Doctype pour les sous-comptes (None si non supporté)
        "subaccount_doctype": "Flutterwave SubAccount",
        # Champ sur Company pointant vers le sous-compte par défaut
        "subaccount_field": "custom_sous_compte_par_defaut",
    },
    "PawaPay": {
        "client_class": "digikuntz_frappe_payment.integrations.pawapay_client.PawaPayClient",
        "settings_doctype": "Pawapay Settings",
        "mop_name": "PawaPay",
        "account_name": "PawaPay Wallet",
        "gateway_name": "PawaPay Gateway",
        "subaccount_doctype": "Pawapay SubAccount",
        "subaccount_field": "custom_sous_compte_pawapay",
    },
}


def get_gateway_config(gateway_name):
    """Retourne la config d'une gateway ou lève une exception."""
    import frappe
    config = GATEWAY_REGISTRY.get(gateway_name)
    if not config:
        frappe.throw(
            f"Passerelle inconnue : '{gateway_name}'. "
            f"Passerelles disponibles : {', '.join(GATEWAY_REGISTRY.keys())}"
        )
    return config


def get_all_gateway_names():
    """Retourne la liste des noms de gateways enregistrées."""
    return list(GATEWAY_REGISTRY.keys())
