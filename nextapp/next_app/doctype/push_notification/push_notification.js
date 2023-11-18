// Copyright (c) 2021, PT. Digital Asia Solusindo and contributors
// For license information, please see license.txt

frappe.ui.form.on('Push Notification', {
	refresh: function(frm) {
		frm.set_query("link_doctype", function() {
	        return {
	            "filters": [["name", "IN", ["Brand", "Item Group", "Item"]]]
	        }
	    })
	},
	onload_post_render: function(frm) {
        $(frm.fields_dict.url.input).on('focus', function(e) {
        	if(frm.doc.link_doctype == undefined)
            	frappe.throw("Please fill Link Doctype first");
        });
    },
    link_doctype: function(frm) {
    	frm.set_value("url", "")
    	if (frm.doc.link_doctype != "" && frm.doc.link_doctype != undefined)
    		frm.set_df_property("url", "reqd", 1)
    	else
    		frm.set_df_property("url", "reqd", 0)
    }
});
