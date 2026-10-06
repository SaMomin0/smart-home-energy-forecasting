"""
AI Anomaly and Outlier Timeline Component.
Chart #8: Power stream with Isolation Forest anomaly occurrences visually highlighted.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette


def render_anomaly_timeline_chart(df: pd.DataFrame, theme: str = "dark") -> None:
    """
    Chart #8 — AI Anomaly Timeline
    Visualizes power load over time with Isolation Forest outlier events
    highlighted as prominent warning diamonds with exact scores and device states.
    """
    pal = get_theme_palette(theme)

    if df.empty or "datetime" not in df.columns or "power_w" not in df.columns:
        st.info("No historical telemetry available for anomaly timeline.")
        return

    fig = go.Figure()

    # 1. Background Nominal Power Line
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["power_w"],
            mode="lines",
            name="Baseline Stream",
            line=dict(color=pal["text_secondary"], width=1.8),
            opacity=0.7,
            hoverinfo="skip",
        )
    )

    # 2. Highlight Anomaly Points
    anom_df = df[df["is_anomaly"] == 1]
    if not anom_df.empty:
        fig.add_trace(
            go.Scatter(
                x=anom_df["datetime"],
                y=anom_df["power_w"],
                mode="markers",
                name="Anomalous Event",
                marker=dict(
                    color=pal["red"],
                    size=9,
                    symbol="diamond",
                    line=dict(color="#FFFFFF", width=1),
                ),
                customdata=anom_df[["datetime", "power_w", "anomaly_score", "active_appliances_str"]].to_numpy(),
                hovertemplate=(
                    "<b>ANOMALY EVENT</b><br>"
                    "<b>Time:</b> %{customdata[0]|%H:%M:%S}<br>"
                    "<b>Power:</b> %{customdata[1]:,.0f} W<br>"
                    "<b>Isolation Score:</b> %{customdata[2]:+.4f}<br>"
                    "<b>Active Appliances:</b> %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )
    else:
        # Show nominal indicator in legend
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name="Zero Anomalies in Window",
                marker=dict(color=pal["green"], size=7),
            )
        )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["title"] = "Time"
    fig.update_layout(layout)

    from dashboard.state import set_selected_anomaly, set_selected_timestamp

    chart_event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="chart_anomaly_timeline",
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": False, "responsive": True},
    )

    if chart_event and hasattr(chart_event, "selection") and chart_event.selection:
        pts = getattr(chart_event.selection, "points", []) or chart_event.selection.get("points", [])
        if pts:
            pt_x = pts[0].get("x")
            if pt_x:
                set_selected_anomaly(str(pt_x))
                set_selected_timestamp(str(pt_x))
