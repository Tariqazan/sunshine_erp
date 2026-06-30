import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add the warranty status field that drives the 4-step claim flow.

	The original create_warranty_custom_fields patch already ran on existing
	sites, so the status field is added here separately. create_custom_fields
	is idempotent, so re-running is safe.
	"""
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_warranty_status",
					"label": "Warranty Status",
					"fieldtype": "Select",
					"options": "\nRequested\nReceived\nReady\nCompleted",
					"insert_after": "custom_warranty_product_condition",
					"depends_on": "eval:doc.custom_is_warranty_claim==1",
					"read_only": 1,
				},
			],
		}
	)
	frappe.clear_cache(doctype="Sales Invoice")
