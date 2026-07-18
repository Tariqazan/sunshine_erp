import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Link warranty replacement Delivery Notes and receipt Stock Entries to the
	specific claim (return Sales Invoice) so per-cycle quantities don't leak
	across repeated warranty claims on the same original invoice."""
	create_custom_fields(
		{
			"Delivery Note": [
				{
					"fieldname": "custom_warranty_return_invoice",
					"label": "Warranty Return Invoice",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "custom_is_warranty_replacement",
					"read_only": 1,
				},
			],
			"Stock Entry": [
				{
					"fieldname": "custom_warranty_return_invoice",
					"label": "Warranty Return Invoice",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "custom_is_warranty_transfer",
					"read_only": 1,
				},
			],
		}
	)
	frappe.clear_cache(doctype="Delivery Note")
	frappe.clear_cache(doctype="Stock Entry")
