import frappe
from frappe import _

SALES_INVOICE_PRIVILEGED_ROLES = frozenset({
	"Administrator",
	"System Manager",
})


def _is_privileged(user: str) -> bool:
	if user == "Administrator":
		return True
	return bool(SALES_INVOICE_PRIVILEGED_ROLES.intersection(frappe.get_roles(user)))


def can_submit_sales_invoice(user: str | None = None) -> bool:
	if not user:
		user = frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


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
			_("Only System Manager and Administrator can submit Sales Invoices."),
			frappe.PermissionError,
		)


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
