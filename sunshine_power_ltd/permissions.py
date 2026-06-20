import frappe
from frappe import _

SALES_INVOICE_PRIVILEGED_ROLES = frozenset({
	"Administrator",
	"System Manager",
	"System Admin",
	"Accounts",
	"Head Office",
})

SALES_INVOICE_SUBMIT_ROLES = frozenset({
	"Administrator",
	"System Manager",
	"System Admin",
	"Accounts",
})

JOURNAL_ENTRY_ADMIN_ROLES = frozenset({
	"Administrator",
	"System Manager",
	"System Admin",
})

JOURNAL_ENTRY_RESTRICTED_PTYPES = frozenset({
	"create",
	"write",
	"submit",
	"cancel",
	"amend",
	"delete",
})

PAYMENT_ENTRY_SUBMIT_ROLES = frozenset({
	"System Admin",
	"Accounts",
	"Head Office",
})

# Salesman (salesperson): create/save drafts only — no submit/cancel/amend.
PAYMENT_ENTRY_DRAFT_ROLES = frozenset({
	"Salesman",
})

PAYMENT_ENTRY_DRAFT_DENIED_PTYPES = frozenset({
	"submit",
	"cancel",
	"amend",
})

ACCOUNTING_RESTRICTED_PTYPES = JOURNAL_ENTRY_RESTRICTED_PTYPES


def _is_privileged(user: str) -> bool:
	if user == "Administrator":
		return True
	return bool(SALES_INVOICE_PRIVILEGED_ROLES.intersection(frappe.get_roles(user)))


def can_submit_sales_invoice(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	return bool(SALES_INVOICE_SUBMIT_ROLES.intersection(frappe.get_roles(user)))


def is_sales_invoice_restricted(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	return not _is_privileged(user)


def get_sales_invoice_permission_query_conditions(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if not is_sales_invoice_restricted(user):
		return ""

	return f"`tabSales Invoice`.custom_sales_user = {frappe.db.escape(user)}"


def _is_new_sales_invoice(doc) -> bool:
	if doc.get("__islocal"):
		return True
	if hasattr(doc, "is_new") and doc.is_new():
		return True
	name = doc.name or ""
	return name.startswith("new-sales-invoice")


def has_sales_invoice_permission(doc, ptype: str | None = None, user: str | None = None, debug=False):
	if not user:
		user = frappe.session.user

	if ptype == "submit" and not can_submit_sales_invoice(user):
		return False

	if not is_sales_invoice_restricted(user):
		return True

	if ptype == "create":
		return True

	if not doc:
		return True

	# Unsaved invoice (e.g. new-sales-invoice-*) — allow adding items and saving draft
	if _is_new_sales_invoice(doc):
		return True

	sales_user = doc.get("custom_sales_user")

	# Draft saved before custom_sales_user is set — allow creator
	if doc.docstatus == 0 and not sales_user:
		return (doc.get("owner") or user) == user

	return sales_user == user


def before_submit_sales_invoice(doc, method=None):
	if not can_submit_sales_invoice():
		frappe.throw(
			_(
				"Only System Manager, System Admin, Accounts, or Administrator can submit Sales Invoices."
			),
			frappe.PermissionError,
		)


def can_manage_journal_entry(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	return bool(JOURNAL_ENTRY_ADMIN_ROLES.intersection(frappe.get_roles(user)))


def has_journal_entry_permission(doc, ptype: str | None = None, user: str | None = None, debug=False):
	if not user:
		user = frappe.session.user

	if can_manage_journal_entry(user):
		return True

	if ptype in JOURNAL_ENTRY_RESTRICTED_PTYPES:
		return False

	return True


def _journal_entry_permission_error():
	frappe.throw(
		_("Only System Administrator can create, save, or submit Journal Entries."),
		frappe.PermissionError,
	)


def validate_journal_entry_admin(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return
	if not can_manage_journal_entry():
		_journal_entry_permission_error()


def before_submit_journal_entry_admin(doc, method=None):
	if not can_manage_journal_entry():
		_journal_entry_permission_error()


def can_submit_payment_entry(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	return bool(PAYMENT_ENTRY_SUBMIT_ROLES.intersection(frappe.get_roles(user)))


def can_manage_payment_entry(user: str | None = None) -> bool:
	return can_submit_payment_entry(user)


def is_payment_entry_draft_only_user(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	if can_manage_payment_entry(user):
		return False
	return bool(PAYMENT_ENTRY_DRAFT_ROLES.intersection(frappe.get_roles(user)))


def has_payment_entry_permission(doc, ptype: str | None = None, user: str | None = None, debug=False):
	if not user:
		user = frappe.session.user

	if can_manage_payment_entry(user):
		return True

	if is_payment_entry_draft_only_user(user):
		if ptype == "submit" or ptype in PAYMENT_ENTRY_DRAFT_DENIED_PTYPES:
			return False
		if ptype == "delete":
			if doc and doc.docstatus == 0 and (doc.get("owner") or user) == user:
				return True
			return False
		if ptype in ("create", "write"):
			if doc and doc.docstatus != 0:
				return False
			return True
		return True

	if ptype in ACCOUNTING_RESTRICTED_PTYPES:
		return False

	return True


def _payment_entry_permission_error():
	frappe.throw(
		_("Only Accounts or System Admin can create, save, or submit Payment Entries."),
		frappe.PermissionError,
	)


def _payment_entry_draft_only_error():
	frappe.throw(
		_("Sales users can only save Payment Entries as draft. Accounts or System Admin must submit."),
		frappe.PermissionError,
	)


def validate_payment_entry_accountant(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return
	if can_manage_payment_entry():
		return
	if is_payment_entry_draft_only_user() and doc.docstatus == 0:
		return
	if is_payment_entry_draft_only_user():
		_payment_entry_draft_only_error()
	_payment_entry_permission_error()


def before_submit_payment_entry_accountant(doc, method=None):
	if not can_submit_payment_entry():
		if is_payment_entry_draft_only_user():
			_payment_entry_draft_only_error()
		_payment_entry_permission_error()


def validate_sales_invoice_sales_user(doc, method=None):
	"""Keep custom_sales_user aligned with the logged-in restricted user."""
	if not is_sales_invoice_restricted():
		return

	user = frappe.session.user

	if doc.is_new() and not doc.get("custom_sales_user"):
		doc.custom_sales_user = user
		return

	if doc.get("custom_sales_user") and doc.custom_sales_user != user:
		frappe.throw(
			_("You can only work on Sales Invoices assigned to you as Sales User."),
			frappe.PermissionError,
		)
