frappe.ui.form.on("Company", {

    refresh(frm) {
        // Supprimer le bouton obsolète vers les paramètres globaux
        frm.remove_custom_button(__("Paramètres de la passerelle"), __("Digikuntz Payment"));

        if (frm.doc.custom_payment_gateway) {
            _render_gateway_status(frm);
            if (frm.doc.custom_payment_gateway === "Flutterwave") {
                frm.add_custom_button(__("Sync Sous-comptes"), () => _sync_subaccounts(frm), __("Digikuntz Payment"));
            }
        } else {
            _render_no_gateway(frm);
        }
    },

    custom_payment_gateway(frm) {
        frm.set_value("custom_sous_compte_par_defaut", "");
        frm.set_value("custom_sous_compte_pawapay", "");
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");

        if (!frm.doc.custom_payment_gateway) {
            _render_no_gateway(frm);
            return;
        }

        frappe.call({
            method: "digikuntz_frappe_payment.api.flutterwave_settings.trigger_gateway_setup",
            args: { company: frm.doc.name },
            freeze: true,
            freeze_message: __("Initialisation de la passerelle en cours..."),
            callback(r) {
                if (r.exc || !r.message) return;
                if (r.message.status === "error") {
                    frappe.msgprint({ title: __("Erreur"), message: __(r.message.message), indicator: "red" });
                }
                _render_gateway_status(frm);
            }
        });
    },

    custom_sous_compte_par_defaut(frm) {
        _load_subaccount_infos(frm, frm.doc.custom_sous_compte_par_defaut);
    },

    custom_sous_compte_pawapay(frm) {
        _load_subaccount_infos(frm, frm.doc.custom_sous_compte_pawapay);
    }
});


function _render_no_gateway(frm) {
    $(frm.fields_dict["custom_payment_status_html"].wrapper).html(
        `<div class="alert alert-warning" style="margin:8px 0">
            <b>⚠</b> Aucune passerelle sélectionnée. Choisissez une passerelle ci-dessus.
        </div>`
    );
}


function _render_gateway_status(frm) {
    const gw = frm.doc.custom_payment_gateway;
    let issues = [];

    if (gw === "Flutterwave") {
        if (!frm.doc.custom_fw_enable) issues.push("Flutterwave est désactivé.");
        if (!frm.doc.custom_fw_secret_key) issues.push("Secret Key manquante.");
        if (!frm.doc.custom_fw_public_key) issues.push("Public Key manquante.");
    } else if (gw === "PawaPay") {
        if (!frm.doc.custom_pp_enable) issues.push("PawaPay est désactivé.");
        if (!frm.doc.custom_pp_secret_key) issues.push("API Token manquant.");
        if (!frm.doc.custom_pp_default_country) issues.push("Pays par défaut (ISO alpha-3) manquant.");
    }

    const wrapper = $(frm.fields_dict["custom_payment_status_html"].wrapper);
    if (issues.length === 0) {
        wrapper.html(
            `<div class="alert alert-success" style="margin:8px 0">
                <b>✔ ${__(gw)} est configuré et opérationnel.</b>
            </div>`
        );
    } else {
        const items = issues.map(i => `<li>${__(i)}</li>`).join("");
        wrapper.html(
            `<div class="alert alert-warning" style="margin:8px 0">
                <b>⚠ Configuration incomplète :</b>
                <ul style="margin:6px 0 0 0">${items}</ul>
            </div>`
        );
    }
}


function _load_subaccount_infos(frm, subaccount_name) {
    if (!subaccount_name) {
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");
        return;
    }
    frappe.call({
        method: "digikuntz_frappe_payment.api.company.get_subaccount_infos",
        args: { company: frm.doc.name, subaccount_name },
        callback(r) {
            if (!r.exc && r.message) {
                frm.set_value("custom_banque", r.message.bank_name);
                frm.set_value("custom_numero_de_compte", r.message.account_number);
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
