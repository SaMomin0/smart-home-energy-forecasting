"""
Appliance Load Contribution and Current Load Composition Charts.
Chart #3: Horizontal bar chart showing active watts and percentage per appliance.
Chart #4: Donut chart displaying current load composition.
"""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.chart_data import calculate_appliance_contributions
from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette
from dashboard.utils.formatting import render_html


def render_appliance_contribution_chart(appliances_dict: Optional[Dict[str, Any]], theme: str = "dark") -> None:
    """
    Chart #3 — Appliance Load Contribution
    Horizontal bar chart sorted descending by active wattage.
    Shows rated wattage if ON, 0 if OFF, with load percentage.
    """
    pal = get_theme_palette(theme)
    contrib_df = calculate_appliance_contributions(appliances_dict)

    if contrib_df.empty:
        st.info("No appliance status telemetry received.")
        return

    # Invert order for horizontal bar chart so top item renders at the top
    plot_df = contrib_df.iloc[::-1].reset_index(drop=True)

    # Bar text with watts and percentage
    text_labels = []
    for _, r in plot_df.iterrows():
        if r["is_on"] and r["percentage"] > 0:
            text_labels.append(f"{int(r['active_watts']):,} W ({r['percentage']:.1f}%)")
        elif r["is_on"]:
            text_labels.append(f"{int(r['active_watts']):,} W")
        else:
            text_labels.append("OFF (0 W)")

    fig = go.Figure(
        go.Bar(
            x=plot_df["active_watts"],
            y=plot_df["name"],
            orientation="h",
            marker=dict(
                color=[r["color"] if r["is_on"] else pal["border"] for _, r in plot_df.iterrows()],
                line=dict(color=pal["border"], width=1),
            ),
            text=text_labels,
            textposition="auto",
            textfont=dict(size=11, color=pal["text"]),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "<b>Active Draw:</b> %{x:,} W<br>"
                "<extra></extra>"
            ),
        )
    )

    layout = get_apple_plotly_layout(theme=theme, height=310, title=None, showlegend=False)
    layout["xaxis"]["title"] = "Active Load (Watts)"
    layout["yaxis"]["tickfont"] = dict(size=11, color=pal["text"])
    layout["margin"] = dict(l=110, r=25, t=15, b=35)
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def render_energy_composition_chart(appliances_dict: Optional[Dict[str, Any]], theme: str = "dark") -> None:
    """
    Chart #4 — Current Load Composition
    Apple-styled Donut chart representing current active load distribution.
    Clearly labeled 'Current Load Composition' to reflect instantaneous telemetry.
    """
    pal = get_theme_palette(theme)
    contrib_df = calculate_appliance_contributions(appliances_dict)
    active_df = contrib_df[contrib_df["is_on"]].copy()

    if active_df.empty or active_df["active_watts"].sum() == 0:
        render_html(
            f"""
            <div style="background:{pal['card_bg']}; border:1px solid {pal['border']}; border-radius:18px; padding:2rem; text-align:center;">
                <div style="font-size:1.1rem; font-weight:600; color:{pal['text']};">All Appliances Idle</div>
                <div style="font-size:0.8rem; color:{pal['text_secondary']}; margin-top:0.35rem;">
                    Household is currently drawing minimal standby power (0 W active appliance load).
                </div>
            </div>
            """
        )
        return

    fig = go.Figure(
        go.Pie(
            labels=active_df["name"],
            values=active_df["active_watts"],
            hole=0.62,
            marker=dict(
                colors=active_df["color"].tolist(),
                line=dict(color=pal["card_bg"], width=2),
            ),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=10, color=pal["text"]),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "<b>Active Load:</b> %{value:,} W<br>"
                "<b>Share:</b> %{percent}<extra></extra>"
            ),
        )
    )

    total_w = int(active_df["active_watts"].sum())
    layout = get_apple_plotly_layout(theme=theme, height=310, title=None, showlegend=False)
    layout["margin"] = dict(l=30, r=30, t=25, b=25)
    layout["annotations"] = [
        dict(
            text=f"<b>{total_w:,}</b><br><span style='font-size:10px; color:{pal['text_secondary']}'>WATTS</span>",
            x=0.5,
            y=0.5,
            font=dict(size=17, color=pal["text"]),
            showarrow=False,
        )
    ]
    fig.update_layout(layout)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
