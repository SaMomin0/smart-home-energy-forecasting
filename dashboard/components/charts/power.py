"""
Power Timeline and Actual vs Expected vs Forecast Charts.
Chart #1: Real-Time Power Timeline with anomaly markers.
Chart #2: AI Power Analysis (Actual vs Model 1 Expected vs Model 2 Short-Term Forecast).
"""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette


def render_power_timeline_chart(
    df: pd.DataFrame,
    selected_appliance: Optional[str] = None,
    theme: str = "dark"
) -> None:
    """
    Chart #1 — Real-Time Power Timeline
    X: timestamp, Y: power_w.
    Includes chronological ordering, readable time axis, hover tooltip, zoom, pan,
    overlaid estimated load trace for selected appliance, and interactive point selection.
    """
    from dashboard.config import APPLIANCE_META
    from dashboard.state import get_selected_appliance, set_selected_timestamp

    pal = get_theme_palette(theme)

    if df.empty or "datetime" not in df.columns or "power_w" not in df.columns:
        st.info("No historical telemetry available yet. Start the IoT simulation to populate the timeline.")
        return

    sel_app = selected_appliance or get_selected_appliance()
    fig = go.Figure()

    # 1. Main Power Stream Trace
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["power_w"],
            mode="lines",
            name="Measured Load",
            line=dict(color=pal["blue"], width=2.5, shape="spline", smoothing=0.3),
            fill="tozeroy",
            fillcolor=pal["blue_soft"],
            customdata=df[["power_w", "occupancy_str", "active_appliances_str"]].to_numpy(),
            hovertemplate=(
                "<b>Time:</b> %{x|%H:%M:%S}<br>"
                "<b>Power:</b> %{customdata[0]:,.0f} W<br>"
                "<b>Occupancy:</b> %{customdata[1]}<br>"
                "<b>Active Devices:</b> %{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )

    # 2. Overlaid Appliance Estimated Load (When an appliance is isolated)
    if sel_app and sel_app != "All Appliances":
        target_k = None
        target_meta = None
        for k, meta in APPLIANCE_META.items():
            if meta["name"].lower() == sel_app.lower() or k.lower() == sel_app.lower():
                target_k = k
                target_meta = meta
                break

        if target_k and target_k in df.columns:
            rated = float(target_meta["watts"])
            app_load = df[target_k] * rated
            fig.add_trace(
                go.Scatter(
                    x=df["datetime"],
                    y=app_load,
                    mode="lines",
                    name=f"{target_meta['name']} (Estimated Load)",
                    line=dict(color=target_meta.get("color", pal.get("orange", "#EE9B00")), width=2, dash="dot"),
                    hovertemplate=(
                        f"<b>{target_meta['name']} Estimated Load:</b> %{{y:,.0f}} W<br>"
                        "<i>(Derived from rated capacity × state)</i>"
                        "<extra></extra>"
                    ),
                )
            )

    # 3. Overlaid Anomaly Markers (Real records where is_anomaly == 1)
    anomalies = df[df["is_anomaly"] == 1]
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["datetime"],
                y=anomalies["power_w"],
                mode="markers",
                name="AI Anomaly",
                marker=dict(
                    color=pal["red"],
                    size=8,
                    symbol="diamond",
                    line=dict(color="#FFFFFF", width=1),
                ),
                customdata=anomalies[["power_w", "anomaly_score", "active_appliances_str"]].to_numpy(),
                hovertemplate=(
                    "<b>ANOMALY DETECTED</b><br>"
                    "<b>Time:</b> %{x|%H:%M:%S}<br>"
                    "<b>Power:</b> %{customdata[0]:,.0f} W<br>"
                    "<b>Isolation Score:</b> %{customdata[1]:+.3f}<br>"
                    "<b>Active Devices:</b> %{customdata[2]}"
                    "<extra></extra>"
                ),
            )
        )

    layout = get_apple_plotly_layout(theme=theme, height=320, title=None)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["title"] = "Time"
    fig.update_layout(layout)

    chart_event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="chart_power_timeline",
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": "hover", "responsive": True},
    )

    # Process interactive point selection from chart click
    if chart_event and hasattr(chart_event, "selection") and chart_event.selection:
        pts = getattr(chart_event.selection, "points", []) or chart_event.selection.get("points", [])
        if pts:
            pt_x = pts[0].get("x")
            if pt_x:
                set_selected_timestamp(str(pt_x))


def render_actual_vs_expected_vs_forecast_chart(
    df: pd.DataFrame,
    forecast_data: Optional[Dict[str, Any]] = None,
    theme: str = "dark"
) -> None:
    """
    Chart #2 — AI Power Analysis (Actual vs Expected vs Forecast)
    Actual: Measured Power.
    Expected: Model 1 Linear Regression load decomposition baseline.
    Forecast: Model 2 next-step autoregression.
    Honest methodology: Plots Model 2 at the forecasted horizon point rather than
    fabricating historical forecast points across time.
    """
    pal = get_theme_palette(theme)

    if df.empty or "datetime" not in df.columns:
        st.info("Insufficient telemetry to display AI load variance. Awaiting records.")
        return

    fig = go.Figure()

    # Trace 1: Actual Measured Power
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["power_w"],
            mode="lines",
            name="Actual Power",
            line=dict(color=pal["blue"], width=2.2),
            customdata=df[["power_w", "predicted_power_w", "occupancy_str"]].to_numpy(),
            hovertemplate=(
                "<b>Actual Power:</b> %{customdata[0]:,.0f} W<br>"
                "<b>Model 1 Expected:</b> %{customdata[1]:,.0f} W<br>"
                "<b>Occupancy:</b> %{customdata[2]}<br>"
                "<b>Time:</b> %{x|%H:%M:%S}"
                "<extra></extra>"
            ),
        )
    )

    # Trace 2: Expected Power (Model 1 Baseline)
    if "predicted_power_w" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["predicted_power_w"],
                mode="lines",
                name="Model 1 Expected Load",
                line=dict(color=pal["text_secondary"], width=2, dash="dash"),
                hovertemplate="<b>Expected Baseline:</b> %{y:,.0f} W<extra></extra>",
            )
        )

    # Trace 3: Model 2 Forecast Horizon Point (Honest methodology)
    if forecast_data and "predicted_next_power_w" in forecast_data:
        next_w = float(forecast_data["predicted_next_power_w"])
        last_dt = df["datetime"].iloc[-1]
        next_dt = last_dt + pd.Timedelta(seconds=2.5)

        # Plot projected step to next horizon
        fig.add_trace(
            go.Scatter(
                x=[last_dt, next_dt],
                y=[df["power_w"].iloc[-1], next_w],
                mode="lines+markers",
                name="Model 2 Forecast (+2.5s)",
                line=dict(color=pal["orange"], width=2.5, dash="dot"),
                marker=dict(size=7, color=pal["orange"], symbol="circle"),
                hovertemplate=(
                    "<b>Model 2 Short-Term Forecast:</b> %{y:,.0f} W<br>"
                    "<b>Horizon:</b> +2.5s"
                    "<extra></extra>"
                ),
            )
        )

    layout = get_apple_plotly_layout(theme=theme, height=320, title=None)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["title"] = "Time"
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": "hover", "responsive": True})
