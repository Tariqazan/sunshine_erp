frappe.pages["dealer-ledger"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Customer / Dealer Ledger",
		single_column: true,
	});

	let current_page = 1;
	const page_size = 20;
	let total_count = 0;

	if (!document.getElementById("dl-style-v2")) {
		$("#dl-style, #dl-style-v2").remove();
		$("head").append(`<style id="dl-style-v2">
/* ── wrapper ── */
.dl-wrap {
	padding: 10px 0 24px;
	position: relative;
}

/* ── filter card (above sticky table header & link dropdowns) ── */
.dl-filter-card {
	position: relative;
	z-index: 100;
	overflow: visible;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	padding: 16px 18px 12px;
	box-shadow: 0 1px 4px rgba(0,0,0,.06);
	margin-bottom: 14px;
}
.dl-filter-card .frappe-control {
	position: relative;
	z-index: 1;
	overflow: visible;
}
.dl-filter-card .link-field,
.dl-filter-card .awesomplete {
	position: relative;
	z-index: 2;
	overflow: visible;
}
.dl-filter-card .awesomplete > ul {
	z-index: 200 !important;
}
.dl-filter-sales-note {
	position: relative;
	z-index: 99;
}
.dl-filter-title {
	font-size: 11px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: .6px;
	color: #64748b;
	margin-bottom: 12px;
}
.dl-filter-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
.dl-filter-field { flex: 1 1 180px; min-width: 150px; }
.dl-filter-actions { display: flex; gap: 8px; padding-bottom: 2px; flex-wrap: wrap; }
.dl-btn-pdf { font-weight: 600; }
.dl-sales-user-note {
	font-size: 12px;
	color: #475569;
	margin: -4px 0 10px;
	padding: 8px 10px;
	background: #f8fafc;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
}

/* ── summary cards ── */
.dl-summary-row {
	position: relative;
	z-index: 90;
	display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px;
}
.dl-scard {
	flex: 1 1 140px;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 10px;
	padding: 12px 14px;
	box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.dl-scard.accent { border-color: #2563eb; background: #eff6ff; }
.dl-scard-lbl { font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: .4px; margin-bottom: 4px; }
.dl-scard-val { font-size: 16px; font-weight: 700; color: #111827; }
.dl-scard.accent .dl-scard-val { color: #1d4ed8; }

/* ── table container ── */
.dl-table-card {
	position: relative;
	z-index: 1;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	padding: 0;
	box-shadow: 0 1px 4px rgba(0,0,0,.06);
	overflow: hidden;
}
.dl-table-scroll {
	overflow-x: auto;
	overflow-y: auto;
	max-height: calc(100vh - 230px);
	min-height: 120px;
	isolation: isolate;
}
/* The actual table */
.dl-tbl {
	width: 100%;
	border-collapse: collapse;
	font-size: 12px;
	table-layout: auto;
}
.dl-tbl thead th {
	position: sticky;
	background: #f1f5f9;
	color: #374151;
	font-weight: 700;
	font-size: 11px;
	text-transform: uppercase;
	letter-spacing: .4px;
	padding: 12px 14px;
	border-bottom: 2px solid #cbd5e1;
	white-space: nowrap;
	text-align: left;
}
.dl-tbl thead th.num { text-align: right; }
/* group header row scrolls away; column headers stay sticky */
.dl-tbl thead tr.dl-group-row th {
	position: static;
	z-index: auto;
	background: #e2e8f0;
	font-size: 10px;
	color: #64748b;
	padding: 5px 12px;
	text-align: center;
	border-bottom: 1px solid #cbd5e1;
	letter-spacing: .5px;
}
.dl-tbl thead tr:not(.dl-group-row) th {
	top: 0;
	z-index: 2;
}

/* body cells — word wrap, no truncate */
.dl-tbl tbody td {
	padding: 12px 14px;
	border-bottom: 1px solid #f1f5f9;
	color: #1f2937;
	word-break: break-word;
	white-space: normal;
	vertical-align: top;
}
.dl-tbl tbody td.num { text-align: right; font-variant-numeric: tabular-nums; }
.dl-tbl tbody tr.parent-row { cursor: pointer; transition: background 0.2s; }
.dl-tbl tbody tr.parent-row:hover { background: #f8fafc; }

/* collapsible child row */
.dl-tbl tbody tr.child-row .child-container {
	padding: 16px 20px 24px 54px;
	background: #f8fafc;
	border-bottom: 2px solid #cbd5e1;
	box-shadow: inset 0 3px 6px -3px rgba(0,0,0,.05);
}

.dl-child-grid {
	display: flex;
	flex-direction: column;
	gap: 16px;
	max-width: 100%;
}
@media (min-width: 992px) {
	.dl-child-grid {
		flex-direction: row;
		align-items: flex-start;
	}
}

/* nested tables */
.nested-table-wrapper {
	flex: 1;
	min-width: 0; /* Prevents flex item from overflowing */
	max-width: 700px;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	overflow: hidden;
	box-shadow: 0 4px 6px -1px rgba(0,0,0,.05);
}
.nested-title {
	background: #fff;
	padding: 10px 14px;
	font-size: 11px;
	font-weight: 700;
	text-transform: uppercase;
	color: #334155;
	border-bottom: 1px solid #e2e8f0;
}
.nested-table-container {
	overflow-x: auto;
	width: 100%;
}
.nested-table {
	width: 100%;
	border-collapse: collapse;
	font-size: 11px;
}
.nested-table th { 
	background: #f8fafc; 
	font-weight: 600; 
	text-align: left; 
	padding: 10px 14px; 
	border-bottom: 1px solid #e2e8f0; 
	white-space: nowrap;
}
.nested-table th.num { text-align: right; }
.nested-table td { 
	padding: 10px 14px; 
	border-bottom: 1px solid #f1f5f9; 
	vertical-align: middle; 
	word-break: break-word; 
}
.nested-table td.num { text-align: right; }

.nested-table th:first-child, .nested-table td:first-child { padding-left: 24px; }
.nested-table th:last-child, .nested-table td:last-child { padding-right: 24px; }

.dl-tbl .col-sl { width: 44px; text-align: center; color: #9ca3af; white-space: nowrap; }

/* alignment utilities */
.text-left { text-align: left !important; }
.text-center { text-align: center !important; }
.text-right { text-align: right !important; }

/* ── Pagination controls ── */
.dl-pagination {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 12px 18px;
	background: #f8fafc;
	border-top: 1px solid #e2e8f0;
	font-size: 12px;
}
.dl-page-info { color: #64748b; font-weight: 500; }
.dl-page-btns { display: flex; gap: 6px; }

/* ── empty / loading ── */
.dl-empty {
	text-align: center;
	padding: 52px 0;
	color: #9ca3af;
}
.dl-empty i { font-size: 40px; display: block; margin-bottom: 12px; }
.dl-empty p { font-size: 13px; margin: 0; }
</style>`);
	}

	const $w = $(`<div class="dl-wrap">
		<div class="dl-filter-card">
			<div class="dl-filter-title">Dealer Ledger — Filters</div>
			<div class="dl-filter-sales-note" style="display:none;"></div>
			<div class="dl-filter-row">
				<div class="dl-filter-field dl-f-sales-user" style="display:none;"></div>
				<div class="dl-filter-field dl-f-customer"></div>
				<div class="dl-filter-field dl-f-from"></div>
				<div class="dl-filter-field dl-f-to"></div>
				<div class="dl-filter-actions">
					<button class="btn btn-primary btn-sm dl-btn-pdf" title="Download filtered ledger as PDF">
						<i class="fa fa-file-pdf-o"></i> Download PDF
					</button>
					<button class="btn btn-default btn-sm dl-btn-reset">Reset Filters</button>
				</div>
			</div>
		</div>

		<div class="dl-summary-row"></div>

		<div class="dl-table-card">
			<div class="dl-table-scroll">
				<div class="dl-empty">
					<i class="fa fa-spinner fa-spin"></i>
					<p>Loading...</p>
				</div>
			</div>
			<div class="dl-pagination">
				<div class="dl-page-info">Showing 0 to 0 of 0</div>
				<div class="dl-page-btns">
					<button class="btn btn-default btn-sm dl-btn-prev" disabled>Previous</button>
					<button class="btn btn-default btn-sm dl-btn-next" disabled>Next</button>
				</div>
			</div>
		</div>
	</div>`);

	page.main.append($w);

	let reload_timeout = null;
	const trigger_reload = () => {
		clearTimeout(reload_timeout);
		reload_timeout = setTimeout(() => {
			current_page = 1;
			load_report();
		}, 300);
	};

	let page_context = {
		can_filter_sales_user: false,
		is_salesman: false,
		current_user: frappe.session.user,
	};

	const f_sales_user = frappe.ui.form.make_control({
		parent: $w.find(".dl-f-sales-user"),
		df: {
			fieldname: "sales_user",
			label: "Sales User",
			fieldtype: "Link",
			options: "User",
			placeholder: "All Sales Users",
			onchange: trigger_reload,
		},
		render_input: true,
	});

	const f_customer = frappe.ui.form.make_control({
		parent: $w.find(".dl-f-customer"),
		df: { 
			fieldname: "customer", label: "Dealer / Customer", fieldtype: "Link", options: "Customer", placeholder: "All Dealers",
			onchange: trigger_reload
		},
		render_input: true,
	});
	const f_from = frappe.ui.form.make_control({
		parent: $w.find(".dl-f-from"),
		df: { 
			fieldname: "from_date", label: "From Date", fieldtype: "Date",
			onchange: trigger_reload
		},
		render_input: true,
	});
	const f_to = frappe.ui.form.make_control({
		parent: $w.find(".dl-f-to"),
		df: { 
			fieldname: "to_date", label: "To Date", fieldtype: "Date",
			onchange: trigger_reload
		},
		render_input: true,
	});

	function fmt_cur(val) {
		const cur = frappe.defaults.get_user_default("currency") || (frappe.boot.sysdefaults || {}).currency || "BDT";
		return format_currency(val || 0, cur);
	}
	function esc(v) { return frappe.utils.escape_html(String(v ?? "")); }

	function render_summary(rows) {
		const T = (rows || []).reduce(
			(a, r) => {
				a.sales   += r.total_selling_price || 0;
				a.comm    += r.total_commission    || 0;
				a.dep     += r.deposit_amount      || 0;
				a.charge  += r.bank_charge         || 0;
				a.net     += r.net_deposit         || 0;
				a.bal     += r.balance_tk          || 0;
				return a;
			},
			{ sales: 0, comm: 0, dep: 0, charge: 0, net: 0, bal: 0 }
		);

		const cards = [
			{ lbl: "Total Sales",    val: fmt_cur(T.sales) },
			{ lbl: "Total Comm.",    val: fmt_cur(T.comm) },
			{ lbl: "Total Deposit",  val: fmt_cur(T.dep) },
			{ lbl: "Bank Charge",    val: fmt_cur(T.charge) },
			{ lbl: "Net Deposit",    val: fmt_cur(T.net) },
			{ lbl: "Balance TK",     val: fmt_cur(T.bal) },
		];

		$w.find(".dl-summary-row").html(
			cards.map(c => `
				<div class="dl-scard${c.accent ? " accent" : ""}">
					<div class="dl-scard-lbl">${esc(c.lbl)}</div>
					<div class="dl-scard-val">${esc(c.val)}</div>
				</div>`
			).join("")
		);
	}

	function render_table(rows) {
		const $scroll = $w.find(".dl-table-scroll");
		$scroll.empty();

		if (!rows || !rows.length) {
			$scroll.html(`<div class="dl-empty">
				<i class="fa fa-inbox"></i>
				<p>No records found for the selected filters.</p>
			</div>`);
			return;
		}

		const body_rows = rows.map(r => {
			const hasDetails = (r.items.length > 0 || r.payments.length > 0);
			const expandIcon = hasDetails ? `<i class="fa fa-chevron-right dl-expand-icon" style="transition: transform 0.2s; font-size:10px;"></i>` : "";
			
			const items_html = r.items.length ? `
				<div class="nested-table-wrapper">
					<div class="nested-title">
						<i class="fa fa-shopping-cart text-muted" style="margin-right:4px;"></i> Sales Items Breakdown
					</div>
					<div class="nested-table-container">
						<table class="nested-table">
							<tr>
								<th class="text-left">Item Name</th>
								<th class="num">Qty</th>
								<th class="num">Reg. Price</th>
								<th class="num">Run. Price</th>
								<th class="num">Amount</th>
								<th class="num">Comm.</th>
							</tr>
							${r.items.map(i => `
								<tr>
									<td class="text-left">${esc(i.item_name)}</td>
									<td class="num">${esc(i.qty)}</td>
									<td class="num">${esc(fmt_cur(i.regular_price))}</td>
									<td class="num">${esc(fmt_cur(i.running_price))}</td>
									<td class="num">${esc(fmt_cur(i.amount))}</td>
									<td class="num">${esc(fmt_cur(i.commission_amount))}</td>
								</tr>`).join("")}
						</table>
					</div>
				</div>
			` : "";

			const payments_html = r.payments.length ? `
				<div class="nested-table-wrapper">
					<div class="nested-title">
						<i class="fa fa-money text-muted" style="margin-right:4px;"></i> Payment Entries Applied
					</div>
					<div class="nested-table-container">
						<table class="nested-table">
							<tr>
								<th class="text-left">Slip / Txn ID</th>
								<th class="text-left">Bank Name</th>
								<th class="text-left">Account</th>
								<th class="num">Deposit</th>
								<th class="num">Charge</th>
								<th class="num">Net</th>
							</tr>
							${r.payments.map(p => `
							<tr>
								<td class="text-left">${esc(p.deposit_slip_no)}</td>
								<td class="text-left">${esc(p.bank_name)}</td>
								<td class="text-left">${esc(p.deposit_account_name)}</td>
								<td class="num">${esc(fmt_cur(p.deposit_amount))}</td>
								<td class="num">${esc(fmt_cur(p.bank_charge))}</td>
								<td class="num">${esc(fmt_cur(p.net_deposit))}</td>
							</tr>`).join("")}
						</table>
					</div>
				</div>
			` : "";

			return `
			<tr class="parent-row" data-id="${esc(r.invoice_name)}">
				<td class="col-sl" style="white-space:nowrap;">
					<div style="display:flex; align-items:center; gap:8px;">
						${expandIcon} <span style="font-weight:600;">${r.entry_sl}</span>
					</div>
				</td>
				<td style="white-space:nowrap;">${esc(r.date ? frappe.datetime.str_to_user(r.date) : "")}</td>
				<td>${esc(r.transport_name)}</td>
				<td>${esc(r.booking_deposit_slip_no)}</td>
				
				<td>${esc(r.items.length)} Items</td>
				<td class="num">${esc(r.total_qty || 0)}</td>
				<td class="num"></td>
				<td class="num"></td>
				<td class="num">${esc(fmt_cur(r.total_selling_price))}</td>
				<td class="num">${esc(fmt_cur(r.total_commission))}</td>
				
				<td>${esc(r.deposit_slip_no)}</td>
				<td>${esc(r.bank_name)}</td>
				<td>${esc(r.deposit_account_name)}</td>
				<td class="num">${esc(fmt_cur(r.deposit_amount))}</td>
				<td class="num">${esc(fmt_cur(r.bank_charge))}</td>
				<td class="num">${esc(fmt_cur(r.net_deposit))}</td>
				
				<td class="num">${esc(fmt_cur(r.balance_tk))}</td>
				
				<td>${esc(r.showroom_name)}</td>
				<td>${esc(r.owner_name)}</td>
			</tr>
			<tr class="child-row" id="child-${esc(r.invoice_name)}" style="display: none;">
				<td colspan="19">
					<div class="child-container">
						<div class="dl-child-grid">
							${items_html}
							${payments_html}
						</div>
					</div>
				</td>
			</tr>
			`;
		}).join("");

		const html = `
		<table class="dl-tbl">
			<thead>
				<tr class="dl-group-row">
					<th colspan="4">Common</th>
					<th colspan="6">Sales Totals</th>
					<th colspan="6">Deposit Totals</th>
					<th colspan="1">Balance</th>
					<th colspan="2">Dealer Info</th>
				</tr>
				<tr>
					<th class="col-sl">Sl#</th>
					<th>Date</th>
					<th>Transport Name</th>
					<th>Booking / Deposit Slip No</th>
					
					<th>Sales Items</th>
					<th class="num">Sales Qty</th>
					<th class="num">Regular Price</th>
					<th class="num">Running Price</th>
					<th class="num">Total Selling Price</th>
					<th class="num">Commission Tk/Pcs</th>
					
					<th>Deposit Slip No / Txn ID</th>
					<th>Bank Name</th>
					<th>Deposit Account Name</th>
					<th class="num">Deposit Amount</th>
					<th class="num">Bank Charge</th>
					<th class="num">Net Deposit</th>
					
					<th class="num">Balance TK</th>
					
					<th>Showroom Name</th>
					<th>Owner Name</th>
				</tr>
			</thead>
			<tbody>${body_rows}</tbody>
		</table>`;

		$scroll.html(html);
	}

	$w.on("click", ".parent-row", function() {
		const id = $(this).attr("data-id");
		const $child = $w.find("#child-" + $.escapeSelector(id));
		const $icon = $(this).find(".dl-expand-icon");
		
		if ($child.is(":visible")) {
			$child.hide();
			$icon.css("transform", "rotate(0deg)");
		} else {
			$child.show();
			$icon.css("transform", "rotate(90deg)");
		}
	});

	function update_pagination() {
		const start_idx = total_count === 0 ? 0 : (current_page - 1) * page_size + 1;
		const end_idx = Math.min(current_page * page_size, total_count);
		
		$w.find(".dl-page-info").text(`Showing ${start_idx} to ${end_idx} of Invoices: ${total_count}`);
		
		$w.find(".dl-btn-prev").prop("disabled", current_page === 1);
		$w.find(".dl-btn-next").prop("disabled", end_idx >= total_count);
	}

	function get_sales_user_filter_value() {
		if (page_context.can_filter_sales_user) {
			return f_sales_user.get_value() || null;
		}
		return null;
	}

	function get_filter_args() {
		return {
			customer: f_customer.get_value() || "",
			from_date: f_from.get_value() || "",
			to_date: f_to.get_value() || "",
			sales_user: get_sales_user_filter_value() || "",
		};
	}

	function download_dealer_ledger_pdf() {
		if (!total_count) {
			frappe.msgprint({
				title: __("No Data"),
				message: __("Apply filters with at least one invoice before downloading PDF."),
				indicator: "orange",
			});
			return;
		}

		const args = get_filter_args();
		const query = Object.keys(args)
			.filter((key) => args[key])
			.map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(args[key])}`)
			.join("&");

		const url =
			frappe.urllib.get_full_url(
				"/api/method/sunshine_power_ltd.sunshine_power_ltd.page.dealer_ledger.dealer_ledger.download_dealer_ledger_pdf"
			) + (query ? `?${query}` : "");

		window.open(url, "_blank");
	}

	async function setup_page_context() {
		try {
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.dealer_ledger.dealer_ledger.get_dealer_ledger_context",
			});
			page_context = res.message || page_context;

			if (page_context.can_filter_sales_user) {
				$w.find(".dl-f-sales-user").show();
			} else if (page_context.is_salesman) {
				$w.find(".dl-filter-sales-note")
					.show()
					.html(
						`<div class="dl-sales-user-note"><i class="fa fa-user"></i> Showing ledger for: <strong>${esc(page_context.current_user)}</strong></div>`
					);
			}
		} catch (err) {
			console.error(err);
		}
	}

	async function load_report() {
		$w.find(".dl-table-scroll").html(`<div class="dl-empty"><i class="fa fa-spinner fa-spin"></i><p>Loading...</p></div>`);
		
		try {
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.dealer_ledger.dealer_ledger.get_dealer_ledger",
				args: {
					customer: f_customer.get_value() || null,
					from_date: f_from.get_value() || null,
					to_date: f_to.get_value() || null,
					sales_user: get_sales_user_filter_value(),
					start: (current_page - 1) * page_size,
					limit: page_size,
				},
			});
			const result = res.message || { data: [], total_count: 0 };
			total_count = result.total_count || 0;
			
			render_summary(result.data);
			render_table(result.data);
			update_pagination();
		} catch (err) {
			console.error(err);
			$w.find(".dl-table-scroll").html(`<div class="dl-empty"><i class="fa fa-exclamation-triangle"></i><p>Failed to load data.</p></div>`);
		}
	}

	$w.find(".dl-btn-prev").on("click", () => {
		if (current_page > 1) {
			current_page--;
			load_report();
		}
	});

	$w.find(".dl-btn-next").on("click", () => {
		if (current_page * page_size < total_count) {
			current_page++;
			load_report();
		}
	});

	$w.find(".dl-btn-pdf").on("click", () => download_dealer_ledger_pdf());

	page.set_secondary_action(__("Download PDF"), () => download_dealer_ledger_pdf(), "file-pdf");

	$w.find(".dl-btn-reset").on("click", () => {
		if (page_context.can_filter_sales_user) {
			f_sales_user.set_value("");
		}
		f_customer.set_value("");
		f_from.set_value("");
		f_to.set_value("");
	});

	(async () => {
		await setup_page_context();
		load_report();
	})();
};