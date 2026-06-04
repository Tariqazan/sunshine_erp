from collections import defaultdict
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import cint, fmt_money, formatdate, getdate, now_datetime, today

DEALER_LEDGER_ADMIN_ROLES = frozenset({
	"Administrator",
	"System Manager",
	"System Admin",
})

PDF_MAX_INVOICES = 500
_TEMPLATE_PATH = Path(__file__).parent / "dealer_ledger_pdf.html"


def _can_view_all_sales_users(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	return bool(DEALER_LEDGER_ADMIN_ROLES.intersection(frappe.get_roles(user)))


def _resolve_sales_user_filter(requested_sales_user=None, user=None):
	if not user:
		user = frappe.session.user
	if _can_view_all_sales_users(user):
		return requested_sales_user or None
	if "Salesman" in frappe.get_roles(user):
		return user
	return requested_sales_user or None


@frappe.whitelist()
def get_dealer_ledger_context():
	user = frappe.session.user
	can_filter = _can_view_all_sales_users(user)
	roles = frappe.get_roles(user)
	return {
		"can_filter_sales_user": can_filter,
		"is_salesman": "Salesman" in roles,
		"default_sales_user": user if not can_filter else None,
		"current_user": user,
	}


def _flt(value):
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0.0


def _get_currency():
	return frappe.db.get_default("currency") or frappe.get_cached_value(
		"Global Defaults", "Global Defaults", "default_currency"
	) or "BDT"


def _money(amount):
	return fmt_money(_flt(amount), currency=_get_currency())


def _build_filter_conditions(customer=None, from_date=None, to_date=None, sales_user=None):
	conditions = ["docstatus = 1"]
	values = []

	sales_user = _resolve_sales_user_filter(sales_user)
	if sales_user:
		conditions.append("custom_sales_user = %s")
		values.append(sales_user)
	if customer:
		conditions.append("customer = %s")
		values.append(customer)
	if from_date:
		conditions.append("posting_date >= %s")
		values.append(from_date)
	if to_date:
		conditions.append("posting_date <= %s")
		values.append(to_date)

	return conditions, values, sales_user


def _fetch_dealer_ledger_rows(customer=None, from_date=None, to_date=None, sales_user=None, start=0, limit=None):
	conditions, values, resolved_sales_user = _build_filter_conditions(
		customer, from_date, to_date, sales_user
	)
	where_clause = " AND ".join(conditions)

	count_query = f"SELECT count(*) FROM `tabSales Invoice` WHERE {where_clause}"
	total_count = frappe.db.sql(count_query, tuple(values))[0][0]

	if total_count == 0:
		return [], 0, resolved_sales_user

	inv_query = f"""
		SELECT
			name as invoice_name, posting_date, customer, custom_sales_user,
			custom_transport_name, custom_booking_slip_no, custom_showroom_name,
			custom_owner_name, grand_total
		FROM `tabSales Invoice`
		WHERE {where_clause}
		ORDER BY posting_date DESC, name DESC
	"""
	query_values = list(values)
	if limit is not None:
		inv_query += " LIMIT %s OFFSET %s"
		query_values.extend([cint(limit), cint(start)])

	invoices = frappe.db.sql(inv_query, tuple(query_values), as_dict=True)
	if not invoices:
		return [], total_count, resolved_sales_user

	invoice_names = [inv.invoice_name for inv in invoices]

	items = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": ["in", invoice_names]},
		fields=[
			"parent", "item_code", "item_name", "qty", "rate", "amount",
			"custom_running_price", "custom_commission_amount",
			"custom_purchase_price", "idx",
		],
		order_by="parent asc, idx asc",
	)

	items_by_inv = defaultdict(list)
	for item in items:
		items_by_inv[item.parent].append(item)

	pay_refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"reference_doctype": "Sales Invoice",
			"reference_name": ["in", invoice_names],
			"docstatus": 1,
		},
		fields=["parent", "reference_name", "allocated_amount"],
		order_by="reference_name asc, parent asc",
	)

	pe_names = list({r.parent for r in pay_refs})
	pe_map = {}
	pe_bank_charge = defaultdict(float)
	pe_total_alloc = defaultdict(float)

	if pe_names:
		payment_entries = frappe.get_all(
			"Payment Entry",
			filters={"name": ["in", pe_names], "docstatus": 1},
			fields=["name", "reference_no", "paid_amount", "mode_of_payment", "bank_account", "party_name"],
		)
		pe_map = {d.name: d for d in payment_entries}

		charge_rows = frappe.db.sql(
			"""
			SELECT parent, COALESCE(SUM(tax_amount), 0) AS bank_charge
			FROM `tabAdvance Taxes and Charges`
			WHERE parent IN %s
			GROUP BY parent
			""",
			(tuple(pe_names),),
			as_dict=True,
		)
		for r in charge_rows:
			pe_bank_charge[r.parent] = _flt(r.bank_charge)

		alloc_rows = frappe.db.sql(
			"""
			SELECT parent, COALESCE(SUM(allocated_amount), 0) AS total_alloc
			FROM `tabPayment Entry Reference`
			WHERE parent IN %s
			GROUP BY parent
			""",
			(tuple(pe_names),),
			as_dict=True,
		)
		for r in alloc_rows:
			pe_total_alloc[r.parent] = _flt(r.total_alloc)

	payments_by_inv = defaultdict(list)
	for ref in pay_refs:
		pe = pe_map.get(ref.parent)
		if not pe:
			continue

		allocated = _flt(ref.allocated_amount)
		total_alloc = pe_total_alloc.get(ref.parent) or 0
		pe_charge = pe_bank_charge.get(ref.parent) or 0
		bank_charge = pe_charge * (allocated / total_alloc) if total_alloc > 0 else 0

		payments_by_inv[ref.reference_name].append({
			"payment_name": pe.name,
			"deposit_slip_no": pe.reference_no,
			"bank_name": pe.mode_of_payment,
			"deposit_account_name": pe.party_name,
			"deposit_amount": allocated,
			"bank_charge": bank_charge,
			"net_deposit": allocated - bank_charge,
		})

	rows = []
	serial = cint(start) + 1

	for inv in invoices:
		inv_items = items_by_inv.get(inv.invoice_name, [])
		inv_payments = payments_by_inv.get(inv.invoice_name, [])

		total_qty = sum(_flt(i.qty) for i in inv_items)
		total_selling_price = sum(_flt(i.amount) for i in inv_items)
		total_commission = sum(_flt(i.custom_commission_amount) for i in inv_items)
		total_purchase_price = sum(
			_flt(i.qty) * _flt(i.custom_purchase_price)
			for i in inv_items
			if i.custom_purchase_price
		)

		total_deposit = sum(_flt(p["deposit_amount"]) for p in inv_payments)
		total_charge = sum(_flt(p["bank_charge"]) for p in inv_payments)
		total_net_deposit = sum(_flt(p["net_deposit"]) for p in inv_payments)
		balance_tk = total_selling_price - total_net_deposit

		deposit_slips = sorted({p["deposit_slip_no"] for p in inv_payments if p["deposit_slip_no"]})
		bank_names = sorted({p["bank_name"] for p in inv_payments if p["bank_name"]})
		deposit_accounts = sorted({
			p["deposit_account_name"] for p in inv_payments if p["deposit_account_name"]
		})

		booking_deposit_slip_no = inv.custom_booking_slip_no or ", ".join(deposit_slips)

		row = {
			"entry_sl": serial,
			"invoice_name": inv.invoice_name,
			"date": inv.posting_date,
			"date_display": formatdate(inv.posting_date),
			"sales_user": inv.custom_sales_user or "",
			"transport_name": inv.custom_transport_name or "",
			"booking_deposit_slip_no": booking_deposit_slip_no,
			"customer": inv.customer,
			"showroom_name": inv.custom_showroom_name or "",
			"owner_name": inv.custom_owner_name or "",
			"total_qty": total_qty,
			"total_selling_price": total_selling_price,
			"total_purchase_price": total_purchase_price,
			"total_commission": total_commission,
			"deposit_slip_no": ", ".join(deposit_slips),
			"bank_name": ", ".join(bank_names),
			"deposit_account_name": ", ".join(deposit_accounts),
			"deposit_amount": total_deposit,
			"bank_charge": total_charge,
			"net_deposit": total_net_deposit,
			"balance_tk": balance_tk,
			"total_selling_price_display": _money(total_selling_price),
			"total_purchase_price_display": _money(total_purchase_price) if total_purchase_price else "—",
			"total_commission_display": _money(total_commission),
			"deposit_amount_display": _money(total_deposit),
			"bank_charge_display": _money(total_charge),
			"net_deposit_display": _money(total_net_deposit),
			"balance_tk_display": _money(balance_tk),
			"items": [],
			"payments": [_format_payment_for_pdf(p) for p in inv_payments],
		}

		for i in inv_items:
			regular_price = _flt(i.rate)
			running_price = _flt(i.custom_running_price) or regular_price
			row["items"].append({
				"item_code": i.item_code,
				"item_name": i.item_name or i.item_code,
				"qty": _flt(i.qty),
				"regular_price": regular_price,
				"running_price": running_price,
				"purchase_price": _flt(i.custom_purchase_price),
				"amount": _flt(i.amount),
				"commission_amount": _flt(i.custom_commission_amount),
				"regular_price_display": _money(regular_price),
				"running_price_display": _money(running_price),
				"amount_display": _money(i.amount),
				"commission_amount_display": _money(i.custom_commission_amount),
			})

		rows.append(row)
		serial += 1

	return rows, total_count, resolved_sales_user


def _format_payment_for_pdf(payment):
	return {
		**payment,
		"deposit_amount_display": _money(payment.get("deposit_amount")),
		"bank_charge_display": _money(payment.get("bank_charge")),
		"net_deposit_display": _money(payment.get("net_deposit")),
	}


def _summarize_rows(rows):
	totals = {"sales": 0, "commission": 0, "deposit": 0, "charge": 0, "net_deposit": 0, "balance": 0}
	for row in rows:
		totals["sales"] += _flt(row.get("total_selling_price"))
		totals["commission"] += _flt(row.get("total_commission"))
		totals["deposit"] += _flt(row.get("deposit_amount"))
		totals["charge"] += _flt(row.get("bank_charge"))
		totals["net_deposit"] += _flt(row.get("net_deposit"))
		totals["balance"] += _flt(row.get("balance_tk"))
	return {key: _money(val) for key, val in totals.items()}


def _generate_dealer_ledger_pdf(html: str) -> bytes:
	"""Build PDF via WeasyPrint (does not require wkhtmltopdf)."""
	from frappe.utils.weasyprint import import_weasyprint

	HTML, CSS = import_weasyprint()
	base_url = frappe.utils.get_url()
	stylesheet = CSS(
		string="""
		@page {
			size: A4;
			margin: 14mm 12mm 16mm;
		}
		"""
	)

	try:
		return HTML(string=html, base_url=base_url).write_pdf(stylesheets=[stylesheet])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Dealer Ledger PDF Generation Failed")
		frappe.throw(
			_(
				"Could not generate PDF. Install WeasyPrint system dependencies "
				"(see https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) "
				"or install wkhtmltopdf on the server."
			),
			title=_("PDF Generation Error"),
		)


def _filter_labels(customer=None, from_date=None, to_date=None, sales_user=None):
	return {
		"customer_label": customer or _("All Dealers"),
		"sales_user_label": sales_user or _("All Sales Users"),
		"from_date_label": formatdate(from_date) if from_date else _("Any"),
		"to_date_label": formatdate(to_date) if to_date else _("Any"),
	}


@frappe.whitelist()
def get_dealer_ledger(
	customer=None,
	from_date=None,
	to_date=None,
	sales_user=None,
	start=0,
	limit=20,
):
	rows, total_count, _resolved = _fetch_dealer_ledger_rows(
		customer=customer,
		from_date=from_date,
		to_date=to_date,
		sales_user=sales_user,
		start=start,
		limit=limit,
	)
	return {"data": rows, "total_count": total_count}


@frappe.whitelist()
def download_dealer_ledger_pdf(
	customer=None,
	from_date=None,
	to_date=None,
	sales_user=None,
):
	frappe.has_permission("Sales Invoice", "read", throw=True)

	rows, total_count, resolved_sales_user = _fetch_dealer_ledger_rows(
		customer=customer,
		from_date=from_date,
		to_date=to_date,
		sales_user=sales_user,
		start=0,
		limit=PDF_MAX_INVOICES,
	)

	if total_count > PDF_MAX_INVOICES:
		frappe.throw(
			_("Too many invoices ({0}) for PDF. Narrow your filters (max {1}).").format(
				total_count, PDF_MAX_INVOICES
			),
			title=_("PDF Limit Exceeded"),
		)

	company = frappe.db.get_default("company") or frappe.get_all("Company", limit=1, pluck="name")[0]
	context = {
		"title": _("Dealer / Customer Ledger"),
		"company": company,
		"generated_on": frappe.format_value(now_datetime(), {"fieldtype": "Datetime"}),
		"generated_by": frappe.session.user,
		"filters": _filter_labels(customer, from_date, to_date, resolved_sales_user),
		"totals": _summarize_rows(rows),
		"rows": rows,
		"footer_note": _("Sunshine Power Ltd — Dealer Ledger Report"),
	}

	with open(_TEMPLATE_PATH) as template_file:
		html = frappe.render_template(template_file.read(), context)

	pdf = _generate_dealer_ledger_pdf(html)

	filename = f"Dealer_Ledger_{getdate(today())}.pdf"
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"
	frappe.local.response.display_content_as = "inline"
