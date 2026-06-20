frappe.pages["warranty"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Warranty"),
		single_column: true,
	});

	const state = { invoice: null, context: {}, active_tab: "claim" };

	if (!document.getElementById("wc-style")) {
		$("head").append(`<style id="wc-style">
.wc-wrap { padding:8px 0 32px; max-width:720px; margin:0 auto; }
.wc-hero { margin-bottom:16px; }
.wc-hero h2 { margin:0 0 4px; font-size:20px; font-weight:700; color:#0f172a; }
.wc-hero p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
.wc-tabs { display:flex; gap:6px; margin-bottom:16px; background:#f1f5f9; padding:4px; border-radius:12px; }
.wc-tab { flex:1; border:0; background:transparent; padding:10px 12px; border-radius:9px; font-size:13px; font-weight:600; color:#64748b; cursor:pointer; }
.wc-tab.active { background:#fff; color:#0f172a; box-shadow:0 1px 2px rgba(0,0,0,.06); }
.wc-tab[data-tab="claim"].active { color:#1d4ed8; }
.wc-tab[data-tab="settle"].active { color:#6d28d9; }
.wc-tab-sub { display:block; font-size:10px; font-weight:500; opacity:.8; margin-top:2px; }
.wc-tab-panel { display:none; }
.wc-tab-panel.active { display:block; }
.wc-search-box { background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:14px; margin-bottom:14px; }
.wc-search-box label.wc-label { display:block; font-size:11px; font-weight:600; color:#64748b; margin-bottom:8px; text-transform:uppercase; letter-spacing:.4px; }
.wc-search-row { display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end; }
.wc-field { flex:1 1 160px; min-width:0; }
.wc-btn-search { min-height:38px; padding:0 18px; border-radius:9px; font-weight:600; white-space:nowrap; }
.wc-result-card { background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; display:none; }
.wc-result-card.show { display:block; }
.wc-result-card.claim { border-left:4px solid #2563eb; }
.wc-result-card.settle { border-left:4px solid #7c3aed; }
.wc-result-head { display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #f1f5f9; }
.wc-result-title { font-size:16px; font-weight:700; color:#0f172a; margin:0; }
.wc-result-sub { font-size:12px; color:#64748b; margin-top:4px; }
.wc-pills { display:flex; flex-wrap:wrap; gap:6px; }
.wc-pill { font-size:11px; padding:4px 10px; border-radius:999px; background:#f1f5f9; color:#475569; font-weight:600; }
.wc-pill.blue { background:#dbeafe; color:#1d4ed8; }
.wc-pill.purple { background:#ede9fe; color:#6d28d9; }
.wc-pill.amber { background:#fef3c7; color:#b45309; }
.wc-pill.green { background:#d1fae5; color:#047857; }
.wc-item-list { display:flex; flex-direction:column; gap:10px; margin-bottom:14px; }
.wc-item { border:1px solid #e2e8f0; border-radius:12px; padding:12px 14px; background:#fafafa; }
.wc-item.done { opacity:.55; }
.wc-item-name { font-weight:600; font-size:14px; color:#111827; margin-bottom:6px; }
.wc-item-stats { display:flex; flex-wrap:wrap; gap:10px 16px; font-size:12px; color:#64748b; margin-bottom:10px; }
.wc-item-stats strong { color:#0f172a; }
.wc-item-input label { display:block; font-size:10px; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:4px; }
.wc-item-input input { width:100%; padding:10px 12px; border:1px solid #d1d5db; border-radius:9px; font-size:16px; box-sizing:border-box; }
.wc-item-input input:disabled { background:#f1f5f9; }
.wc-form-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px; }
.wc-hint { font-size:12px; color:#64748b; margin:0 0 12px; line-height:1.5; }
.wc-hint-box { background:#f8fafc; border:1px dashed #cbd5e1; border-radius:10px; padding:10px 12px; font-size:12px; color:#475569; margin-bottom:14px; line-height:1.5; }
.wc-btn-main { width:100%; min-height:46px; font-size:15px; font-weight:600; border-radius:11px; margin-top:4px; }
.wc-list-section { margin-top:6px; }
.wc-list-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.wc-list-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#94a3b8; }
.wc-list-count { font-size:11px; color:#94a3b8; }
.wc-list { border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; background:#fff; }
.wc-list-item { padding:12px 14px; border-bottom:1px solid #f1f5f9; cursor:pointer; display:flex; justify-content:space-between; align-items:center; gap:10px; }
.wc-list-item:last-child { border-bottom:0; }
.wc-list-item:hover { background:#f8fafc; }
.wc-list-item.selected { background:#eff6ff; }
.wc-list-item.settle:hover { background:#faf5ff; }
.wc-list-item.settle.selected { background:#f5f3ff; }
.wc-list-main strong { display:block; font-size:13px; color:#0f172a; }
.wc-list-main span { font-size:11px; color:#64748b; }
.wc-empty { text-align:center; padding:28px 14px; color:#94a3b8; font-size:13px; }
.wc-flow-steps { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; }
.wc-flow-step { flex:1; min-width:80px; text-align:center; padding:8px 6px; border-radius:8px; background:#f1f5f9; font-size:10px; font-weight:600; color:#94a3b8; }
.wc-flow-step.on { background:#ede9fe; color:#6d28d9; }
@media (max-width:600px) {
	.wc-wrap { padding:6px 10px 28px; }
	.wc-form-grid { grid-template-columns:1fr; }
	.wc-search-row { flex-direction:column; }
	.wc-btn-search { width:100%; }
}
</style>`);
	}

	const $w = $(`
		<div class="wc-wrap">
			<div class="wc-hero">
				<h2>${__("Warranty")}</h2>
				<p>${__("Field team registers claim qty. Office team completes everything in one step.")}</p>
			</div>

			<div class="wc-tabs wc-tab-switcher" style="display:none;">
				<button type="button" class="wc-tab active" data-tab="claim">
					${__("Claim")}
					<span class="wc-tab-sub">${__("Register qty")}</span>
				</button>
				<button type="button" class="wc-tab" data-tab="settle">
					${__("Settle")}
					<span class="wc-tab-sub">${__("Complete")}</span>
				</button>
			</div>

			<div class="wc-tab-panel wc-tab-claim active">
				<div class="wc-search-box">
					<label class="wc-label">${__("Find invoice")}</label>
					<div class="wc-search-row">
						<div class="wc-field wc-f-invoice-claim"></div>
						<div class="wc-field wc-f-barcode-claim"></div>
						<button class="btn btn-primary wc-btn-search wc-btn-search-claim">${__("Search")}</button>
					</div>
				</div>

				<div class="wc-result-card claim wc-claim-result">
					<div class="wc-result-head">
						<div>
							<div class="wc-result-title wc-claim-invoice-title">—</div>
							<div class="wc-result-sub wc-claim-invoice-sub"></div>
						</div>
						<div class="wc-pills wc-claim-pills"></div>
					</div>
					<div class="wc-item-list wc-items-claim"></div>
					<button class="btn btn-primary wc-btn-main wc-btn-return">${__("Register Claim")}</button>
					<p class="wc-hint" style="margin-top:10px;margin-bottom:0;">${__("Only enter how many items the customer is claiming. Office will handle the rest.")}</p>
				</div>

				<div class="wc-list-section">
					<div class="wc-list-head">
						<span class="wc-list-title">${__("Your claims")}</span>
						<span class="wc-list-count wc-claim-queue-count"></span>
					</div>
					<div class="wc-list wc-claim-queue"><div class="wc-empty">${__("Loading...")}</div></div>
				</div>
			</div>

			<div class="wc-tab-panel wc-tab-settle">
				<div class="wc-search-box">
					<label class="wc-label">${__("Find invoice to settle")}</label>
					<div class="wc-search-row">
						<div class="wc-field wc-f-invoice-settle"></div>
						<button class="btn btn-primary wc-btn-search wc-btn-search-settle">${__("Search")}</button>
					</div>
				</div>

				<div class="wc-result-card settle wc-settle-result">
					<div class="wc-result-head">
						<div>
							<div class="wc-result-title wc-settle-invoice-title">—</div>
							<div class="wc-result-sub wc-settle-invoice-sub"></div>
						</div>
						<div class="wc-pills wc-settle-pills"></div>
					</div>

					<div class="wc-flow-steps wc-settle-flow" style="display:none;">
						<div class="wc-flow-step">${__("Receive")}</div>
						<div class="wc-flow-step">${__("Transfer")}</div>
						<div class="wc-flow-step">${__("Replace")}</div>
					</div>

					<div class="wc-hint-box wc-settle-hint"></div>

					<div class="wc-settle-fields">
						<div class="wc-form-grid">
							<div class="wc-field wc-f-receive-wh wc-settle-wh-receive"></div>
							<div class="wc-field wc-f-condition wc-settle-wh-condition"></div>
							<div class="wc-field wc-f-target-wh wc-settle-wh-target"></div>
							<div class="wc-field wc-f-replacement-wh wc-settle-wh-replace"></div>
						</div>
					</div>

					<div class="wc-item-list wc-items-settle"></div>

					<button class="btn btn-primary wc-btn-main wc-btn-settle-complete">${__("Complete Settlement")}</button>
					<p class="wc-hint" style="margin-top:10px;margin-bottom:0;">${__("One click: receive stock, move to correct warehouse, and give replacement to customer.")}</p>
				</div>

				<div class="wc-list-section">
					<div class="wc-list-head">
						<span class="wc-list-title">${__("Waiting to settle")}</span>
						<span class="wc-list-count wc-settle-queue-count"></span>
					</div>
					<div class="wc-list wc-settle-queue"><div class="wc-empty">${__("Loading...")}</div></div>
				</div>
			</div>
		</div>
	`);

	page.main.append($w);

	const controls = {};
	const make_control = (parent, df) =>
		frappe.ui.form.make_control({ parent: $w.find(parent), df, render_input: true });

	controls.invoice_claim = make_control(".wc-f-invoice-claim", {
		fieldname: "invoice_no",
		label: __("Invoice No"),
		fieldtype: "Data",
		placeholder: __("e.g. SINV-00001"),
	});
	controls.barcode_claim = make_control(".wc-f-barcode-claim", {
		fieldname: "barcode",
		label: __("Barcode / Serial"),
		fieldtype: "Data",
		placeholder: __("Optional"),
	});
	controls.invoice_settle = make_control(".wc-f-invoice-settle", {
		fieldname: "invoice_no",
		label: __("Invoice No"),
		fieldtype: "Data",
		placeholder: __("e.g. SINV-00001"),
	});
	controls.receive_wh = make_control(".wc-f-receive-wh", {
		fieldname: "receive_warehouse",
		label: __("Receive warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
		reqd: 1,
	});
	controls.condition = make_control(".wc-f-condition", {
		fieldname: "product_condition",
		label: __("Product condition"),
		fieldtype: "Select",
		options: "\nDamaged\nSellable\nRepairable",
		reqd: 1,
	});
	controls.target_wh = make_control(".wc-f-target-wh", {
		fieldname: "target_warehouse",
		label: __("Move to warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
		reqd: 1,
	});
	controls.replacement_wh = make_control(".wc-f-replacement-wh", {
		fieldname: "replacement_warehouse",
		label: __("Replacement from warehouse"),
		fieldtype: "Link",
		options: "Warehouse",
		reqd: 1,
	});

	const WarehouseHelper = {
		bind_company(company) {
			const filters = company ? { company, is_group: 0 } : { is_group: 0 };
			["receive_wh", "target_wh", "replacement_wh"].forEach((key) => {
				controls[key].get_query = () => ({ filters });
			});
		},
		show_fields(mode) {
			const is_full = mode === "full";
			$w.find(".wc-settle-wh-receive, .wc-settle-wh-condition, .wc-settle-wh-target").toggle(is_full);
			$w.find(".wc-settle-fields").show();
		},
	};

	const esc = (v) => frappe.utils.escape_html(String(v ?? ""));
	const to_flt = (v) => flt(v);

	const RowReader = {
		scope(tab) {
			return tab ? $w.find(`.wc-tab-${tab}`) : $w;
		},
		read_number(idx, selector, tab = null) {
			let value = 0;
			this.scope(tab).find(`.wc-item-row[data-idx="${idx}"]`).each(function () {
				const val = to_flt($(this).find(selector).val());
				if (val > value) value = val;
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
			if (!show_claim_tab) $w.find(".wc-tab-claim").remove();
			if (!show_settle_tab) $w.find(".wc-tab-settle").remove();
			if (show_tab_switcher) {
				$w.find(".wc-tab-switcher").show();
				$w.find('.wc-tab[data-tab="claim"]').toggle(show_claim_tab);
				$w.find('.wc-tab[data-tab="settle"]').toggle(show_settle_tab);
			}
			this.switch_to(default_tab || "claim");
		},
		switch_to(tab) {
			if (tab === "claim" && !state.context.show_claim_tab) tab = "settle";
			if (tab === "settle" && !state.context.show_settle_tab) tab = "claim";
			state.active_tab = tab;
			$w.find(".wc-tab").removeClass("active");
			$w.find(`.wc-tab[data-tab="${tab}"]`).addClass("active");
			$w.find(".wc-tab-panel").removeClass("active").hide();
			$w.find(`.wc-tab-${tab}`).addClass("active").show();
			if (tab === "claim") QueueLoader.load_claim_queue();
			if (tab === "settle") QueueLoader.load_settle_queue();
		},
	};

	const QueueLoader = {
		async load_claim_queue() {
			if (!state.context.show_claim_tab) return;
			try {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.get_claim_queue",
				});
				this.render_claim_queue(res.message || {});
			} catch (e) {
				console.error(e);
			}
		},
		render_claim_queue(data) {
			const rows = data.rows || [];
			$w.find(".wc-claim-queue-count").text(rows.length ? `${rows.length}` : "");
			if (!rows.length) {
				$w.find(".wc-claim-queue").html(`<div class="wc-empty">${__("No claims yet")}</div>`);
				return;
			}
			$w.find(".wc-claim-queue").html(rows.map((row) => `
				<div class="wc-list-item ${state.invoice?.sales_invoice === row.sales_invoice ? "selected" : ""}"
					data-sales-invoice="${esc(row.sales_invoice)}">
					<div class="wc-list-main">
						<strong>${esc(row.sales_invoice)}</strong>
						<span>${esc(row.customer_name || row.customer)} · ${__("Qty")} ${to_flt(row.claimed_qty)}</span>
					</div>
					<span class="wc-pill ${row.status_key === "registered" ? "amber" : "green"}">${esc(row.status)}</span>
				</div>
			`).join(""));
		},
		async load_settle_queue() {
			if (!state.context.show_settle_tab) return;
			try {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.get_settle_queue",
				});
				this.render_settle_queue(res.message || {});
			} catch (e) {
				console.error(e);
			}
		},
		render_settle_queue(data) {
			const rows = data.rows || [];
			$w.find(".wc-settle-queue-count").text(rows.length ? `${rows.length}` : "");
			if (!rows.length) {
				$w.find(".wc-settle-queue").html(`<div class="wc-empty">${__("Nothing waiting")}</div>`);
				return;
			}
			$w.find(".wc-settle-queue").html(rows.map((row) => `
				<div class="wc-list-item settle ${state.invoice?.sales_invoice === row.sales_invoice ? "selected" : ""}"
					data-sales-invoice="${esc(row.sales_invoice)}">
					<div class="wc-list-main">
						<strong>${esc(row.sales_invoice)}</strong>
						<span>${esc(row.customer_name || row.customer)} · ${__("Qty")} ${to_flt(row.claimed_qty)}</span>
					</div>
					<span class="wc-pill ${row.status_key === "awaiting_receive" ? "amber" : "purple"}">${esc(row.status)}</span>
				</div>
			`).join(""));
		},
	};

	const InvoiceLoader = {
		async load(search = {}, mode = "claim") {
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.search_sales_invoice",
				args: search,
			});
			state.invoice = res.message;
			this.render(state.invoice, mode);
			return state.invoice;
		},
		async load_by_name(sales_invoice, mode = "settle") {
			const res = await frappe.call({
				method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.load_sales_invoice",
				args: { sales_invoice },
			});
			state.invoice = res.message;
			this.render(state.invoice, mode);
			if (mode === "settle") controls.invoice_settle.set_value(sales_invoice);
			if (mode === "claim") controls.invoice_claim.set_value(sales_invoice);
			return state.invoice;
		},
		render(data, mode) {
			if (mode === "claim") this.render_claim(data);
			if (mode === "settle") this.render_settle(data);
			QueueLoader.load_claim_queue();
			QueueLoader.load_settle_queue();
		},
		render_claim(data) {
			$w.find(".wc-claim-result").addClass("show");
			$w.find(".wc-claim-invoice-title").text(data.sales_invoice);
			$w.find(".wc-claim-invoice-sub").text(
				`${data.customer_name || data.customer} · ${frappe.datetime.str_to_user(data.posting_date)}`
			);
			const s = data.summary || {};
			$w.find(".wc-claim-pills").html(`
				<span class="wc-pill blue">${__("Left to claim")}: ${to_flt(s.pending_qty)}</span>
				${to_flt(s.registered_qty) ? `<span class="wc-pill amber">${__("Registered")}: ${to_flt(s.registered_qty)}</span>` : ""}
			`);
			$w.find(".wc-items-claim").html((data.items || []).map((row, idx) => {
				if (row.fully_claimed) {
					return `<div class="wc-item done wc-item-row" data-idx="${idx}">
						<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
						<div class="wc-item-stats"><span>${__("Fully claimed")}</span></div>
					</div>`;
				}
				return `<div class="wc-item wc-item-row" data-idx="${idx}">
					<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
					<div class="wc-item-stats">
						<span>${__("Sold")}: <strong>${to_flt(row.sold_qty)}</strong></span>
						<span>${__("Can claim")}: <strong>${to_flt(row.remaining_qty)}</strong></span>
					</div>
					<div class="wc-item-input">
						<label>${__("Claim qty")}</label>
						<input type="number" min="0" class="wc-claim-qty" value="0">
					</div>
					${row.has_serial_no ? `<div class="wc-item-input" style="margin-top:8px;"><label>${__("Serial")}</label><input type="text" class="wc-serial-no" value="${esc(row.serial_no)}"></div>` : `<input type="hidden" class="wc-serial-no" value="${esc(row.serial_no)}">`}
					<input type="hidden" class="wc-batch-no" value="${esc(row.batch_no)}">
				</div>`;
			}).join("") || `<div class="wc-empty">${__("No items")}</div>`);
		},
		render_settle(data) {
			$w.find(".wc-settle-result").addClass("show");
			$w.find(".wc-settle-invoice-title").text(data.sales_invoice);
			$w.find(".wc-settle-invoice-sub").text(
				`${data.customer_name || data.customer} · ${frappe.datetime.str_to_user(data.posting_date)}`
			);

			const mode = data.settle_mode || "none";
			const s = data.summary || {};
			$w.find(".wc-settle-pills").html(`
				<span class="wc-pill purple">${esc(s.status || "—")}</span>
				${to_flt(s.registered_qty) ? `<span class="wc-pill amber">${__("To receive")}: ${to_flt(s.registered_qty)}</span>` : ""}
				${to_flt(s.claimed_qty) ? `<span class="wc-pill blue">${__("Received")}: ${to_flt(s.claimed_qty)}</span>` : ""}
			`);

			const $flow = $w.find(".wc-settle-flow");
			const $hint = $w.find(".wc-settle-hint");
			const $btn = $w.find(".wc-btn-settle-complete");

			WarehouseHelper.bind_company(data.company);

			if (mode === "none") {
				$flow.hide();
				$w.find(".wc-settle-fields").hide();
				$btn.prop("disabled", true);
				$hint.text(__("No claim on this invoice. Pick one from the list below or search another."));
				$w.find(".wc-items-settle").empty();
				return;
			}

			$btn.prop("disabled", false);
			WarehouseHelper.show_fields(mode);

			if (mode === "full") {
				$flow.show().find(".wc-flow-step").addClass("on");
				$hint.text(__("Choose all warehouses from the dropdowns below, then tap Complete."));
			} else {
				$flow.show().find(".wc-flow-step").removeClass("on").last().addClass("on");
				$hint.text(__("Choose replacement warehouse and qty, then tap Complete."));
			}

			$w.find(".wc-items-settle").html((data.items || []).map((row, idx) => {
				const pending = to_flt(row.pending_settle_qty);
				if (pending <= 0) return "";
				return `<div class="wc-item wc-item-row" data-idx="${idx}"
					data-item="${esc(row.item_code)}" data-serial="${esc(row.serial_no)}" data-batch="${esc(row.batch_no)}">
					<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
					<div class="wc-item-stats">
						<span>${__("Claim qty")}: <strong>${to_flt(row.registered_qty) || to_flt(row.claimed_qty)}</strong></span>
						${to_flt(row.replaced_qty) ? `<span>${__("Already replaced")}: <strong>${to_flt(row.replaced_qty)}</strong></span>` : ""}
					</div>
					<div class="wc-item-input">
						<label>${__("Replacement qty")}</label>
						<input type="number" min="0" class="wc-replacement-qty" value="${pending}">
					</div>
					<input type="hidden" class="wc-replacement-item-code" value="${esc(row.item_code)}">
				</div>`;
			}).filter(Boolean).join("") || `<div class="wc-empty">${__("Nothing to settle on this invoice")}</div>`);
		},
	};

	const ClaimActions = {
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
		async register() {
			const items = this.collect_claim_items();
			if (!items.length) frappe.throw(__("Enter claim quantity for at least one item."));
			await frappe.confirm(__("Register claim for {0} item(s)?", [items.length]), async () => {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.create_warranty_return",
					args: { sales_invoice: state.invoice.sales_invoice, items },
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "claim");
				frappe.show_alert({ message: __("Claim registered"), indicator: "green" });
			});
		},
	};

	const SettleActions = {
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
		async complete() {
			if (!state.invoice?.sales_invoice) frappe.throw(__("Search an invoice first."));
			const items = this.collect_replacement_items();
			if (!items.length) frappe.throw(__("Enter replacement quantity."));
			const replacement_warehouse = controls.replacement_wh.get_value();
			if (!replacement_warehouse) frappe.throw(__("Select replacement warehouse."));

			const mode = state.invoice.settle_mode;
			const args = {
				sales_invoice: state.invoice.sales_invoice,
				return_invoice: state.invoice.pending_return_invoice || null,
				replacement_warehouse,
				items,
			};

			if (mode === "full") {
				args.receive_warehouse = controls.receive_wh.get_value();
				args.product_condition = controls.condition.get_value();
				args.target_warehouse = controls.target_wh.get_value();
				if (!args.receive_warehouse) frappe.throw(__("Select receive warehouse."));
				if (!args.product_condition) frappe.throw(__("Select product condition."));
				if (!args.target_warehouse) frappe.throw(__("Select move to warehouse."));
			}

			const msg = mode === "full"
				? __("Complete settlement? This will receive stock, transfer by condition, and issue replacement.")
				: __("Issue replacement to customer?");

			await frappe.confirm(msg, async () => {
				const res = await frappe.call({
					method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.settle_warranty_claim",
					args,
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "settle");
				frappe.show_alert({ message: __("Settlement complete"), indicator: "green" });
			});
		},
	};

	async function setup_context() {
		const res = await frappe.call({
			method: "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty.get_warranty_context",
		});
		state.context = res.message || {};
		TabManager.init(state.context);
	}

	$w.on("click", ".wc-tab", function () {
		TabManager.switch_to($(this).data("tab"));
	});

	$w.find(".wc-btn-search-claim").on("click", async () => {
		try {
			await InvoiceLoader.load({
				invoice_no: controls.invoice_claim.get_value(),
				barcode: controls.barcode_claim.get_value(),
			}, "claim");
		} catch (e) {
			console.error(e);
		}
	});

	$w.find(".wc-btn-search-settle").on("click", async () => {
		try {
			await InvoiceLoader.load({
				invoice_no: controls.invoice_settle.get_value(),
			}, "settle");
		} catch (e) {
			console.error(e);
		}
	});

	$w.on("click", ".wc-claim-queue .wc-list-item", async function () {
		const sales_invoice = $(this).data("sales-invoice");
		if (!sales_invoice) return;
		try {
			await InvoiceLoader.load_by_name(sales_invoice, "claim");
		} catch (e) {
			console.error(e);
		}
	});

	$w.on("click", ".wc-settle-queue .wc-list-item", async function () {
		const sales_invoice = $(this).data("sales-invoice");
		if (!sales_invoice) return;
		try {
			await InvoiceLoader.load_by_name(sales_invoice, "settle");
		} catch (e) {
			console.error(e);
		}
	});

	$w.find(".wc-btn-return").on("click", () => ClaimActions.register());
	$w.find(".wc-btn-settle-complete").on("click", () => SettleActions.complete());

	controls.invoice_claim.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search-claim").trigger("click");
	});
	controls.invoice_settle.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search-settle").trigger("click");
	});

	setup_context();
};
