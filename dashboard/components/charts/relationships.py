"""
Occupancy and Temperature Relationship Scatter Plots.
Chart #6: Occupancy vs Power Scatter.
Chart #7: Temperature vs Power Relationship.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette


def render_occupancy_vs_power_chart(df: pd.DataFrame, theme: str = "dark") -> None:
    """
    Chart #6 — Occupancy vs Power
    Scatter plot examining power distributions during Occupied vs Vacant states.
    Applies documented subtle jitter (+/- 0.06) on binary X for point separation.
    """
    pal = get_theme_palette(theme)

    if df.empty or "occupancy" not in df.columns or "power_w" not in df.columns:
        st.info("Insufficient telemetry observations to plot occupancy distribution.")
        return

    # Add subtle deterministic jitter to avoid overlap on binary axis (0 vs 1)
    np.random.seed(42)
    jitter = np.random.uniform(-0.06, 0.06, size=len(df))
    x_jittered = df["occupancy"] + jitter

    # Split into normal vs wasteful/anomalous for clear semantic separation
    is_waste_or_anom = (df["wasteful"] == 1) | (df["is_anomaly"] == 1)

    fig = go.Figure()

    # Normal points
    normal_df = df[~is_waste_or_anom]
    if not normal_df.empty:
        fig.add_trace(
            go.Scatter(
                x=x_jittered[~is_waste_or_anom],
                y=normal_df["power_w"],
                mode="markers",
                name="Normal Load",
                marker=dict(
                    color=pal["blue"],
                    size=7,
                    opacity=0.65,
                    line=dict(color=pal["border"], width=0.5),
                ),
                customdata=normal_df[["datetime", "occupancy_str", "power_w", "active_appliances_str"]].to_numpy(),
                hovertemplate=(
                    "<b>State:</b> Normal<br>"
                    "<b>Occupancy:</b> %{customdata[1]}<br>"
                    "<b>Power:</b> %{customdata[2]:,.0f} W<br>"
                    "<b>Time:</b> %{customdata[0]|%H:%M:%S}<br>"
                    "<b>Active:</b> %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )

    # Wasteful / Anomalous points
    alert_df = df[is_waste_or_anom]
    if not alert_df.empty:
        fig.add_trace(
            go.Scatter(
                x=x_jittered[is_waste_or_anom],
                y=alert_df["power_w"],
                mode="markers",
                name="Waste / Anomaly",
                marker=dict(
                    color=pal["orange"],
                    size=8,
                    symbol="diamond",
                    opacity=0.85,
                    line=dict(color="#FFFFFF", width=0.8),
                ),
                customdata=alert_df[["datetime", "occupancy_str", "power_w", "active_appliances_str"]].to_numpy(),
                hovertemplate=(
                    "<b>State:</b> Waste / Anomaly<br>"
                    "<b>Occupancy:</b> %{customdata[1]}<br>"
                    "<b>Power:</b> %{customdata[2]:,.0f} W<br>"
                    "<b>Time:</b> %{customdata[0]|%H:%M:%S}<br>"
                    "<b>Active:</b> %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["title"] = "Room Occupancy (with jitter)"
    layout["xaxis"]["tickmode"] = "array"
    layout["xaxis"]["tickvals"] = [0, 1]
    layout["xaxis"]["ticktext"] = ["Vacant", "Occupied"]
    layout["xaxis"]["range"] = [-0.25, 1.25]
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def render_temperature_vs_power_chart(df: pd.DataFrame, theme: str = "dark") -> None:
    """
    Chart #7 — Temperature vs Power
    Scatter plot tracking relationship between ambient temperature and household power.
    Color-coded by Air Conditioner operation (ON vs OFF).
    """
    pal = get_theme_palette(theme)

    if df.empty or "temperature" not in df.columns or "power_w" not in df.columns:
        st.info("Insufficient sensor observations to plot temperature correlation.")
        return

    ac_on = df["ac"] == 1

    fig = go.Figure()

    # AC OFF observations
    if not df[~ac_on].empty:
        sub = df[~ac_on]
        fig.add_trace(
            go.Scatter(
                x=sub["temperature"],
                y=sub["power_w"],
                mode="markers",
                name="AC OFF",
                marker=dict(
                    color=pal["gray"],
                    size=6,
                    opacity=0.6,
                ),
                customdata=sub[["datetime", "temperature", "power_w", "occupancy_str"]].to_numpy(),
                hovertemplate=(
                    "<b>AC State:</b> OFF<br>"
                    "<b>Temp:</b> %{customdata[1]:.1f} °C<br>"
                    "<b>Power:</b> %{customdata[2]:,.0f} W<br>"
                    "<b>Occupancy:</b> %{customdata[3]}<br>"
                    "<b>Time:</b> %{customdata[0]|%H:%M:%S}"
                    "<extra></extra>"
                ),
            )
        )

    # AC ON observations
    if not df[ac_on].empty:
        sub = df[ac_on]
        fig.add_trace(
            go.Scatter(
                x=sub["temperature"],
                y=sub["power_w"],
                mode="markers",
                name="AC ON",
                marker=dict(
                    color=pal["blue"],
                    size=8,
                    symbol="circle",
                    opacity=0.8,
                    line=dict(color=pal["border"], width=0.5),
                ),
                customdata=sub[["datetime", "temperature", "power_w", "occupancy_str"]].to_numpy(),
                hovertemplate=(
                    "<b>AC State:</b> ACTIVE<br>"
                    "<b>Temp:</b> %{customdata[1]:.1f} °C<br>"
                    "<b>Power:</b> %{customdata[2]:,.0f} W<br>"
                    "<b>Occupancy:</b> %{customdata[3]}<br>"
                    "<b>Time:</b> %{customdata[0]|%H:%M:%S}"
                    "<extra></extra>"
                ),
            )
        )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["title"] = "Ambient Temperature (°C)"
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
