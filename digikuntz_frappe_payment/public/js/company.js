frappe.ui.form.on("Company", {

    refresh(frm) {
        // Toujours afficher le statut si une gateway est sélectionnée
        if (frm.doc.custom_payment_gateway) {
            _render_gateway_status(frm);
        } else {
            _render_no_gateway(frm);
        }
    },

    custom_payment_gateway(frm) {
        // Réinitialiser les sous-comptes à chaque changement de gateway
        frm.set_value("custom_sous_compte_par_defaut", "");
        frm.set_value("custom_sous_compte_pawapay", "");
        frm.set_value("custom_banque", "");
        frm.set_value("custom_numero_de_compte", "");

        if (!frm.doc.custom_payment_gateway) {
            _render_no_gateway(frm);
            return;
        }

        // 1. Créer les ressources ERPNext manquantes (Payment Gateway, MoP, Account)
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
                // 2. Vérifier et afficher le statut dans tous les cas
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


// ─── Rendu du statut de configuration ────────────────────────────────────────

function _render_no_gateway(frm) {
    $(frm.fields_dict["custom_payment_status_html"].wrapper).html(
        `<div class="alert alert-warning" style="margin:8px 0">
            <b>⚠</b> Aucune passerelle sélectionnée. Choisissez une passerelle ci-dessus.
        </div>`
    );
    // Retirer les boutons liés à la gateway
    frm.remove_custom_button(__("Paramètres de la passerelle"));
    frm.remove_custom_button(__("Sync Sous-comptes"));
}


function _render_gateway_status(frm) {
    frappe.call({
        method: "digikuntz_frappe_payment.api.company.check_gateway_config",
        args: { company: frm.doc.name },
        callback(r) {
            if (r.exc || !r.message) return;
            const data = r.message;

            _render_status_html(frm, data);
            _render_gateway_buttons(frm, data);
        }
    });
}


function _render_status_html(frm, data) {
    const wrapper = $(frm.fields_dict["custom_payment_status_html"].wrapper);

    if (data.status === "success") {
        wrapper.html(
            `<div class="alert alert-success" style="margin:8px 0">
                <b>✔ ${__(data.gateway)} est configuré et opérationnel.</b>
            </div>`
        );
    } else if (data.status === "warning") {
        const items = (data.issues || []).map(i => `<li>${__(i)}</li>`).join("");
        wrapper.html(
            `<div class="alert alert-warning" style="margin:8px 0">
                <b>⚠ Configuration incomplète :</b>
                <ul style="margin:6px 0 0 0">${items}</ul>
            </div>`
        );
    } else {
        wrapper.html(
            `<div class="alert alert-danger" style="margin:8px 0">
                <b>✖ ${__(data.message || "Erreur de configuration")}</b>
            </div>`
        );
    }
}


function _render_gateway_buttons(frm, data) {
    // Bouton vers les paramètres de la gateway sélectionnée
    frm.remove_custom_button(__("Paramètres de la passerelle"));
    if (data.settings_doctype) {
        frm.add_custom_button(__("Paramètres de la passerelle"), () => {
            frappe.set_route("Form", data.settings_doctype);
        }, __("Digikuntz Payment"));
    }

    // Bouton sync sous-comptes (seulement si gateway opérationnelle)
    frm.remove_custom_button(__("Sync Sous-comptes"));
    if (data.status === "success") {
        frm.add_custom_button(__("Sync Sous-comptes"), () => {
            _sync_subaccounts(frm);
        }, __("Digikuntz Payment"));
    }
}


// ─── Sous-comptes ─────────────────────────────────────────────────────────────

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
