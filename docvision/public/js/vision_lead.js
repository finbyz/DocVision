frappe.listview_settings["Lead"] = {
    onload(listview) {
        listview.page.add_menu_item(__("Scan Card"), () => {
            frappe.prompt(
                {
                    fieldname: "image",
                    fieldtype: "Attach Image",
                    label: __("Upload Image"),
                    reqd: 1,
                    options: "Image",
                },
                (values) => extractBusinessCard(values.image),
                __("Upload Image"),
            );
        });
    },
};

function extractBusinessCard(fileId) {
    frappe.call({
        method: "docvision.scan_api.extract_lead_from_image",
        args: { file_id: fileId },
    }).then((response) => {
        if (!response.message) {
            frappe.msgprint(__("No data returned from the card extraction agent."));
            return;
        }

        const values = typeof response.message === "string"
            ? JSON.parse(response.message)
            : response.message;
        frappe.new_doc("Lead", values);
    });
}
