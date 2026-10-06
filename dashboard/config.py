"""
Dashboard Configuration and Design Constants.
Centralizes Backend API URL, Refresh Intervals, Appliance Metadata, and Navigation.
"""

import os
from typing import Dict, Any, List

# Backend API Configuration
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT_SECONDS: float = float(os.getenv("API_TIMEOUT_SECONDS", "3.0"))

# Refresh Settings
DEFAULT_REFRESH_INTERVAL_SECONDS: float = 2.5
MIN_REFRESH_INTERVAL_SECONDS: float = 1.0
MAX_REFRESH_INTERVAL_SECONDS: float = 10.0

# Navigation Pages (Consolidated Minimum Pages)
NAV_PAGES: List[str] = [
    "Dashboard",
    "Analytics",
    "System"
]

# Time Range Options
TIME_RANGE_OPTIONS: List[str] = [
    "10 seconds",
    "1 minute",
    "5 minutes",
    "15 minutes",
    "1 hour",
    "Today",
    "All"
]

# Scenario Selector Options
SCENARIO_OPTIONS: List[str] = [
    "LIVE TELEMETRY",
    "NORMAL",
    "WASTEFUL",
    "HIGH LOAD",
    "SPIKE"
]

# Appliance Definition Mirroring Backend Config
# (Provides display names, ratings in Watts, and icon designations)
APPLIANCE_META: Dict[str, Dict[str, Any]] = {
    "ac": {
        "name": "Air Conditioner",
        "key": "ac",
        "watts": 1500,
        "category": "HVAC",
        "icon": "ac",
        "color": "#AE2012", # Secondary Crimson
    },
    "fan": {
        "name": "Ceiling Fan",
        "key": "fan",
        "watts": 75,
        "category": "Climate",
        "icon": "fan",
        "color": "#0A9396", # Secondary Teal
    },
    "tv": {
        "name": "Television",
        "key": "tv",
        "watts": 120,
        "category": "Entertainment",
        "icon": "tv",
        "color": "#005F73", # Secondary Deep Teal
    },
    "room_light": {
        "name": "Room Light",
        "key": "room_light",
        "watts": 20,
        "category": "Lighting",
        "icon": "light",
        "color": "#EE9B00", # Secondary Amber
    },
    "refrigerator": {
        "name": "Refrigerator",
        "key": "refrigerator",
        "watts": 150,
        "category": "Kitchen",
        "icon": "fridge",
        "color": "#94D2BD", # Secondary Sage
    },
    "heater": {
        "name": "Space Heater",
        "key": "heater",
        "watts": 2000,
        "category": "HVAC",
        "icon": "heater",
        "color": "#BB3E03", # Secondary Rust
    },
    "microwave": {
        "name": "Microwave Oven",
        "key": "microwave",
        "watts": 1000,
        "category": "Kitchen",
        "icon": "microwave",
        "color": "#CA6702", # Secondary Ochre
    },
}

# Appliance filter list for interaction state
APPLIANCE_FILTER_OPTIONS: List[str] = [
    "All Appliances",
    "AC",
    "Fan",
    "TV",
    "Room Light",
    "Refrigerator",
    "Heater",
    "Microwave"
]
