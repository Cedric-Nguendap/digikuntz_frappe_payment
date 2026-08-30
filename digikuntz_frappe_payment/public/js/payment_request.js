frappe.ui.form.on('Payment Request', {
    refresh: function(frm) {
        
        if (frm.doc.status !== "Paid" && frm.doc.docstatus === 1) {
            
            frm.add_custom_button(__('Lancer le Prompt MoMo'), function() {
                
                // Ouverture d'une boîte de dialogue pour que l'opérateur saisisse les détails
                let d = new frappe.ui.Dialog({
                    title: 'Initiation Directe Mobile Money',
                    fields: [
                        {
                            label: 'Réseau Mobile',
                            fieldname: 'network',
                            fieldtype: 'Select',
                            options: ['MTN', 'ORANGE'],
                            reqd: 1
                        },
                        {
                            label: 'Numéro de téléphone (avec code pays sans +)',
                            fieldname: 'phone',
                            fieldtype: 'Data',
                            default: frm.doc.contact_mobile || '',
                            reqd: 1
                        }
                    ],
                    primary_action_label: 'Déclencher le paiement',
                    primary_action(values) {
                        d.hide();
                        frappe.dom.freeze(__('Déclenchement du paiement en cours...'));

                        frappe.show_alert({message: __('Envoi du prompt en cours...'), color: 'blue'});
                        
                        // Appel de la méthode Python
                        frappe.call({
                            method: "digikuntz_frappe_payment.api.payment.initiate_momo_push",
                            args: {
                                payment_request_name: frm.doc.name,
                                phone_number: values.phone,
                                network: values.network
                            },
                            callback: function(r) {
                                if (r.message && r.message.status === "success") {
                                    frappe.msgprint({
                                        title: __('Succès'),
                                        indicator: 'green',
                                        message: __(r.message.message)
                                    });
                                    frm.reload_doc();
                                    verify_paiement_momo(frm);
                                } else {
                                    frappe.msgprint({
                                        title: __('Échec'),
                                        indicator: 'red',
                                        message: __("Erreur: " + r.message.message)
                                    });
                                }
                            }
                        });
                    }
                });
                d.show();
                
            }, __("Actions de paiement"));
            
        }
    }
});

const verify_paiement_momo = function(frm) {
    frappe.dom.freeze(__('En attente de la saisie du code PIN sur le téléphone du client...'));

    let interval = setInterval(() => {
        frappe.call({
            method: "digikuntz_frappe_payment.api.payment.check_momo_push",
            args: {
                payment_request_name: frm.doc.name
            },
            callback(r) {

                if (r.message)
                {
                    if (r.message == "successful") {
                         frappe.dom.unfreeze();
                        frappe.msgprint({
                            title: __('Paiement confirmé'),
                            indicator: 'green',
                            message: __(r.message.message)
                        });
                        frm.reload_doc();
                        clearInterval(interval);
                    } else if (r.message == "pending") {
                        // Toujours en attente, ne rien faire
                    } else {
                        frappe.dom.unfreeze();
                        frappe.msgprint({
                            title: __('Paiement échoué'),
                            indicator: 'red',
                            message: __(r.message.message)
                        });
                        clearInterval(interval);
                    }
                }
                else
                {
                     frappe.dom.unfreeze();
                    frappe.msgprint({
                        title: __('Erreur système'),
                        indicator: 'red',
                        message: __('Impossible de vérifier le paiement')
                    });
                    clearInterval(interval);
                }
            },
                error(err) {

                    // 🔥 TRÈS IMPORTANT
                    clearInterval(interval);

                    frappe.msgprint({
                        title: __('Erreur système'),
                        indicator: 'red',
                        message: __('Impossible de vérifier le paiement')
                    });
                }
            });

    }, 5000);
}
