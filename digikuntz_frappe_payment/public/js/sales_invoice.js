frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.outstanding_amount <= 0) return;

        frappe.call({
            method: "digikuntz_frappe_payment.api.flutterwave_settings.is_gateway_configured",
            args: { company: frm.doc.company },
            callback(r) {
                if (!r.message) {
                    frm.dashboard.add_comment(
                        __("Aucune passerelle de paiement configurée ou activée pour cette société."),
                        "red", false
                    );
                }
            }
        });
    }
});
