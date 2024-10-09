frappe.listview_settings['Contact'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__('Scan Card'), function() {
            uploadImage(listview);
        });
    }
};

function uploadImage(frm) {
    frappe.prompt({
        fieldname: 'image',
        fieldtype: 'Attach Image',
        label: 'Upload Image',
        reqd: 1,
        options: 'Image'
    }, function(data) {
        const imgData = data.image;
        callExtractTextApi(imgData);
    }, 'Upload Image');
}

function callExtractTextApi(image_url) {
    frappe.call({
        method: "docvision.docvision.api.extract_data_from_image",
        args: {
            "file_id": image_url
        },
        callback: function(response) {
            if (response.message) {
                let data = response.message;

                if (typeof data === 'string') {
                    data = JSON.parse(data);
                }
                frappe.new_doc('Contact');
                setTimeout(() => {
                    window.cur_frm.set_value(data);
                }, 500);
            } else {
                frappe.msgprint(__('No data returned from API.'));
            }
        }
    });
}
