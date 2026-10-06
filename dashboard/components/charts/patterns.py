"""
Energy Pattern Heatmap Component.
Chart #5: 7-Day x 24-Hour Average Power Heatmap from real historical telemetry.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.chart_data import prepare_heatmap_matrix
from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette


def render_energy_pattern_heatmap(df: pd.DataFrame, theme: str = "dark") -> None:
    """
    Chart #5 — Day x Hour Energy Pattern Heatmap
    X: hour of day (0-23)
    Y: day of week (Monday-Sunday)
    Color: average power (Watts)
    """
    pal = get_theme_palette(theme)

    if df.empty or "datetime" not in df.columns:
        st.info("Insufficient historical telemetry to aggregate diurnal heatmap patterns.")
        return

    matrix, days, hours = prepare_heatmap_matrix(df)

    # Invert days order so Monday appears at the top
    matrix_rev = matrix[::-1]
    days_rev = days[::-1]

    # Apple-inspired calm gradient (Deep Midnight Blue to Electric Cyan/Orange)
    if theme == "dark":
        colorscale = [
            [0.0, "rgba(20, 20, 24, 0.6)"],
            [0.2, "rgba(10, 45, 90, 0.8)"],
            [0.5, "rgba(0, 113, 227, 0.9)"],
            [0.8, "rgba(41, 151, 255, 1.0)"],
            [1.0, "rgba(255, 159, 10, 1.0)"],
        ]
    else:
        colorscale = [
            [0.0, "rgba(240, 242, 246, 0.8)"],
            [0.25, "rgba(180, 215, 255, 0.85)"],
            [0.55, "rgba(80, 160, 255, 0.9)"],
            [0.85, "rgba(0, 113, 227, 0.95)"],
            [1.0, "rgba(255, 149, 0, 1.0)"],
        ]

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix_rev,
            x=[f"{h:02d}:00" for h in hours],
            y=days_rev,
            colorscale=colorscale,
            hoverongaps=False,
            hovertemplate=(
                "<b>Day:</b> %{y}<br>"
                "<b>Hour:</b> %{x}<br>"
                "<b>Avg Power:</b> %{z:,.0f} W<br>"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Avg W", font=dict(size=11, color=pal["text_secondary"])),
                tickfont=dict(size=10, color=pal["text_secondary"]),
                thickness=12,
                len=0.85,
            ),
        )
    )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None, showlegend=False)
    layout["xaxis"]["title"] = "Hour of Day"
    layout["yaxis"]["title"] = None
    layout["margin"] = dict(l=85, r=25, t=20, b=35)
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
