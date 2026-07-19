import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, nowdate


def sync_sales_invoice_item_running_price(doc, method=None):
	for row in doc.get("items") or []:
		if flt(row.custom_running_price):
			continue
		rate = flt(row.rate)
		if rate:
			row.custom_running_price = rate


def sales_invoice_on_submit(doc, method=None):
	"""
	On Sales Invoice submit:
	1. Update last_purchase_rate on each Item using custom_purchase_price.
	2. Submit a Material Receipt Stock Entry to record the purchase cost
	   at the custom_purchase_price rate — this directly impacts COGS
	   via the Stock Ledger valuation rate.
	3. If custom_expense_amount is set, create a Journal Entry:
	   Debit  5214 - Sales Expenses - SPL
	   Credit 1110 - Cash - SPL

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

	# Re-fetch purchase prices directly from DB to bypass permlevel restrictions
	item_prices = {}
	for row in items_with_price:
		db_price = frappe.db.get_value(
			"Sales Invoice Item",
			row.name,
			"custom_purchase_price",
		)
		if flt(db_price):
			item_prices[row.name] = flt(db_price)

	if not item_prices:
		frappe.msgprint(
			_("No purchase price found on invoice items. Stock Entry skipped."),
			alert=True,
		)
		return

	default_warehouse = frappe.db.get_value(
		"Warehouse",
		{"company": company, "is_group": 0, "disabled": 0},
		"name",
	)

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.company = company
	# Receive the stock one day before the invoice so the valuation rate is in the
	# ledger before the sale consumes it.
	se.posting_date = add_days(doc.posting_date, -1)
	se.set_posting_time = 1
	se.remarks = _("Auto-generated: Valuation update from Sales Invoice {0}").format(doc.name)

	for row in items_with_price:
		purchase_price = item_prices.get(row.name)
		if not purchase_price:
			continue

		target_wh = row.get("warehouse") or default_warehouse
		if not target_wh:
			frappe.throw(
				_("No warehouse found for item {0}. Cannot create Stock Entry.").format(row.item_code),
			)

		se.append("items", {
			"item_code": row.item_code,
			"qty": row.qty,
			"basic_rate": purchase_price,
			"t_warehouse": target_wh,
			"uom": row.uom,
			"conversion_factor": row.conversion_factor or 1,
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

	# --- 3. Journal Entry for sales expense taken as cash ---
	_create_sales_expense_journal(doc)


def customer_assign_to_creator(doc, method=None):
	"""On creation, assign the Customer to whoever created it.

	This sets ``custom_assigned_for`` to the creator so a Salesman who adds a
	customer immediately sees it under their own restricted view. An explicit
	assignment entered on the form is respected and left untouched.
	"""
	if doc.get("custom_assigned_for"):
		return

	creator = doc.owner or frappe.session.user
	doc.db_set("custom_assigned_for", creator, update_modified=False)


def customer_create_opening_entry(doc, method=None):
	"""Create an opening-balance Journal Entry the first time a Customer is
	saved with an Opening Balance.

	The created entry's name is stored on ``custom_opening_entry`` so it is
	never duplicated on later saves. A positive balance is a receivable
	(debit the customer); a negative balance is an advance (credit the customer).
	"""
	opening_balance = flt(doc.get("custom_opening_balance"))
	if not opening_balance:
		return

	# Already created — do not post a second opening entry on re-save.
	if doc.get("custom_opening_entry"):
		return

	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)
	if not company:
		frappe.throw(
			_("Please set a default Company before adding a Customer Opening Balance."),
			title=_("Opening Entry Error"),
		)

	from erpnext.accounts.party import get_party_account
	from erpnext.accounts.doctype.opening_invoice_creation_tool.opening_invoice_creation_tool import (
		get_temporary_opening_account,
	)

	receivable_account = get_party_account("Customer", doc.name, company)
	if not receivable_account:
		frappe.throw(
			_("No receivable account found for Customer {0} in company {1}.").format(doc.name, company),
			title=_("Opening Entry Error"),
		)

	temporary_opening_account = get_temporary_opening_account(company)

	amount = abs(opening_balance)

	party_entry = {
		"account": receivable_account,
		"party_type": "Customer",
		"party": doc.name,
		"debit_in_account_currency": amount if opening_balance > 0 else 0,
		"credit_in_account_currency": 0 if opening_balance > 0 else amount,
	}
	opening_entry = {
		"account": temporary_opening_account,
		"debit_in_account_currency": 0 if opening_balance > 0 else amount,
		"credit_in_account_currency": amount if opening_balance > 0 else 0,
	}

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Opening Entry"
	je.company = company
	je.posting_date = nowdate()
	je.is_opening = "Yes"
	je.remark = _("Opening balance for Customer {0}").format(doc.name)
	je.append("accounts", party_entry)
	je.append("accounts", opening_entry)

	try:
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Opening Journal Entry failed for Customer {0}".format(doc.name),
		)
		frappe.throw(
			_("Could not create opening Journal Entry for Customer {0}: {1}").format(doc.name, str(e)),
			title=_("Opening Entry Error"),
		)

	doc.db_set("custom_opening_entry", je.name, update_modified=False)
	frappe.msgprint(
		_("Opening Journal Entry {0} created for Customer opening balance.").format(je.name),
		alert=True,
	)


def payment_entry_on_submit(doc, method=None):
	charge_amount = flt(doc.get("custom_charge_amount"))
	if not charge_amount:
		return

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = doc.company
	je.posting_date = doc.posting_date
	je.cheque_no = doc.name
	je.cheque_date = doc.posting_date
	je.remark = _("Bank charges for Payment Entry {0}").format(doc.name)

	je.append("accounts", {
		"account": "5221 - Bank Charges - SPL",
		"debit_in_account_currency": charge_amount,
		"credit_in_account_currency": 0,
	})

	je.append("accounts", {
		"account": "1110 - Cash - SPL",
		"debit_in_account_currency": 0,
		"credit_in_account_currency": charge_amount,
	})

	try:
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		frappe.msgprint(
			_("Journal Entry {0} created for bank charges.").format(je.name),
			alert=True,
		)
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Journal Entry failed for Payment Entry {0}".format(doc.name),
		)
		frappe.throw(
			_("Could not create Journal Entry for bank charges: {0}").format(str(e)),
			title=_("Journal Entry Error"),
		)


def _create_sales_expense_journal(doc):
	expense_amount = flt(doc.get("custom_expense_amount"))
	if not expense_amount:
		return

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = doc.company
	je.posting_date = doc.posting_date
	je.cheque_no = doc.name
	je.cheque_date = doc.posting_date
	je.remark = _("Sales expense for Invoice {0}").format(doc.name)

	je.append("accounts", {
		"account": "5214 - Sales Expenses - SPL",
		"debit_in_account_currency": expense_amount,
		"credit_in_account_currency": 0,
		"cost_center": doc.cost_center,
	})

	je.append("accounts", {
		"account": "1110 - Cash - SPL",
		"debit_in_account_currency": 0,
		"credit_in_account_currency": expense_amount,
		"cost_center": doc.cost_center,
	})

	try:
		je.flags.ignore_permissions = True
		je.insert()
		je.submit()
		frappe.msgprint(
			_("Journal Entry {0} created for sales expense.").format(je.name),
			alert=True,
		)
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Journal Entry failed for Sales Invoice {0}".format(doc.name),
		)
		frappe.throw(
			_("Could not create Journal Entry for sales expense: {0}").format(str(e)),
			title=_("Journal Entry Error"),
		)
