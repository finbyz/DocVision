frappe.ui.form.on('Telegram Setting', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Disconnect Webhook'), function () {
                frappe.confirm(
                    __('Are you sure you want to disconnect the Telegram webhook?'),
                    function () {
                        frm.call({
                            method: 'disconnect_webhook',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Disconnecting webhook...')
                        });
                    }
                );
            });
        }
    }
});