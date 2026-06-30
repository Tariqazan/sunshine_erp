import frappe


def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    # Full-bleed landing page — no Frappe container / breadcrumbs
    context.full_width = 1
    context.no_breadcrumbs = 1

    # ── Brand theme from Frappe Whitelabel "Sidebar Configuration" ──
    # Pull logo + brand colors from the active configuration record so
    # the landing page always matches the app's whitelabel branding.
    theme = {
        "logo":             "",
        "primary_color":    "#6366f1",
        "secondary_color":  "#64748b",
        "background_light": "#f8fafc",
        "background_dark":  "#0b0f19",
    }
    try:
        if frappe.db.exists("DocType", "Sidebar Configuration"):
            cfg = frappe.db.get_value(
                "Sidebar Configuration",
                {"active": 1},
                ["logo", "primary_color", "secondary_color",
                 "background_light", "background_dark"],
                as_dict=True,
            )
            # Fall back to most recent config if none flagged active
            if not cfg:
                cfg = frappe.db.get_value(
                    "Sidebar Configuration",
                    {},
                    ["logo", "primary_color", "secondary_color",
                     "background_light", "background_dark"],
                    order_by="modified desc",
                    as_dict=True,
                )
            if cfg:
                for key in theme:
                    if cfg.get(key):
                        theme[key] = cfg.get(key)
    except Exception:
        # Whitelabel app not installed / table missing — keep defaults
        pass

    context.theme = theme

    # ── Company info ──────────────────────────────────────────────
    context.company = {
        "name":        "Sunshine Power Ltd",
        "tagline":     "Powering Bangladesh with Clean, Reliable Energy",
        "description": (
            "Leading provider of solar energy solutions, IPS systems, and power backup products. "
            "Trusted by thousands of homes and businesses across Bangladesh since 2010."
        ),
        "phone":     "+880 1700-000000",
        "email":     "info@sunshinepowerltd.com",
        "address":   "House 12, Road 5, Sector 7, Uttara, Dhaka-1230, Bangladesh",
        "whatsapp":  "8801700000000",
        "facebook":  "#",
        "youtube":   "#",
    }

    # ── Stats ─────────────────────────────────────────────────────
    context.stats = [
        {"value": "15+",    "label": "Years of Experience"},
        {"value": "10,000+","label": "Happy Customers"},
        {"value": "50+",    "label": "Products"},
        {"value": "64",     "label": "Districts Served"},
    ]

    # ── Why us ────────────────────────────────────────────────────
    context.why_us = [
        {"icon": "🏆", "title": "Certified & Trusted",   "desc": "ISO certified with BSTI and SREDA approvals."},
        {"icon": "🔧", "title": "Expert Installation",   "desc": "Trained engineers for safe and efficient setups."},
        {"icon": "📞", "title": "After-Sales Support",   "desc": "Dedicated helpline, 7 days a week."},
        {"icon": "💰", "title": "Best Price Guarantee",  "desc": "We match any genuine lower market price."},
        {"icon": "🚚", "title": "Nationwide Delivery",   "desc": "Fast delivery to all 64 districts."},
        {"icon": "📋", "title": "EMI Available",         "desc": "Easy 0% EMI through banks and MFS."},
    ]

    # ── Products from Item doctype ────────────────────────────────
    # Fetch items that are enabled (not disabled) and have a standard_rate
    item_fields = [
        "item_name", "item_code", "item_group",
        "description", "standard_rate", "image", "warranty_period",
    ]

    raw_items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=item_fields,
        order_by="creation desc",
        limit=12,
    )

    # Icon and badge mappings keyed by item_group (case-insensitive keywords)
    # badge_cls maps to a CSS class defined in index.html (avoids Jinja-in-style lint errors)
    GROUP_META = {
        "solar":       {"icon": "☀️",  "badge": "Solar",       "badge_cls": "badge-amber"},
        "panel":       {"icon": "🔆",  "badge": "Solar Panel", "badge_cls": "badge-green"},
        "ips":         {"icon": "🔋",  "badge": "IPS/UPS",     "badge_cls": "badge-blue"},
        "ups":         {"icon": "🔋",  "badge": "IPS/UPS",     "badge_cls": "badge-blue"},
        "battery":     {"icon": "⚡",  "badge": "Battery",     "badge_cls": "badge-purple"},
        "inverter":    {"icon": "🔌",  "badge": "Inverter",    "badge_cls": "badge-amber"},
        "commercial":  {"icon": "🏭",  "badge": "Commercial",  "badge_cls": "badge-red"},
        "lighting":    {"icon": "💡",  "badge": "Lighting",    "badge_cls": "badge-cyan"},
        "stabilizer":  {"icon": "⚙️",  "badge": "Stabilizer",  "badge_cls": "badge-slate"},
    }
    DEFAULT_META = {"icon": "🔆", "badge": "Energy", "badge_cls": "badge-indigo"}

    def get_meta(group):
        g = (group or "").lower()
        for key, meta in GROUP_META.items():
            if key in g:
                return meta
        return DEFAULT_META

    products = []
    for item in raw_items:
        meta = get_meta(item.get("item_group") or "")
        # Format price
        rate = item.get("standard_rate") or 0
        price = f"৳ {rate:,.0f}" if rate else "Contact for price"
        # Strip HTML from description
        desc = frappe.utils.strip_html(item.get("description") or "")[:180] or "Premium quality energy product by Sunshine Power Ltd."
        if len(frappe.utils.strip_html(item.get("description") or "")) > 180:
            desc += "…"

        products.append({
            "item_code":  item.item_code,
            "name":       item.item_name,
            "group":      item.get("item_group") or "General",
            "description": desc,
            "price":      price,
            "image":      item.get("image") or "",
            "warranty":   item.get("warranty_period") or "",
            "icon":      meta["icon"],
            "badge":     meta["badge"],
            "badge_cls": meta["badge_cls"],
        })

    # Fallback demo products when no items exist in the system yet
    if not products:
        products = [
            {
                "item_code":  "SHS-100W",
                "name":       "Solar Home System 100W",
                "group":      "Solar",
                "description": "Complete solar home system — lights, fan, TV, and phone charging. Zero electricity bill, 5-year warranty.",
                "price":      "৳ 22,000",
                "image":      "",
                "warranty":   "5 years",
                "icon":      "☀️",
                "badge":     "Best Seller",
                "badge_cls": "badge-amber",
            },
            {
                "item_code":  "PANEL-250W",
                "name":       "Monocrystalline Solar Panel 250W",
                "group":      "Solar Panel",
                "description": "High-efficiency Tier-1 monocrystalline solar panel. Anti-reflective coating, 25-year performance guarantee.",
                "price":      "৳ 12,500",
                "image":      "",
                "warranty":   "25 years",
                "icon":      "🔆",
                "badge":     "High Efficiency",
                "badge_cls": "badge-green",
            },
            {
                "item_code":  "IPS-1500VA",
                "name":       "Digital IPS 1500VA",
                "group":      "IPS",
                "description": "Pure sine wave IPS with fast auto-switch, LCD display, and overload protection. Ideal for home & office.",
                "price":      "৳ 18,500",
                "image":      "",
                "warranty":   "2 years",
                "icon":      "🔋",
                "badge":     "Popular",
                "badge_cls": "badge-blue",
            },
            {
                "item_code":  "BATT-100AH",
                "name":       "Lithium LiFePO4 Battery 100Ah",
                "group":      "Battery",
                "description": "Next-gen lithium iron phosphate battery. 2000+ charge cycles, 80% DoD, built-in BMS protection.",
                "price":      "৳ 32,000",
                "image":      "",
                "warranty":   "3 years",
                "icon":      "⚡",
                "badge":     "New Arrival",
                "badge_cls": "badge-purple",
            },
            {
                "item_code":  "INV-3KW",
                "name":       "Hybrid Solar Inverter 3kW",
                "group":      "Inverter",
                "description": "Grid-tie & off-grid hybrid inverter with MPPT charge controller and Wi-Fi monitoring app.",
                "price":      "৳ 45,000",
                "image":      "",
                "warranty":   "2 years",
                "icon":      "🔌",
                "badge":     "Hybrid",
                "badge_cls": "badge-amber",
            },
            {
                "item_code":  "COM-10KW",
                "name":       "Commercial Solar System 10kW",
                "group":      "Commercial",
                "description": "Turnkey rooftop installation for factories and offices. Reduce electricity bills by up to 80%.",
                "price":      "Custom Quote",
                "image":      "",
                "warranty":   "10 years",
                "icon":      "🏭",
                "badge":     "Enterprise",
                "badge_cls": "badge-red",
            },
        ]

    context.products = products
