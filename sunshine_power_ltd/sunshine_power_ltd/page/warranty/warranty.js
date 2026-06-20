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
		active_tab: "claim",
	};

	if (!document.getElementById("wc-style")) {
		$("head").append(`<style id="wc-style">
.wc-wrap { padding:10px 0 24px; max-width:1100px; margin:0 auto; }
.wc-hero { margin-bottom:14px; }
.wc-hero h2 { margin:0 0 4px; font-size:22px; font-weight:700; color:#0f172a; }
.wc-hero p { margin:0; font-size:13px; color:#64748b; }
.wc-card { background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
.wc-card.claim { border-top:3px solid #2563eb; }
.wc-card.settle { border-top:3px solid #7c3aed; }
.wc-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:#64748b; margin-bottom:12px; }
.wc-search-row { display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end; }
.wc-field { flex:1 1 220px; min-width:180px; }
.wc-actions { display:flex; gap:8px; flex-wrap:wrap; }
.wc-summary-row { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; }
.wc-scard { flex:1 1 120px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:12px 14px; }
.wc-scard-lbl { font-size:10px; color:#6b7280; text-transform:uppercase; margin-bottom:4px; }
.wc-scard-val { font-size:18px; font-weight:700; color:#111827; }
.wc-tabs { display:flex; gap:8px; margin-bottom:14px; padding:6px; background:#f1f5f9; border-radius:12px; }
.wc-tab { flex:1; border:0; background:transparent; padding:12px 16px; border-radius:10px; font-size:13px; font-weight:600; color:#64748b; cursor:pointer; transition:all .2s; }
.wc-tab.active { background:#fff; color:#0f172a; box-shadow:0 1px 3px rgba(0,0,0,.08); }
.wc-tab[data-tab="claim"].active { color:#1d4ed8; }
.wc-tab[data-tab="settle"].active { color:#6d28d9; }
.wc-tab-icon { display:block; font-size:10px; font-weight:500; opacity:.75; margin-top:2px; }
.wc-tab-panel { display:none; }
.wc-tab-panel.active { display:block; }
.wc-phase-banner { display:flex; gap:12px; align-items:flex-start; padding:12px 14px; border-radius:10px; margin-bottom:14px; font-size:12px; line-height:1.5; }
.wc-phase-banner.claim { background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a; }
.wc-phase-banner.settle { background:#f5f3ff; border:1px solid #ddd6fe; color:#5b21b6; }
.wc-phase-banner strong { display:block; font-size:13px; margin-bottom:2px; }
.wc-phase-num { flex:0 0 28px; height:28px; border-radius:999px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:12px; color:#fff; }
.wc-phase-banner.claim .wc-phase-num { background:#2563eb; }
.wc-phase-banner.settle .wc-phase-num { background:#7c3aed; }
.wc-meta { display:flex; flex-wrap:wrap; gap:12px 18px; font-size:12px; color:#475569; margin-bottom:12px; }
.wc-meta strong { color:#111827; }
.wc-table-scroll { overflow:auto; border:1px solid #e2e8f0; border-radius:10px; }
.wc-tbl { width:100%; border-collapse:collapse; font-size:12px; }
.wc-tbl thead th { position:sticky; top:0; z-index:2; background:#f8fafc; padding:10px 12px; text-align:left; font-size:11px; text-transform:uppercase; border-bottom:1px solid #e2e8f0; }
.wc-tbl tbody td { padding:10px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.wc-tbl .num { text-align:right; }
.wc-tbl input { width:100%; min-width:64px; padding:8px 10px; border:1px solid #d1d5db; border-radius:8px; font-size:14px; }
.wc-item-card { border:1px solid #e2e8f0; border-radius:12px; padding:14px; margin-bottom:10px; background:#fff; }
.wc-item-card.done { opacity:.65; background:#f8fafc; }
.wc-item-card-head { font-weight:700; color:#111827; margin-bottom:8px; }
.wc-item-card-meta { display:flex; flex-wrap:wrap; gap:8px 14px; font-size:11px; color:#64748b; margin-bottom:10px; }
.wc-item-card-field { margin-bottom:10px; }
.wc-item-card-field label { display:block; font-size:10px; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:4px; }
.wc-item-card-field input { width:100%; padding:10px 12px; border:1px solid #d1d5db; border-radius:8px; font-size:15px; }
.wc-mobile-items { display:none; }
.wc-desktop-table { display:block; }
.wc-form-row { display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end; margin-bottom:12px; }
.wc-step-note { font-size:12px; color:#64748b; margin:0 0 12px; line-height:1.5; }
.wc-btn-main { width:100%; min-height:44px; font-size:14px; font-weight:600; border-radius:10px; }
.wc-empty { text-align:center; padding:36px 16px; color:#94a3b8; font-size:13px; }
.wc-badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:11px; font-weight:600; background:#e2e8f0; }
.wc-badge.returned { background:#dbeafe; color:#1d4ed8; }
.wc-badge.replaced { background:#ede9fe; color:#6d28d9; }
.wc-badge.completed { background:#d1fae5; color:#047857; }
.wc-history-item { border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; margin-bottom:8px; font-size:12px; }
.wc-alert { padding:10px 12px; border-radius:8px; background:#fff7ed; border:1px solid #fdba74; color:#9a3412; font-size:12px; margin-bottom:12px; }
.wc-settle-empty { text-align:center; padding:28px 16px; color:#64748b; }
@media (max-width:768px) {
	.wc-wrap { padding:8px 8px 24px; }
	.wc-search-row, .wc-form-row { flex-direction:column; }
	.wc-field, .wc-actions, .wc-actions .btn { width:100%; }
	.wc-actions .btn { min-height:42px; }
	.wc-scard { flex:1 1 calc(50% - 8px); }
	.wc-mobile-items { display:block; }
	.wc-desktop-table { display:none; }
	.wc-f-barcode { display:none; }
	.wc-tab { padding:10px 12px; font-size:12px; }
}
</style>`);
	}

	const $w = $(`
		<div class="wc-wrap">
			<div class="wc-hero">
				<h2>${__("Warranty")}</h2>
				<p>${__("Claim returned products first, then settle with inspection and replacement.")}</p>
			</div>

			<div class="wc-card">
				<div class="wc-title">${__("Find Invoice")}</div>
				<div class="wc-search-row">
					<div class="wc-field wc-f-invoice"></div>
					<div class="wc-field wc-f-barcode"></div>
					<div class="wc-actions">
						<button class="btn btn-primary wc-btn-search">${__("Search")}</button>
						<button class="btn btn-default wc-btn-clear">${__("Clear")}</button>
					</div>
				</div>
			</div>

			<div class="wc-summary-row wc-summary-panel" style="display:none;"></div>

			<div class="wc-tabs wc-tab-switcher" style="display:none;">
				<button type="button" class="wc-tab active" data-tab="claim">
					${__("Claim")}
					<span class="wc-tab-icon">${__("Receive product")}</span>
				</button>
				<button type="button" class="wc-tab" data-tab="settle">
					${__("Settle")}
					<span class="wc-tab-icon">${__("Transfer & replace")}</span>
				</button>
			</div>

			<div class="wc-invoice-panel" style="display:none;">
				<div class="wc-tab-panel wc-tab-claim active">
					<div class="wc-phase-banner claim">
						<div class="wc-phase-num">1</div>
						<div>
							<strong>${__("Claim — receive returned product")}</strong>
							${__("Enter claim quantity and create a draft return. Submit the return invoice only after the customer hands over the product.")}
						</div>
					</div>
					<div class="wc-card claim">
						<div class="wc-meta wc-invoice-meta-claim"></div>
						<div class="wc-alert wc-claim-alert" style="display:none;"></div>
						<div class="wc-table-scroll wc-items-claim"></div>
						<div class="wc-form-row" style="margin-top:14px;">
							<div class="wc-field wc-f-receive-wh"></div>
							<div class="wc-field wc-f-condition"></div>
						</div>
						<button class="btn btn-primary wc-btn-main wc-btn-return">${__("Create Draft Return")}</button>
					</div>
				</div>

				<div class="wc-tab-panel wc-tab-settle">
					<div class="wc-phase-banner settle">
						<div class="wc-phase-num">2</div>
						<div>
							<strong>${__("Settle — inspect, move stock & replace")}</strong>
							${__("After the return is submitted, transfer items to the right warehouse and issue replacement product to the customer.")}
						</div>
					</div>
					<div class="wc-card settle">
						<div class="wc-meta wc-invoice-meta-settle"></div>
						<div class="wc-alert wc-settle-alert" style="display:none;"></div>
						<div class="wc-table-scroll wc-items-settle"></div>
					</div>
					<div class="wc-card settle">
						<div class="wc-title">${__("Warehouse Transfer")}</div>
						<p class="wc-step-note">${__("Move received items from incoming to damaged / sellable / repair warehouse.")}</p>
						<div class="wc-form-row">
							<div class="wc-field wc-f-source-wh"></div>
							<div class="wc-field wc-f-target-wh"></div>
						</div>
						<button class="btn btn-default wc-btn-main wc-btn-transfer">${__("Create Stock Entry")}</button>
					</div>
					<div class="wc-card settle">
						<div class="wc-title">${__("Issue Replacement")}</div>
						<p class="wc-step-note">${__("Give new product to the customer from replacement warehouse.")}</p>
						<div class="wc-form-row">
							<div class="wc-field wc-f-replacement-wh"></div>
						</div>
						<button class="btn btn-primary wc-btn-main wc-btn-replacement">${__("Issue Replacement")}</button>
					</div>
					<div class="wc-card">
						<div class="wc-title">${__("History")}</div>
						<div class="wc-history-list"></div>
					</div>
				</div>
			</div>

			<div class="wc-settle-only wc-settle-empty wc-card" style="display:none;">
				<p>${__("Search an invoice above to start settling warranty claims.")}</p>
			</div>
		</div>
	`);

	page.main.append($w);

	const controls = {};
	const make_control = (parent, df) =>
		frappe.ui.form.make_control({ parent: $w.find(parent), df, render_input: true });

	controls.invoice = make_control(".wc-f-invoice", {
		fieldname: "invoice_no",
		label: __("Sales Invoice"),
		fieldtype: "Data",
		placeholder: __("SINV-00001"),
	});
	controls.barcode = make_control(".wc-f-barcode", {
		fieldname: "barcode",
		label: __("Barcode / Serial"),
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
		label: __("From Warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
	});
	controls.target_wh = make_control(".wc-f-target-wh", {
		fieldname: "target_warehouse",
		label: __("To Warehouse"),
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

	const RowReader = {
		scope(tab) {
			return tab ? $w.find(`.wc-tab-${tab}`) : $w;
		},
		read_number(idx, selector, tab = null) {
			let value = 0;
			this.scope(tab).find(`.wc-item-row[data-idx="${idx}"]`).each(function () {
				$(this).find(selector).each(function () {
					value = Math.max(value, to_flt($(this).val()));
				});
			});
			return value;
		},
		read_text(idx, selector, tab = null) {
			let value = "";
			this.scope(tab).find(`.wc-item-row[data-idx="${idx}"] ${selector}`).each(function () {
				const val = $(this).val();
				if (val) value = val;
			});
			return value;
		},
	};

	const TabManager = {
		init(ctx) {
			state.context = ctx;
			const { show_claim_tab, show_settle_tab, show_tab_switcher, default_tab } = ctx;

			if (show_tab_switcher) {
				$w.find(".wc-tab-switcher").show();
				$w.find('.wc-tab[data-tab="claim"]').toggle(show_claim_tab);
				$w.find('.wc-tab[data-tab="settle"]').toggle(show_settle_tab);
			} else {
				$w.find(".wc-tab-switcher").hide();
			}

			if (!show_claim_tab) {
				$w.find(".wc-tab-claim").remove();
			}
			if (!show_settle_tab) {
				$w.find(".wc-tab-settle").remove();
			} else if (!show_claim_tab) {
				$w.find(".wc-settle-only").show();
			}

			this.switch_to(default_tab || "claim");
		},
		switch_to(tab) {
			if (tab === "claim" && !state.context.show_claim_tab) tab = "settle";
			if (tab === "settle" && !state.context.show_settle_tab) tab = "claim";
			state.active_tab = tab;
			$w.find(".wc-tab").removeClass("active");
			$w.find(`.wc-tab[data-tab="${tab}"]`).addClass("active");
			$w.find(".wc-tab-panel").removeClass("active");
			$w.find(`.wc-tab-${tab}`).addClass("active");
		},
	};

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
			$w.find(".wc-invoice-panel, .wc-summary-panel, .wc-settle-only").hide();
			$w.find(".wc-invoice-panel").show();
			this.render_summary(data.summary);
			this.render_meta(data);
			this.render_claim_items(data.items);
			this.render_settle_items(data.items);
			this.render_settle_state(data);
			HistoryLoader.render(data.history || []);

			if (to_flt(data.summary?.claimed_qty) > 0 && state.context.show_settle_tab) {
				TabManager.switch_to("settle");
			}
		},
		render_summary(summary) {
			const status = (summary?.status || "Draft").toLowerCase();
			$w.find(".wc-summary-panel").show().html(`
				<div class="wc-scard"><div class="wc-scard-lbl">${__("Status")}</div><div class="wc-scard-val"><span class="wc-badge ${esc(status)}">${esc(summary?.status || "Draft")}</span></div></div>
				<div class="wc-scard"><div class="wc-scard-lbl">${__("Claimed")}</div><div class="wc-scard-val">${to_flt(summary?.claimed_qty)}</div></div>
				<div class="wc-scard"><div class="wc-scard-lbl">${__("Replaced")}</div><div class="wc-scard-val">${to_flt(summary?.replaced_qty)}</div></div>
				<div class="wc-scard"><div class="wc-scard-lbl">${__("Pending")}</div><div class="wc-scard-val">${to_flt(summary?.pending_qty)}</div></div>
			`);
		},
		render_meta(data) {
			const html = `
				<div><strong>${__("Invoice")}:</strong> ${esc(data.sales_invoice)}</div>
				<div><strong>${__("Customer")}:</strong> ${esc(data.customer_name || data.customer)}</div>
				<div><strong>${__("Date")}:</strong> ${esc(frappe.datetime.str_to_user(data.posting_date))}</div>
			`;
			$w.find(".wc-invoice-meta-claim, .wc-invoice-meta-settle").html(html);
		},
		render_claim_items(items) {
			const mobile = (items || []).map((row, idx) => this._claim_card(row, idx)).join("");
			const desktop = (items || []).map((row, idx) => this._claim_row(row, idx)).join("");
			$w.find(".wc-items-claim").html(`
				<div class="wc-mobile-items">${mobile || `<div class="wc-empty">${__("No items")}</div>`}</div>
				<div class="wc-desktop-table"><table class="wc-tbl"><thead><tr>
					<th>${__("Item")}</th><th class="num">${__("Sold")}</th><th class="num">${__("Left")}</th>
					<th class="num">${__("Claim Qty")}</th><th>${__("Serial")}</th>
				</tr></thead><tbody>${desktop}</tbody></table></div>
			`);
		},
		_claim_card(row, idx) {
			const disabled = row.fully_claimed ? "disabled" : "";
			return `
				<div class="wc-item-card wc-item-row ${row.fully_claimed ? "done" : ""}" data-idx="${idx}">
					<div class="wc-item-card-head">${esc(row.item_name || row.item_code)}</div>
					<div class="wc-item-card-meta">
						<span>${__("Sold")}: <strong>${to_flt(row.sold_qty)}</strong></span>
						<span>${__("Left")}: <strong>${to_flt(row.remaining_qty)}</strong></span>
					</div>
					<div class="wc-item-card-field"><label>${__("Claim Qty")}</label>
						<input type="number" min="0" class="wc-claim-qty" value="0" ${disabled}></div>
					${row.has_serial_no ? `<div class="wc-item-card-field"><label>${__("Serial")}</label><input type="text" class="wc-serial-no" value="${esc(row.serial_no)}" ${disabled}></div>` : `<input type="hidden" class="wc-serial-no" value="${esc(row.serial_no)}">`}
					<input type="hidden" class="wc-batch-no" value="${esc(row.batch_no)}">
				</div>`;
		},
		_claim_row(row, idx) {
			const disabled = row.fully_claimed ? "disabled" : "";
			return `<tr class="wc-item-row ${row.fully_claimed ? "done" : ""}" data-idx="${idx}">
				<td>${esc(row.item_name || row.item_code)}</td>
				<td class="num">${to_flt(row.sold_qty)}</td>
				<td class="num">${to_flt(row.remaining_qty)}</td>
				<td class="num"><input type="number" min="0" class="wc-claim-qty" value="0" ${disabled}></td>
				<td>${row.has_serial_no ? `<input type="text" class="wc-serial-no" value="${esc(row.serial_no)}" ${disabled}>` : "—"}</td>
			</tr>`;
		},
		render_settle_items(items) {
			const mobile = (items || []).map((row, idx) => this._settle_card(row, idx)).join("");
			const desktop = (items || []).map((row, idx) => this._settle_row(row, idx)).join("");
			$w.find(".wc-items-settle").html(`
				<div class="wc-mobile-items">${mobile || `<div class="wc-empty">${__("No items")}</div>`}</div>
				<div class="wc-desktop-table"><table class="wc-tbl"><thead><tr>
					<th>${__("Item")}</th><th class="num">${__("Claimed")}</th><th class="num">${__("Replaced")}</th>
					<th class="num">${__("Replace Qty")}</th>
				</tr></thead><tbody>${desktop}</tbody></table></div>
			`);
		},
		_settle_card(row, idx) {
			const can_replace = to_flt(row.claimed_qty) > 0;
			return `
				<div class="wc-item-card wc-item-row" data-idx="${idx}">
					<div class="wc-item-card-head">${esc(row.item_name || row.item_code)}</div>
					<div class="wc-item-card-meta">
						<span>${__("Claimed")}: <strong>${to_flt(row.claimed_qty)}</strong></span>
						<span>${__("Replaced")}: <strong>${to_flt(row.replaced_qty)}</strong></span>
					</div>
					<div class="wc-item-card-field"><label>${__("Replacement Qty")}</label>
						<input type="number" min="0" class="wc-replacement-qty" value="0" ${can_replace ? "" : "disabled"}></div>
					<input type="hidden" class="wc-transfer-qty" value="0">
					<input type="hidden" class="wc-serial-no" value="${esc(row.serial_no)}">
					<input type="hidden" class="wc-batch-no" value="${esc(row.batch_no)}">
					<input type="hidden" class="wc-replacement-item-code" value="${esc(row.item_code)}">
					<input type="hidden" class="wc-claim-qty" value="0">
				</div>`;
		},
		_settle_row(row, idx) {
			const can_replace = to_flt(row.claimed_qty) > 0;
			return `<tr class="wc-item-row" data-idx="${idx}"
				data-serial="${esc(row.serial_no)}" data-batch="${esc(row.batch_no)}" data-item="${esc(row.item_code)}">
				<td>${esc(row.item_name || row.item_code)}</td>
				<td class="num">${to_flt(row.claimed_qty)}</td>
				<td class="num">${to_flt(row.replaced_qty)}</td>
				<td class="num"><input type="number" min="0" class="wc-replacement-qty" value="0" ${can_replace ? "" : "disabled"}></td>
			</tr>`;
		},
		render_settle_state(data) {
			const claimed = to_flt(data.summary?.claimed_qty);
			const $alert = $w.find(".wc-settle-alert");
			if (claimed <= 0) {
				$alert.show().text(__("No submitted return yet. Complete Claim first and submit the return invoice, then come back here to settle."));
			} else {
				$alert.hide();
			}
			const fully_claimed = (data.items || []).every((r) => r.fully_claimed);
			const $claim_alert = $w.find(".wc-claim-alert");
			if (fully_claimed) {
				$claim_alert.show().text(__("All items on this invoice are fully claimed."));
			} else {
				$claim_alert.hide();
			}
		},
	};

	const ClaimValidator = {
		collect_claim_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const claim_qty = RowReader.read_number(idx, ".wc-claim-qty", "claim");
				if (claim_qty <= 0) return;
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					claim_qty,
					serial_no: RowReader.read_text(idx, ".wc-serial-no", "claim"),
					batch_no: RowReader.read_text(idx, ".wc-batch-no", "claim"),
				});
			});
			return items;
		},
		collect_transfer_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				let transfer_qty = RowReader.read_number(idx, ".wc-transfer-qty", "settle");
				if (transfer_qty <= 0) transfer_qty = to_flt(row.claimed_qty);
				if (transfer_qty <= 0) return;
				const $row = $w.find(`.wc-tab-settle .wc-item-row[data-idx="${idx}"]`).first();
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					uom: row.uom,
					transfer_qty,
					serial_no: RowReader.read_text(idx, ".wc-serial-no", "settle") || $row.data("serial") || row.serial_no,
					batch_no: RowReader.read_text(idx, ".wc-batch-no", "settle") || $row.data("batch") || row.batch_no,
				});
			});
			return items;
		},
		collect_replacement_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const replacement_qty = RowReader.read_number(idx, ".wc-replacement-qty", "settle");
				if (replacement_qty <= 0) return;
				const $row = $w.find(`.wc-tab-settle .wc-item-row[data-idx="${idx}"]`).first();
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					replacement_item_code:
						RowReader.read_text(idx, ".wc-replacement-item-code", "settle") || $row.data("item") || row.item_code,
					replacement_qty,
				});
			});
			return items;
		},
		validate_claim_items(items) {
			if (!items.length) frappe.throw(__("Enter claim quantity for at least one item."));
		},
	};

	const SalesReturnGenerator = {
		async create() {
			const items = ClaimValidator.collect_claim_items();
			ClaimValidator.validate_claim_items(items);
			const receive_warehouse = controls.receive_wh.get_value();
			const product_condition = controls.condition.get_value();
			if (!receive_warehouse) frappe.throw(__("Receive Warehouse is mandatory."));
			if (!product_condition) frappe.throw(__("Product Condition is mandatory."));

			await frappe.confirm(__("Create draft return for {0} item(s)?", [items.length]), async () => {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_return",
					args: {
						sales_invoice: state.invoice.sales_invoice,
						items,
						receive_warehouse,
						product_condition,
						submit: 0,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice);
				frappe.msgprint({
					title: __("Draft Return Created"),
					indicator: "green",
					message: __("Return {0} saved. Submit it in Sales Invoice, then open the Settle tab.", [res.message.name]),
				});
				if (state.context.show_settle_tab) TabManager.switch_to("settle");
			});
		},
	};

	const StockTransferGenerator = {
		async create() {
			const items = ClaimValidator.collect_transfer_items();
			if (!items.length) frappe.throw(__("No claimed items available to transfer."));
			const source_warehouse = controls.source_wh.get_value();
			const target_warehouse = controls.target_wh.get_value();
			if (!source_warehouse || !target_warehouse) frappe.throw(__("Select source and target warehouse."));

			await frappe.confirm(__("Create stock transfer?"), async () => {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_stock_transfer",
					args: {
						sales_invoice: state.invoice.sales_invoice,
						items,
						source_warehouse,
						target_warehouse,
						submit: 0,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice);
				frappe.show_alert({ message: __("Stock Entry {0} created", [res.message.name]), indicator: "green" });
			});
		},
	};

	const DeliveryNoteGenerator = {
		async create() {
			const items = ClaimValidator.collect_replacement_items();
			if (!items.length) frappe.throw(__("Enter replacement quantity."));
			if (!(state.invoice?.items || []).some((r) => to_flt(r.claimed_qty) > 0)) {
				frappe.throw(__("Submit the return invoice first before issuing replacement."));
			}
			const replacement_warehouse = controls.replacement_wh.get_value();
			if (!replacement_warehouse) frappe.throw(__("Replacement Warehouse is mandatory."));

			await frappe.confirm(__("Issue replacement for {0} item(s)?", [items.length]), async () => {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_replacement",
					args: {
						sales_invoice: state.invoice.sales_invoice,
						items,
						replacement_warehouse,
						submit: 1,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice);
				frappe.show_alert({ message: __("Delivery Note {0} created", [res.message.name]), indicator: "green" });
			});
		},
	};

	const HistoryLoader = {
		render(history) {
			if (!history.length) {
				$w.find(".wc-history-list").html(`<div class="wc-empty">${__("No history yet.")}</div>`);
				return;
			}
			$w.find(".wc-history-list").html(
				history.map((row) => `
					<div class="wc-history-item">
						<a href="${frappe.utils.get_form_link(row.doctype, row.reference, true)}">${esc(row.reference)}</a>
						<span class="text-muted"> · ${esc(row.type)} · ${esc(frappe.datetime.str_to_user(row.date))}</span>
						<div>${esc(row.items || "")} · ${__("Qty")}: ${to_flt(row.qty)}</div>
					</div>`
				).join("")
			);
		},
	};

	async function setup_context() {
		const res = await frappe.call({
			method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.get_warranty_context",
		});
		TabManager.init(res.message || {});
		if (res.message?.default_receive_warehouse) {
			controls.receive_wh.set_value(res.message.default_receive_warehouse);
			controls.source_wh.set_value(res.message.default_receive_warehouse);
		}
	}

	$w.on("click", ".wc-tab", function () {
		TabManager.switch_to($(this).data("tab"));
	});

	controls.condition.$input.on("change", () => {
		const wh = state.context.condition_warehouses?.[controls.condition.get_value()];
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
		controls.invoice.set_value("");
		controls.barcode.set_value("");
		$w.find(".wc-invoice-panel, .wc-summary-panel").hide();
		if (!state.context.show_claim_tab && state.context.show_settle_tab) {
			$w.find(".wc-settle-only").show();
		}
	});

	$w.find(".wc-btn-return").on("click", () => SalesReturnGenerator.create());
	$w.find(".wc-btn-transfer").on("click", () => StockTransferGenerator.create());
	$w.find(".wc-btn-replacement").on("click", () => DeliveryNoteGenerator.create());

	controls.invoice.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search").trigger("click");
	});

	setup_context();
};
