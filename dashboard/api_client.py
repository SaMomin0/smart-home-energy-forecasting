"""
Centralized Backend API Client for Dashboard.
Handles HTTP requests, network timeouts, error recovery, and data normalization.
Provides a unified data layer so UI components never make direct ad-hoc HTTP calls.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
import requests

from dashboard.config import BACKEND_URL, API_TIMEOUT_SECONDS
from dashboard.utils.data import normalize_analysis_payload

logger = logging.getLogger("dashboard.api_client")


class ApiClient:
    """Client for communicating with the FastAPI Smart Home backend."""

    def __init__(self, base_url: str = BACKEND_URL, timeout: float = API_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._last_error: Optional[str] = None
        self._is_online: bool = False

    @property
    def is_online(self) -> bool:
        return self._is_online

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Queries GET /health.
        Returns:
            (is_online: bool, health_data: dict)
        """
        url = f"{self.base_url}/health"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                self._is_online = True
                self._last_error = None
                return True, resp.json()
            else:
                self._is_online = False
                self._last_error = f"Health check returned HTTP {resp.status_code}"
                return False, {"status": "degraded", "error": self._last_error}
        except requests.exceptions.ConnectionError:
            self._is_online = False
            self._last_error = f"Cannot connect to backend at {self.base_url}. Connection refused."
            return False, {"status": "offline", "error": self._last_error}
        except requests.exceptions.Timeout:
            self._is_online = False
            self._last_error = f"Connection to {self.base_url} timed out after {self.timeout}s."
            return False, {"status": "offline", "error": self._last_error}
        except Exception as e:
            self._is_online = False
            self._last_error = f"Health check failed: {str(e)}"
            return False, {"status": "error", "error": self._last_error}

    def fetch_analysis(self) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Queries GET /analysis for the unified real-time dashboard state.
        Returns:
            (success: bool, normalized_payload: dict, error_message: Optional[str])
        """
        url = f"{self.base_url}/analysis"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                self._is_online = True
                self._last_error = None
                normalized = normalize_analysis_payload(resp.json())
                return True, normalized, None
            elif resp.status_code == 404:
                # Backend is running but database is empty
                self._is_online = True
                msg = "No telemetry received yet. Start the Wokwi simulation or seed the database."
                self._last_error = msg
                return False, normalize_analysis_payload({}), msg
            else:
                self._is_online = False
                msg = f"Backend returned HTTP {resp.status_code}: {resp.text[:100]}"
                self._last_error = msg
                return False, normalize_analysis_payload({}), msg
        except requests.exceptions.RequestException as req_err:
            self._is_online = False
            msg = f"Backend unavailable: {req_err}"
            self._last_error = msg
            return False, normalize_analysis_payload({}), msg
        except Exception as ex:
            msg = f"Unexpected error reading analysis: {ex}"
            self._last_error = msg
            return False, normalize_analysis_payload({}), msg

    def fetch_history(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Queries GET /history?limit=N for historical time-series data.
        """
        url = f"{self.base_url}/history?limit={limit}"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    def fetch_latest(self) -> Optional[Dict[str, Any]]:
        """Queries GET /latest for the latest raw telemetry frame."""
        url = f"{self.base_url}/latest"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def fetch_forecast(self) -> Optional[Dict[str, Any]]:
        """Queries GET /forecast for Model 2 short-term power forecast."""
        url = f"{self.base_url}/forecast"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def trigger_scenario(self, scenario: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sends POST /scenario to inject canonical scenario telemetry through backend pipeline.
        Returns (success, response_dict, error_message).
        """
        url = f"{self.base_url}/scenario"
        try:
            resp = requests.post(url, json={"scenario": scenario}, timeout=self.timeout)
            if resp.status_code == 200:
                return True, resp.json(), None
            else:
                return False, None, f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, None, str(e)


# Global API Client Instance
_api_client_instance: Optional[ApiClient] = None


def get_api_client() -> ApiClient:
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = ApiClient()
    return _api_client_instance
