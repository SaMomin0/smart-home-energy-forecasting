"""
SQLite Database Layer for Persistent Telemetry and AI Inference Storage.
Stores real-time telemetry from Phase 1 and exports historical energy datasets to CSV.
"""

import sqlite3
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import DATABASE_PATH, CSV_PATH

logger = logging.getLogger("smart_home.database")

CREATE_TELEMETRY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    uptime_ms INTEGER DEFAULT 0,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    occupancy INTEGER NOT NULL,
    light_level INTEGER NOT NULL,
    ac INTEGER NOT NULL,
    fan INTEGER NOT NULL,
    tv INTEGER NOT NULL,
    room_light INTEGER NOT NULL,
    refrigerator INTEGER NOT NULL,
    heater INTEGER NOT NULL,
    microwave INTEGER NOT NULL,
    power_w INTEGER NOT NULL,
    energy_wh REAL DEFAULT 0.0,
    energy_kwh REAL DEFAULT 0.0,
    predicted_power_w REAL,
    prediction_error_w REAL,
    is_anomaly INTEGER DEFAULT 0,
    anomaly_score REAL DEFAULT 0.0,
    wasteful INTEGER DEFAULT 0,
    severity TEXT DEFAULT 'NORMAL',
    status_msg TEXT,
    recommendation TEXT
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry (timestamp);
"""


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory enabled."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and indexes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CREATE_TELEMETRY_TABLE_SQL)
        cursor.execute(CREATE_INDEX_SQL)
        conn.commit()
    logger.info(f"Database initialized at {DATABASE_PATH}")


def save_telemetry(record: Dict[str, Any]) -> int:
    """
    Inserts a processed telemetry record into the database.
    Returns the inserted row ID.
    """
    sql = """
    INSERT INTO telemetry (
        timestamp, uptime_ms, temperature, humidity, occupancy, light_level,
        ac, fan, tv, room_light, refrigerator, heater, microwave,
        power_w, energy_wh, energy_kwh, predicted_power_w, prediction_error_w,
        is_anomaly, anomaly_score, wasteful, severity, status_msg, recommendation
    ) VALUES (
        :timestamp, :uptime_ms, :temperature, :humidity, :occupancy, :light_level,
        :ac, :fan, :tv, :room_light, :refrigerator, :heater, :microwave,
        :power_w, :energy_wh, :energy_kwh, :predicted_power_w, :prediction_error_w,
        :is_anomaly, :anomaly_score, :wasteful, :severity, :status_msg, :recommendation
    )
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, record)
        inserted_id = cursor.lastrowid
        conn.commit()
    return inserted_id


def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    """Fetches the single most recent telemetry entry."""
    sql = "SELECT * FROM telemetry ORDER BY id DESC LIMIT 1"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches the last N historical records in reverse chronological order."""
    limit = min(max(1, limit), 1000)
    sql = "SELECT * FROM telemetry ORDER BY id DESC LIMIT ?"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_telemetry_count() -> int:
    """Returns total number of telemetry records in SQLite."""
    sql = "SELECT COUNT(*) as count FROM telemetry"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        return row["count"] if row else 0


def export_to_csv(target_path: Optional[Path] = None) -> int:
    """
    Exports all records from SQLite table 'telemetry' to a structured CSV file.
    Returns the count of exported records.
    """
    out_file = target_path or CSV_PATH
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sql = "SELECT * FROM telemetry ORDER BY id ASC"
    count = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            logger.warning("No records in database to export to CSV.")
            return 0

        fieldnames = [col[0] for col in cursor.description]
        with open(out_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(dict(r))
                count += 1

    logger.info(f"Exported {count} records from SQLite to CSV at {out_file}")
    return count
