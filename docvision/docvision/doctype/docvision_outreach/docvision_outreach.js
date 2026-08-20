// Copyright (c) 2026, Finbyz and contributors
// For license information, please see license.txt

frappe.ui.form.on('DocVision Outreach', {
    refresh: function(frm) {
        if (frm.doc.status !== 'Sent' && frm.doc.recipient_email) {
            frm.add_custom_button(__('Send Email Now'), function() {
                frappe.confirm(
                    __('Are you sure you want to send this outreach email to {0}?', [frm.doc.recipient_email]),
                    function() {
                        frappe.call({
                            doc: frm.doc,
                            method: 'send_outreach_email',
                            freeze: true,
                            freeze_message: __('Sending email...'),
                            callback: function() {
                                frm.reload_doc();
                                frappe.show_alert({
                                    message: __('Email sent successfully'),
                                    indicator: 'green'
                                });
                            }
                        });
                    }
                );
            }).addClass('btn-primary');
        }
    }
});
