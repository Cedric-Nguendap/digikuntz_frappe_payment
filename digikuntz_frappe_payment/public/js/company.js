frappe.ui.form.on("Company", {

    custom_sous_compte_par_defaut(frm) {

       let selected_value = frm.doc.custom_sous_compte_par_defaut;
        if(selected_value)
        {
            frappe.call({
                method: "frappe_digikuntz_flutterwave.api.company.get_subaccount_infos",
                args: {
                    subaccount_businness_name: selected_value,
                },
                freeze: true,
                freeze_message: __("Load subaccount infos..."),
                callback(e) {
                    if (!e.exc) {
                        if (e.message) {
                            frm.set_value("custom_banque", e.message.bank_name);
                            frm.set_value("custom_numero_de_compte", e.message.account_number);
                            // frm.reload_doc();
                        }

                    }
                    else
                    {
                        frappe.msgprint({
                            title: __('Erreur'),
                            message: e.message.error || __('An error occured'),
                            indicator: 'red'
                        });
                    }
                }
            })
        }
        else
        {
            frm.set_value("custom_banque", "");
            frm.set_value("custom_numero_de_compte", "");
        }
        

    }

});


function sync_flutterwave(frm) {   
    frappe.call({
        method: "frappe_digikuntz_flutterwave.api.company.sync_flutterwave_company",
        args: {
            company: frm.doc.name,
        },
        freeze: true,
        freeze_message: __("Sync Flutterwave subaccount..."),
        callback(e) {
            // console.log("R ",e,e.exc)
            if (!e.exc) {
                if (e.message && e.message.status=="success")
                {
                    frappe.show_alert({
                        message: __("Flutterwave synchronized"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
                else if(e.message && e.message.status=="error")
                {
                    frappe.show_alert({
                        message: __(e.message.message),
                        indicator: "red"
                    });
                }
                else
                {
                    frappe.msgprint({
                        title: __('Erreur'),
                        message: e.message.error || __('An error occured'),
                        indicator: 'red'
                    });
                }
                
            }
            else {
                frappe.msgprint({
                    title: __('Erreur'),
                    message: e.message.error || __('An error occured'),
                    indicator: 'red'
                });
            }

        }

    });

}


frappe.ui.form.on("Company", {
    refresh(frm) {
        // frm.dashboard.add_comment(
        //     __( "Flutterwave subaccount connected: "),"green",true
        // );

        if (!frm.doc.custom_activer) {
            return;
        }      
        frm.add_custom_button( __("Sync Flutterwave"),() => sync_flutterwave(frm) );
        if(frm.doc.custom_sous_compte_par_defaut) {
            frappe.db.get_doc("Flutterwave SubAccount", frm.doc.custom_sous_compte_par_defaut).then(subaccount => {
                //  frm.doc.custom_pays.set_value(subaccount.country);
                //  frm.doc.custom_compte_bancaire.set_value(subaccount.bank_name);
                //  frm.doc["custom_numéro_du_compte"].set_value(subaccount.bank_name);

            });
        }
           
    }

});