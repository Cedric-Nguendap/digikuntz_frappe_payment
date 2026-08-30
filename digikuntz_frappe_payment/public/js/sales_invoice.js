frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.outstanding_amount <= 0) return;

        frappe.db.get_value("Company", frm.doc.company, "custom_payment_gateway").then(r => {
            const gateway = r.message && r.message.custom_payment_gateway;
            if (!gateway) {
                frm.dashboard.add_comment(__("Aucune passerelle de paiement configurée pour cette société."), "red", false);
                return;
            }

            if (gateway === "Flutterwave") {
                frappe.call({
                    method: "digikuntz_frappe_payment.api.flutterwave_settings.is_flutterwave_configured",
                    callback(r) {
                        if (!r.message) {
                            frm.dashboard.add_comment(__("Flutterwave désactivé ou non configuré."), "red", false);
                        }
                    }
                });
            } else if (gateway === "PawaPay") {
                frappe.call({
                    method: "frappe_digikuntz_pawapay.api.pawapay_settings.is_pawapay_configured",
                    callback(r) {
                        if (!r.message) {
                            frm.dashboard.add_comment(__("PawaPay désactivé ou non configuré."), "red", false);
                        }
                    }
                });
            }
        });
    }
});
