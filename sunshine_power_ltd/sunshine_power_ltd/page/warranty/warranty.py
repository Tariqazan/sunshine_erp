import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate

PRODUCT_CONDITIONS = ("Damaged", "Sellable", "Repairable")

WARRANTY_CLAIM_ROLES = frozenset({"Salesman"})
WARRANTY_SETTLE_ROLES = frozenset({"Factory User"})

# Linear claim lifecycle, tracked on the (always-draft) return Sales Invoice.
STATUS_REQUESTED = "Requested"
STATUS_RECEIVED = "Received"
STATUS_READY = "Ready"
STATUS_COMPLETED = "Completed"
OPEN_STATUSES = (STATUS_REQUESTED, STATUS_RECEIVED, STATUS_READY)


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
		frappe.has_permission("Delivery Note", "create", user=user)
		or frappe.has_permission("Stock Entry", "create", user=user)
	)


def can_warranty_handover(user=None):
	"""Step 4 (hand over) is owned by the salesman, but settle/admin may also do it."""
	return can_warranty_claim(user) or can_warranty_settle(user)


def _require_warranty_claim():
	if not can_warranty_claim():
		frappe.throw(_("You are not allowed to register warranty claims."), frappe.PermissionError)


def _require_warranty_settle():
	if not can_warranty_settle():
		frappe.throw(_("You are not allowed to process warranty claims."), frappe.PermissionError)


def _require_warranty_handover():
	if not can_warranty_handover():
		frappe.throw(_("You are not allowed to hand over warranty replacements."), frappe.PermissionError)


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


def _has_status_field():
	return _has_warranty_field("Sales Invoice", "custom_warranty_status")


def _get_company_warehouse(company):
	if not company:
		return None
	return frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")


def _set_warranty_status(return_invoice, status):
	if return_invoice and _has_status_field():
		frappe.db.set_value("Sales Invoice", return_invoice, "custom_warranty_status", status)


def _warranty_si_filter():
	if _has_warranty_field("Sales Invoice", "custom_is_warranty_claim"):
		return "AND IFNULL(si.custom_is_warranty_claim, 0) = 1"
	return ""


def _action_for_status(status):
	"""Which actor/action the claim is waiting on."""
	return {
		STATUS_REQUESTED: "receive",
		STATUS_RECEIVED: "prepare",
		STATUS_READY: "handover",
		STATUS_COMPLETED: "none",
	}.get(status, "none")


@frappe.whitelist()
def get_warranty_context():
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	is_administrator = user == "Administrator" or "Administrator" in roles

	has_claim_role = bool(roles.intersection(WARRANTY_CLAIM_ROLES))
	has_settle_role = bool(roles.intersection(WARRANTY_SETTLE_ROLES))

	if is_administrator:
		show_claim_tab = True
		show_settle_tab = True
	elif has_claim_role or has_settle_role:
		# Evaluate each role independently so a user holding both roles sees both tabs.
		show_claim_tab = has_claim_role
		show_settle_tab = has_settle_role
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


def _claim_rows(limit):
	"""All open warranty claims (draft returns), newest first, with status."""
	status_select = "'' AS warranty_status"
	if _has_status_field():
		status_select = "IFNULL(si.custom_warranty_status, '') AS warranty_status"

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name AS return_invoice,
			si.return_against AS sales_invoice,
			si.customer,
			si.customer_name,
			si.posting_date,
			si.owner,
			si.modified,
			{status_select},
			SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.is_return = 1
			AND si.docstatus = 0
			AND si.return_against IS NOT NULL
			AND si.return_against != ''
			{_warranty_si_filter()}
		GROUP BY si.name, si.return_against, si.customer, si.customer_name,
			si.posting_date, si.owner, si.modified, warranty_status
		ORDER BY si.modified DESC
		LIMIT %s
		""",
		(limit,),
		as_dict=True,
	)
	return rows


def _claim_status_label(status):
	"""(label, status_key) for a claim status, translated per request."""
	return {
		STATUS_REQUESTED: (_("Requested — awaiting factory"), "requested"),
		STATUS_RECEIVED: (_("Received by factory"), "received"),
		STATUS_READY: (_("Ready — confirm hand-over"), "ready"),
		STATUS_COMPLETED: (_("Completed"), "completed"),
	}.get(status, (status, "requested"))


@frappe.whitelist()
def get_claim_queue(limit=40):
	"""Salesman view: every claim this team raised, with where it stands."""
	_require_warranty_claim()
	limit = min(cint(limit) or 40, 100)

	rows = []
	for row in _claim_rows(limit):
		status = row.warranty_status or STATUS_REQUESTED
		label, key = _claim_status_label(status)
		rows.append({
			"return_invoice": row.return_invoice,
			"sales_invoice": row.sales_invoice,
			"customer": row.customer,
			"customer_name": row.customer_name,
			"posting_date": row.posting_date,
			"claimed_qty": _flt(row.claimed_qty),
			"warranty_status": status,
			"status": label,
			"status_key": key,
			"can_handover": status == STATUS_READY,
		})

	ready_count = sum(1 for r in rows if r["warranty_status"] == STATUS_READY)
	return {"rows": rows, "ready_count": ready_count, "total_count": len(rows)}


@frappe.whitelist()
def get_settle_queue(limit=40):
	"""Factory view: claims awaiting receive (Requested) or replacement prep (Received)."""
	_require_warranty_settle()
	limit = min(cint(limit) or 40, 100)

	rows = []
	for row in _claim_rows(limit * 2):
		status = row.warranty_status or STATUS_REQUESTED
		if status == STATUS_REQUESTED:
			label, key = _("Awaiting receive"), "receive"
		elif status == STATUS_RECEIVED:
			label, key = _("Awaiting replacement prep"), "prepare"
		else:
			continue
		rows.append({
			"return_invoice": row.return_invoice,
			"sales_invoice": row.sales_invoice,
			"customer": row.customer,
			"customer_name": row.customer_name,
			"posting_date": row.posting_date,
			"claimed_qty": _flt(row.claimed_qty),
			"warranty_status": status,
			"status": label,
			"status_key": key,
		})
		if len(rows) >= limit:
			break

	return {"rows": rows, "total_count": len(rows)}


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

	active_returns = _get_active_returns(sales_invoice)
	requested_map = _aggregate_return_items(active_returns)
	prepared_map = _get_prepared_qty_map(sales_invoice)
	completed_map = _get_completed_qty_map(sales_invoice)
	received_map = _get_received_qty_map(sales_invoice)
	history = get_claim_history(sales_invoice)

	pending_return = active_returns[0] if active_returns else None
	# Fall back to Requested for claims created before the status field was added.
	claim_status = (pending_return or {}).get("warranty_status") or (STATUS_REQUESTED if pending_return else "")
	product_condition = (pending_return or {}).get("product_condition") or ""
	pending_delivery_note = _get_draft_replacement_dn(sales_invoice)

	items = []
	for row in si.items:
		sold_qty = _flt(row.qty)
		requested_qty = _flt(requested_map.get(row.name))
		prepared_qty = _flt(prepared_map.get(row.name))
		completed_qty = _flt(completed_map.get(row.name))
		received_qty = _flt(received_map.get(row.item_code))
		remaining_qty = max(sold_qty - requested_qty - completed_qty, 0)
		pending_prepare_qty = max(requested_qty - prepared_qty - completed_qty, 0)

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
				"requested_qty": requested_qty,
				"received_qty": received_qty,
				"prepared_qty": prepared_qty,
				"completed_qty": completed_qty,
				"remaining_qty": remaining_qty,
				"pending_prepare_qty": pending_prepare_qty,
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

	summary = _build_summary(sales_invoice, si.customer, items, claim_status)

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
		"claim_status": claim_status,
		"product_condition": product_condition,
		"action": _action_for_status(claim_status) if pending_return else "none",
		"pending_return_invoice": (pending_return or {}).get("name") or "",
		"pending_delivery_note": pending_delivery_note,
		"has_open_claim": bool(pending_return),
	}


def _get_active_returns(sales_invoice):
	"""Draft warranty return invoices that are not yet Completed, newest first."""
	status_select = "'' AS warranty_status"
	if _has_status_field():
		status_select = "IFNULL(si.custom_warranty_status, '') AS warranty_status"
	condition_select = "'' AS product_condition"
	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		condition_select = "IFNULL(si.custom_warranty_product_condition, '') AS product_condition"

	rows = frappe.db.sql(
		f"""
		SELECT si.name, si.posting_date, si.creation, {status_select}, {condition_select}
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 0
			AND si.is_return = 1
			AND si.return_against = %s
			{_warranty_si_filter()}
		ORDER BY si.creation DESC
		""",
		sales_invoice,
		as_dict=True,
	)
	return [row for row in rows if (row.get("warranty_status") or "") != STATUS_COMPLETED]


def _aggregate_return_items(returns):
	if not returns:
		return {}
	names = [row["name"] for row in returns]
	placeholders = ", ".join(["%s"] * len(names))
	rows = frappe.db.sql(
		f"""
		SELECT sii.sales_invoice_item, SUM(ABS(sii.qty)) AS qty
		FROM `tabSales Invoice Item` sii
		WHERE sii.parent IN ({placeholders})
			AND sii.sales_invoice_item IS NOT NULL
			AND sii.sales_invoice_item != ''
		GROUP BY sii.sales_invoice_item
		""",
		tuple(names),
		as_dict=True,
	)
	return {row.sales_invoice_item: _flt(row.qty) for row in rows}


def _get_prepared_qty_map(sales_invoice):
	"""Qty sitting in DRAFT warranty Delivery Notes (Ready, not handed over)."""
	if not _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		return {}
	replacement_filter = ""
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		replacement_filter = "AND IFNULL(dn.custom_is_warranty_replacement, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT dni.si_detail AS sales_invoice_item, SUM(dni.qty) AS qty
		FROM `tabDelivery Note Item` dni
		INNER JOIN `tabDelivery Note` dn ON dn.name = dni.parent
		WHERE dn.docstatus = 0
			AND dn.custom_warranty_sales_invoice = %s
			AND dni.si_detail IS NOT NULL
			AND dni.si_detail != ''
			{replacement_filter}
		GROUP BY dni.si_detail
		""",
		sales_invoice,
		as_dict=True,
	)
	return {row.sales_invoice_item: _flt(row.qty) for row in rows}


def _get_completed_qty_map(sales_invoice):
	"""Qty handed over via SUBMITTED warranty Delivery Notes."""
	if not _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		return {}
	replacement_filter = ""
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		replacement_filter = "AND IFNULL(dn.custom_is_warranty_replacement, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT dni.si_detail AS sales_invoice_item, SUM(dni.qty) AS qty
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
	return {row.sales_invoice_item: _flt(row.qty) for row in rows}


def _get_received_qty_map(sales_invoice):
	"""Qty received into condition warehouse via Material Receipt Stock Entries."""
	if not _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		return {}
	se_filter = ""
	if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
		se_filter = "AND IFNULL(se.custom_is_warranty_transfer, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT sed.item_code, SUM(sed.qty) AS qty
		FROM `tabStock Entry Detail` sed
		INNER JOIN `tabStock Entry` se ON se.name = sed.parent
		WHERE se.docstatus = 1
			AND se.purpose = 'Material Receipt'
			AND se.custom_warranty_sales_invoice = %s
			{se_filter}
		GROUP BY sed.item_code
		""",
		sales_invoice,
		as_dict=True,
	)
	return {row.item_code: _flt(row.qty) for row in rows}


def _get_draft_replacement_dn(sales_invoice):
	if not _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		return ""
	replacement_filter = ""
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		replacement_filter = "AND IFNULL(dn.custom_is_warranty_replacement, 0) = 1"

	rows = frappe.db.sql(
		f"""
		SELECT dn.name
		FROM `tabDelivery Note` dn
		WHERE dn.docstatus = 0
			AND dn.custom_warranty_sales_invoice = %s
			{replacement_filter}
		ORDER BY dn.creation DESC
		LIMIT 1
		""",
		sales_invoice,
	)
	return rows[0][0] if rows else ""


@frappe.whitelist()
def get_claim_history(sales_invoice):
	_require_warranty_read()

	status_select = "'' AS warranty_status"
	if _has_status_field():
		status_select = "IFNULL(si.custom_warranty_status, '') AS warranty_status"
	product_condition_select = "'' AS product_condition"
	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		product_condition_select = "IFNULL(si.custom_warranty_product_condition, '') AS product_condition"

	return_rows = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.posting_date,
			{status_select},
			{product_condition_select},
			GROUP_CONCAT(DISTINCT sii.item_code ORDER BY sii.item_code SEPARATOR ', ') AS items,
			SUM(ABS(sii.qty)) AS claimed_qty
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE si.docstatus = 0
			AND si.is_return = 1
			AND si.return_against = %s
			{_warranty_si_filter()}
		GROUP BY si.name, si.posting_date, warranty_status, product_condition
		ORDER BY si.creation DESC
		""",
		sales_invoice,
		as_dict=True,
	)

	delivery_rows = []
	if _has_warranty_field("Delivery Note", "custom_warranty_sales_invoice"):
		replacement_filter = ""
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
			WHERE dn.docstatus < 2
				AND dn.custom_warranty_sales_invoice = %s
				{replacement_filter}
			GROUP BY dn.name, dn.posting_date, dn.docstatus
			ORDER BY dn.creation DESC
			""",
			sales_invoice,
			as_dict=True,
		)

	receipt_rows = []
	if _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		se_filter = ""
		if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
			se_filter = "AND IFNULL(se.custom_is_warranty_transfer, 0) = 1"

		receipt_rows = frappe.db.sql(
			f"""
			SELECT
				se.name,
				se.posting_date,
				se.purpose,
				GROUP_CONCAT(DISTINCT sed.item_code ORDER BY sed.item_code SEPARATOR ', ') AS items,
				SUM(sed.qty) AS qty
			FROM `tabStock Entry` se
			INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
			WHERE se.docstatus = 1
				AND se.custom_warranty_sales_invoice = %s
				{se_filter}
			GROUP BY se.name, se.posting_date, se.purpose
			ORDER BY se.creation DESC
			""",
			sales_invoice,
			as_dict=True,
		)

	history = []
	for row in return_rows:
		status = row.warranty_status or STATUS_REQUESTED
		label, key = _claim_status_label(status)
		history.append(
			{
				"doctype": "Sales Invoice",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.claimed_qty),
				"status": label,
				"status_key": key,
				"detail": row.product_condition or "",
				"type": "Claim",
			}
		)

	for row in receipt_rows:
		history.append(
			{
				"doctype": "Stock Entry",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.qty),
				"status": _("Received"),
				"detail": row.purpose,
				"type": "Receive",
			}
		)

	for row in delivery_rows:
		is_submitted = cint(row.docstatus) == 1
		history.append(
			{
				"doctype": "Delivery Note",
				"reference": row.name,
				"date": row.posting_date,
				"items": row.items,
				"qty": _flt(row.replaced_qty),
				"status": _("Completed") if is_submitted else _("Ready (draft)"),
				"detail": _("Replacement"),
				"type": "Replacement",
			}
		)

	history.sort(key=lambda row: str(row.get("date") or ""), reverse=True)
	return history


def _build_summary(sales_invoice, customer, items, claim_status):
	requested_qty = sum(_flt(row.get("requested_qty")) for row in items)
	prepared_qty = sum(_flt(row.get("prepared_qty")) for row in items)
	completed_qty = sum(_flt(row.get("completed_qty")) for row in items)
	received_qty = sum(_flt(row.get("received_qty")) for row in items)
	pending_qty = sum(max(_flt(row.get("remaining_qty")), 0) for row in items)

	status = claim_status or (STATUS_REQUESTED if requested_qty > 0 else "")

	return {
		"sales_invoice": sales_invoice,
		"customer": customer,
		"requested_qty": requested_qty,
		"received_qty": received_qty,
		"prepared_qty": prepared_qty,
		"completed_qty": completed_qty,
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


# ---------------------------------------------------------------------------
# Step 1 — Request (Salesman): create a draft claim record, no stock movement.
# ---------------------------------------------------------------------------
@frappe.whitelist()
def create_warranty_return(sales_invoice, items):
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
	if _has_status_field():
		return_doc.custom_warranty_status = STATUS_REQUESTED

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


# ---------------------------------------------------------------------------
# Step 2 — Receive (Factory): Material Receipt into the condition warehouse.
# ---------------------------------------------------------------------------
def _build_receipt_items_from_return(return_doc):
	items = []
	for row in return_doc.items:
		qty = abs(_flt(row.qty))
		if qty <= 0:
			continue
		items.append({
			"item_code": row.item_code,
			"qty": qty,
			"uom": row.uom,
			"rate": _flt(row.rate),
			"serial_no": row.serial_no or "",
			"batch_no": row.batch_no or "",
		})
	return items


@frappe.whitelist()
def receive_warranty_claim(
	sales_invoice,
	return_invoice=None,
	condition_warehouse=None,
	product_condition=None,
):
	"""Factory confirms the goods are in hand and books them into the condition warehouse."""
	_require_warranty_settle()
	ignore_permissions = bool(_user_roles().intersection(WARRANTY_SETTLE_ROLES))

	if product_condition not in PRODUCT_CONDITIONS:
		frappe.throw(_("Select a valid product condition."))
	if not condition_warehouse:
		frappe.throw(_("Select the condition warehouse to receive into."))

	invoice_data = load_sales_invoice(sales_invoice)
	if not return_invoice:
		return_invoice = invoice_data.get("pending_return_invoice")
	if not return_invoice:
		frappe.throw(_("No open claim found for this invoice."))

	return_doc = frappe.get_doc("Sales Invoice", return_invoice)
	if return_doc.docstatus != 0:
		frappe.throw(_("Claim record is not editable."))
	if (return_doc.get("custom_warranty_status") or STATUS_REQUESTED) != STATUS_REQUESTED:
		frappe.throw(_("This claim has already been received."))

	receipt_items = _build_receipt_items_from_return(return_doc)
	if not receipt_items:
		frappe.throw(_("Nothing to receive on this claim."))

	create_warranty_material_receipt(
		sales_invoice,
		receipt_items,
		condition_warehouse,
		submit=1,
		ignore_permissions=ignore_permissions,
	)

	if _has_warranty_field("Sales Invoice", "custom_warranty_product_condition"):
		return_doc.custom_warranty_product_condition = product_condition
	if _has_status_field():
		return_doc.custom_warranty_status = STATUS_RECEIVED
	return_doc.flags.ignore_permissions = ignore_permissions
	return_doc.save()

	return {
		"doctype": "Sales Invoice",
		"name": return_doc.name,
		"invoice": load_sales_invoice(sales_invoice),
	}


@frappe.whitelist()
def create_warranty_material_receipt(
	sales_invoice,
	items,
	target_warehouse,
	submit=1,
	ignore_permissions=False,
):
	if not ignore_permissions and not can_warranty_settle():
		frappe.has_permission("Stock Entry", "create", throw=True)

	items = _parse_json(items)
	if not target_warehouse:
		frappe.throw(_("Target warehouse is mandatory."))

	receipt_items = [row for row in items if _flt(row.get("qty")) > 0]
	if not receipt_items:
		frappe.throw(_("Enter quantity for at least one item."))

	si = frappe.get_doc("Sales Invoice", sales_invoice)

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.purpose = "Material Receipt"
	se.company = si.company
	se.posting_date = nowdate()
	if _has_warranty_field("Stock Entry", "custom_warranty_sales_invoice"):
		se.custom_warranty_sales_invoice = sales_invoice
	if _has_warranty_field("Stock Entry", "custom_is_warranty_transfer"):
		se.custom_is_warranty_transfer = 1

	for row in receipt_items:
		item_code = row.get("item_code")
		if not item_code:
			continue
		se.append(
			"items",
			{
				"item_code": item_code,
				"qty": _flt(row.get("qty")),
				"t_warehouse": target_warehouse,
				"uom": row.get("uom") or frappe.db.get_value("Item", item_code, "stock_uom"),
				"conversion_factor": 1,
				"basic_rate": _flt(row.get("rate")),
				"allow_zero_valuation_rate": 1,
				"serial_no": row.get("serial_no") or "",
				"batch_no": row.get("batch_no") or "",
			},
		)

	if not se.items:
		frappe.throw(_("No receipt items could be created."))

	se.flags.ignore_permissions = ignore_permissions
	se.insert(ignore_permissions=ignore_permissions)
	if cint(submit):
		se.submit()

	return {
		"doctype": "Stock Entry",
		"name": se.name,
		"docstatus": se.docstatus,
	}


# ---------------------------------------------------------------------------
# Step 3 — Prepare (Factory): draft the replacement Delivery Note.
# ---------------------------------------------------------------------------
@frappe.whitelist()
def prepare_warranty_replacement(
	sales_invoice,
	return_invoice=None,
	replacement_warehouse=None,
	items=None,
):
	_require_warranty_settle()
	ignore_permissions = bool(_user_roles().intersection(WARRANTY_SETTLE_ROLES))

	if not replacement_warehouse:
		frappe.throw(_("Select the replacement warehouse."))

	invoice_data = load_sales_invoice(sales_invoice)
	if not return_invoice:
		return_invoice = invoice_data.get("pending_return_invoice")
	if not return_invoice:
		frappe.throw(_("No open claim found for this invoice."))

	status = invoice_data.get("claim_status")
	if status not in (STATUS_RECEIVED, STATUS_READY):
		frappe.throw(_("Receive the product into stock before preparing a replacement."))

	items = _parse_json(items)
	replacement_items = [row for row in items if _flt(row.get("replacement_qty")) > 0]
	if not replacement_items:
		frappe.throw(_("Enter replacement quantity for at least one item."))

	result = create_warranty_replacement(
		sales_invoice,
		replacement_items,
		replacement_warehouse,
		submit=0,
		ignore_permissions=ignore_permissions,
	)

	_set_warranty_status(return_invoice, STATUS_READY)

	return {
		"doctype": "Delivery Note",
		"name": result.get("name"),
		"docstatus": result.get("docstatus"),
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
	pending_map = {
		row["sales_invoice_item"]: _flt(row["pending_prepare_qty"]) for row in invoice_data["items"]
	}

	for row in replacement_items:
		si_item = row.get("sales_invoice_item")
		replacement_qty = _flt(row.get("replacement_qty"))
		pending = pending_map.get(si_item, 0)
		if replacement_qty > pending:
			frappe.throw(
				_("Replacement quantity {0} exceeds the claimed quantity still pending ({1}) for item {2}.").format(
					replacement_qty, pending, row.get("item_code") or si_item
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


# ---------------------------------------------------------------------------
# Step 4 — Hand over (Salesman): submit the draft replacement note.
# ---------------------------------------------------------------------------
@frappe.whitelist()
def handover_warranty_replacement(sales_invoice, delivery_note=None, return_invoice=None):
	_require_warranty_handover()
	ignore_permissions = bool(_user_roles().intersection(WARRANTY_CLAIM_ROLES | WARRANTY_SETTLE_ROLES))

	invoice_data = load_sales_invoice(sales_invoice)
	if not delivery_note:
		delivery_note = invoice_data.get("pending_delivery_note")
	if not delivery_note:
		frappe.throw(_("Nothing is ready to hand over for this invoice."))

	dn = frappe.get_doc("Delivery Note", delivery_note)
	if dn.docstatus != 0:
		frappe.throw(_("This replacement has already been handed over."))
	if _has_warranty_field("Delivery Note", "custom_is_warranty_replacement"):
		if not cint(dn.custom_is_warranty_replacement):
			frappe.throw(_("This is not a warranty replacement note."))

	dn.flags.ignore_permissions = ignore_permissions
	dn.submit()

	if not return_invoice:
		return_invoice = invoice_data.get("pending_return_invoice")
	_set_warranty_status(return_invoice, STATUS_COMPLETED)

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
