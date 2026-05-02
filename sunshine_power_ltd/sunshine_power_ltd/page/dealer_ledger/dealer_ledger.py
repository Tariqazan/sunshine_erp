import frappe
from collections import defaultdict

def _flt(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0

@frappe.whitelist()
def get_dealer_ledger(customer=None, from_date=None, to_date=None, start=0, limit=20):
    start = frappe.utils.cint(start)
    limit = frappe.utils.cint(limit)

    conditions = ["docstatus = 1"]
    values = []
    
    if customer:
        conditions.append("customer = %s")
        values.append(customer)
    if from_date:
        conditions.append("posting_date >= %s")
        values.append(from_date)
    if to_date:
        conditions.append("posting_date <= %s")
        values.append(to_date)

    where_clause = " AND ".join(conditions)

    count_query = f"SELECT count(*) FROM `tabSales Invoice` WHERE {where_clause}"
    total_count = frappe.db.sql(count_query, tuple(values))[0][0]

    if total_count == 0:
        return {"data": [], "total_count": 0}

    inv_query = f"""
        SELECT 
            name as invoice_name, posting_date, customer, custom_transport_name, 
            custom_booking_slip_no, custom_showroom_name, custom_owner_name, grand_total
        FROM `tabSales Invoice`
        WHERE {where_clause}
        ORDER BY posting_date DESC, name DESC
        LIMIT %s OFFSET %s
    """
    invoices = frappe.db.sql(inv_query, tuple(values + [limit, start]), as_dict=True)
    
    invoice_names = [inv.invoice_name for inv in invoices]

    items = frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": ["in", invoice_names]},
        fields=[
            "parent", "item_code", "item_name", "qty", "rate", "amount",
            "custom_running_price", "custom_commission_amount",
            "custom_purchase_price", "idx"
        ],
        order_by="parent asc, idx asc",
    )
    
    items_by_inv = defaultdict(list)
    for item in items:
        items_by_inv[item.parent].append(item)

    pay_refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_doctype": "Sales Invoice", "reference_name": ["in", invoice_names], "docstatus": 1},
        fields=["parent", "reference_name", "allocated_amount"],
        order_by="reference_name asc, parent asc"
    )
    
    pe_names = list(set(r.parent for r in pay_refs))
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

        charge_rows = frappe.db.sql("""
            SELECT parent, COALESCE(SUM(tax_amount), 0) AS bank_charge
            FROM `tabAdvance Taxes and Charges`
            WHERE parent IN %s
            GROUP BY parent
        """, (tuple(pe_names),), as_dict=True)
        for r in charge_rows:
            pe_bank_charge[r.parent] = _flt(r.bank_charge)
            
        alloc_rows = frappe.db.sql("""
            SELECT parent, COALESCE(SUM(allocated_amount), 0) AS total_alloc
            FROM `tabPayment Entry Reference`
            WHERE parent IN %s
            GROUP BY parent
        """, (tuple(pe_names),), as_dict=True)
        for r in alloc_rows:
            pe_total_alloc[r.parent] = _flt(r.total_alloc)

    payments_by_inv = defaultdict(list)
    for ref in pay_refs:
        pe = pe_map.get(ref.parent)
        if not pe: continue
        
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
            "net_deposit": allocated - bank_charge
        })

    rows = []
    serial = start + 1
    
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
        
        deposit_slips = sorted(list(set(p["deposit_slip_no"] for p in inv_payments if p["deposit_slip_no"])))
        bank_names = sorted(list(set(p["bank_name"] for p in inv_payments if p["bank_name"])))
        deposit_accounts = sorted(list(set(p["deposit_account_name"] for p in inv_payments if p["deposit_account_name"])))
        
        booking_deposit_slip_no = inv.custom_booking_slip_no or ", ".join(deposit_slips)
        
        row = {
            "entry_sl": serial,
            "invoice_name": inv.invoice_name,
            "date": inv.posting_date,
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
            
            "items": [],
            "payments": inv_payments
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
                "commission_amount": _flt(i.custom_commission_amount)
            })
            
        rows.append(row)
        serial += 1

    return {
        "data": rows,
        "total_count": total_count
    }
