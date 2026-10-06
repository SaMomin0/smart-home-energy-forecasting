"""
Power Flow Sankey and Load Waterfall Decomposition Charts.
Chart #9: Current Power Flow (Sankey).
Chart #10: Appliance Load Waterfall Breakdown.
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.chart_data import calculate_appliance_contributions, prepare_waterfall_decomposition
from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette
from dashboard.utils.formatting import render_html


def render_power_flow_sankey(
    appliances_dict: Optional[Dict[str, Any]],
    current_power_w: Optional[float] = None,
    theme: str = "dark"
) -> None:
    """
    Chart #9 — Current Power Flow (Sankey)
    Flows from Total Household Influx down to active appliances.
    Accurately labeled 'Current Power Flow' to reflect instantaneous wattage.
    """
    pal = get_theme_palette(theme)
    contrib_df = calculate_appliance_contributions(appliances_dict)
    active_df = contrib_df[contrib_df["is_on"]].copy()

    total_w = float(current_power_w) if current_power_w is not None else active_df["active_watts"].sum()

    if total_w <= 0 or (active_df.empty and total_w < 5.0):
        render_html(
            f"""
            <div style="background:{pal['card_bg']}; border:1px solid {pal['border']}; border-radius:18px; padding:2rem; text-align:center;">
                <div style="font-size:1.1rem; font-weight:600; color:{pal['text']};">Zero Power Influx</div>
                <div style="font-size:0.8rem; color:{pal['text_secondary']}; margin-top:0.35rem;">
                    Household is completely powered down (0 W total active draw).
                </div>
            </div>
            """
        )
        return

    # Build nodes: Node 0 is "Total Influx"
    node_labels = ["Total Household Load"]
    node_colors = [pal["blue"]]
    sources = []
    targets = []
    values = []
    link_colors = []

    sum_active = 0.0
    for _, row in active_df.iterrows():
        node_labels.append(row["name"])
        node_colors.append(row["color"])
        target_idx = len(node_labels) - 1
        sources.append(0)
        targets.append(target_idx)
        w = row["active_watts"]
        values.append(w)
        sum_active += w
        # Semi-transparent link color
        link_colors.append(row["color"])

    # Unmetered standby / baseline if total exceeds sum
    standby = max(0.0, total_w - sum_active)
    if standby > 0:
        node_labels.append("Standby & Phantom")
        node_colors.append(pal["gray"])
        target_idx = len(node_labels) - 1
        sources.append(0)
        targets.append(target_idx)
        values.append(standby)
        link_colors.append("rgba(134, 134, 139, 0.4)")

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=16,
                    thickness=16,
                    line=dict(color=pal["border"], width=1),
                    label=node_labels,
                    color=node_colors,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    hovertemplate=(
                        "<b>Flow:</b> %{source.label} → %{target.label}<br>"
                        "<b>Power:</b> %{value:,.0f} W<extra></extra>"
                    ),
                ),
            )
        ]
    )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None, showlegend=False)
    layout["margin"] = dict(l=20, r=20, t=20, b=20)
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def render_energy_waterfall_chart(
    appliances_dict: Optional[Dict[str, Any]],
    current_power_w: Optional[float] = None,
    theme: str = "dark"
) -> None:
    """
    Chart #10 — Appliance Load Waterfall Breakdown
    Mathematically sound additive decomposition of active appliance draws summing to Total Power.
    """
    pal = get_theme_palette(theme)
    steps = prepare_waterfall_decomposition(appliances_dict, current_power_w)

    if not steps or steps[-1]["value"] <= 0:
        st.info("No active loads to decompose into a waterfall breakdown.")
        return

    x_labels = [s["name"] for s in steps]
    measure = ["relative" if s["type"] == "relative" else "total" for s in steps]
    y_vals = [s["value"] for s in steps]
    text_vals = [s["text"] for s in steps]

    fig = go.Figure(
        go.Waterfall(
            name="Load Waterfall",
            orientation="v",
            measure=measure,
            x=x_labels,
            textposition="outside",
            text=text_vals,
            y=y_vals,
            connector=dict(line=dict(color=pal["grid"], width=1, dash="dot")),
            increasing=dict(marker=dict(color=pal["blue"])),
            totals=dict(marker=dict(color=pal["green"])),
            textfont=dict(size=11, color=pal["text"]),
            hovertemplate="<b>%{x}</b>: %{text}<extra></extra>",
        )
    )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None, showlegend=False)
    layout["yaxis"]["title"] = "Power (Watts)"
    layout["xaxis"]["tickfont"] = dict(size=10, color=pal["text"])
    layout["margin"] = dict(l=45, r=25, t=25, b=35)
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
