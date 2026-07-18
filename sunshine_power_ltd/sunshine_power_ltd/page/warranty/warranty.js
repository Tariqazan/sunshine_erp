frappe.pages["warranty"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Warranty"),
		single_column: true,
	});

	const M = "sunshine_power_ltd.sunshine_power_ltd.page.warranty.warranty";
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
.wc-flow-step { flex:1; min-width:70px; text-align:center; padding:8px 6px; border-radius:8px; background:#f1f5f9; font-size:10px; font-weight:600; color:#94a3b8; }
.wc-flow-step.on { background:#ede9fe; color:#6d28d9; }
.wc-flow-step.done { background:#d1fae5; color:#047857; }
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
				<p>${__("Field team raises and hands over claims. Factory receives and prepares replacements.")}</p>
			</div>

			<div class="wc-tabs wc-tab-switcher" style="display:none;">
				<button type="button" class="wc-tab active" data-tab="claim">
					${__("Claim")}
					<span class="wc-tab-sub">${__("Request & hand over")}</span>
				</button>
				<button type="button" class="wc-tab" data-tab="settle">
					${__("Factory")}
					<span class="wc-tab-sub">${__("Receive & prepare")}</span>
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

					<div class="wc-flow-steps wc-claim-flow" style="display:none;">
						<div class="wc-flow-step" data-step="1">${__("Request")}</div>
						<div class="wc-flow-step" data-step="2">${__("Receive")}</div>
						<div class="wc-flow-step" data-step="3">${__("Prepare")}</div>
						<div class="wc-flow-step" data-step="4">${__("Hand over")}</div>
					</div>

					<div class="wc-hint-box wc-claim-hint" style="display:none;"></div>
					<div class="wc-item-list wc-items-claim"></div>

					<button class="btn btn-primary wc-btn-main wc-btn-register">${__("Register Claim")}</button>
					<button class="btn btn-primary wc-btn-main wc-btn-handover" style="display:none;">${__("Confirm Customer Received")}</button>
					<p class="wc-hint wc-claim-foot" style="margin-top:10px;margin-bottom:0;">${__("Enter how many items the customer is claiming. Factory will handle the rest.")}</p>
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
					<label class="wc-label">${__("Find invoice to process")}</label>
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
						<div class="wc-flow-step" data-step="1">${__("Request")}</div>
						<div class="wc-flow-step" data-step="2">${__("Receive")}</div>
						<div class="wc-flow-step" data-step="3">${__("Prepare")}</div>
						<div class="wc-flow-step" data-step="4">${__("Hand over")}</div>
					</div>

					<div class="wc-hint-box wc-settle-hint"></div>

					<div class="wc-settle-receive-fields" style="display:none;">
						<div class="wc-form-grid">
							<div class="wc-field wc-f-condition"></div>
							<div class="wc-field wc-f-condition-wh"></div>
						</div>
					</div>

					<div class="wc-settle-prepare-fields" style="display:none;">
						<div class="wc-form-grid">
							<div class="wc-field wc-f-replacement-wh"></div>
						</div>
					</div>

					<div class="wc-item-list wc-items-settle"></div>

					<button class="btn btn-primary wc-btn-main wc-btn-receive" style="display:none;">${__("Confirm Receipt")}</button>
					<button class="btn btn-primary wc-btn-main wc-btn-prepare" style="display:none;">${__("Prepare Replacement")}</button>
					<p class="wc-hint wc-settle-foot" style="margin-top:10px;margin-bottom:0;"></p>
				</div>

				<div class="wc-list-section">
					<div class="wc-list-head">
						<span class="wc-list-title">${__("Waiting for factory")}</span>
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
	controls.condition = make_control(".wc-f-condition", {
		fieldname: "product_condition",
		label: __("Product condition"),
		fieldtype: "Select",
		options: "\nDamaged\nSellable\nRepairable",
	});
	controls.condition_wh = make_control(".wc-f-condition-wh", {
		fieldname: "condition_warehouse",
		label: __("Receive into warehouse"),
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
			["condition_wh", "replacement_wh"].forEach((key) => {
				controls[key].get_query = () => ({ filters });
			});
		},
		default_warehouse(data) {
			const item = (data.items || []).find((row) => row.warehouse);
			return item ? item.warehouse : null;
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

	const FlowSteps = {
		// active = the step the claim is waiting on (1..4); steps before it are done.
		render($flow, active) {
			$flow.show().find(".wc-flow-step").each(function () {
				const step = parseInt($(this).data("step"), 10);
				$(this).removeClass("on done");
				if (step < active) $(this).addClass("done");
				else if (step === active) $(this).addClass("on");
			});
		},
		step_for(status) {
			return { Requested: 2, Received: 3, Ready: 4, Completed: 4 }[status] || 1;
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
				const res = await frappe.call({ method: `${M}.get_claim_queue` });
				this.render_queue(res.message || {}, "claim");
			} catch (e) {
				console.error(e);
			}
		},
		async load_settle_queue() {
			if (!state.context.show_settle_tab) return;
			try {
				const res = await frappe.call({ method: `${M}.get_settle_queue` });
				this.render_queue(res.message || {}, "settle");
			} catch (e) {
				console.error(e);
			}
		},
		render_queue(data, tab) {
			const rows = data.rows || [];
			const empty = tab === "claim" ? __("No claims yet") : __("Nothing waiting");
			$w.find(`.wc-${tab}-queue-count`).text(rows.length ? `${rows.length}` : "");
			if (!rows.length) {
				$w.find(`.wc-${tab}-queue`).html(`<div class="wc-empty">${empty}</div>`);
				return;
			}
			const pill_class = (key) => {
				if (key === "ready" || key === "prepare") return "purple";
				if (key === "completed") return "green";
				return "amber";
			};
			$w.find(`.wc-${tab}-queue`).html(rows.map((row) => `
				<div class="wc-list-item ${tab === "settle" ? "settle " : ""}${state.invoice?.sales_invoice === row.sales_invoice ? "selected" : ""}"
					data-sales-invoice="${esc(row.sales_invoice)}">
					<div class="wc-list-main">
						<strong>${esc(row.sales_invoice)}</strong>
						<span>${esc(row.customer_name || row.customer)} · ${__("Qty")} ${to_flt(row.claimed_qty)}</span>
					</div>
					<span class="wc-pill ${pill_class(row.status_key)}">${esc(row.status)}</span>
				</div>
			`).join(""));
		},
	};

	const InvoiceLoader = {
		async load(search = {}, mode = "claim") {
			const res = await frappe.call({ method: `${M}.search_sales_invoice`, args: search });
			state.invoice = res.message;
			this.render(state.invoice, mode);
			return state.invoice;
		},
		async load_by_name(sales_invoice, mode = "claim") {
			const res = await frappe.call({ method: `${M}.load_sales_invoice`, args: { sales_invoice } });
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
		render_head(prefix, data) {
			$w.find(`.wc-${prefix}-result`).addClass("show");
			$w.find(`.wc-${prefix}-invoice-title`).text(data.sales_invoice);
			$w.find(`.wc-${prefix}-invoice-sub`).text(
				`${data.customer_name || data.customer} · ${frappe.datetime.str_to_user(data.posting_date)}`
			);
		},
		status_pill(status) {
			const cls = { Requested: "amber", Received: "blue", Ready: "purple", Completed: "green" }[status] || "";
			return status ? `<span class="wc-pill ${cls}">${esc(status)}</span>` : "";
		},

		render_claim(data) {
			this.render_head("claim", data);
			const status = data.claim_status || "";
			const s = data.summary || {};

			$w.find(".wc-claim-pills").html(`
				${this.status_pill(status)}
				${to_flt(s.pending_qty) ? `<span class="wc-pill blue">${__("Left to claim")}: ${to_flt(s.pending_qty)}</span>` : ""}
			`);

			const $flow = $w.find(".wc-claim-flow");
			const $hint = $w.find(".wc-claim-hint");
			const $btnRegister = $w.find(".wc-btn-register");
			const $btnHandover = $w.find(".wc-btn-handover");
			const $foot = $w.find(".wc-claim-foot");
			$btnRegister.hide();
			$btnHandover.hide();
			$hint.hide();

			if (status === "Ready") {
				// Step 4 — salesman hands the replacement to the customer.
				FlowSteps.render($flow, 4);
				$hint.show().text(__("Factory has prepared the replacement. Confirm the customer has received it."));
				$w.find(".wc-items-claim").html((data.items || []).map((row, idx) => {
					if (to_flt(row.prepared_qty) <= 0) return "";
					return `<div class="wc-item wc-item-row" data-idx="${idx}">
						<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
						<div class="wc-item-stats">
							<span>${__("Replacement ready")}: <strong>${to_flt(row.prepared_qty)}</strong></span>
						</div>
					</div>`;
				}).filter(Boolean).join("") || `<div class="wc-empty">${__("Nothing to hand over")}</div>`);
				$btnHandover.show();
				$foot.text(__("Tapping confirm submits the replacement delivery note."));
				return;
			}

			if (status === "Requested" || status === "Received") {
				// Claim is open and with the factory — read-only for the salesman.
				FlowSteps.render($flow, FlowSteps.step_for(status));
				$hint.show().text(
					status === "Requested"
						? __("Claim registered. Factory will receive the product next.")
						: __("Factory has received the product and is preparing the replacement.")
				);
				$w.find(".wc-items-claim").html((data.items || []).map((row) => {
					if (to_flt(row.requested_qty) <= 0) return "";
					return `<div class="wc-item done">
						<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
						<div class="wc-item-stats"><span>${__("Claimed")}: <strong>${to_flt(row.requested_qty)}</strong></span></div>
					</div>`;
				}).filter(Boolean).join(""));
				$foot.text(__("This claim is being handled by the factory team."));
				return;
			}

			// No open claim — register a new one (step 1).
			$flow.hide();
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
			$btnRegister.show();
			$foot.text(__("Enter how many items the customer is claiming. Factory will handle the rest."));
		},

		render_settle(data) {
			this.render_head("settle", data);
			const status = data.claim_status || "";
			const action = data.action || "none";

			$w.find(".wc-settle-pills").html(`
				${this.status_pill(status)}
				${to_flt((data.summary || {}).requested_qty) ? `<span class="wc-pill amber">${__("Claimed")}: ${to_flt(data.summary.requested_qty)}</span>` : ""}
			`);

			WarehouseHelper.bind_company(data.company);
			const default_wh = WarehouseHelper.default_warehouse(data);

			const $flow = $w.find(".wc-settle-flow");
			const $hint = $w.find(".wc-settle-hint");
			const $foot = $w.find(".wc-settle-foot");
			const $receiveFields = $w.find(".wc-settle-receive-fields");
			const $prepareFields = $w.find(".wc-settle-prepare-fields");
			const $btnReceive = $w.find(".wc-btn-receive");
			const $btnPrepare = $w.find(".wc-btn-prepare");

			$receiveFields.hide();
			$prepareFields.hide();
			$btnReceive.hide();
			$btnPrepare.hide();

			if (action === "receive") {
				FlowSteps.render($flow, 2);
				$hint.text(__("Confirm the product is in hand, pick its condition and the warehouse to receive it into."));
				$receiveFields.show();
				if (default_wh && !controls.condition_wh.get_value()) controls.condition_wh.set_value(default_wh);
				$w.find(".wc-items-settle").html((data.items || []).map((row) => {
					if (to_flt(row.requested_qty) <= 0) return "";
					return `<div class="wc-item">
						<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
						<div class="wc-item-stats"><span>${__("Claimed qty")}: <strong>${to_flt(row.requested_qty)}</strong></span></div>
					</div>`;
				}).filter(Boolean).join("") || `<div class="wc-empty">${__("Nothing to receive")}</div>`);
				$btnReceive.show();
				$foot.text(__("This books a Material Receipt into the condition warehouse."));
				return;
			}

			if (action === "prepare") {
				FlowSteps.render($flow, 3);
				$hint.text(__("Choose the replacement warehouse and quantity, then prepare the delivery note."));
				$prepareFields.show();
				if (default_wh && !controls.replacement_wh.get_value()) controls.replacement_wh.set_value(default_wh);
				$w.find(".wc-items-settle").html((data.items || []).map((row, idx) => {
					const pending = to_flt(row.pending_prepare_qty);
					if (pending <= 0) return "";
					return `<div class="wc-item wc-item-row" data-idx="${idx}"
						data-item="${esc(row.item_code)}">
						<div class="wc-item-name">${esc(row.item_name || row.item_code)}</div>
						<div class="wc-item-stats">
							<span>${__("Claimed qty")}: <strong>${to_flt(row.requested_qty)}</strong></span>
							<span>${__("In stock")}: <strong>${to_flt(row.received_qty)}</strong></span>
						</div>
						<div class="wc-item-input">
							<label>${__("Replacement qty")}</label>
							<input type="number" min="0" class="wc-replacement-qty" value="${pending}">
						</div>
						<input type="hidden" class="wc-replacement-item-code" value="${esc(row.item_code)}">
					</div>`;
				}).filter(Boolean).join("") || `<div class="wc-empty">${__("Nothing to prepare")}</div>`);
				$btnPrepare.show();
				$foot.text(__("This drafts the replacement delivery note. The salesman submits it on hand-over."));
				return;
			}

			// Ready (with salesman) or Completed / no claim — nothing for factory to do.
			FlowSteps.render($flow, status === "Completed" ? 4 : FlowSteps.step_for(status));
			$w.find(".wc-items-settle").empty();
			if (status === "Ready") {
				$hint.text(__("Replacement is prepared and waiting for the salesman to hand it over."));
				$foot.text("");
			} else if (status === "Completed") {
				$hint.text(__("This claim is complete."));
				$foot.text("");
			} else {
				$flow.hide();
				$hint.text(__("No open claim on this invoice. Pick one from the list below or search another."));
				$foot.text("");
			}
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
					method: `${M}.create_warranty_return`,
					args: { sales_invoice: state.invoice.sales_invoice, items },
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "claim");
				frappe.show_alert({ message: __("Claim registered"), indicator: "green" });
			});
		},
		async handover() {
			if (!state.invoice?.pending_delivery_note) frappe.throw(__("Nothing is ready to hand over."));
			await frappe.confirm(__("Confirm the customer has received the replacement?"), async () => {
				const res = await frappe.call({
					method: `${M}.handover_warranty_replacement`,
					args: {
						sales_invoice: state.invoice.sales_invoice,
						delivery_note: state.invoice.pending_delivery_note,
						return_invoice: state.invoice.pending_return_invoice,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "claim");
				frappe.show_alert({ message: __("Handed over — claim completed"), indicator: "green" });
			});
		},
	};

	const SettleActions = {
		async receive() {
			if (!state.invoice?.sales_invoice) frappe.throw(__("Search an invoice first."));
			const product_condition = controls.condition.get_value();
			const condition_warehouse = controls.condition_wh.get_value();
			if (!condition_warehouse) frappe.throw(__("Select the warehouse to receive into."));

			await frappe.confirm(__("Receive the claimed product into stock?"), async () => {
				const res = await frappe.call({
					method: `${M}.receive_warranty_claim`,
					args: {
						sales_invoice: state.invoice.sales_invoice,
						return_invoice: state.invoice.pending_return_invoice,
						condition_warehouse,
						product_condition,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "settle");
				frappe.show_alert({ message: __("Received into stock"), indicator: "green" });
			});
		},
		collect_replacement_items() {
			const items = [];
			(state.invoice?.items || []).forEach((row, idx) => {
				const replacement_qty = RowReader.read_number(idx, ".wc-replacement-qty", "settle");
				if (replacement_qty <= 0) return;
				items.push({
					sales_invoice_item: row.sales_invoice_item,
					item_code: row.item_code,
					replacement_item_code:
						RowReader.read_text(idx, ".wc-replacement-item-code", "settle") || row.item_code,
					replacement_qty,
				});
			});
			return items;
		},
		async prepare() {
			if (!state.invoice?.sales_invoice) frappe.throw(__("Search an invoice first."));
			const items = this.collect_replacement_items();
			if (!items.length) frappe.throw(__("Enter replacement quantity."));
			const replacement_warehouse = controls.replacement_wh.get_value();
			if (!replacement_warehouse) frappe.throw(__("Select replacement warehouse."));

			await frappe.confirm(__("Prepare the replacement delivery note?"), async () => {
				const res = await frappe.call({
					method: `${M}.prepare_warranty_replacement`,
					args: {
						sales_invoice: state.invoice.sales_invoice,
						return_invoice: state.invoice.pending_return_invoice,
						replacement_warehouse,
						items,
					},
					freeze: true,
				});
				state.invoice = res.message.invoice;
				InvoiceLoader.render(state.invoice, "settle");
				frappe.show_alert({ message: __("Replacement prepared — ready for hand-over"), indicator: "green" });
			});
		},
	};

	async function setup_context() {
		const res = await frappe.call({ method: `${M}.get_warranty_context` });
		state.context = res.message || {};
		TabManager.init(state.context);

		const { show_claim_tab, show_settle_tab } = state.context;
		if (show_claim_tab && !show_settle_tab) {
			$w.find(".wc-hero p").text(__("Register claims and confirm hand-over to the customer."));
		} else if (show_settle_tab && !show_claim_tab) {
			$w.find(".wc-hero p").text(__("Receive claimed products and prepare replacements."));
		}
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
			await InvoiceLoader.load({ invoice_no: controls.invoice_settle.get_value() }, "settle");
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

	$w.find(".wc-btn-register").on("click", () => ClaimActions.register());
	$w.find(".wc-btn-handover").on("click", () => ClaimActions.handover());
	$w.find(".wc-btn-receive").on("click", () => SettleActions.receive());
	$w.find(".wc-btn-prepare").on("click", () => SettleActions.prepare());

	controls.invoice_claim.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search-claim").trigger("click");
	});
	controls.invoice_settle.$input.on("keydown", (e) => {
		if (e.key === "Enter") $w.find(".wc-btn-search-settle").trigger("click");
	});

	setup_context();
};
