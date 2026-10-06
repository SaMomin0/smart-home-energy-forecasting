"""
Environmental Sensor Cards.
Temperature, Humidity, Occupancy, and Light Level.
Directly consumes real sensor readings from analysis.sensors.
"""

from typing import Optional
import streamlit as st

from dashboard.utils.formatting import (
    format_temp,
    format_humidity,
    format_occupancy,
    format_lux,
    get_icon,
    render_html,
)


def temperature_card(temp_c: Optional[float]) -> None:
    """
    Renders the Ambient Temperature Card.
    Source: analysis.sensors.temperature
    """
    val_str = format_temp(temp_c)
    icon_svg = get_icon("thermometer", size=18, color="var(--warning)")
    
    # Context note based on standard comfort range
    note = "Normal comfort range"
    if temp_c is not None:
        if temp_c > 30.0:
            note = "Warm / Cooling recommended"
        elif temp_c < 20.0:
            note = "Cool / Heating recommended"

    render_html(
        f"""
        <div class="apple-card sensor-card">
            <div class="sensor-header">
                <span class="sensor-name">Ambient Temp</span>
                <span class="sensor-icon" style="color:var(--warning);">{icon_svg}</span>
            </div>
            <div class="sensor-val">{val_str}</div>
            <div class="sensor-sub">{note}</div>
        </div>
        """
    )


def humidity_card(humidity_pct: Optional[float]) -> None:
    """
    Renders the Relative Humidity Card.
    Source: analysis.sensors.humidity
    """
    val_str = format_humidity(humidity_pct)
    icon_svg = get_icon("droplet", size=18, color="var(--accent)")
    
    note = "Optimal humidity"
    if humidity_pct is not None:
        if humidity_pct > 65.0:
            note = "Elevated humidity"
        elif humidity_pct < 35.0:
            note = "Dry environment"

    render_html(
        f"""
        <div class="apple-card sensor-card">
            <div class="sensor-header">
                <span class="sensor-name">Relative Humidity</span>
                <span class="sensor-icon" style="color:var(--accent);">{icon_svg}</span>
            </div>
            <div class="sensor-val">{val_str}</div>
            <div class="sensor-sub">{note}</div>
        </div>
        """
    )


def occupancy_card(occupancy: Optional[int]) -> None:
    """
    Renders the Room Occupancy Card.
    Source: analysis.sensors.occupancy (1=Occupied, 0=Vacant)
    """
    state_str = format_occupancy(occupancy)
    is_occ = (occupancy == 1)
    
    icon_name = "user" if is_occ else "user-x"
    icon_color = "var(--success)" if is_occ else "var(--text-tertiary)"
    icon_svg = get_icon(icon_name, size=18, color=icon_color)
    
    badge_class = "online" if is_occ else "offline"
    badge_label = "PIR Active" if is_occ else "No Motion"

    render_html(
        f"""
        <div class="apple-card sensor-card">
            <div class="sensor-header">
                <span class="sensor-name">Room Occupancy</span>
                <span class="sensor-icon">{icon_svg}</span>
            </div>
            <div class="sensor-val" style="display:flex; align-items:baseline; gap:0.4rem;">
                <span>{state_str}</span>
            </div>
            <div class="sensor-sub">
                <span class="status-chip {badge_class}" style="font-size:0.68rem; padding:0.15rem 0.45rem;">{badge_label}</span>
            </div>
        </div>
        """
    )


def light_level_card(light_level: Optional[int]) -> None:
    """
    Renders the Ambient Light Level Card.
    Source: analysis.sensors.light_level (LDR sensor reading)
    """
    val_str = format_lux(light_level)
    icon_svg = get_icon("sun", size=18, color="var(--warning)")
    
    note = "Ambient Light"
    if light_level is not None:
        if light_level > 500:
            note = "Daylight / Well-lit"
        elif light_level < 100:
            note = "Dim / Dark room"
        else:
            note = "Normal indoor light"

    render_html(
        f"""
        <div class="apple-card sensor-card">
            <div class="sensor-header">
                <span class="sensor-name">Ambient Illuminance</span>
                <span class="sensor-icon" style="color:var(--warning);">{icon_svg}</span>
            </div>
            <div class="sensor-val">{val_str}</div>
            <div class="sensor-sub">{note}</div>
        </div>
        """
    )
