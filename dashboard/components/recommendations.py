"""
Recommendation and Action Items Components (Phase 3.3 Enhanced).
Displays AI-driven actionable optimization advice and interactive prescribed steps
with estimated potential impact in watts and appliance isolation links.
"""

from typing import Optional, List, Dict, Any
import streamlit as st

from dashboard.config import APPLIANCE_META
from dashboard.utils.formatting import get_icon, format_watts, render_html
from dashboard.components.alerts import severity_badge
from dashboard.state import set_selected_appliance


def _estimate_action_impact(action_str: str) -> Optional[float]:
    """Infers potential wattage reduction if the suggested action targets a known appliance."""
    import re
    action_lower = action_str.lower()
    # First pass: match full appliance name (e.g. 'Space Heater', 'Air Conditioner')
    for key, meta in APPLIANCE_META.items():
        if meta["name"].lower() in action_lower:
            return float(meta["watts"])
    # Second pass: match isolated word key (e.g. 'heater', 'ac', 'fan')
    for key, meta in APPLIANCE_META.items():
        if re.search(r'\b' + re.escape(key) + r'\b', action_lower):
            return float(meta["watts"])
    return None


def recommendation_panel(recommendation: Optional[str], severity: Optional[str] = "NORMAL") -> None:
    """
    Renders the Recommendation Panel.
    Source: analysis.recommendation, analysis.severity
    """
    text = recommendation or "Energy consumption aligns with historical patterns and occupancy. No manual intervention required."
    badge_html = severity_badge(severity)

    render_html(
        f"""
        <div class="apple-card" style="height:100%;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('activity', size=18, color='var(--accent)')}
                    <span style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">Intelligent Recommendation</span>
                </div>
                {badge_html}
            </div>
            <div style="font-size:0.95rem; color:var(--text-primary); line-height:1.5; font-weight:500; margin-bottom:0.6rem;">
                "{text}"
            </div>
            <div style="font-size:0.75rem; color:var(--text-secondary);">
                Synthesized dynamically from environmental context, occupancy, and appliance load decomposition.
            </div>
        </div>
        """
    )


def action_items_panel(action_items: Optional[List[str]] = None) -> None:
    """
    Renders the Action Items Panel with interactive action guidance and potential impact.
    Strictly follows Data Integrity Rule #6:
    Labels items as 'Suggested Action' rather than pretending actuators exist to switch off physical hardware.
    """
    items = action_items or []

    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.6rem;">
            {get_icon('zap', size=18, color='var(--warning)')}
            <span style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">Suggested Actions & Potential Impact</span>
        </div>
        """
    )

    if not items:
        render_html(
            f"""
            <div class="apple-card">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span style="color:var(--success);">{get_icon('check-circle', size=16, color='var(--success)')}</span>
                    <span style="font-size:0.85rem; color:var(--text-secondary);">No immediate action items. System operating at peak efficiency.</span>
                </div>
            </div>
            """
        )
        return

    for idx, item in enumerate(items):
        impact_w = _estimate_action_impact(item)
        impact_str = f"~{int(impact_w)} W" if impact_w else "Load reduction"

        with st.container():
            col_text, col_action = st.columns([3, 1])
            with col_text:
                render_html(
                    f"""
                    <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px; margin-bottom:0.4rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.85rem; font-weight:600; color:var(--text-primary);">{item}</span>
                            <span class="severity-badge warning" style="font-size:0.65rem;">POTENTIAL IMPACT: {impact_str}</span>
                        </div>
                        <div style="font-size:0.72rem; color:var(--text-secondary); margin-top:0.2rem;">
                            Actionable advisory: Hardware actuation requires physical user control or Home Assistant bridge.
                        </div>
                    </div>
                    """
                )
            with col_action:
                # Find matching appliance to isolate in view
                target_app = None
                for k, meta in APPLIANCE_META.items():
                    if k in item.lower() or meta["name"].lower() in item.lower():
                        target_app = meta["name"]
                        break

                if target_app:
                    if st.button(f"Isolate {target_app}", key=f"btn_action_isolate_{idx}", use_container_width=True):
                        set_selected_appliance(target_app)
                        st.rerun()
                else:
                    st.button("Advisory Only", key=f"btn_action_advisory_{idx}", disabled=True, use_container_width=True)
