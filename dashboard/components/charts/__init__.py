"""
Interactive Visualization Engine Components for Phase 3.2.
Exposes all 10 Apple-inspired Plotly charts.
"""

from dashboard.components.charts.theme import get_apple_plotly_layout, get_theme_palette
from dashboard.components.charts.power import (
    render_power_timeline_chart,
    render_actual_vs_expected_vs_forecast_chart,
)
from dashboard.components.charts.appliances import (
    render_appliance_contribution_chart,
    render_energy_composition_chart,
)
from dashboard.components.charts.patterns import render_energy_pattern_heatmap
from dashboard.components.charts.relationships import (
    render_occupancy_vs_power_chart,
    render_temperature_vs_power_chart,
)
from dashboard.components.charts.anomalies import render_anomaly_timeline_chart
from dashboard.components.charts.flows import (
    render_power_flow_sankey,
    render_energy_waterfall_chart,
)

__all__ = [
    "get_apple_plotly_layout",
    "get_theme_palette",
    # 1. Power Timeline
    "render_power_timeline_chart",
    # 2. Actual vs Expected vs Forecast
    "render_actual_vs_expected_vs_forecast_chart",
    # 3. Appliance Contribution
    "render_appliance_contribution_chart",
    # 4. Energy / Load Composition
    "render_energy_composition_chart",
    # 5. Day x Hour Heatmap
    "render_energy_pattern_heatmap",
    # 6. Occupancy vs Power
    "render_occupancy_vs_power_chart",
    # 7. Temperature vs Power
    "render_temperature_vs_power_chart",
    # 8. Anomaly Timeline
    "render_anomaly_timeline_chart",
    # 9. Power Flow Sankey
    "render_power_flow_sankey",
    # 10. Load Waterfall
    "render_energy_waterfall_chart",
]
