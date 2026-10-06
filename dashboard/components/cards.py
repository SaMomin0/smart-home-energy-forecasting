"""
Premium KPI Card Components.
Current Power, Expected Power, Forecast Power, Energy Today,
and Forecast Direction Indicator.
"""

from typing import Optional
import streamlit as st

from dashboard.utils.formatting import (
    format_watts,
    format_kwh,
    format_delta_watts,
    get_icon,
    render_html,
)


def forecast_direction_indicator(current_w: Optional[float], forecast_w: Optional[float]) -> str:
    """
    Returns HTML indicating whether forecasted power is expected to rise, drop, or hold steady.
    """
    if current_w is None or forecast_w is None:
        return ""
    diff = float(forecast_w) - float(current_w)
    if abs(diff) < 15.0:
        return '<span class="kpi-trend flat">Steady</span>'
    elif diff > 0:
        return f'<span class="kpi-trend up">{get_icon("trending-up", size=13, color="var(--warning)")} Rising (+{int(diff)}W)</span>'
    else:
        return f'<span class="kpi-trend down">{get_icon("trending-down", size=13, color="var(--success)")} Easing ({int(diff)}W)</span>'


def current_power_card(current_w: Optional[float], delta_w: Optional[float] = None) -> None:
    """
    Renders the CURRENT POWER KPI Card.
    Source: analysis.energy.current_power_w
    """
    val_str, unit_str = format_watts(current_w)
    delta_str, direction = format_delta_watts(delta_w)
    
    icon_svg = get_icon("zap", size=16, color="var(--accent)")
    
    trend_html = ""
    if delta_w is not None and abs(delta_w) >= 1.0:
        trend_class = "up" if direction == "up" else "down"
        trend_icon = get_icon("trending-up" if direction == "up" else "trending-down", size=12)
        trend_html = f'<div class="kpi-trend {trend_class}">{trend_icon} <span>{delta_str} vs prev</span></div>'
    else:
        trend_html = '<div class="kpi-trend flat"><span>Steady state</span></div>'

    render_html(
        f"""
        <div class="apple-card kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Current Power</span>
                <span class="kpi-icon-badge" style="color:var(--accent);">{icon_svg}</span>
            </div>
            <div class="kpi-metric-row">
                <span class="kpi-metric-val">{val_str}</span>
                <span class="kpi-metric-unit">{unit_str}</span>
            </div>
            <div class="kpi-footer">
                {trend_html}
                <span style="font-size:0.7rem; color:var(--text-tertiary);">Real-time</span>
            </div>
        </div>
        """
    )


def expected_power_card(expected_w: Optional[float], current_w: Optional[float] = None) -> None:
    """
    Renders the EXPECTED POWER KPI Card (Model 1 baseline estimation).
    Source: analysis.energy.predicted_power_w
    """
    val_str, unit_str = format_watts(expected_w)
    icon_svg = get_icon("activity", size=16, color="var(--info)")
    
    context_html = ""
    if current_w is not None and expected_w is not None:
        diff = float(current_w) - float(expected_w)
        if abs(diff) < 20.0:
            context_html = '<span class="kpi-trend flat">Matches baseline</span>'
        elif diff > 0:
            context_html = f'<span class="kpi-trend up">+{int(diff)}W excess</span>'
        else:
            context_html = f'<span class="kpi-trend down">{int(diff)}W below</span>'
    else:
        context_html = '<span style="font-size:0.75rem; color:var(--text-secondary);">Model 1 baseline</span>'

    render_html(
        f"""
        <div class="apple-card kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Expected Power</span>
                <span class="kpi-icon-badge" style="color:var(--info);">{icon_svg}</span>
            </div>
            <div class="kpi-metric-row">
                <span class="kpi-metric-val">{val_str}</span>
                <span class="kpi-metric-unit">{unit_str}</span>
            </div>
            <div class="kpi-footer">
                {context_html}
                <span style="font-size:0.7rem; color:var(--text-tertiary);">Load Model</span>
            </div>
        </div>
        """
    )


def forecast_power_card(forecast_w: Optional[float], current_w: Optional[float] = None) -> None:
    """
    Renders the NEXT FORECAST KPI Card (Model 2 short-term autoregression).
    Source: analysis.forecast.predicted_next_power_w
    """
    val_str, unit_str = format_watts(forecast_w)
    icon_svg = get_icon("trending-up", size=16, color="var(--warning)")
    trend_html = forecast_direction_indicator(current_w, forecast_w)

    render_html(
        f"""
        <div class="apple-card kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Next Forecast</span>
                <span class="kpi-icon-badge" style="color:var(--warning);">{icon_svg}</span>
            </div>
            <div class="kpi-metric-row">
                <span class="kpi-metric-val">{val_str}</span>
                <span class="kpi-metric-unit">{unit_str}</span>
            </div>
            <div class="kpi-footer">
                {trend_html if trend_html else '<span style="font-size:0.75rem; color:var(--text-secondary);">Horizon: +2.5s</span>'}
                <span style="font-size:0.7rem; color:var(--text-tertiary);">Forecast M2</span>
            </div>
        </div>
        """
    )


def energy_today_card(energy_kwh: Optional[float]) -> None:
    """
    Renders the ENERGY KPI Card (Cumulative household consumption).
    Source: analysis.energy.energy_kwh
    """
    val_str, unit_str = format_kwh(energy_kwh)
    icon_svg = get_icon("sun", size=16, color="var(--success)")

    render_html(
        f"""
        <div class="apple-card kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Cumulative Energy</span>
                <span class="kpi-icon-badge" style="color:var(--success);">{icon_svg}</span>
            </div>
            <div class="kpi-metric-row">
                <span class="kpi-metric-val">{val_str}</span>
                <span class="kpi-metric-unit">{unit_str}</span>
            </div>
            <div class="kpi-footer">
                <span style="font-size:0.75rem; color:var(--text-secondary);">Integrated session</span>
                <span style="font-size:0.7rem; color:var(--text-tertiary);">Total</span>
            </div>
        </div>
        """
    )
