"""
Appliance Grid and Status Components (Ultra-Minimized).
Displays real-time appliance states (ON/OFF), rated power, estimated load, contribution %,
and intelligent status chips (NORMAL, ATTENTION, WASTEFUL, HIGH LOAD).
Supports bidirectional cross-filtering across charts and panels.
"""

from typing import Optional, Dict, Any, List
import streamlit as st

from dashboard.config import APPLIANCE_META, APPLIANCE_FILTER_OPTIONS
from dashboard.utils.formatting import get_icon, format_watts, render_html
from dashboard.state import get_selected_appliance, set_selected_appliance


def appliance_wattage_badge(rated_watts: float, is_on: bool) -> str:
    """Returns HTML for the rated wattage badge of an appliance."""
    opacity = "1" if is_on else "0.6"
    return f'<span class="appliance-watts-badge" style="opacity:{opacity};">{int(rated_watts)}W</span>'


def appliance_status_card(
    appliance_key: str,
    name: str,
    is_on: bool,
    rated_watts: float,
    current_watts: float,
    contribution_pct: float = 0.0,
    status_label: str = "NORMAL",
    is_selected: bool = False,
) -> str:
    """
    Returns HTML for a single Apple-styled, ultra-dense appliance card.
    Displays:
    - Inline icon
    - Active status pill (ON/OFF)
    - Device title
    - Active wattage + Rated capacity
    """
    meta = APPLIANCE_META.get(appliance_key, {})
    icon_name = meta.get("icon", "zap")
    app_color = meta.get("color", "var(--accent)")
    
    selected_class = "selected" if is_selected else ""
    active_class = "active" if is_on else ""
    
    state_pill = '<span class="appliance-state-pill on">ON</span>' if is_on else '<span class="appliance-state-pill off">OFF</span>'
    
    icon_color = app_color if is_on else "var(--text-tertiary)"
    icon_svg = get_icon(icon_name, size=13, color=icon_color)
    
    power_str, power_unit = format_watts(current_watts)
    active_power_markup = (
        f'<span class="appliance-power-active">{power_str} <span style="font-size:0.62rem; font-weight:500;">{power_unit}</span></span>'
        if is_on else
        '<span class="appliance-power-active off">0 W</span>'
    )

    return f"""<div class="appliance-card {active_class} {selected_class}" id="appliance-{appliance_key}">
<div class="appliance-top-row">
<div class="appliance-icon-box">{icon_svg}</div>
{state_pill}
</div>
<div class="appliance-title" title="{name}">{name}</div>
<div class="appliance-sub-row">
{active_power_markup}
<span class="appliance-watts-badge">{int(rated_watts)}W</span>
</div>
</div>"""


def appliance_grid(
    appliances_data: Optional[Dict[str, int]] = None,
    waste_reasons: Optional[List[str]] = None,
    total_power_w: Optional[float] = None,
    selected_appliance: Optional[str] = "All Appliances"
) -> None:
    """
    Renders the ultra-compact 7-column Appliance Ribbon with isolation selection.
    """
    states = appliances_data or {}
    current_selected = get_selected_appliance()
    reasons = waste_reasons or []
    total_active_w = float(total_power_w) if total_power_w and total_power_w > 0 else sum(
        APPLIANCE_META[k]["watts"] for k, v in states.items() if v == 1 and k in APPLIANCE_META
    )

    # Compact header with appliance isolation selectbox
    c_label, c_filter = st.columns([5, 2])
    with c_label:
        active_count = sum(1 for v in states.values() if v == 1)
        render_html(
            f"""
            <div style="font-size:0.75rem; color:var(--text-secondary); font-weight:600; text-transform:uppercase; letter-spacing:0.03em; margin-bottom:0.15rem;">
                Connected Devices ({active_count}/7 Active • {int(total_active_w)} W)
            </div>
            """
        )
    with c_filter:
        try:
            curr_idx = APPLIANCE_FILTER_OPTIONS.index(current_selected)
        except ValueError:
            curr_idx = 0
        new_sel = st.selectbox(
            "Filter Appliance",
            options=APPLIANCE_FILTER_OPTIONS,
            index=curr_idx,
            label_visibility="collapsed",
            key="app_quick_filter"
        )
        if new_sel != current_selected:
            set_selected_appliance(new_sel)
            st.rerun()

    # Calculate individual statuses and contribution percentages
    cards_html = []
    for key, meta in APPLIANCE_META.items():
        is_on = bool(states.get(key, 0) == 1)
        rated = float(meta.get("watts", 0))
        current_w = rated if is_on else 0.0
        contrib_pct = (current_w / total_active_w * 100.0) if total_active_w > 0 else 0.0

        status = "NORMAL"
        key_or_name_in_waste = any(key in r.lower() or meta["name"].lower() in r.lower() for r in reasons)
        if is_on and key_or_name_in_waste:
            status = "WASTEFUL"
        elif is_on and total_active_w > 3500 and rated >= 1000:
            status = "HIGH LOAD"
        elif is_on and key in ["ac", "heater"] and states.get("ac") == 1 and states.get("heater") == 1:
            status = "ATTENTION"
        
        is_sel = (current_selected == meta["name"]) or (current_selected == key.upper()) or (current_selected == "AC" and key == "ac") or (current_selected == "Fan" and key == "fan") or (current_selected == "TV" and key == "tv")
        
        card_html = appliance_status_card(
            appliance_key=key,
            name=meta["name"],
            is_on=is_on,
            rated_watts=rated,
            current_watts=current_w,
            contribution_pct=contrib_pct,
            status_label=status,
            is_selected=is_sel,
        )
        cards_html.append(card_html)

    grid_markup = f"""<div class="appliance-grid-row">
{"".join(cards_html)}
</div>"""
    render_html(grid_markup)
