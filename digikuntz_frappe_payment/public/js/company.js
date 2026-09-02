frappe.ui.form.on("Company", {

    custom_payment_gateway(frm) {
        frm.set_value("custom_sous_compte_par_defaut", "");
        frm.set_value("custom_sous_compte_pawapay", "");
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");

        if (!frm.doc.custom_payment_gateway) return;

        frappe.call({
            method: "digikuntz_frappe_payment.api.flutterwave_settings.trigger_gateway_setup",
            args: { company: frm.doc.name },
            freeze: true,
            freeze_message: __("Vérification de la configuration en cours..."),
            callback(r) {
                if (!r.exc && r.message) {
                    if (r.message.status === "success") {
                        frappe.show_alert({ message: __(r.message.message), indicator: "green" });
                        _check_and_display_config_status(frm);
                    } else {
                        frappe.msgprint({
                            title: __("Erreur de configuration"),
                            message: __(r.message.message),
                            indicator: "red"
                        });
                    }
                }
            }
        });
    },

    custom_sous_compte_par_defaut(frm) {
        _load_subaccount_infos(frm, frm.doc.custom_sous_compte_par_defaut);
    },

    custom_sous_compte_pawapay(frm) {
        _load_subaccount_infos(frm, frm.doc.custom_sous_compte_pawapay);
    },

    refresh(frm) {
        if (!frm.doc.custom_payment_gateway) return;
        frm.add_custom_button(__("Sync Sous-comptes"), () => _sync_subaccounts(frm));
        _check_and_display_config_status(frm);
    }
});


function _load_subaccount_infos(frm, subaccount_name) {
    if (!subaccount_name) {
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");
        return;
    }
    frappe.call({
        method: "digikuntz_frappe_payment.api.company.get_subaccount_infos",
        args: { company: frm.doc.name, subaccount_name },
        freeze: true,
        freeze_message: __("Chargement des infos du sous-compte..."),
        callback(r) {
            if (!r.exc && r.message) {
                frm.set_value("custom_banque", r.message.bank_name);
                frm.set_value("custom_numero_de_compte", r.message.account_number);
            }
        }
    });
}


function _check_and_display_config_status(frm) {
    frappe.call({
        method: "digikuntz_frappe_payment.api.company.check_gateway_config",
        args: { company: frm.doc.name },
        callback(r) {
            if (!r.exc && r.message) {
                if (r.message.status === "warning" && r.message.issues) {
                    r.message.issues.forEach(issue => {
                        frm.dashboard.add_comment(__("⚠ ") + __(issue), "orange", false);
                    });
                } else if (r.message.status === "success") {
                    frm.dashboard.add_comment(
                        __("✔ Passerelle {0} configurée et opérationnelle.", [r.message.gateway]),
                        "green", false
                    );
                }
            }
        }
    });
}


function _sync_subaccounts(frm) {
    frappe.call({
        method: "digikuntz_frappe_payment.api.company.sync_gateway_company",
        args: { company: frm.doc.name },
        freeze: true,
        freeze_message: __("Synchronisation des sous-comptes..."),
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
