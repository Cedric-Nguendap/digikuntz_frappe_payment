frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {        
        // Vérifier si pas encore payée
        if (frm.doc.outstanding_amount > 0) {
            // Vérifier si flutterwave desactiver ou pas configuré
            frappe.call({
                method: "frappe_digikuntz_flutterwave.api.flutterwave_settings.is_flutterwave_configured",
                callback: function(r) {
                    if (!r.message) {
                        //Afficher la notification pour demander d'activer flutterwave
                        frm.dashboard.add_comment(  __( "Flutterwave disabled or not configured"),"red",false);
                    }
                }
            });
        }
    }
});