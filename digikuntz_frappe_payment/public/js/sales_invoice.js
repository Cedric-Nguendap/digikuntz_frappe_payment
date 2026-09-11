frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.outstanding_amount <= 0 || frm.doc.docstatus !== 1) return;

        frappe.db.get_value("Company", frm.doc.company, "custom_payment_gateway").then(r => {
            const gateway = r.message && r.message.custom_payment_gateway;
            if (!gateway) {
                frm.dashboard.add_comment(
                    __("Aucune passerelle de paiement configurée pour cette société."),
                    "red", false
                );
            }
        });
    }
});
