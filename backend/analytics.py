"""Time series analytics scaffolding for GuardianEye defense event analysis."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from pandas import DataFrame, Series
from statsmodels.tsa.seasonal import DecomposeResult, seasonal_decompose


class TimeSeriesAnalytics:
    """Provide reusable statistical utilities for alert trend exploration."""

    def __init__(self, frame: DataFrame) -> None:
        """Initialize analytics helper with required datetime column validation."""
        if frame.empty:
            raise ValueError("Input DataFrame must not be empty.")
        if "start_time" not in frame.columns:
            raise ValueError("Input DataFrame must contain a `start_time` column.")

        self.frame: DataFrame = frame.copy()
        self.frame["start_time"] = pd.to_datetime(self.frame["start_time"], utc=True, errors="coerce")
        self.frame = self.frame.dropna(subset=["start_time"])

        if self.frame.empty:
            raise ValueError("No valid `start_time` values available for analysis.")

    def hourly_frequency_analysis(self) -> Series:
        """Return hourly alert frequency as a pandas Series indexed by timestamp."""
        try:
            hourly_series: Series = self.frame.set_index("start_time").resample("H").size()
            return hourly_series.rename("alert_count")
        except Exception as exc:
            raise RuntimeError("Failed to compute hourly frequency analysis.") from exc

    def regional_heat_calculations(self) -> DataFrame:
        """Compute regional heat table by counting alerts per region and date."""
        if "region" not in self.frame.columns:
            raise ValueError("Input DataFrame must contain a `region` column.")

        try:
            daily: DataFrame = self.frame.assign(date=self.frame["start_time"].dt.date)
            heat_table: DataFrame = (
                daily.groupby(["region", "date"]).size().rename("alert_count").reset_index()
            )
            return heat_table
        except Exception as exc:
            raise RuntimeError("Failed to compute regional heat calculations.") from exc

    def seasonality_decomposition(self, period: int = 24) -> Optional[DecomposeResult]:
        """Run additive seasonality decomposition over hourly frequency counts."""
        if period <= 1:
            raise ValueError("`period` must be greater than 1.")

        try:
            signal: Series = self.hourly_frequency_analysis()
            if signal.shape[0] < period * 2:
                return None
            return seasonal_decompose(signal, model="additive", period=period)
        except ValueError:
            return None
        except Exception as exc:
            raise RuntimeError("Unexpected error while running seasonality decomposition.") from exc


def summarize_risk_indicators(frame: DataFrame) -> Dict[str, Any]:
    """Generate summary risk indicators suitable for dashboard-level KPIs."""
    if frame.empty:
        return {"total_alerts": 0, "avg_duration_minutes": 0.0, "critical_alert_ratio": 0.0}

    safe_frame: DataFrame = frame.copy()
    safe_frame["duration"] = pd.to_numeric(safe_frame.get("duration"), errors="coerce").fillna(0)

    total_alerts: int = int(len(safe_frame))
    avg_duration: float = float(safe_frame["duration"].mean())
    critical_ratio: float = 0.0

    try:
        if "risk_level" in safe_frame.columns:
            critical_ratio = float((safe_frame["risk_level"].astype(str).str.lower() == "critical").mean())
    except Exception:
        critical_ratio = 0.0

    return {
        "total_alerts": total_alerts,
        "avg_duration_minutes": round(avg_duration, 2),
        "critical_alert_ratio": round(critical_ratio, 4),
    }
