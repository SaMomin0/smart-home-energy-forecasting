"""
Tests for Phase 3.2: Interactive Visualization Engine & Chart Data Pipeline.
Verifies data transformations, time-range filtering, appliance attribution,
heatmap matrix aggregation, waterfall decomposition, and empty/null handling.
"""

import unittest
from datetime import datetime, timezone
import numpy as np
import pandas as pd

from dashboard.utils.chart_data import (
    normalize_history,
    filter_by_time_range,
    calculate_appliance_contributions,
    prepare_heatmap_matrix,
    prepare_waterfall_decomposition,
)
from dashboard.components.charts.theme import (
    get_apple_plotly_layout,
    get_theme_palette,
)
from dashboard.components.charts import (
    render_power_timeline_chart,
    render_actual_vs_expected_vs_forecast_chart,
    render_appliance_contribution_chart,
    render_energy_composition_chart,
    render_energy_pattern_heatmap,
    render_occupancy_vs_power_chart,
    render_temperature_vs_power_chart,
    render_anomaly_timeline_chart,
    render_power_flow_sankey,
    render_energy_waterfall_chart,
)


class TestChartDataPipeline(unittest.TestCase):
    """Verifies telemetry normalization, timestamp parsing, and filtering."""

    def setUp(self):
        # Sample realistic historical records
        self.sample_history = [
            {
                "id": 103,
                "timestamp": "2026-10-04T12:00:10.000000+00:00",
                "power_w": 2500,
                "predicted_power_w": 2500.0,
                "temperature": 27.5,
                "humidity": 55.0,
                "occupancy": 1,
                "light_level": 500,
                "ac": 1,
                "fan": 0,
                "tv": 0,
                "room_light": 0,
                "refrigerator": 1,
                "heater": 0,
                "microwave": 0,
                "is_anomaly": 0,
                "anomaly_score": 0.12,
                "wasteful": 0,
                "severity": "NORMAL",
            },
            {
                "id": 102,
                "timestamp": "2026-10-04T12:00:05.000000+00:00",
                "power_w": 4500,
                "predicted_power_w": 4500.0,
                "temperature": 28.0,
                "humidity": 56.0,
                "occupancy": 1,
                "light_level": 500,
                "ac": 1,
                "fan": 0,
                "tv": 0,
                "room_light": 0,
                "refrigerator": 1,
                "heater": 1,
                "microwave": 0,
                "is_anomaly": 1,
                "anomaly_score": -0.045,
                "wasteful": 1,
                "severity": "CRITICAL",
            },
            {
                "id": 101,
                "timestamp": "2026-10-04T12:00:00.000000+00:00",
                "power_w": 150,
                "predicted_power_w": 150.0,
                "temperature": 26.5,
                "humidity": 50.0,
                "occupancy": 0,
                "light_level": 100,
                "ac": 0,
                "fan": 0,
                "tv": 0,
                "room_light": 0,
                "refrigerator": 1,
                "heater": 0,
                "microwave": 0,
                "is_anomaly": 0,
                "anomaly_score": 0.18,
                "wasteful": 0,
                "severity": "NORMAL",
            },
        ]

    def test_normalize_history_chronological_sort(self):
        df = normalize_history(self.sample_history)
        self.assertEqual(len(df), 3)
        # Verify oldest record is first
        self.assertEqual(df["id"].iloc[0], 101)
        self.assertEqual(df["id"].iloc[-1], 103)
        self.assertTrue(df["datetime"].is_monotonic_increasing)

    def test_normalize_history_derived_fields(self):
        df = normalize_history(self.sample_history)
        self.assertIn("occupancy_str", df.columns)
        self.assertIn("active_appliances_str", df.columns)
        # Row 101 (occupancy=0) -> "Vacant"
        self.assertEqual(df.loc[df["id"] == 101, "occupancy_str"].iloc[0], "Vacant")
        # Row 103 (occupancy=1) -> "Occupied"
        self.assertEqual(df.loc[df["id"] == 103, "occupancy_str"].iloc[0], "Occupied")

    def test_empty_and_null_history(self):
        empty_df = normalize_history([])
        self.assertTrue(empty_df.empty)
        self.assertIn("datetime", empty_df.columns)
        self.assertIn("power_w", empty_df.columns)

        none_df = normalize_history(None)
        self.assertTrue(none_df.empty)

    def test_time_range_filtering(self):
        df = normalize_history(self.sample_history)
        # Records span 10 seconds: 12:00:00, 12:00:05, 12:00:10
        # 10 seconds from 12:00:10 includes all 3
        f_10s = filter_by_time_range(df, "10 seconds")
        self.assertEqual(len(f_10s), 3)

        # "All" returns all
        f_all = filter_by_time_range(df, "All")
        self.assertEqual(len(f_all), 3)

        # Empty fallback
        f_empty = filter_by_time_range(pd.DataFrame(), "5 minutes")
        self.assertTrue(f_empty.empty)


class TestApplianceAndFlowTransformations(unittest.TestCase):
    """Verifies appliance contributions, donut composition, Sankey and Waterfall logic."""

    def test_calculate_appliance_contributions(self):
        appliances = {"ac": 1, "refrigerator": 1, "room_light": 0}
        contrib_df = calculate_appliance_contributions(appliances)

        # AC rated 1500W, Refrigerator rated 150W -> Total 1650W
        ac_row = contrib_df[contrib_df["key"] == "ac"].iloc[0]
        self.assertTrue(ac_row["is_on"])
        self.assertEqual(ac_row["active_watts"], 1500)

        light_row = contrib_df[contrib_df["key"] == "room_light"].iloc[0]
        self.assertFalse(light_row["is_on"])
        self.assertEqual(light_row["active_watts"], 0)

        # Verify sorted descending
        self.assertTrue(contrib_df["active_watts"].iloc[0] >= contrib_df["active_watts"].iloc[1])

        # Verify percentages sum to 100% across active
        total_pct = contrib_df["percentage"].sum()
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_waterfall_decomposition_additive_integrity(self):
        # 1500W (AC) + 150W (Fridge) = 1650W. If total_power_w is 1700W, standby = 50W.
        appliances = {"ac": 1, "refrigerator": 1}
        steps = prepare_waterfall_decomposition(appliances, current_power_w=1700)

        self.assertTrue(len(steps) >= 3)
        # Final step must be total
        self.assertEqual(steps[-1]["type"], "total")
        self.assertEqual(steps[-1]["value"], 1700)

        # Sum of relatives must equal total
        relative_sum = sum(s["value"] for s in steps if s["type"] == "relative")
        self.assertEqual(relative_sum, 1700)

    def test_heatmap_matrix_aggregation(self):
        # Create timestamps over 2 different days
        records = [
            {"timestamp": "2026-10-04T10:00:00Z", "power_w": 1200}, # Sunday 10:00
            {"timestamp": "2026-10-04T10:30:00Z", "power_w": 1800}, # Sunday 10:00
            {"timestamp": "2026-10-05T14:00:00Z", "power_w": 800},  # Monday 14:00
        ]
        df = normalize_history(records)
        matrix, days, hours = prepare_heatmap_matrix(df)

        self.assertEqual(matrix.shape, (7, 24))
        self.assertEqual(len(days), 7)
        self.assertEqual(len(hours), 24)

        # Sunday is index 6, Hour 10 average should be (1200+1800)/2 = 1500
        sun_idx = days.index("Sunday")
        self.assertEqual(matrix[sun_idx, 10], 1500.0)

        # Monday is index 0, Hour 14 average should be 800
        mon_idx = days.index("Monday")
        self.assertEqual(matrix[mon_idx, 14], 800.0)


class TestPlotlyThemeAndLayout(unittest.TestCase):
    """Verifies Plotly theme generation for Light and Dark modes."""

    def test_theme_layouts(self):
        dark_layout = get_apple_plotly_layout(theme="dark", height=320)
        self.assertEqual(dark_layout["height"], 320)
        self.assertIn("font", dark_layout)

        light_layout = get_apple_plotly_layout(theme="light", height=400)
        self.assertEqual(light_layout["height"], 400)

    def test_theme_palettes(self):
        dark_pal = get_theme_palette("dark")
        light_pal = get_theme_palette("light")
        self.assertIn("blue", dark_pal)
        self.assertIn("red", dark_pal)
        self.assertNotEqual(dark_pal["card_bg"], light_pal["card_bg"])


if __name__ == "__main__":
    unittest.main()
