frappe.provide("sunshine_power_ltd");

let _running_price_sync_timer = null;

frappe.ui.form.on("Sales Invoice", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.custom_sales_user) {
			frm.set_value("custom_sales_user", frappe.session.user);
		}
		if (is_new_sales_invoice(frm)) {
			patch_calculate_taxes_and_totals(frm);
		}
	},
	refresh(frm) {
		if (frm.is_new() && !frm.doc.custom_sales_user) {
			frm.set_value("custom_sales_user", frappe.session.user);
		}
		if (is_new_sales_invoice(frm)) {
			sync_all_running_prices(frm);
		}
	},
	items_add(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
});

frappe.ui.form.on("Sales Invoice Item", {
	rate(frm, cdt, cdn) {
		sync_running_price_from_rate(frm, cdt, cdn);
	},
	price_list_rate(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
	item_code(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
	qty(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
	discount_percentage(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
	discount_amount(frm, cdt, cdn) {
		schedule_running_price_sync(frm, cdt, cdn);
	},
});

function is_new_sales_invoice(frm) {
	return Boolean(frm.doc.__islocal || frm.is_new());
}

function schedule_running_price_sync(frm, cdt, cdn) {
	if (!is_new_sales_invoice(frm)) {
		return;
	}
	clearTimeout(_running_price_sync_timer);
	_running_price_sync_timer = setTimeout(() => {
		frappe.after_ajax(() => {
			sync_running_price_from_rate(frm, cdt, cdn);
			sync_all_running_prices(frm);
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

	const rate = flt(row.rate);
	if (!rate) {
		return;
	}

	if (flt(row.custom_running_price) === rate) {
		return;
	}

	frappe.model.set_value(cdt, cdn, "custom_running_price", rate);
}

function sync_all_running_prices(frm) {
	if (!is_new_sales_invoice(frm)) {
		return;
	}
	(frm.doc.items || []).forEach((row) => {
		sync_running_price_from_rate(frm, row.doctype, row.name);
	});
}

function patch_calculate_taxes_and_totals(frm) {
	if (frm._sunshine_running_price_patched || !frm.cscript?.calculate_taxes_and_totals) {
		return;
	}

	const original = frm.cscript.calculate_taxes_and_totals.bind(frm.cscript);
	frm.cscript.calculate_taxes_and_totals = async function (...args) {
		const result = await original(...args);
		sync_all_running_prices(frm);
		return result;
	};
	frm._sunshine_running_price_patched = true;
}
