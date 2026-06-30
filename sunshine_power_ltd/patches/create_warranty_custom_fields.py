import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_is_warranty_claim",
					"label": "Is Warranty Claim",
					"fieldtype": "Check",
					"insert_after": "is_return",
					"default": "0",
				},
				{
					"fieldname": "custom_warranty_product_condition",
					"label": "Warranty Product Condition",
					"fieldtype": "Select",
					"options": "Damaged\nSellable\nRepairable",
					"insert_after": "custom_is_warranty_claim",
					"depends_on": "eval:doc.custom_is_warranty_claim==1",
				},
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
			"Delivery Note": [
				{
					"fieldname": "custom_warranty_sales_invoice",
					"label": "Warranty Sales Invoice",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "customer",
				},
				{
					"fieldname": "custom_is_warranty_replacement",
					"label": "Is Warranty Replacement",
					"fieldtype": "Check",
					"insert_after": "custom_warranty_sales_invoice",
					"default": "0",
				},
			],
			"Stock Entry": [
				{
					"fieldname": "custom_warranty_sales_invoice",
					"label": "Warranty Sales Invoice",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "company",
				},
				{
					"fieldname": "custom_is_warranty_transfer",
					"label": "Is Warranty Transfer",
					"fieldtype": "Check",
					"insert_after": "custom_warranty_sales_invoice",
					"default": "0",
				},
			],
		}
	)
	frappe.clear_cache(doctype="Sales Invoice")
	frappe.clear_cache(doctype="Delivery Note")
	frappe.clear_cache(doctype="Stock Entry")
