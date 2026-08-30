frappe.ui.form.on("Company", {

    custom_payment_gateway(frm) {
        frm.set_value("custom_sous_compte_par_defaut", "");
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");
    },

    custom_sous_compte_par_defaut(frm) {
        const selected_value = frm.doc.custom_sous_compte_par_defaut;
        if (!selected_value) {
            frm.set_value("custom_banque", "");
            frm.set_value("custom_numero_de_compte", "");
            return;
        }

        const gateway = frm.doc.custom_payment_gateway;
        let method = "";
        if (gateway === "Flutterwave") {
            method = "digikuntz_frappe_payment.api.company.get_subaccount_infos";
        } else if (gateway === "PawaPay") {
            method = "frappe_digikuntz_pawapay.api.company.get_subaccount_infos";
        }

        if (!method) return;

        frappe.call({
            method: method,
            args: { subaccount_business_name: selected_value },
            freeze: true,
            freeze_message: __("Chargement des infos du sous-compte..."),
            callback(r) {
                if (!r.exc && r.message) {
                    frm.set_value("custom_banque", r.message.bank_name);
                    frm.set_value("custom_numero_de_compte", r.message.account_number);
                } else {
                    frappe.msgprint({
                        title: __("Erreur"),
                        message: __("Impossible de charger les infos du sous-compte."),
                        indicator: "red"
                    });
                }
            }
        });
    },

    refresh(frm) {
        if (!frm.doc.custom_payment_gateway) return;

        frm.add_custom_button(__("Sync Passerelle"), () => sync_payment_gateway(frm));
    }
});


function sync_payment_gateway(frm) {
    const gateway = frm.doc.custom_payment_gateway;
    let method = "";

    if (gateway === "Flutterwave") {
        method = "digikuntz_frappe_payment.api.company.sync_flutterwave_company";
    } else if (gateway === "PawaPay") {
        method = "frappe_digikuntz_pawapay.api.company.sync_pawapay_company";
    } else {
        frappe.msgprint(__("Aucune passerelle de paiement configurée."));
        return;
    }

    frappe.call({
        method: method,
        args: { company: frm.doc.name },
        freeze: true,
        freeze_message: __("Synchronisation en cours..."),
        callback(r) {
            if (!r.exc && r.message && r.message.status === "success") {
                frappe.show_alert({ message: __("Synchronisation réussie"), indicator: "green" });
                frm.reload_doc();
            } else {
                frappe.show_alert({
                    message: r.message ? __(r.message.message) : __("Une erreur est survenue"),
                    indicator: "red"
                });
            }
        }
    });
}
