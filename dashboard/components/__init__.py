"""
Reusable UI Components for Smart Home Energy Dashboard (Phase 3.1).
Exposes 35+ Apple-inspired modular design components.
"""

# Layout & Shell
from dashboard.components.layout import (
    app_header,
    navigation_bar,
    empty_state,
    loading_state,
    error_state,
    expandable_detail_panel,
    chart_placeholder,
)

# Typography & Headers
from dashboard.components.typography import (
    page_title,
    section_header,
    card_title,
    caption,
    meta_tag,
)

# Status & Connectivity Indicators
from dashboard.components.status import (
    live_indicator,
    backend_connection_indicator,
    last_updated_indicator,
    data_freshness_indicator,
    system_status_panel,
    model_status_panel,
)

# Metric & KPI Cards
from dashboard.components.cards import (
    current_power_card,
    expected_power_card,
    forecast_power_card,
    energy_today_card,
    forecast_direction_indicator,
)

# Environmental Sensors
from dashboard.components.sensors import (
    temperature_card,
    humidity_card,
    occupancy_card,
    light_level_card,
)

# AI, Anomaly & Waste Alerts
from dashboard.components.alerts import (
    severity_badge,
    ai_status_card,
    anomaly_score_card,
    waste_alert_card,
    ai_explanation_panel,
)

# Recommendations & Actions
from dashboard.components.recommendations import (
    recommendation_panel,
    action_items_panel,
)

# Appliances
from dashboard.components.appliances import (
    appliance_grid,
    appliance_status_card,
    appliance_wattage_badge,
)

# User Controls & Navigation Architecture
from dashboard.components.controls import (
    time_range_selector,
    live_pause_control,
    refresh_control,
    scenario_selector,
)

# Phase 3.3 Energy Intelligence & Diagnostics
from dashboard.components.intelligence import (
    render_ai_explanation_panel,
    render_forecast_intelligence_card,
    render_telemetry_investigation_panel,
    render_anomaly_investigation_panel,
    render_appliance_detail_panel,
)

__all__ = [
    # 1-4 Header & Connectivity
    "app_header",
    "navigation_bar",
    "live_indicator",
    "backend_connection_indicator",
    # 5-8 KPIs
    "current_power_card",
    "expected_power_card",
    "forecast_power_card",
    "energy_today_card",
    # 9-12 Sensors
    "temperature_card",
    "humidity_card",
    "occupancy_card",
    "light_level_card",
    # 13-16 AI & Anomaly
    "ai_status_card",
    "anomaly_score_card",
    "waste_alert_card",
    "severity_badge",
    # 17-18 Recommendations
    "recommendation_panel",
    "action_items_panel",
    # 19-21 Appliances
    "appliance_grid",
    "appliance_status_card",
    "appliance_wattage_badge",
    # 22-24 Trends & Timestamps
    "forecast_direction_indicator",
    "last_updated_indicator",
    "data_freshness_indicator",
    # 25-28 Controls
    "time_range_selector",
    "live_pause_control",
    "refresh_control",
    "scenario_selector",
    # 29-31 System & Model Diagnostics
    "ai_explanation_panel",
    "system_status_panel",
    "model_status_panel",
    # 32-35 Lifecycle States
    "empty_state",
    "loading_state",
    "error_state",
    "expandable_detail_panel",
    # Bonus Utilities
    "chart_placeholder",
    "page_title",
    "section_header",
    "card_title",
    "caption",
    "meta_tag",
    # Phase 3.3 Intelligence Components
    "render_ai_explanation_panel",
    "render_forecast_intelligence_card",
    "render_telemetry_investigation_panel",
    "render_anomaly_investigation_panel",
    "render_appliance_detail_panel",
]
