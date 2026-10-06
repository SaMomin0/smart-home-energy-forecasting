"""
Apple-Inspired Plotly Theme & Layout Generator.
Provides clean typography, subtle translucent grids, restrained semantic palettes,
and dark/light mode consistency.
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go

# Apple Semantic Color System with User Defined Palette
COLORS = {
    "dark": {
        "bg": "rgba(0, 0, 0, 0)",
        "paper_bg": "rgba(0, 0, 0, 0)",
        "card_bg": "rgba(0, 18, 25, 0.75)",
        "text": "#FFFFFF",
        "text_secondary": "#94D2BD",
        "grid": "rgba(148, 210, 189, 0.10)",
        "border": "rgba(148, 210, 189, 0.16)",
        "blue": "#0A9396",
        "blue_soft": "rgba(10, 147, 150, 0.25)",
        "green": "#94D2BD",
        "green_soft": "rgba(148, 210, 189, 0.22)",
        "orange": "#EE9B00",
        "amber": "#EE9B00",
        "orange_soft": "rgba(238, 155, 0, 0.25)",
        "red": "#AE2012",
        "red_soft": "rgba(174, 32, 18, 0.28)",
        "purple": "#CA6702",
        "gray": "#7D8E95",
        "hover_bg": "rgba(0, 18, 25, 0.95)",
    },
    "light": {
        "bg": "rgba(0, 0, 0, 0)",
        "paper_bg": "rgba(0, 0, 0, 0)",
        "card_bg": "rgba(255, 255, 255, 0.9)",
        "text": "#080708",
        "text_secondary": "#005F73",
        "grid": "rgba(0, 18, 25, 0.06)",
        "border": "rgba(0, 18, 25, 0.12)",
        "blue": "#0A9396",
        "blue_soft": "rgba(10, 147, 150, 0.15)",
        "green": "#0A9396",
        "green_soft": "rgba(148, 210, 189, 0.3)",
        "orange": "#EE9B00",
        "amber": "#EE9B00",
        "orange_soft": "rgba(238, 155, 0, 0.15)",
        "red": "#AE2012",
        "red_soft": "rgba(174, 32, 18, 0.15)",
        "purple": "#BB3E03",
        "gray": "#6E7B82",
        "hover_bg": "rgba(255, 255, 255, 0.98)",
    },
}

FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif'


def get_apple_plotly_layout(
    theme: str = "dark",
    height: int = 280,
    title: Optional[str] = None,
    showlegend: bool = True,
) -> Dict[str, Any]:
    """
    Returns a Plotly layout dictionary styled with Apple Design aesthetic.
    Supports seamless Light and Dark mode transitions with compact height.
    """
    pal = COLORS.get(theme, COLORS["dark"])

    layout = dict(
        height=height,
        paper_bgcolor=pal["paper_bg"],
        plot_bgcolor=pal["bg"],
        font=dict(
            family=FONT_FAMILY,
            color=pal["text"],
            size=11,
        ),
        margin=dict(l=35, r=15, t=30 if title else 15, b=25),
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=pal["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=pal["hover_bg"],
            bordercolor=pal["border"],
            font=dict(family=FONT_FAMILY, size=12, color=pal["text"]),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=pal["grid"],
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=pal["grid"],
            tickfont=dict(size=10, color=pal["text_secondary"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=pal["grid"],
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=pal["grid"],
            tickfont=dict(size=10, color=pal["text_secondary"]),
        ),
    )

    if title:
        layout["title"] = dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color=pal["text"]),
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top",
        )

    return layout


def get_theme_palette(theme: str = "dark") -> Dict[str, str]:
    """Returns the color palette dictionary for the specified theme."""
    return COLORS.get(theme, COLORS["dark"])
