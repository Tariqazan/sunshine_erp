from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate

PRODUCT_CONDITIONS = ("Damaged", "Sellable", "Repairable")

WARRANTY_CLAIM_ROLES = frozenset({"Salesman"})
WARRANTY_SETTLE_ROLES = frozenset({"Factory User"})


def _user_roles(user=None):
	if not user:
		user = frappe.session.user
	return set(frappe.get_roles(user))


def _is_warranty_administrator(user=None):
	if not user:
		user = frappe.session.user
	return user == "Administrator" or "Administrator" in _user_roles(user)


def can_warranty_claim(user=None):
	if _is_warranty_administrator(user):
		return True
	if _user_roles(user).intersection(WARRANTY_CLAIM_ROLES):
		return True
	return frappe.has_permission("Sales Invoice", "create", user=user or frappe.session.user)


def can_warranty_settle(user=None):
	if _is_warranty_administrator(user):
		return True
	if _user_roles(user).intersection(WARRANTY_SETTLE_ROLES):
		return True
	user = user or frappe.session.user
	return (
		frappe.has_permission("Sales Invoice", "submit", user=user)
		or frappe.has_permission("Delivery Note", "create", user=user)
		or frappe.has_permission("Stock Entry", "create", user=user)
	)


def _require_warranty_claim():
	if not can_warranty_claim():
		frappe.throw(_("You are not allowed to register warranty claims."), frappe.PermissionError)


def _require_warranty_settle():
	if not can_warranty_settle():
		frappe.throw(_("You are not allowed to settle warranty claims."), frappe.PermissionError)


def _require_warranty_read():
	if can_warranty_claim() or can_warranty_settle():
		return
	frappe.has_permission("Sales Invoice", "read", throw=True)


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


def _get_company_warehouse(company):
	if not company:
		return None
	return frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")


@frappe.whitelist()
def get_warranty_context():
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	is_administrator = user == "Administrator" or "Administrator" in roles

	if is_administrator:
		show_claim_tab = True
		show_settle_tab = True
	elif roles.intersection(WARRANTY_CLAIM_ROLES):
		show_claim_tab = True
		show_settle_tab = False
	elif roles.intersection(WARRANTY_SETTLE_ROLES):
		show_claim_tab = False
		show_settle_tab = True
	else:
		show_claim_tab = can_warranty_claim(user)
		show_settle_tab = can_warranty_settle(user)

	show_tab_switcher = is_administrator or (show_claim_tab and show_settle_tab)

	default_tab = "claim"
	if show_settle_tab and not show_claim_tab:
		default_tab = "settle"

	return {
		"product_conditions": list(PRODUCT_CONDITIONS),
		"is_administrator": is_administrator,
		"show_claim_tab": show_claim_tab,
		"show_settle_tab": show_settle_tab,
		"show_tab_switcher": show_tab_switcher,
		"default_tab": default_tab,
	}


@frappe.whitelist()
def get_claim_queue(limit=40):
	"""Claims registered by field team — qty only, awaiting settle team."""
	_require_warranty_claim()
	limit = min(cint(limit) or 40, 100)

	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name AS return_invoice,
			si.return_against AS sales_invoice,
			si.customer,
			si.customer_name,
			si.posting_date,
			si.docstatus,
			si.owner,
			si.modified,
			SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.is_return = 1
			AND si.docstatus < 2
			AND si.return_against IS NOT NULL
			AND si.return_against != ''
			{warranty_filter}
		GROUP BY si.name, si.return_against, si.customer, si.customer_name,
			si.posting_date, si.docstatus, si.owner, si.modified
		ORDER BY si.modified DESC
		LIMIT %s
		""",
		(limit,),
		as_dict=True,
	)

	queue = []
	for row in rows:
		is_draft = cint(row.docstatus) == 0
		queue.append({
			"return_invoice": row.return_invoice,
			"sales_invoice": row.sales_invoice,
			"customer": row.customer,
			"customer_name": row.customer_name,
			"posting_date": row.posting_date,
			"claimed_qty": _flt(row.claimed_qty),
			"owner": row.owner,
			"modified": row.modified,
			"docstatus": row.docstatus,
			"status": _("Registered — with Settle Team") if is_draft else _("Received in Stock"),
			"status_key": "registered" if is_draft else "received",
		})

	registered_count = sum(1 for row in queue if row["status_key"] == "registered")
	return {"rows": queue, "registered_count": registered_count, "total_count": len(queue)}


@frappe.whitelist()
def get_settle_queue(limit=40):
	"""Draft claims awaiting receive/submit, and submitted claims pending replacement."""
	_require_warranty_settle()
	limit = min(cint(limit) or 40, 100)

	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	candidates = frappe.db.sql(
		f"""
		SELECT
			si.return_against AS sales_invoice,
			si.name AS return_invoice,
			si.docstatus,
			SUM(ABS(sii.qty)) AS return_qty,
			MAX(si.modified) AS modified
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.is_return = 1
			AND si.docstatus < 2
			AND si.return_against IS NOT NULL
			AND si.return_against != ''
			{warranty_filter}
		GROUP BY si.return_against, si.name, si.docstatus
		ORDER BY modified DESC
		LIMIT %s
		""",
		(limit * 3,),
		as_dict=True,
	)

	queue = []
	seen = set()
	for row in candidates:
		sales_invoice = row.sales_invoice
		if sales_invoice in seen:
			continue

		try:
			invoice_data = load_sales_invoice(sales_invoice)
		except Exception:
			continue

		is_draft = cint(row.docstatus) == 0
		claimed = _flt(invoice_data["summary"].get("claimed_qty"))
		registered = _flt(invoice_data["summary"].get("registered_qty"))
		replaced = _flt(invoice_data["summary"].get("replaced_qty"))

		if is_draft:
			queue.append({
				"sales_invoice": sales_invoice,
				"return_invoice": row.return_invoice,
				"customer": invoice_data.get("customer"),
				"customer_name": invoice_data.get("customer_name"),
				"posting_date": invoice_data.get("posting_date"),
				"claimed_qty": _flt(row.return_qty),
				"replaced_qty": replaced,
				"pending_qty": _flt(row.return_qty),
				"status": _("Awaiting Receive & Submit"),
				"status_key": "awaiting_receive",
			})
			seen.add(sales_invoice)
			if len(queue) >= limit:
				break
			continue

		if claimed <= 0:
			continue

		pending = max(claimed - replaced, 0)
		if pending <= 0:
			continue

		queue.append({
			"sales_invoice": sales_invoice,
			"return_invoice": row.return_invoice,
			"customer": invoice_data.get("customer"),
			"customer_name": invoice_data.get("customer_name"),
			"posting_date": invoice_data.get("posting_date"),
			"claimed_qty": claimed,
			"replaced_qty": replaced,
			"pending_qty": pending,
			"status": _("Awaiting Replacement"),
			"status_key": "awaiting_replacement",
		})
		seen.add(sales_invoice)
		if len(queue) >= limit:
			break

	return {"rows": queue, "total_count": len(queue)}


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
	_require_warranty_read()

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	if si.docstatus != 1:
		frappe.throw(_("Only submitted Sales Invoices are allowed."))
	if cint(si.is_return):
		frappe.throw(_("Please search the original Sales Invoice, not a return."))

	claimed_map = _get_claimed_qty_map(sales_invoice)
	registered_map = _get_registered_qty_map(sales_invoice)
	replaced_map = _get_replaced_qty_map(sales_invoice)
	transfer_count = _get_transfer_count(sales_invoice)
	draft_returns = _get_draft_returns(sales_invoice)
	history = get_claim_history(sales_invoice)

	items = []
	for row in si.items:
		claimed_qty = _flt(claimed_map.get(row.name, {}).get("claimed_qty"))
		registered_qty = _flt(registered_map.get(row.name, {}).get("registered_qty"))
		replaced_qty = _flt(replaced_map.get(row.name, {}).get("replaced_qty"))
		sold_qty = _flt(row.qty)
		remaining_qty = max(sold_qty - claimed_qty - registered_qty, 0)

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
				"registered_qty": registered_qty,
				"replaced_qty": replaced_qty,
				"remaining_qty": remaining_qty,
				"claim_qty": 0,
				"serial_no": row.serial_no or "",
				"batch_no": row.batch_no or "",
				"has_serial_no": cint(item_meta.get("has_serial_no")),
				"has_batch_no": cint(item_meta.get("has_batch_no")),
				"fully_claimed": remaining_qty <= 0,
				"pending_settle_qty": registered_qty if registered_qty > 0 else max(claimed_qty - replaced_qty, 0),
				"rate": _flt(row.rate),
				"uom": row.uom,
				"warehouse": row.warehouse,
			}
		)

	summary = _build_summary(sales_invoice, si.customer, items, history, transfer_count)
	has_draft = bool(draft_returns)
	claimed_qty = _flt(summary.get("claimed_qty"))
	settle_mode = "none"
	if has_draft:
		settle_mode = "full"
	elif claimed_qty > _flt(summary.get("replaced_qty")):
		settle_mode = "replacement_only"

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
		"draft_returns": draft_returns,
		"has_draft_return": has_draft,
		"pending_return_invoice": draft_returns[0]["name"] if draft_returns else "",
		"settle_mode": settle_mode,
	}


@frappe.whitelist()
def get_claim_history(sales_invoice):
	_require_warranty_read()

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
		WHERE si.docstatus < 2
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
				"status": _("Received") if row.docstatus == 1 else _("Registered"),
				"status_key": "received" if row.docstatus == 1 else "registered",
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


def _get_registered_qty_map(sales_invoice):
	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT sii.sales_invoice_item, SUM(ABS(sii.qty)) AS registered_qty
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 0
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


def _get_draft_returns(sales_invoice):
	warranty_filter = ""
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		warranty_filter = "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.posting_date,
			SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.docstatus = 0
			AND si.is_return = 1
			AND si.return_against = %s
			{warranty_filter}
		GROUP BY si.name, si.posting_date
		ORDER BY si.creation DESC
		""",
		sales_invoice,
		as_dict=True,
	)
	return [
		{
			"name": row.name,
			"posting_date": row.posting_date,
			"claimed_qty": _flt(row.claimed_qty),
		}
		for row in rows
	]


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
	registered_qty = sum(_flt(row.get("registered_qty")) for row in items)
	replaced_qty = sum(_flt(row.get("replaced_qty")) for row in items)
	returned_qty = sum(
		_flt(row.get("qty"))
		for row in history
		if row.get("type") == "Return" and row.get("status_key") == "received"
	)
	pending_qty = sum(max(_flt(row.get("remaining_qty")), 0) for row in items)

	status = "Registered" if registered_qty > 0 and claimed_qty <= 0 else "Draft"
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
		"registered_qty": registered_qty,
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
def create_warranty_return(sales_invoice, items, receive_warehouse=None, product_condition=None, submit=0):
	"""Claim team registers qty only — draft return without stock movement."""
	_require_warranty_claim()

	items = _parse_json(items)
	_validate_claim_items(sales_invoice, items)

	si = frappe.get_doc("Sales Invoice", sales_invoice)
	claim_map = {row["sales_invoice_item"]: row for row in items}
	company_wh = _get_company_warehouse(si.company)

	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	return_doc = frappe.get_doc(make_return_doc("Sales Invoice", sales_invoice))
	return_doc.set("items", [])
	return_doc.update_outstanding_for_self = 0
	return_doc.update_stock = 0
	return_doc.posting_date = nowdate()

	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		return_doc.custom_is_warranty_claim = 1

	for source_item in si.items:
		claim = claim_map.get(source_item.name)
		if not claim:
			continue

		claim_qty = _flt(claim.get("claim_qty"))
		if claim_qty <= 0:
			continue

		item_warehouse = source_item.warehouse or company_wh

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
				"warehouse": item_warehouse,
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
	return_doc.insert(ignore_permissions=bool(_user_roles().intersection(WARRANTY_CLAIM_ROLES)))

	return {
		"doctype": "Sales Invoice",
		"name": return_doc.name,
		"docstatus": return_doc.docstatus,
		"invoice": load_sales_invoice(sales_invoice),
	}


def _submit_warranty_return_doc(return_doc, receive_warehouse, product_condition, ignore_permissions=False):
	if product_condition not in PRODUCT_CONDITIONS:
		frappe.throw(_("Select a valid product condition."))

	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		if not cint(return_doc.custom_is_warranty_claim):
			frappe.throw(_("This is not a warranty return invoice."))

	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		return_doc.custom_warranty_product_condition = product_condition

	return_doc.update_stock = 1
	for item in return_doc.items:
		item.warehouse = receive_warehouse

	return_doc.flags.ignore_permissions = ignore_permissions
	return_doc.save()
	return_doc.submit()
	return return_doc


def _build_transfer_items_from_return(return_doc):
	items = []
	for row in return_doc.items:
		qty = abs(_flt(row.qty))
		if qty <= 0:
			continue
		items.append({
			"sales_invoice_item": row.sales_invoice_item,
			"item_code": row.item_code,
			"uom": row.uom,
			"transfer_qty": qty,
			"serial_no": row.serial_no or "",
			"batch_no": row.batch_no or "",
		})
	return items


@frappe.whitelist()
def settle_warranty_claim(
	sales_invoice,
	return_invoice=None,
	receive_warehouse=None,
	product_condition=None,
	target_warehouse=None,
	replacement_warehouse=None,
	items=None,
):
	"""One step: submit return (if draft), transfer to condition warehouse, issue replacement."""
	_require_warranty_settle()
	ignore_permissions = bool(_user_roles().intersection(WARRANTY_SETTLE_ROLES))

	items = _parse_json(items)
	replacement_items = [row for row in items if _flt(row.get("replacement_qty")) > 0]
	if not replacement_items:
		frappe.throw(_("Enter replacement quantity for at least one item."))
	if not replacement_warehouse:
		frappe.throw(_("Replacement Warehouse is mandatory."))

	invoice_data = load_sales_invoice(sales_invoice)
	if not return_invoice:
		return_invoice = invoice_data.get("pending_return_invoice")

	has_draft = invoice_data.get("has_draft_return")

	if has_draft:
		if not return_invoice:
			frappe.throw(_("No pending return found for this invoice."))
		if not receive_warehouse:
			frappe.throw(_("Receive Warehouse is mandatory."))

		return_doc = frappe.get_doc("Sales Invoice", return_invoice)
		if return_doc.docstatus != 0:
			frappe.throw(_("Return invoice is already submitted."))

		_submit_warranty_return_doc(
			return_doc, receive_warehouse, product_condition, ignore_permissions=ignore_permissions
		)
		if not target_warehouse:
			frappe.throw(_("Select warehouse to move received item to."))

		transfer_items = _build_transfer_items_from_return(return_doc)
		if transfer_items and target_warehouse and receive_warehouse != target_warehouse:
			create_warranty_stock_transfer(
				sales_invoice,
				transfer_items,
				receive_warehouse,
				target_warehouse,
				submit=1,
				ignore_permissions=ignore_permissions,
			)
	elif _flt(invoice_data["summary"].get("claimed_qty")) <= 0:
		frappe.throw(_("No claim found for this invoice."))

	return create_warranty_replacement(
		sales_invoice,
		replacement_items,
		replacement_warehouse,
		submit=1,
		ignore_permissions=ignore_permissions,
	)


@frappe.whitelist()
def submit_warranty_return(return_invoice, receive_warehouse=None, product_condition=None):
	"""Settle team receives product — set warehouse, condition, and submit return."""
	_require_warranty_settle()
	ignore_permissions = bool(_user_roles().intersection(WARRANTY_SETTLE_ROLES))

	if not frappe.db.exists("Sales Invoice", return_invoice):
		frappe.throw(_("Return invoice {0} not found.").format(return_invoice))

	if not receive_warehouse:
		frappe.throw(_("Receive Warehouse is mandatory."))
	if product_condition not in PRODUCT_CONDITIONS:
		frappe.throw(_("Select a valid product condition."))

	return_doc = frappe.get_doc("Sales Invoice", return_invoice)
	if not cint(return_doc.is_return):
		frappe.throw(_("Only return invoices can be submitted here."))
	if return_doc.docstatus != 0:
		frappe.throw(_("Return invoice is already submitted or cancelled."))

	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		if not cint(return_doc.custom_is_warranty_claim):
			frappe.throw(_("This is not a warranty return invoice."))

	_submit_warranty_return_doc(
		return_doc, receive_warehouse, product_condition, ignore_permissions=ignore_permissions
	)

	sales_invoice = return_doc.return_against
	return {
		"doctype": "Sales Invoice",
		"name": return_doc.name,
		"docstatus": return_doc.docstatus,
		"sales_invoice": sales_invoice,
		"receive_warehouse": receive_warehouse,
		"invoice": load_sales_invoice(sales_invoice) if sales_invoice else None,
	}


@frappe.whitelist()
def create_warranty_stock_transfer(
	sales_invoice,
	items,
	source_warehouse,
	target_warehouse,
	submit=0,
	ignore_permissions=False,
):
	if not ignore_permissions and not can_warranty_settle():
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

	se.flags.ignore_permissions = ignore_permissions
	se.insert(ignore_permissions=ignore_permissions)
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
	ignore_permissions=False,
):
	if not ignore_permissions and not can_warranty_settle():
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
	dn.flags.ignore_permissions = ignore_permissions
	dn.insert(ignore_permissions=ignore_permissions)

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
