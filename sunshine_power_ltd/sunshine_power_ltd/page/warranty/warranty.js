frappe.pages["warranty"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Warranty"),
		single_column: true,
	});

	const state = {
		invoice: null,
		context: {},
		session_docs: [],
	};

	if (!document.getElementById("wc-style")) {
		$("head").append(`<style id="wc-style">
.wc-wrap { padding: 10px 0 80px; }
.wc-card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.wc-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:#64748b; margin-bottom:12px; }
.wc-search-row { display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end; }
.wc-field { flex:1 1 220px; min-width:180px; }
.wc-actions { display:flex; gap:8px; flex-wrap:wrap; }
.wc-summary-row { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; }
.wc-scard { flex:1 1 130px; background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.wc-scard.accent { border-color:#2563eb; background:#eff6ff; }
.wc-scard.warn { border-color:#f59e0b; background:#fffbeb; }
.wc-scard.ok { border-color:#10b981; background:#ecfdf5; }
.wc-scard-lbl { font-size:10px; color:#6b7280; text-transform:uppercase; letter-spacing:.4px; margin-bottom:4px; }
.wc-scard-val { font-size:16px; font-weight:700; color:#111827; }
.wc-meta { display:flex; flex-wrap:wrap; gap:16px; font-size:12px; color:#475569; margin-bottom:12px; }
.wc-meta strong { color:#111827; }
.wc-table-scroll { overflow:auto; max-height:360px; border:1px solid #e2e8f0; border-radius:10px; }
.wc-tbl { width:100%; border-collapse:collapse; font-size:12px; }
.wc-tbl thead th { position:sticky; top:0; z-index:2; background:#f1f5f9; padding:10px 12px; text-align:left; font-size:11px; text-transform:uppercase; border-bottom:2px solid #cbd5e1; white-space:nowrap; }
.wc-tbl tbody td { padding:10px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.wc-tbl tbody tr.warn-row { background:#fff7ed; }
.wc-tbl tbody tr.done-row { background:#f8fafc; color:#64748b; }
.wc-tbl .num { text-align:right; font-variant-numeric:tabular-nums; }
.wc-tbl input[type=number], .wc-tbl input[type=text] { width:100%; min-width:70px; padding:4px 8px; border:1px solid #d1d5db; border-radius:6px; font-size:12px; }
.wc-grid-2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; }
.wc-form-row { display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end; margin-bottom:10px; }
.wc-sticky-actions { position:sticky; bottom:0; z-index:20; background:#fff; border-top:1px solid #e2e8f0; padding:12px 18px; display:flex; gap:8px; flex-wrap:wrap; box-shadow:0 -4px 12px rgba(0,0,0,.05); }
.wc-empty { text-align:center; padding:40px 0; color:#9ca3af; }
.wc-badge { display:inline-block; padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600; background:#e2e8f0; color:#334155; }
.wc-badge.draft { background:#e2e8f0; }
.wc-badge.returned { background:#dbeafe; color:#1d4ed8; }
.wc-badge.inspected { background:#fef3c7; color:#b45309; }
.wc-badge.replaced { background:#ede9fe; color:#6d28d9; }
.wc-badge.completed { background:#d1fae5; color:#047857; }
.wc-history-item { border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; margin-bottom:8px; font-size:12px; }
.wc-history-item a { font-weight:600; }
.wc-alert { padding:10px 12px; border-radius:8px; background:#fff7ed; border:1px solid #fdba74; color:#9a3412; font-size:12px; margin-bottom:12px; }
</style>`);
	}

	const $w = $(`
		<div class="wc-wrap">
			<div class="wc-card">
				<div class="wc-title">${__("Invoice Search")}</div>
				<div class="wc-search-row">
					<div class="wc-field wc-f-invoice"></div>
					<div class="wc-field wc-f-barcode"></div>
					<div class="wc-actions">
						<button class="btn btn-primary btn-sm wc-btn-search">${__("Search Invoice")}</button>
						<button class="btn btn-default btn-sm wc-btn-clear">${__("Clear")}</button>
					</div>
				</div>
			</div>

			<div class="wc-summary-row wc-summary-panel" style="display:none;"></div>
			<div class="wc-invoice-panel" style="display:none;">
				<div class="wc-card">
					<div class="wc-title">${__("Sales Invoice Details")}</div>
					<div class="wc-meta wc-invoice-meta"></div>
					<div class="wc-alert wc-claim-alert" style="display:none;"></div>
					<div class="wc-table-scroll">
						<div class="wc-empty wc-items-loading"><i class="fa fa-spinner fa-spin"></i> ${__("Loading items...")}</div>
					</div>
				</div>

				<div class="wc-grid-2">
					<div class="wc-card">
						<div class="wc-title">${__("Receive Product")}</div>
						<div class="wc-form-row">
							<div class="wc-field wc-f-receive-wh"></div>
							<div class="wc-field wc-f-condition"></div>
						</div>
						<button class="btn btn-primary btn-sm wc-btn-return">${__("Create Warranty Return")}</button>
					</div>

					<div class="wc-card">
						<div class="wc-title">${__("Warehouse Transfer")}</div>
						<div class="wc-form-row">
							<div class="wc-field wc-f-source-wh"></div>
							<div class="wc-field wc-f-target-wh"></div>
						</div>
						<button class="btn btn-default btn-sm wc-btn-transfer">${__("Create Stock Entry")}</button>
					</div>

					<div class="wc-card">
						<div class="wc-title">${__("Replacement Product")}</div>
						<div class="wc-form-row">
							<div class="wc-field wc-f-replacement-wh"></div>
						</div>
						<button class="btn btn-default btn-sm wc-btn-replacement">${__("Issue Replacement Product")}</button>
					</div>

					<div class="wc-card">
						<div class="wc-title">${__("Claim History")}</div>
						<div class="wc-history-list"></div>
					</div>
				</div>
			</div>

			<div class="wc-sticky-actions wc-action-bar" style="display:none;">
				<button class="btn btn-default btn-sm wc-btn-reload">${__("Refresh")}</button>
				<span class="text-muted" style="font-size:12px; align-self:center;"></span>
			</div>
		</div>
	`);

	page.main.append($w);

	const controls = {};
	const make_control = (parent, df) => {
		const control = frappe.ui.form.make_control({
			parent: $w.find(parent),
			df,
			render_input: true,
		});
		return control;
	};

	controls.invoice = make_control(".wc-f-invoice", {
		fieldname: "invoice_no",
		label: __("Sales Invoice Number"),
		fieldtype: "Data",
		placeholder: __("SINV-00001"),
	});
	controls.barcode = make_control(".wc-f-barcode", {
		fieldname: "barcode",
		label: __("Barcode / Serial Number"),
		fieldtype: "Data",
		placeholder: __("Optional"),
	});
	controls.receive_wh = make_control(".wc-f-receive-wh", {
		fieldname: "receive_warehouse",
		label: __("Receive Warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
		reqd: 1,
	});
	controls.condition = make_control(".wc-f-condition", {
		fieldname: "product_condition",
		label: __("Product Condition"),
		fieldtype: "Select",
		options: "\nDamaged\nSellable\nRepairable",
		reqd: 1,
	});
	controls.source_wh = make_control(".wc-f-source-wh", {
		fieldname: "source_warehouse",
		label: __("Source Warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
	});
	controls.target_wh = make_control(".wc-f-target-wh", {
		fieldname: "target_warehouse",
		label: __("Target Warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
	});
	controls.replacement_wh = make_control(".wc-f-replacement-wh", {
		fieldname: "replacement_warehouse",
		label: __("Replacement Warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
	});

	const esc = (v) => frappe.utils.escape_html(String(v ?? ""));
	const to_flt = (v) => flt(v);

	const InvoiceLoader = {
		async load(search = {}) {
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.search_sales_invoice",
				args: search,
			});
			state.invoice = res.message;
			this.render(state.invoice);
			return state.invoice;
		},
		async reload() {
			if (!state.invoice?.sales_invoice) return;
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.load_sales_invoice",
				args: { sales_invoice: state.invoice.sales_invoice },
			});
			state.invoice = res.message;
			this.render(state.invoice);
		},
		render(data) {
			$w.find(".wc-invoice-panel, .wc-summary-panel, .wc-action-bar").show();
			this.render_summary(data.summary);
			this.render_meta(data);
			this.render_items(data.items);
			HistoryLoader.render(data.history || []);
			$w.find(".wc-action-bar span").text(
				`${__("Session documents")}: ${state.session_docs.length}`
			);
		},
		render_summary(summary) {
			const status = (summary?.status || "Draft").toLowerCase();
			const cards = [
				{ lbl: __("Status"), val: summary?.status || "Draft", cls: status },
				{ lbl: __("Claimed Qty"), val: to_flt(summary?.claimed_qty) },
				{ lbl: __("Returned Qty"), val: to_flt(summary?.returned_qty) },
				{ lbl: __("Replaced Qty"), val: to_flt(summary?.replaced_qty) },
				{ lbl: __("Pending Qty"), val: to_flt(summary?.pending_qty), accent: summary?.pending_qty > 0 },
			];
			$w.find(".wc-summary-panel").html(
				cards.map((c) => `
					<div class="wc-scard ${c.cls ? c.cls : ""} ${c.accent ? "warn" : ""}">
						<div class="wc-scard-lbl">${esc(c.lbl)}</div>
						<div class="wc-scard-val">${c.cls ? `<span class="wc-badge ${esc(c.cls)}">${esc(c.val)}</span>` : esc(c.val)}</div>
					</div>`
				).join("")
			);
		},
		render_meta(data) {
			$w.find(".wc-invoice-meta").html(`
				<div><strong>${__("Sales Invoice")}:</strong> ${esc(data.sales_invoice)}</div>
				<div><strong>${__("Customer")}:</strong> ${esc(data.customer_name || data.customer)}</div>
				<div><strong>${__("Posting Date")}:</strong> ${esc(frappe.datetime.str_to_user(data.posting_date))}</div>
				<div><strong>${__("Company")}:</strong> ${esc(data.company)}</div>
			`);
			const fully_claimed = (data.items || []).every((row) => row.fully_claimed);
			const $alert = $w.find(".wc-claim-alert");
			if (fully_claimed) {
				$alert.show().text(__("All items on this invoice are already fully claimed."));
			} else {
				$alert.hide();
			}
		},
		render_items(items) {
			const rows = (items || []).map((row, idx) => {
				const row_cls = row.fully_claimed ? "done-row" : row.remaining_qty <= 0 ? "warn-row" : "";
				return `
					<tr class="${row_cls}" data-idx="${idx}">
						<td>${esc(row.item_code)}</td>
						<td>${esc(row.item_name)}</td>
						<td class="num">${to_flt(row.sold_qty)}</td>
						<td class="num">${to_flt(row.claimed_qty)}</td>
						<td class="num"><input type="number" min="0" step="1" class="wc-claim-qty" value="${to_flt(row.claim_qty)}" ${row.fully_claimed ? "disabled" : ""}></td>
						<td class="num">${to_flt(row.remaining_qty)}</td>
						<td><input type="text" class="wc-serial-no" value="${esc(row.serial_no)}" placeholder="${row.has_serial_no ? __("Serial No") : ""}" ${row.fully_claimed ? "disabled" : ""}></td>
						<td><input type="text" class="wc-batch-no" value="${esc(row.batch_no)}" placeholder="${row.has_batch_no ? __("Batch No") : ""}" ${row.fully_claimed ? "disabled" : ""}></td>
						<td class="num wc-transfer-qty-cell"><input type="number" min="0" step="1" class="wc-transfer-qty" value="0"></td>
						<td class="wc-replacement-item"><input type="text" class="wc-replacement-item-code" value="${esc(row.item_code)}"></td>
						<td class="num"><input type="number" min="0" step="1" class="wc-replacement-qty" value="0"></td>
					</tr>`;
			}).join("");

			$w.find(".wc-table-scroll").html(`
				<table class="wc-tbl">
					<thead>
						<tr>
							<th>${__("Item Code")}</th>
							<th>${__("Item Name")}</th>
							<th class="num">${__("Sold Qty")}</th>
							<th class="num">${__("Prev. Claimed")}</th>
							<th class="num">${__("Claim Qty")}</th>
							<th class="num">${__("Remaining")}</th>
							<th>${__("Serial No")}</th>
							<th>${__("Batch No")}</th>
							<th class="num">${__("Transfer Qty")}</th>
							<th>${__("Replacement Item")}</th>
							<th class="num">${__("Replacement Qty")}</th>
						</tr>
					</thead>
					<tbody>${rows || `<tr><td colspan="11" class="wc-empty">${__("No items found")}</td></tr>`}</tbody>
				</table>
			`);
		},
	};

	const ClaimValidator = {
		collect_claim_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const $tr = $w.find(`tr[data-idx="${idx}"]`);
				const claim_qty = to_flt($tr.find(".wc-claim-qty").val());
				if (claim_qty <= 0) return;
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					claim_qty,
					serial_no: $tr.find(".wc-serial-no").val(),
					batch_no: $tr.find(".wc-batch-no").val(),
				});
			});
			return items;
		},
		collect_transfer_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const $tr = $w.find(`tr[data-idx="${idx}"]`);
				const transfer_qty = to_flt($tr.find(".wc-transfer-qty").val());
				if (transfer_qty <= 0) return;
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					uom: row.uom,
					transfer_qty,
					serial_no: $tr.find(".wc-serial-no").val(),
					batch_no: $tr.find(".wc-batch-no").val(),
				});
			});
			return items;
		},
		collect_replacement_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const $tr = $w.find(`tr[data-idx="${idx}"]`);
				const replacement_qty = to_flt($tr.find(".wc-replacement-qty").val());
				if (replacement_qty <= 0) return;
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					replacement_item_code: $tr.find(".wc-replacement-item-code").val() || row.item_code,
					replacement_qty,
				});
			});
			return items;
		},
		validate_claim_items(items) {
			if (!items.length) {
				frappe.throw(__("Enter claim quantity for at least one item."));
			}
			items.forEach((row) => {
				if (to_flt(row.claim_qty) <= 0) {
					frappe.throw(__("Claim quantity cannot be zero."));
				}
			});
		},
	};

	const SalesReturnGenerator = {
		async create(submit = 1) {
			const items = ClaimValidator.collect_claim_items();
			ClaimValidator.validate_claim_items(items);

			const receive_warehouse = controls.receive_wh.get_value();
			const product_condition = controls.condition.get_value();
			if (!receive_warehouse) frappe.throw(__("Receive Warehouse is mandatory."));
			if (!product_condition) frappe.throw(__("Product Condition is mandatory."));

			await frappe.confirm(
				__("Create Sales Invoice Return for {0} item(s)?", [items.length]),
				async () => {
					const res = await frappe.call({
						method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_return",
						args: {
							sales_invoice: state.invoice.sales_invoice,
							items,
							receive_warehouse,
							product_condition,
							submit,
						},
						freeze: true,
						freeze_message: __("Creating warranty return..."),
					});
					this._handle_result(res.message, __("Warranty return created"));
				}
			);
		},
		_handle_result(message, title) {
			state.session_docs.push(message);
			state.invoice = message.invoice;
			InvoiceLoader.render(state.invoice);
			frappe.show_alert({
				message: `${title}: ${message.name}`,
				indicator: "green",
			});
			frappe.set_route("Form", message.doctype, message.name);
		},
	};

	const StockTransferGenerator = {
		async create(submit = 1) {
			const items = ClaimValidator.collect_transfer_items();
			if (!items.length) frappe.throw(__("Enter transfer quantity for at least one item."));

			const source_warehouse = controls.source_wh.get_value();
			const target_warehouse = controls.target_wh.get_value();
			if (!source_warehouse || !target_warehouse) {
				frappe.throw(__("Source and target warehouse are required."));
			}

			await frappe.confirm(
				__("Create Material Transfer Stock Entry?"),
				async () => {
					const res = await frappe.call({
						method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_stock_transfer",
						args: {
							sales_invoice: state.invoice.sales_invoice,
							items,
							source_warehouse,
							target_warehouse,
							submit,
						},
						freeze: true,
						freeze_message: __("Creating stock transfer..."),
					});
					state.session_docs.push(res.message);
					state.invoice = res.message.invoice;
					InvoiceLoader.render(state.invoice);
					frappe.show_alert({
						message: __("Stock Entry created: {0}", [res.message.name]),
						indicator: "green",
					});
					frappe.set_route("Form", res.message.doctype, res.message.name);
				}
			);
		},
	};

	const DeliveryNoteGenerator = {
		async create(submit = 1) {
			const items = ClaimValidator.collect_replacement_items();
			if (!items.length) frappe.throw(__("Enter replacement quantity for at least one item."));

			const replacement_warehouse = controls.replacement_wh.get_value();
			if (!replacement_warehouse) frappe.throw(__("Replacement Warehouse is mandatory."));

			await frappe.confirm(
				__("Issue replacement delivery note for {0} item(s)?", [items.length]),
				async () => {
					const res = await frappe.call({
						method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_replacement",
						args: {
							sales_invoice: state.invoice.sales_invoice,
							items,
							replacement_warehouse,
							submit,
						},
						freeze: true,
						freeze_message: __("Creating delivery note..."),
					});
					state.session_docs.push(res.message);
					state.invoice = res.message.invoice;
					InvoiceLoader.render(state.invoice);
					frappe.show_alert({
						message: __("Delivery Note created: {0}", [res.message.name]),
						indicator: "green",
					});
					frappe.set_route("Form", res.message.doctype, res.message.name);
				}
			);
		},
	};

	const HistoryLoader = {
		render(history) {
			if (!history.length) {
				$w.find(".wc-history-list").html(`<div class="wc-empty">${__("No warranty history yet.")}</div>`);
				return;
			}
			$w.find(".wc-history-list").html(
				history.map((row) => `
					<div class="wc-history-item">
						<div><a href="${frappe.utils.get_form_link(row.doctype, row.reference, true)}">${esc(row.reference)}</a>
						<span class="text-muted"> · ${esc(row.type)} · ${esc(frappe.datetime.str_to_user(row.date))}</span></div>
						<div>${__("Items")}: ${esc(row.items || "")}</div>
						<div>${__("Qty")}: ${to_flt(row.qty)} · ${__("Status")}: ${esc(row.status)} ${row.detail ? `· ${esc(row.detail)}` : ""}</div>
					</div>`
				).join("")
			);
		},
	};

	async function setup_context() {
		const res = await frappe.call({
			method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.get_warranty_context",
		});
		state.context = res.message || {};
		if (state.context.default_receive_warehouse) {
			controls.receive_wh.set_value(state.context.default_receive_warehouse);
			controls.source_wh.set_value(state.context.default_receive_warehouse);
		}
	}

	controls.condition.$input.on("change", () => {
		const condition = controls.condition.get_value();
		const wh = state.context.condition_warehouses?.[condition];
		if (wh) controls.target_wh.set_value(wh);
	});

	$w.find(".wc-btn-search").on("click", async () => {
		try {
			await InvoiceLoader.load({
				invoice_no: controls.invoice.get_value(),
				barcode: controls.barcode.get_value(),
			});
		} catch (e) {
			console.error(e);
		}
	});

	$w.find(".wc-btn-clear").on("click", () => {
		state.invoice = null;
		state.session_docs = [];
		controls.invoice.set_value("");
		controls.barcode.set_value("");
		$w.find(".wc-invoice-panel, .wc-summary-panel, .wc-action-bar").hide();
	});

	$w.find(".wc-btn-return").on("click", () => SalesReturnGenerator.create(1));
	$w.find(".wc-btn-transfer").on("click", () => StockTransferGenerator.create(1));
	$w.find(".wc-btn-replacement").on("click", () => DeliveryNoteGenerator.create(1));
	$w.find(".wc-btn-reload").on("click", () => InvoiceLoader.reload());

	controls.invoice.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search").trigger("click");
	});
	controls.barcode.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search").trigger("click");
	});

	setup_context();
};
