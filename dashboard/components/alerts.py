"""
AI Status, Anomaly Detection, and Waste Alert Components.
Includes Severity Badge, AI Status Card, Anomaly Score Card,
Waste Alert Card, and AI Explanation Panel.
"""

from typing import Optional, List, Dict, Any
import streamlit as st

from dashboard.utils.formatting import format_watts, get_icon, render_html


def severity_badge(severity: Optional[str] = "NORMAL") -> str:
    """
    Returns an Apple-styled restrained semantic badge for the given severity.
    NORMAL | WARNING | HIGH | CRITICAL
    """
    sev = (severity or "NORMAL").upper()
    css_class = {
        "NORMAL": "normal",
        "WARNING": "warning",
        "HIGH": "high",
        "CRITICAL": "critical",
    }.get(sev, "normal")

    return f'<span class="severity-badge {css_class}">{sev}</span>'


def ai_status_card(ai_data: Optional[Dict[str, Any]], severity: Optional[str] = "NORMAL") -> None:
    """
    Renders the AI Status Summary Card.
    Source: analysis.ai, analysis.severity
    """
    sev = (severity or "NORMAL").upper()
    is_anomaly = False
    score = 0.0
    
    if ai_data:
        is_anomaly = bool(ai_data.get("is_anomaly", False))
        score = float(ai_data.get("anomaly_score", 0.0))

    status_title = "Abnormal Pattern Detected" if is_anomaly else "Normal Consumption Pattern"
    status_color = "var(--danger)" if is_anomaly else "var(--success)"
    badge_html = severity_badge(sev)

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid {status_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('shield', size=18, color=status_color)}
                    <span style="font-weight:600; font-size:0.9rem; color:var(--text-primary);">AI Guard & Anomaly Engine</span>
                </div>
                {badge_html}
            </div>

            <div style="font-size:1.1rem; font-weight:600; color:var(--text-primary); margin-bottom:0.35rem;">
                {status_title}
            </div>

            <p style="font-size:0.8rem; color:var(--text-secondary); margin:0 0 0.75rem 0; line-height:1.4;">
                Isolation Forest ensemble evaluates continuous multidimensional telemetry against baseline behavior.
            </p>

            <div style="display:flex; gap:0.75rem; flex-wrap:wrap;">
                <span class="metric-chip">Isolation Score: {score:+.4f}</span>
                <span class="metric-chip">State: {"FLAGGED" if is_anomaly else "CLEAR"}</span>
                <span class="metric-chip">Sensitivity: 5%</span>
            </div>
        </div>
        """
    )


def anomaly_score_card(ai_data: Optional[Dict[str, Any]]) -> None:
    """
    Renders the Isolation Forest Anomaly Score Detail Card.
    Source: analysis.ai.anomaly_score
    """
    score = float(ai_data.get("anomaly_score", 0.0)) if ai_data else 0.0
    is_anomaly = bool(ai_data.get("is_anomaly", False)) if ai_data else False
    
    score_label = f"{score:+.3f}"
    status_tag = "ANOMALOUS" if is_anomaly else "NOMINAL"
    tag_class = "danger" if is_anomaly else "online"

    render_html(
        f"""
        <div class="apple-card" style="height:100%;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <span class="kpi-label">Anomaly Score</span>
                <span class="status-chip {tag_class}">{status_tag}</span>
            </div>
            <div style="font-size:1.85rem; font-weight:600; color:var(--text-primary); font-variant-numeric:tabular-nums; margin-bottom:0.25rem;">
                {score_label}
            </div>
            <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.4;">
                Negative values indicate deviation from normal power distributions.
            </div>
        </div>
        """
    )


def waste_alert_card(waste_data: Optional[Dict[str, Any]], action_items: Optional[List[str]] = None) -> None:
    """
    Renders the Dedicated Waste Detection Card.
    Shows:
    - Waste detected / No waste detected
    - Potential avoidable load in kW/W
    - Reasons list from backend
    - Recommended actions from backend
    Source: analysis.waste, analysis.action_items
    """
    is_waste = False
    wasted_w = 0.0
    reasons: List[str] = []
    
    if waste_data:
        is_waste = bool(waste_data.get("is_wasteful", False))
        wasted_w = float(waste_data.get("wasted_power_w", 0.0))
        reasons = waste_data.get("waste_reasons", [])

    actions = action_items or []
    val_str, unit_str = format_watts(wasted_w)
    
    if is_waste:
        header_title = "Wasteful Usage Detected"
        accent_color = "var(--warning)"
        status_tag = f'<span class="severity-badge warning">AVOIDABLE LOAD</span>'
        reasons_list_html = "".join([f'<li style="margin-bottom:0.3rem;">{r}</li>' for r in reasons]) if reasons else "<li>Unnecessary idle consumption</li>"
        actions_list_html = "".join([f'<li style="margin-bottom:0.3rem;">{a}</li>' for a in actions]) if actions else "<li>Turn off inactive high-draw appliances</li>"
        
        content_body = f"""
        <div style="display:flex; align-items:baseline; gap:0.4rem; margin:0.6rem 0;">
            <span style="font-size:1.9rem; font-weight:700; color:var(--warning);">{val_str}</span>
            <span style="font-size:1rem; font-weight:500; color:var(--text-secondary);">{unit_str} potential avoidable load</span>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem; margin-top:0.75rem;">
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.75rem; border-radius:12px;">
                <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.4rem;">
                    Identified Inefficiencies:
                </div>
                <ul style="font-size:0.8rem; color:var(--text-primary); margin:0; padding-left:1.1rem;">
                    {reasons_list_html}
                </ul>
            </div>
            
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.75rem; border-radius:12px;">
                <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.4rem;">
                    Recommended Actions:
                </div>
                <ul style="font-size:0.8rem; color:var(--text-primary); margin:0; padding-left:1.1rem;">
                    {actions_list_html}
                </ul>
            </div>
        </div>
        """
    else:
        header_title = "No Wasteful Usage Detected"
        accent_color = "var(--success)"
        status_tag = '<span class="status-chip online">EFFICIENT</span>'
        content_body = """
        <div style="display:flex; align-items:center; gap:0.5rem; margin:0.8rem 0;">
            <span style="font-size:1.3rem; font-weight:600; color:var(--success);">0 W</span>
            <span style="font-size:0.85rem; color:var(--text-secondary);">No unnecessary loads identified. All appliances match home occupancy.</span>
        </div>
        <p style="font-size:0.8rem; color:var(--text-secondary); margin:0;">
            Rules verification confirmed HVAC and lighting states align with environmental conditions.
        </p>
        """

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid {accent_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('alert-triangle' if is_waste else 'check-circle', size=18, color=accent_color)}
                    <span style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">{header_title}</span>
                </div>
                {status_tag}
            </div>
            {content_body}
        </div>
        """
    )


def ai_explanation_panel(ai_data: Optional[Dict[str, Any]], waste_data: Optional[Dict[str, Any]], recommendation: Optional[str] = None) -> None:
    """
    Renders an explainable AI panel detailing why an anomaly or waste status was assigned.
    """
    rec_text = recommendation or "All systems operating within nominal baseline parameters."
    is_anomaly = bool(ai_data.get("is_anomaly", False)) if ai_data else False
    is_waste = bool(waste_data.get("is_wasteful", False)) if waste_data else False

    render_html(
        f"""
        <div class="apple-card" style="margin-top:0.75rem;">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
                {get_icon('info', size=16, color='var(--accent)')}
                <span style="font-weight:600; font-size:0.85rem; color:var(--text-primary);">AI Inference Diagnostics</span>
            </div>
            <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.5;">
                <strong style="color:var(--text-primary);">Recommendation:</strong> {rec_text}
            </div>
            <div style="display:flex; gap:0.6rem; margin-top:0.6rem;">
                <span class="metric-chip">Isolation Forest: {"TRIGGERED" if is_anomaly else "STABLE"}</span>
                <span class="metric-chip">Waste Rule Engine: {"TRIGGERED" if is_waste else "CLEAR"}</span>
            </div>
        </div>
        """
    )
