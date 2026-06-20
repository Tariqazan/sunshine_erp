frappe.provide("sunshine_power_ltd");

let _running_price_sync_timer = null;

frappe.ui.form.on("Sales Invoice", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.custom_sales_user) {
			frm.set_value("custom_sales_user", frappe.session.user);
		}
	},
	refresh(frm) {
		if (frm.is_new() && !frm.doc.custom_sales_user) {
			frm.set_value("custom_sales_user", frappe.session.user);
		}
		if (is_new_sales_invoice(frm)) {
			(frm.doc.items || []).forEach((row) => {
				sync_running_price_from_rate(frm, row.doctype, row.name);
			});
		}
	},
	items_add(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
});

frappe.ui.form.on("Sales Invoice Item", {
	item_code(frm, cdt, cdn) {
		get_synced_rows(frm).delete(cdn);
		schedule_running_price_sync(frm, cdt, cdn);
	},
});

function is_new_sales_invoice(frm) {
	return Boolean(frm.doc.__islocal || frm.is_new());
}

function get_synced_rows(frm) {
	if (!frm._sunshine_running_price_synced_rows) {
		frm._sunshine_running_price_synced_rows = new Set();
	}
	return frm._sunshine_running_price_synced_rows;
}

function schedule_running_price_sync(frm, cdt, cdn) {
	if (!is_new_sales_invoice(frm)) {
		return;
	}
	clearTimeout(_running_price_sync_timer);
	_running_price_sync_timer = setTimeout(() => {
		frappe.after_ajax(() => {
			sync_running_price_from_rate(frm, cdt, cdn);
		});
	}, 300);
}

function sync_running_price_from_rate(frm, cdt, cdn) {
	if (!is_new_sales_invoice(frm)) {
		return;
	}

	const row = locals[cdt]?.[cdn];
	if (!row || !row.item_code) {
		return;
	}

	if (get_synced_rows(frm).has(cdn)) {
		return;
	}

	const rate = flt(row.rate);
	if (!rate) {
		return;
	}

	frappe.model.set_value(cdt, cdn, "custom_running_price", rate);
	get_synced_rows(frm).add(cdn);
}
