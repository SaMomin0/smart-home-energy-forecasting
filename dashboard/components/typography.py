"""
Apple-Inspired Typography Components (Ultra-Minimized).
Provides clean, hierarchy-focused headings, subtitles, captions, and compact section headers.
"""

from typing import Optional
import streamlit as st
from dashboard.utils.formatting import get_icon, render_html


def page_title(title: str, subtitle: Optional[str] = None) -> None:
    """Renders an ultra-compact page header."""
    sub_html = f'<p style="font-size:0.75rem; color:var(--text-secondary); margin:0.1rem 0 0 0;">{subtitle}</p>' if subtitle else ""
    render_html(
        f"""
        <div style="margin-bottom: 0.5rem;">
            <h1 style="font-size:1.15rem; font-weight:700; color:var(--text-primary); margin:0; line-height:1.2;">{title}</h1>
            {sub_html}
        </div>
        """
    )


def section_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None, action_html: Optional[str] = None) -> None:
    """Renders an ultra-compact section header with zero unnecessary margin."""
    icon_html = f'<span style="display:inline-flex; align-items:center; opacity:0.85;">{get_icon(icon, size=15)}</span>' if icon else ""
    sub_html = f'<span style="font-size:0.7rem; color:var(--text-tertiary); margin-left:0.5rem; font-weight:400;">• {subtitle}</span>' if subtitle else ""
    action_box = f'<div>{action_html}</div>' if action_html else ""

    render_html(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem; margin-bottom:0.25rem; padding-bottom:0.2rem; border-bottom:1px solid var(--border-subtle);">
            <div style="display:flex; align-items:center; gap:0.35rem;">
                {icon_html}
                <span class="section-header-title">{title}</span>
                {sub_html}
            </div>
            {action_box}
        </div>
        """
    )


def card_title(title: str, icon: Optional[str] = None, badge_text: Optional[str] = None) -> str:
    """Returns HTML for an internal card header with icon and optional badge."""
    icon_html = f'<span style="display:inline-flex; align-items:center;">{get_icon(icon, size=14)}</span>' if icon else ""
    badge_html = f'<span class="kpi-badge">{badge_text}</span>' if badge_text else ""
    return f"""<div style="display:flex; justify-content:space-between; align-items:center; width:100%; margin-bottom:0.25rem;">
<div style="display:flex; align-items:center; gap:0.35rem;">
{icon_html}
<span class="kpi-label">{title}</span>
</div>
{badge_html}
</div>"""


def caption(text: str) -> None:
    """Renders secondary muted caption text."""
    render_html(f'<p style="font-size:0.7rem; color:var(--text-tertiary); margin:0.15rem 0;">{text}</p>')


def meta_tag(label: str, value: str) -> str:
    """Returns an inline metadata tag."""
    return f'<span class="metric-chip"><strong>{label}:</strong> {value}</span>'
