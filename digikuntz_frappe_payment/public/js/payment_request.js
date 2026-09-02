frappe.ui.form.on("Payment Request", {
    refresh(frm) {
        if (frm.doc.status === "Paid" || frm.doc.docstatus !== 1) return;

        // Vérifier la passerelle configurée sur la company du Payment Request
        frappe.db.get_value("Company", frm.doc.company, "custom_payment_gateway").then(r => {
            const gateway = r.message && r.message.custom_payment_gateway;
            if (!gateway) return;

            // Le bouton MoMo est disponible pour Flutterwave et PawaPay
            frm.add_custom_button(__("Lancer le Prompt MoMo"), () => {
                _show_momo_dialog(frm, gateway);
            }, __("Actions de paiement"));
        });
    }
});


function _show_momo_dialog(frm, gateway) {
    const d = new frappe.ui.Dialog({
        title: __("Initiation Mobile Money"),
        fields: [
            {
                label: __("Réseau Mobile"),
                fieldname: "network",
                fieldtype: "Select",
                options: ["MTN", "ORANGE"],
                reqd: 1
            },
            {
                label: __("Numéro de téléphone (avec indicatif pays, sans +)"),
                fieldname: "phone",
                fieldtype: "Data",
                default: frm.doc.contact_mobile || "",
                reqd: 1
            }
        ],
        primary_action_label: __("Déclencher le paiement"),
        primary_action(values) {
            d.hide();
            frappe.dom.freeze(__("Déclenchement du paiement en cours..."));
            frappe.show_alert({ message: __("Envoi du prompt en cours..."), indicator: "blue" });

            frappe.call({
                method: "digikuntz_frappe_payment.api.payment.initiate_momo_push",
                args: {
                    payment_request_name: frm.doc.name,
                    phone_number: values.phone,
                    network: values.network
                },
                callback(r) {
                    frappe.dom.unfreeze();
                    if (r.message && r.message.status_code === "success") {
                        frappe.show_alert({ message: __("Prompt envoyé avec succès"), indicator: "green" });
                        frm.reload_doc();
                        _poll_payment_status(frm);
                    } else {
                        frappe.msgprint({
                            title: __("Échec"),
                            indicator: "red",
                            message: r.message ? __(r.message.message || "Erreur inconnue") : __("Erreur inconnue")
                        });
                    }
                }
            });
        }
    });
    d.show();
}


function _poll_payment_status(frm) {
    frappe.dom.freeze(__("En attente de la confirmation du paiement..."));

    const interval = setInterval(() => {
        frappe.call({
            method: "digikuntz_frappe_payment.api.payment.check_momo_push",
            args: { payment_request_name: frm.doc.name },
            callback(r) {
                const status = r.message;
                if (!status) {
                    frappe.dom.unfreeze();
                    clearInterval(interval);
                    frappe.msgprint({
                        title: __("Erreur système"),
                        indicator: "red",
                        message: __("Impossible de vérifier le paiement.")
                    });
                    return;
                }

                if (status === "successful") {
                    frappe.dom.unfreeze();
                    clearInterval(interval);
                    frappe.msgprint({
                        title: __("Paiement confirmé"),
                        indicator: "green",
                        message: __("Le paiement a été effectué avec succès.")
                    });
                    frm.reload_doc();
                } else if (status === "pending") {
                    // Toujours en attente — on continue de poller
                } else {
                    frappe.dom.unfreeze();
                    clearInterval(interval);
                    frappe.msgprint({
                        title: __("Paiement échoué"),
                        indicator: "red",
                        message: __("Le paiement a échoué ou a été annulé.")
                    });
                }
            },
            error() {
                frappe.dom.unfreeze();
                clearInterval(interval);
                frappe.msgprint({
                    title: __("Erreur système"),
                    indicator: "red",
                    message: __("Impossible de vérifier le paiement.")
                });
            }
        });
    }, 5000);
}
