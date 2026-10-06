"""
Dashboard Shell, Layout, and State Feedback Components.
Includes App Header, Navigation Bar, Empty State, Loading State, Error State,
Expandable Detail Panel, and Phase 3.2 Chart Placeholders.
"""

from typing import Optional, List, Any
import streamlit as st

from dashboard.config import NAV_PAGES
from dashboard.utils.formatting import get_icon, render_html
from dashboard.components.status import live_indicator, backend_connection_indicator


def app_header(
    is_live: bool = True,
    is_online: bool = True,
    latency_ms: Optional[float] = None,
    theme: str = "light",
) -> None:
    """
    Renders the Apple-inspired Top App Header.
    Left: Brand title ("Smart Home Energy") + subtitle ("AI Energy Intelligence")
    Right: Live indicator + Backend connection pill + Theme toggle
    """
    live_html = live_indicator(is_live)
    conn_html = backend_connection_indicator(is_online, latency_ms)
    
    render_html(
        f"""
        <div class="app-header-container">
            <div class="brand-wrapper">
                <div style="background:var(--accent); width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:white;">
                    {get_icon('zap', size=20, color='white')}
                </div>
                <div>
                    <h1 class="brand-title">Smart Home Energy</h1>
                    <p class="brand-subtitle">AI Energy Intelligence</p>
                </div>
            </div>
            
            <div class="header-status-group">
                {live_html}
                {conn_html}
            </div>
        </div>
        """
    )


def navigation_bar(current_page: str = "Dashboard") -> str:
    """
    Renders the top navigation pill bar across:
    Dashboard | Energy | AI Insights | Appliances | Analytics | System
    """
    cols = st.columns(len(NAV_PAGES))
    for i, page_name in enumerate(NAV_PAGES):
        with cols[i]:
            is_active = (page_name == current_page)
            btn_type = "primary" if is_active else "secondary"
            if st.button(page_name, key=f"nav_btn_{page_name}", type=btn_type, use_container_width=True):
                st.session_state.active_page = page_name
                st.rerun()

    return st.session_state.get("active_page", "Dashboard")


def empty_state(title: str = "No Telemetry Recorded", message: str = "Awaiting the first telemetry packet from the MQTT broker.") -> None:
    """Renders a calm, Apple-styled empty state container."""
    render_html(
        f"""
        <div class="state-container">
            <div style="color:var(--text-tertiary);">{get_icon('info', size=36, color='var(--text-tertiary)')}</div>
            <h3 class="state-title">{title}</h3>
            <p class="state-desc">{message}</p>
        </div>
        """
    )


def loading_state(message: str = "Connecting to telemetry stream...") -> None:
    """Renders a calm, translucent loading state container."""
    render_html(
        f"""
        <div class="state-container">
            <div style="color:var(--accent);">{get_icon('refresh-cw', size=32, color='var(--accent)')}</div>
            <h3 class="state-title">Synchronizing Real-Time Telemetry</h3>
            <p class="state-desc">{message}</p>
        </div>
        """
    )


def error_state(title: str = "Backend Unavailable", message: str = "Unable to connect to FastAPI service at http://localhost:8000.") -> None:
    """Renders an error container with helpful non-crashing instructions."""
    render_html(
        f"""
        <div class="state-container error">
            <div style="color:var(--danger);">{get_icon('alert-triangle', size=36, color='var(--danger)')}</div>
            <h3 class="state-title" style="color:var(--danger);">{title}</h3>
            <p class="state-desc">{message}</p>
            <div style="margin-top:0.5rem; font-size:0.75rem; color:var(--text-secondary); background:var(--surface); padding:0.4rem 0.8rem; border-radius:8px; border:1px solid var(--border);">
                Run: <code>uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000</code>
            </div>
        </div>
        """
    )


def expandable_detail_panel(title: str, content_callback_or_str: Any, expanded: bool = False) -> None:
    """Renders an Apple-styled collapsible detail drawer."""
    with st.expander(title, expanded=expanded):
        if callable(content_callback_or_str):
            content_callback_or_str()
        else:
            st.write(content_callback_or_str)


def chart_placeholder(chart_title: str, description: str) -> None:
    """
    Renders an elegant placeholder surface for Phase 3.2 visualization handoff.
    Never invents or fabricates fake chart curves.
    """
    render_html(
        f"""
        <div class="chart-placeholder-box">
            <span class="placeholder-tag">Phase 3.2 Visualization Engine</span>
            <h4 class="placeholder-title">{chart_title}</h4>
            <p class="placeholder-desc">{description}</p>
            <div style="font-size:0.75rem; color:var(--text-tertiary); margin-top:0.25rem;">
                Visualization will be connected in Phase 3.2
            </div>
        </div>
        """
    )
