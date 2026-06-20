from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate

PRODUCT_CONDITIONS = ("Damaged", "Sellable", "Repairable")


def _flt(value):
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0.0


def _parse_json(value):
	if isinstance(value, str):
		return frappe.parse_json(value)
	return value or []


def _has_warranty_field(doctype, fieldname):
	return frappe.db.has_column(doctype, fieldname)


@frappe.whitelist()
def get_warranty_context():
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	is_administrator = user == "Administrator" or "Administrator" in roles

	can_claim = frappe.has_permission("Sales Invoice", "create", user=user)
	can_settle = (
		frappe.has_permission("Delivery Note", "create", user=user)
		or frappe.has_permission("Stock Entry", "create", user=user)
	)

	show_claim_tab = is_administrator or can_claim
	show_settle_tab = is_administrator or can_settle
	show_tab_switcher = is_administrator or (show_claim_tab and show_settle_tab)

	default_tab = "claim"
	if show_settle_tab and not show_claim_tab:
		default_tab = "settle"

	return {
		"product_conditions": list(PRODUCT_CONDITIONS),
		"condition_warehouses": {
			"Damaged": "Warranty Damaged Warehouse",
			"Sellable": "Warranty Sellable Warehouse",
			"Repairable": "Warranty Repair Warehouse",
		},
		"default_receive_warehouse": "Warranty Incoming Warehouse",
		"is_administrator": is_administrator,
		"show_claim_tab": show_claim_tab,
		"show_settle_tab": show_settle_tab,
		"show_tab_switcher": show_tab_switcher,
		"default_tab": default_tab,
	}


@frappe.whitelist()
def search_sales_invoice(invoice_no=None, barcode=None):
	invoice_name = _resolve_sales_invoice(invoice_no, barcode)
	if not invoice_name:
		frappe.throw(_("No submitted Sales Invoice found for the given search."), title=_("Not Found"))

	return load_sales_invoice(invoice_name)


def _resolve_sales_invoice(invoice_no=None, barcode=None):
	search = (invoice_no or barcode or "").strip()
	if not search:
		frappe.throw(_("Enter a Sales Invoice number or barcode / serial number."))

	if frappe.db.exists(
		"Sales Invoice",
		{"name": search, "docstatus": 1, "is_return": 0},
	):
		return search

	if barcode or not invoice_no:
		by_serial = frappe.db.sql(
			"""
			SELECT si.name
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			WHERE si.docstatus = 1
				AND IFNULL(si.is_return, 0) = 0
				AND (
					sii.serial_no = %s
					OR sii.serial_no LIKE %s
					OR sii.serial_no LIKE %s
					OR sii.serial_no LIKE %s
				)
			ORDER BY si.posting_date DESC, si.creation DESC
			LIMIT 1
			""",
			(search, f"{search}\n%", f"%\n{search}", f"%\n{search}\n%"),
		)
		if by_serial:
			return by_serial[0][0]

		item_code = frappe.db.get_value("Item Barcode", {"barcode": search}, "parent")
		if item_code:
			by_barcode = frappe.db.sql(
				"""
				SELECT si.name
				FROM `tabSales Invoice` si
				INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
				WHERE si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND sii.item_code = %s
				ORDER BY si.posting_date DESC, si.creation DESC
				LIMIT 1
				""",
				item_code,
			)
			if by_barcode:
				return by_barcode[0][0]

	return None


@frappe.whitelist()
def load_sales_invoice(sales_invoice):
	frappe.has_permission("Sales Invoice", "read", throw=True)

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	if si.docstatus != 1:
		frappe.throw(_("Only submitted Sales Invoices are allowed."))
	if cint(si.is_return):
		frappe.throw(_("Please search the original Sales Invoice, not a return."))

	claimed_map = _get_claimed_qty_map(sales_invoice)
	replaced_map = _get_replaced_qty_map(sales_invoice)
	transfer_count = _get_transfer_count(sales_invoice)
	history = get_claim_history(sales_invoice)

	items = []
	for row in si.items:
		claimed_qty = _flt(claimed_map.get(row.name, {}).get("claimed_qty"))
		replaced_qty = _flt(replaced_map.get(row.name, {}).get("replaced_qty"))
		sold_qty = _flt(row.qty)
		remaining_qty = max(sold_qty - claimed_qty, 0)

		item_meta = frappe.get_cached_value(
			"Item",
			row.item_code,
			["has_serial_no", "has_batch_no"],
			as_dict=True,
		) or {}

		items.append(
			{
				"sales_invoice_item": row.name,
				"item_code": row.item_code,
				"item_name": row.item_name or row.item_code,
				"sold_qty": sold_qty,
				"claimed_qty": claimed_qty,
				"replaced_qty": replaced_qty,
				"remaining_qty": remaining_qty,
				"claim_qty": 0,
				"serial_no": row.serial_no or "",
				"batch_no": row.batch_no or "",
				"has_serial_no": cint(item_meta.get("has_serial_no")),
				"has_batch_no": cint(item_meta.get("has_batch_no")),
				"fully_claimed": remaining_qty <= 0,
				"rate": _flt(row.rate),
				"uom": row.uom,
				"warehouse": row.warehouse,
			}
		)

	summary = _build_summary(sales_invoice, si.customer, items, history, transfer_count)

	return {
		"sales_invoice": si.name,
		"customer": si.customer,
		"customer_name": si.customer_name,
		"company": si.company,
		"posting_date": si.posting_date,
		"grand_total": _flt(si.grand_total),
		"items": items,
		"summary": summary,
		"history": history,
	}


@frappe.whitelist()
def get_claim_history(sales_invoice):
	frappe.has_permission("Sales Invoice", "read", throw=True)

	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	product_condition_select = "'' AS product_condition"
	group_product_condition = ""
	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		product_condition_select = "si.custom_warranty_product_condition AS product_condition"
		group_product_condition = ", si.custom_warranty_product_condition"

	return_rows = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.posting_date,
			si.docstatus,
			{product_condition_select},
			GROUP_CONCAT(DISTINCT sii.item_code ORDER BY sii.item_code SEPARATOR ', ') AS items,
			SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.docstatus = 1
			AND si.is_return = 1
			AND si.return_against = %s
			{warranty_filter}
		GROUP BY si.name, si.posting_date, si.docstatus{group_product_condition}
		ORDER BY si.posting_date DESC, si.creation DESC
		""",
		sales_invoice,
		as_dict=True,
	)

	replacement_filter = ""
	delivery_rows = []
	if _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
			replacement_filter = "AND IFNULL(dn.custom_is_warranty_replacement, 0) = 1"

		delivery_rows = frappe.db.sql(
			f"""
			SELECT
				dn.name,
				dn.posting_date,
				dn.docstatus,
				GROUP_CONCAT(DISTINCT dni.item_code ORDER BY dni.item_code SEPARATOR ', ') AS items,
				SUM(dni.qty) AS replaced_qty
			FROM `tabDelivery Note` dn
			INNER JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
			WHERE dn.docstatus = 1
				AND dn.custom_warranty_sales_invoice = %s
				{replacement_filter}
			GROUP BY dn.name, dn.posting_date, dn.docstatus
			ORDER BY dn.posting_date DESC, dn.creation DESC
			""",
			sales_invoice,
			as_dict=True,
		)

	transfer_rows = []
	if _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		transfer_filter = ""
		if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
			transfer_filter = "AND IFNULL(se.custom_is_warranty_transfer, 0) = 1"

		transfer_rows = frappe.db.sql(
			f"""
			SELECT
				se.name,
				se.posting_date,
				se.docstatus,
				GROUP_CONCAT(DISTINCT sed.item_code ORDER BY sed.item_code SEPARATOR ', ') AS items,
				SUM(sed.qty) AS transfer_qty
			FROM `tabStock Entry` se
			INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
			WHERE se.docstatus = 1
				AND se.custom_warranty_sales_invoice = %s
				{transfer_filter}
			GROUP BY se.name, se.posting_date, se.docstatus
			ORDER BY se.posting_date DESC, se.creation DESC
			""",
			sales_invoice,
			as_dict=True,
		)

	history = []
	for row in return_rows:
		history.append(
			{
				"doctype": "Sales Invoice",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.claimed_qty),
				"status": _("Submitted") if row.docstatus == 1 else _("Draft"),
				"detail": row.product_condition or "",
				"type": "Return",
			}
		)

	for row in delivery_rows:
		history.append(
			{
				"doctype": "Delivery Note",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.replaced_qty),
				"status": _("Submitted") if row.docstatus == 1 else _("Draft"),
				"detail": _("Replacement"),
				"type": "Replacement",
			}
		)

	for row in transfer_rows:
		history.append(
			{
				"doctype": "Stock Entry",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.transfer_qty),
				"status": _("Submitted") if row.docstatus == 1 else _("Draft"),
				"detail": _("Warehouse Transfer"),
				"type": "Transfer",
			}
		)

	history.sort(key=lambda row: str(row.get("date") or ""), reverse=True)
	return history


def _get_claimed_qty_map(sales_invoice):
	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT sii.sales_invoice_item, SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1
			AND si.is_return = 1
			AND si.return_against = %s
			AND sii.sales_invoice_item IS NOT NULL
			AND sii.sales_invoice_item != ''
			{warranty_filter}
		GROUP BY sii.sales_invoice_item
		""",
		sales_invoice,
		as_dict=True,
	)
	return {row.sales_invoice_item: row for row in rows}


def _get_replaced_qty_map(sales_invoice):
	if not _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		return {}

	replacement_filter = ""
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		replacement_filter = "AND IFNULL(dn.custom_is_warranty_replacement, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT dni.si_detail AS sales_invoice_item, SUM(dni.qty) AS replaced_qty
		FROM `tabDelivery Note Item` dni
		INNER JOIN `tabDelivery Note` dn ON dn.name = dni.parent
		WHERE dn.docstatus = 1
			AND dn.custom_warranty_sales_invoice = %s
			AND dni.si_detail IS NOT NULL
			AND dni.si_detail != ''
			{replacement_filter}
		GROUP BY dni.si_detail
		""",
		sales_invoice,
		as_dict=True,
	)
	return {row.sales_invoice_item: row for row in rows}


def _get_transfer_count(sales_invoice):
	if not _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		return 0

	filters = {"docstatus": 1, "custom_warranty_sales_invoice": sales_invoice}
	if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
		filters["custom_is_warranty_transfer"] = 1

	return frappe.db.count("Stock Entry", filters)


def _build_summary(sales_invoice, customer, items, history, transfer_count):
	claimed_qty = sum(_flt(row.get("claimed_qty")) for row in items)
	replaced_qty = sum(_flt(row.get("replaced_qty")) for row in items)
	returned_qty = sum(
		_flt(row.get("qty"))
		for row in history
		if row.get("type") == "Return"
	)
	pending_qty = sum(max(_flt(row.get("remaining_qty")), 0) for row in items)

	status = "Draft"
	if returned_qty > 0:
		status = "Returned"
	if transfer_count > 0:
		status = "Inspected"
	if replaced_qty > 0:
		status = "Replaced"
	if pending_qty <= 0 and claimed_qty > 0 and replaced_qty >= claimed_qty:
		status = "Completed"

	return {
		"sales_invoice": sales_invoice,
		"customer": customer,
		"claimed_qty": claimed_qty,
		"returned_qty": returned_qty,
		"replaced_qty": replaced_qty,
		"pending_qty": pending_qty,
		"status": status,
	}


@frappe.whitelist()
def validate_claim_items(sales_invoice, items):
	items = _parse_json(items)
	_validate_claim_items(sales_invoice, items)
	return {"valid": True}


def _validate_claim_items(sales_invoice, items):
	if not items:
		frappe.throw(_("Select at least one item with claim quantity."))

	invoice_data = load_sales_invoice(sales_invoice)
	remaining_map = {
		row["sales_invoice_item"]: _flt(row["remaining_qty"]) for row in invoice_data["items"]
	}

	for row in items:
		si_item = row.get("sales_invoice_item")
		claim_qty = _flt(row.get("claim_qty"))
		if not si_item:
			frappe.throw(_("Each claim row must reference a sales invoice item."))
		if claim_qty <= 0:
			frappe.throw(
				_("Claim quantity must be greater than zero for item {0}.").format(
					row.get("item_code") or si_item
				)
			)
		remaining = remaining_map.get(si_item, 0)
		if claim_qty > remaining:
			frappe.throw(
				_("Claim quantity {0} exceeds remaining quantity {1} for item {2}.").format(
					claim_qty, remaining, row.get("item_code") or si_item
				)
			)


@frappe.whitelist()
def create_warranty_return(sales_invoice, items, receive_warehouse, product_condition, submit=0):
	frappe.has_permission("Sales Invoice", "create", throw=True)

	items = _parse_json(items)
	_validate_claim_items(sales_invoice, items)

	if not receive_warehouse:
		frappe.throw(_("Receive Warehouse is mandatory."))
	if product_condition not in PRODUCT_CONDITIONS:
		frappe.throw(_("Select a valid product condition."))

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	claim_map = {row["sales_invoice_item"]: row for row in items}

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	return_doc = frappe.get_doc(make_return_doc("Sales Invoice", sales_invoice))
	return_doc.set("items", [])
	return_doc.update_outstanding_for_self = 0
	return_doc.update_stock = 1
	return_doc.posting_date = nowdate()

	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		return_doc.custom_is_warranty_claim = 1
	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		return_doc.custom_warranty_product_condition = product_condition

	for source_item in si.items:
		claim = claim_map.get(source_item.name)
		if not claim:
			continue

		claim_qty = _flt(claim.get("claim_qty"))
		if claim_qty <= 0:
			continue

		return_doc.append(
			"items",
			{
				"item_code": source_item.item_code,
				"item_name": source_item.item_name,
				"description": source_item.description,
				"uom": source_item.uom,
				"stock_uom": source_item.stock_uom,
				"conversion_factor": source_item.conversion_factor or 1,
				"qty": -claim_qty,
				"rate": source_item.rate,
				"warehouse": receive_warehouse,
				"income_account": source_item.income_account,
				"expense_account": source_item.expense_account,
				"cost_center": source_item.cost_center,
				"sales_invoice_item": source_item.name,
				"dn_detail": source_item.dn_detail,
				"so_detail": source_item.so_detail,
				"delivery_note": source_item.delivery_note,
				"sales_order": source_item.sales_order,
				"serial_no": claim.get("serial_no") or source_item.serial_no,
				"batch_no": claim.get("batch_no") or source_item.batch_no,
			},
		)

	if not return_doc.items:
		frappe.throw(_("No return items could be created."))

	return_doc.run_method("calculate_taxes_and_totals")
	return_doc.insert()

	if cint(submit):
		return_doc.submit()

	return {
		"doctype": "Sales Invoice",
		"name": return_doc.name,
		"docstatus": return_doc.docstatus,
		"invoice": load_sales_invoice(sales_invoice),
	}


@frappe.whitelist()
def create_warranty_stock_transfer(
	sales_invoice,
	items,
	source_warehouse,
	target_warehouse,
	submit=0,
):
	frappe.has_permission("Stock Entry", "create", throw=True)

	items = _parse_json(items)
	if not source_warehouse or not target_warehouse:
		frappe.throw(_("Source and target warehouses are mandatory."))
	if source_warehouse == target_warehouse:
		frappe.throw(_("Source and target warehouse must be different."))

	transfer_items = [row for row in items if _flt(row.get("transfer_qty")) > 0]
	if not transfer_items:
		frappe.throw(_("Enter transfer quantity for at least one item."))

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	company = si.company

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Transfer"
	se.purpose = "Material Transfer"
	se.company = company
	se.posting_date = nowdate()
	if _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		se.custom_warranty_sales_invoice = sales_invoice
	if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
		se.custom_is_warranty_transfer = 1

	for row in transfer_items:
		qty = _flt(row.get("transfer_qty"))
		item_code = row.get("item_code")
		if not item_code:
			continue

		available = _get_stock_balance(item_code, source_warehouse)
		if qty > available:
			frappe.throw(
				_("Insufficient stock for {0} in {1}. Available: {2}, Required: {3}").format(
					item_code, source_warehouse, available, qty
				)
			)

		se.append(
			"items",
			{
				"item_code": item_code,
				"qty": qty,
				"s_warehouse": source_warehouse,
				"t_warehouse": target_warehouse,
				"uom": row.get("uom") or frappe.db.get_value("Item", item_code, "stock_uom"),
				"conversion_factor": 1,
				"serial_no": row.get("serial_no") or "",
				"batch_no": row.get("batch_no") or "",
			},
		)

	if not se.items:
		frappe.throw(_("No stock transfer items could be created."))

	se.insert()
	if cint(submit):
		se.submit()

	return {
		"doctype": "Stock Entry",
		"name": se.name,
		"docstatus": se.docstatus,
		"invoice": load_sales_invoice(sales_invoice),
	}


@frappe.whitelist()
def create_warranty_replacement(
	sales_invoice,
	items,
	replacement_warehouse,
	submit=0,
):
	frappe.has_permission("Delivery Note", "create", throw=True)

	items = _parse_json(items)
	if not replacement_warehouse:
		frappe.throw(_("Replacement Warehouse is mandatory."))

	replacement_items = [row for row in items if _flt(row.get("replacement_qty")) > 0]
	if not replacement_items:
		frappe.throw(_("Enter replacement quantity for at least one item."))

	invoice_data = load_sales_invoice(sales_invoice)
	claimed_map = {row["sales_invoice_item"]: row for row in invoice_data["items"]}

	for row in replacement_items:
		si_item = row.get("sales_invoice_item")
		replacement_qty = _flt(row.get("replacement_qty"))
		claimed_qty = _flt(claimed_map.get(si_item, {}).get("claimed_qty"))
		if replacement_qty > claimed_qty:
			frappe.throw(
				_("Replacement quantity cannot exceed submitted claim quantity for item {0}. Submit the return invoice first.").format(
					row.get("item_code") or si_item
				)
			)

		item_code = row.get("replacement_item_code") or row.get("item_code")
		available = _get_stock_balance(item_code, replacement_warehouse)
		if replacement_qty > available:
			frappe.throw(
				_("Insufficient stock for {0} in {1}. Available: {2}, Required: {3}").format(
					item_code, replacement_warehouse, available, replacement_qty
				)
			)

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	dn = frappe.new_doc("Delivery Note")
	dn.customer = si.customer
	dn.company = si.company
	dn.posting_date = nowdate()
	if _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		dn.custom_warranty_sales_invoice = sales_invoice
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		dn.custom_is_warranty_replacement = 1

	source_items = {row.name: row for row in si.items}

	for row in replacement_items:
		source_item = source_items.get(row.get("sales_invoice_item"))
		if not source_item:
			continue

		replacement_qty = _flt(row.get("replacement_qty"))
		replacement_item_code = row.get("replacement_item_code") or source_item.item_code

		dn.append(
			"items",
			{
				"item_code": replacement_item_code,
				"item_name": frappe.db.get_value("Item", replacement_item_code, "item_name")
				or replacement_item_code,
				"qty": replacement_qty,
				"uom": source_item.uom,
				"stock_uom": source_item.stock_uom,
				"conversion_factor": source_item.conversion_factor or 1,
				"rate": source_item.rate,
				"warehouse": replacement_warehouse,
				"against_sales_invoice": sales_invoice,
				"si_detail": source_item.name,
				"cost_center": source_item.cost_center,
			},
		)

	if not dn.items:
		frappe.throw(_("No replacement items could be created."))

	dn.run_method("set_missing_values")
	dn.run_method("calculate_taxes_and_totals")
	dn.insert()

	if cint(submit):
		dn.submit()

	return {
		"doctype": "Delivery Note",
		"name": dn.name,
		"docstatus": dn.docstatus,
		"invoice": load_sales_invoice(sales_invoice),
	}


@frappe.whitelist()
def get_stock_availability(item_code, warehouse):
	return {
		"item_code": item_code,
		"warehouse": warehouse,
		"available_qty": _get_stock_balance(item_code, warehouse),
	}


def _get_stock_balance(item_code, warehouse):
	from erpnext.stock.utils import get_stock_balance

	return _flt(get_stock_balance(item_code, warehouse))
