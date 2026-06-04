import frappe
from frappe import _
from frappe.utils import cint, flt


def sync_sales_invoice_item_running_price(doc, method=None):
	for row in doc.get("items") or []:
		row.custom_running_price = flt(row.rate)


def sales_invoice_on_submit(doc, method=None):
	"""
	On Sales Invoice submit:
	1. Update last_purchase_rate on each Item using custom_purchase_price.
	2. Submit a Material Receipt Stock Entry to record the purchase cost
	   at the custom_purchase_price rate — this directly impacts COGS
	   via the Stock Ledger valuation rate.

	Skipped for Sales Return invoices.
	"""
	if cint(doc.get("is_return")):
		return

	items_with_price = [
		row for row in doc.items
		if row.get("custom_purchase_price") and row.item_code
	]

	if not items_with_price:
		return

	# --- 1. Update last_purchase_rate on Item ---
	for row in items_with_price:
		frappe.db.set_value(
			"Item",
			row.item_code,
			"last_purchase_rate",
			row.custom_purchase_price,
			update_modified=False,
		)

	# --- 2. Stock Entry (Material Receipt) to record valuation rate ---
	company = doc.company
	default_warehouse = frappe.db.get_value(
		"Warehouse",
		{"company": company, "is_group": 0, "disabled": 0},
		"name",
	)

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.company = company
	se.remarks = _("Auto-generated: Valuation update from Sales Invoice {0}").format(doc.name)

	for row in items_with_price:
		target_wh = row.get("warehouse") or default_warehouse
		if not target_wh:
			frappe.msgprint(
				_("No warehouse found for item {0}. Skipping Stock Entry row.").format(row.item_code),
				alert=True,
			)
			continue

		se.append("items", {
			"item_code": row.item_code,
			"qty": row.qty,
			"basic_rate": row.custom_purchase_price,
			"t_warehouse": target_wh,
		})

	if not se.items:
		return

	try:
		se.flags.ignore_permissions = True
		se.insert()
		se.submit()
		frappe.msgprint(
			_("Stock Entry {0} submitted to update valuation rate for COGS.").format(se.name),
			alert=True,
		)
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Stock Entry failed for Sales Invoice {0}".format(doc.name),
		)
		frappe.throw(
			_("Could not create Stock Entry for valuation update: {0}").format(str(e)),
			title=_("Stock Entry Error"),
		)
