"""
Medallion Architecture ETL Pipeline
Bronze (raw parquet) → Silver (normalized domains) → Gold (aggregated analytics)
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "DATA"
BRONZE_DIR = BASE_DIR / "bronze"
SILVER_DIR = BASE_DIR / "silver"
GOLD_DIR = BASE_DIR / "gold"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write DataFrame to parquet, converting timezone-aware timestamps to UTC string."""
    # Pyarrow can't handle mixed tz-aware columns cleanly on Windows — convert to string
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df.to_parquet(path, index=False, engine="pyarrow")


def _safe_parquet(df: pd.DataFrame, path: Path, label: str) -> None:
    try:
        _write_parquet(df, path)
        log.info(f"{label}: {len(df)} rows → {path.name}")
    except Exception as e:
        log.error(f"{label} write failed: {e}")
        # Write empty file so downstream doesn't crash
        pd.DataFrame().to_parquet(path, index=False, engine="pyarrow")


def _parse_samsung_ts(series: pd.Series) -> pd.Series:
    """Parse Samsung ISO timestamps (2020-01-01T22:41:00.000+0100) → UTC string."""
    parsed = pd.to_datetime(series, utc=True, errors="coerce")
    return parsed


# ---------------------------------------------------------------------------
# Bronze Layer
# ---------------------------------------------------------------------------

class BronzeLayer:
    """Ingest raw source files as-is into parquet, adding metadata columns."""

    SOURCE_MAP = {
        "samsung_sleep":        ("samsung/com.samsung.health.sleep.csv",            {}),
        "samsung_heart_rate":   ("samsung/com.samsung.health.heart_rate.csv",       {}),
        "samsung_steps":        ("samsung/com.samsung.health.step_daily_trend.csv", {}),
        "samsung_blood_oxygen": ("samsung/com.samsung.health.blood_oxygen.csv",     {}),
        "samsung_stress":       ("samsung/com.samsung.health.stress.csv",           {}),
        "samsung_calories":     ("samsung/com.samsung.health.calories_burned.csv",  {}),
        "sundhed_lab_results":  ("sundhed/lab_results.csv",                         {}),
        "sundhed_vaccinations": ("sundhed/vaccinations.csv",                        {}),
        "sundhed_diagnoses_txt":("sundhed/diagnoses.txt",                           {"raw": True}),
        "sundhed_besoeg":       ("sundhed/besoeg_real.csv",                         {"encoding": "utf-8-sig"}),
        "sundhed_diagnoser":    ("sundhed/diagnoser_real.csv",                      {"encoding": "utf-8-sig"}),
        "sundhed_proevesvar":   ("sundhed/proevesvar_real.csv",                     {}),
    }

    def _meta(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        df = df.copy()
        df["_ingestion_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        df["_source_filename"] = filename
        return df

    def _ingest_csv(self, path: Path, encoding: str = "utf-8") -> pd.DataFrame:
        df = pd.read_csv(path, encoding=encoding, low_memory=False)
        return self._meta(df, path.name)

    def _ingest_txt(self, path: Path) -> pd.DataFrame:
        lines = path.read_text(encoding="utf-8").splitlines()
        df = pd.DataFrame({"raw_line": [l for l in lines if l.strip()]})
        return self._meta(df, path.name)

    def run(self) -> Dict[str, Path]:
        BRONZE_DIR.mkdir(parents=True, exist_ok=True)
        results: Dict[str, Path] = {}
        for table_name, (rel_path, kwargs) in self.SOURCE_MAP.items():
            src = DATA_DIR / rel_path
            if not src.exists():
                log.warning(f"Source not found, skipping: {src}")
                continue
            try:
                raw_flag = kwargs.pop("raw", False)
                if raw_flag:
                    df = self._ingest_txt(src)
                else:
                    df = self._ingest_csv(src, **kwargs)
                out = BRONZE_DIR / f"{table_name}.parquet"
                _safe_parquet(df, out, f"Bronze/{table_name}")
                results[table_name] = out
            except Exception as e:
                log.error(f"Bronze/{table_name} failed: {e}")
        return results


# ---------------------------------------------------------------------------
# Silver Layer
# ---------------------------------------------------------------------------

class SilverLayer:
    """Normalize bronze data into clean domain tables."""

    def run(self, bronze_paths: Dict[str, Path]) -> Dict[str, Path]:
        SILVER_DIR.mkdir(parents=True, exist_ok=True)
        bronze: Dict[str, pd.DataFrame] = {}
        for k, v in bronze_paths.items():
            try:
                bronze[k] = pd.read_parquet(v)
            except Exception as e:
                log.error(f"Silver: could not read bronze/{k}: {e}")

        results: Dict[str, Path] = {}
        transforms = [
            ("sleep",           self._transform_sleep),
            ("heart_rate",      self._transform_heart_rate),
            ("activity",        self._transform_activity),
            ("blood_oxygen",    self._transform_blood_oxygen),
            ("stress",          self._transform_stress),
            ("calories",        self._transform_calories),
            ("running",         self._transform_running),
            ("lab_results",     self._transform_lab_results),
            ("hospital_visits", self._transform_hospital_visits),
            ("diagnoses",       self._transform_diagnoses),
            ("vaccinations",    self._transform_vaccinations),
        ]
        for domain, method in transforms:
            out = SILVER_DIR / f"{domain}.parquet"
            try:
                df = method(bronze)
                _safe_parquet(df, out, f"Silver/{domain}")
            except Exception as e:
                log.error(f"Silver/{domain} failed: {e}")
                pd.DataFrame().to_parquet(out, index=False, engine="pyarrow")
            results[domain] = out
        return results

    # --- Samsung transforms ---

    def _transform_sleep(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_sleep", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["end_time_utc"] = _parse_samsung_ts(df["end_time"])
        # Use local date of sleep end (morning person wakes up next calendar day)
        df["date"] = df["end_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df = df.rename(columns={
            "sleep_duration": "total_sleep_min",
            "rem_duration": "rem_min",
            "deep_sleep_duration": "deep_min",
            "light_duration": "light_min",
        })
        # Validate
        df["efficiency"] = pd.to_numeric(df["efficiency"], errors="coerce")
        df.loc[~df["efficiency"].between(0, 100), "efficiency"] = np.nan
        df["total_sleep_min"] = pd.to_numeric(df["total_sleep_min"], errors="coerce")
        df.loc[~df["total_sleep_min"].between(60, 900), "total_sleep_min"] = np.nan
        df = df.drop_duplicates(subset=["date"], keep="last")
        cols = ["date", "start_time_utc", "end_time_utc", "total_sleep_min",
                "rem_min", "deep_min", "light_min", "efficiency"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_heart_rate(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_heart_rate", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["end_time_utc"] = _parse_samsung_ts(df["end_time"])
        df["date"] = df["start_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df["heart_rate"] = pd.to_numeric(df["heart_rate"], errors="coerce")
        df.loc[~df["heart_rate"].between(30, 220), "heart_rate"] = np.nan
        df = df.dropna(subset=["heart_rate"])
        df = df.drop_duplicates(subset=["start_time_utc"])
        cols = ["date", "start_time_utc", "end_time_utc", "heart_rate", "heart_beat_count"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_activity(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_steps", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["date"] = df["start_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df = df.rename(columns={
            "count": "steps",
            "calorie": "active_calories",
            "distance": "distance_km",
            "speed": "avg_speed_kmh",
        })
        df["steps"] = pd.to_numeric(df["steps"], errors="coerce")
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
        df["active_calories"] = pd.to_numeric(df["active_calories"], errors="coerce")
        df = df.drop_duplicates(subset=["date"], keep="last")
        cols = ["date", "steps", "distance_km", "active_calories", "avg_speed_kmh"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_blood_oxygen(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_blood_oxygen", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["date"] = df["start_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df["spo2"] = pd.to_numeric(df["spo2"], errors="coerce")
        df["min_spo2"] = pd.to_numeric(df["min_spo2"], errors="coerce")
        df.loc[~df["spo2"].between(80, 100), "spo2"] = np.nan
        df.loc[~df["min_spo2"].between(80, 100), "min_spo2"] = np.nan
        df = df.drop_duplicates(subset=["date"], keep="last")
        cols = ["date", "start_time_utc", "spo2", "min_spo2"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_stress(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_stress", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["date"] = df["start_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df["stress_level"] = pd.to_numeric(df["stress_level"], errors="coerce")
        df.loc[~df["stress_level"].between(0, 100), "stress_level"] = np.nan
        df = df.dropna(subset=["stress_level"])
        df = df.drop_duplicates(subset=["start_time_utc"])
        cols = ["date", "start_time_utc", "stress_level", "score"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_calories(self, b: dict) -> pd.DataFrame:
        df = b.get("samsung_calories", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_utc"] = _parse_samsung_ts(df["start_time"])
        df["date"] = df["start_time_utc"].dt.tz_convert("Europe/Copenhagen").dt.date.astype(str)
        df["calorie"] = pd.to_numeric(df["calorie"], errors="coerce")
        df["active_time"] = pd.to_numeric(df["active_time"], errors="coerce")
        df = df.drop_duplicates(subset=["date"], keep="last")
        cols = ["date", "calorie", "active_time"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    def _transform_running(self, b: dict) -> pd.DataFrame:
        """Normalize Strava activities (fetched by strava_sync.py) into daily runs."""
        df = b.get("strava_activities", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["start_time_local"] = pd.to_datetime(df["start_date_local"], errors="coerce")
        df["date"] = df["start_time_local"].dt.date.astype(str)
        df["distance_km"] = pd.to_numeric(df["distance"], errors="coerce") / 1000
        df["duration_min"] = pd.to_numeric(df["moving_time"], errors="coerce") / 60
        df["avg_pace_min_per_km"] = np.where(
            df["distance_km"] > 0, df["duration_min"] / df["distance_km"], np.nan
        )
        df["avg_hr"] = pd.to_numeric(df.get("average_heartrate"), errors="coerce")
        df["max_hr"] = pd.to_numeric(df.get("max_heartrate"), errors="coerce")
        df["elevation_gain_m"] = pd.to_numeric(df.get("total_elevation_gain"), errors="coerce")
        df = df.rename(columns={"id": "activity_id", "name": "activity_name"})
        df = df.drop_duplicates(subset=["activity_id"], keep="last")
        cols = ["date", "activity_id", "activity_name", "distance_km", "duration_min",
                "avg_pace_min_per_km", "avg_hr", "max_hr", "elevation_gain_m", "start_time_local"]
        return df[[c for c in cols if c in df.columns]].reset_index(drop=True)

    # --- Sundhed transforms ---

    def _transform_lab_results(self, b: dict) -> pd.DataFrame:
        frames = []

        # Source 1: lab_results.csv
        df1 = b.get("sundhed_lab_results", pd.DataFrame()).copy()
        if not df1.empty:
            df1["date"] = pd.to_datetime(df1["date"], errors="coerce").dt.date.astype(str)
            df1 = df1.rename(columns={"test": "test_name"})
            df1["value"] = pd.to_numeric(df1["value"], errors="coerce")
            df1["abnormal"] = (
                (df1["value"] < pd.to_numeric(df1["reference_low"], errors="coerce")) |
                (df1["value"] > pd.to_numeric(df1["reference_high"], errors="coerce"))
            )
            df1["source"] = "lab_results"
            frames.append(df1[["date", "test_name", "value", "unit",
                                "reference_low", "reference_high", "abnormal", "source"]])

        # Source 2: proevesvar_real.csv
        df2 = b.get("sundhed_proevesvar", pd.DataFrame()).copy()
        if not df2.empty:
            df2["date"] = pd.to_datetime(df2["dato_iso"], errors="coerce").dt.date.astype(str)
            df2 = df2.rename(columns={"navn": "test_name"})
            df2["value"] = np.nan  # no numeric values in this source
            df2["unit"] = None
            df2["reference_low"] = np.nan
            df2["reference_high"] = np.nan
            abnormal_raw = df2.get("abnormal", pd.Series(dtype=str))
            df2["abnormal"] = abnormal_raw.astype(str).str.lower().isin(["true", "1", "yes"])
            df2["source"] = "proevesvar"
            frames.append(df2[["date", "test_name", "value", "unit",
                                "reference_low", "reference_high", "abnormal", "source"]])

        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        out = out.drop_duplicates(subset=["date", "test_name", "source"])
        return out.reset_index(drop=True)

    def _transform_hospital_visits(self, b: dict) -> pd.DataFrame:
        df = b.get("sundhed_besoeg", pd.DataFrame()).copy()
        if df.empty:
            return df
        # BOM already handled at bronze (utf-8-sig)
        # Rename Danish columns
        df = df.rename(columns={
            "dato": "date_raw",
            "afdeling": "department",
            "laege": "doctor",
            "type": "visit_type",
            "hospital": "hospital",
            "note_tilg": "note_available",
        })
        df["date"] = pd.to_datetime(df["date_raw"], format="mixed", dayfirst=False, errors="coerce").dt.date.astype(str)
        df["note_available"] = df["note_available"].astype(str).str.lower().isin(["true", "1"])
        cols = ["date", "department", "doctor", "visit_type", "hospital", "note_available"]
        return df[[c for c in cols if c in df.columns]].dropna(subset=["date"]).reset_index(drop=True)

    def _transform_diagnoses(self, b: dict) -> pd.DataFrame:
        frames = []

        # Source 1: diagnoser_real.csv
        df1 = b.get("sundhed_diagnoser", pd.DataFrame()).copy()
        if not df1.empty:
            df1 = df1.rename(columns={
                "diagnose": "diagnosis",
                "icd_kode": "icd_code",
                "dato": "date_raw",
                "hospital": "hospital",
                "status": "status",
            })
            df1["date"] = pd.to_datetime(df1["date_raw"], dayfirst=True, errors="coerce").dt.date.astype(str)
            df1["source"] = "diagnoser_real"
            frames.append(df1[["diagnosis", "icd_code", "date", "hospital", "status", "source"]])

        # Source 2: diagnoses.txt
        df_txt = b.get("sundhed_diagnoses_txt", pd.DataFrame()).copy()
        if not df_txt.empty:
            icd_pattern = re.compile(r"[A-Z]\d{2}\.?\d*\w*")
            date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})\b")
            records = []
            for line in df_txt.get("raw_line", []):
                icd_match = icd_pattern.search(str(line))
                date_match = date_pattern.search(str(line))
                if icd_match:
                    icd = icd_match.group()
                    date_str = None
                    if date_match:
                        raw = date_match.group()
                        parsed = pd.to_datetime(raw, dayfirst=True, errors="coerce")
                        date_str = parsed.date().isoformat() if not pd.isna(parsed) else None
                    # Diagnosis text: everything before the ICD code
                    diag = str(line)[:icd_match.start()].strip(" -:")
                    records.append({"diagnosis": diag, "icd_code": icd, "date": date_str,
                                    "hospital": None, "status": None, "source": "diagnoses_txt"})
            if records:
                frames.append(pd.DataFrame(records))

        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        out = out.drop_duplicates(subset=["icd_code", "date"])
        return out.reset_index(drop=True)

    def _transform_vaccinations(self, b: dict) -> pd.DataFrame:
        df = b.get("sundhed_vaccinations", pd.DataFrame()).copy()
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df.dropna(subset=["date"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Gold Layer
# ---------------------------------------------------------------------------

class GoldLayer:
    """Build aggregated, analytics-ready tables from silver."""

    def run(self, silver_paths: Dict[str, Path]) -> Dict[str, Path]:
        GOLD_DIR.mkdir(parents=True, exist_ok=True)
        silver: Dict[str, pd.DataFrame] = {}
        for k, v in silver_paths.items():
            try:
                df = pd.read_parquet(v)
                if not df.empty and "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df.dropna(subset=["date"])
                silver[k] = df
            except Exception as e:
                log.error(f"Gold: could not read silver/{k}: {e}")
                silver[k] = pd.DataFrame()

        results: Dict[str, Path] = {}
        tasks = [
            ("sleep_gold",                self._build_sleep_gold),
            ("activity_gold",             self._build_activity_gold),
            ("heart_rate_gold",           self._build_heart_rate_gold),
            ("blood_oxygen_gold",         self._build_blood_oxygen_gold),
            ("stress_gold",               self._build_stress_gold),
            ("running_gold",              self._build_running_gold),
            ("wellness_score",            self._build_wellness_score),
            ("lab_results_gold",          self._build_lab_results_gold),
            ("cross_domain_sleep_activity", self._build_cross_domain_sleep_activity),
            ("daily_summary",             self._build_daily_summary),
            ("weekly_summary",            self._build_weekly_summary),
            ("monthly_summary",           self._build_monthly_summary),
        ]
        gold: Dict[str, pd.DataFrame] = {}
        for name, method in tasks:
            out = GOLD_DIR / f"{name}.parquet"
            try:
                df = method(silver, gold)
                gold[name] = df
                _safe_parquet(df, out, f"Gold/{name}")
            except Exception as e:
                log.error(f"Gold/{name} failed: {e}")
                gold[name] = pd.DataFrame()
                pd.DataFrame().to_parquet(out, index=False, engine="pyarrow")
            results[name] = out
        return results

    # --- Domain golds ---

    def _build_sleep_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("sleep", pd.DataFrame()).copy()
        if df.empty:
            return df
        df = df.sort_values("date").set_index("date")
        for col in ["total_sleep_min", "efficiency", "rem_min", "deep_min", "light_min"]:
            if col in df.columns:
                df[f"{col}_7d_avg"] = df[col].rolling(7, min_periods=3).mean()
        if "total_sleep_min" in df.columns and "deep_min" in df.columns:
            df["rem_pct"] = (df["rem_min"] / df["total_sleep_min"] * 100).round(1)
            df["deep_pct"] = (df["deep_min"] / df["total_sleep_min"] * 100).round(1)
        return df.reset_index()

    def _build_activity_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("activity", pd.DataFrame()).copy()
        if df.empty:
            return df
        df = df.sort_values("date").set_index("date")
        df["steps_7d_avg"] = df["steps"].rolling(7, min_periods=3).mean()
        df["steps_personal_record"] = df["steps"].expanding().max()

        # 30-day trend slope (steps per day)
        def rolling_slope(series, window=30):
            slopes = [np.nan] * len(series)
            arr = series.values
            for i in range(window - 1, len(arr)):
                chunk = arr[i - window + 1: i + 1]
                valid = ~np.isnan(chunk)
                if valid.sum() >= 10:
                    idx = np.where(valid)[0]
                    slopes[i] = np.polyfit(idx, chunk[valid], 1)[0]
            return pd.Series(slopes, index=series.index)

        df["steps_30d_trend"] = rolling_slope(df["steps"])
        return df.reset_index()

    def _build_heart_rate_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("heart_rate", pd.DataFrame()).copy()
        if df.empty:
            return df
        df = df.copy()

        # Resting HR: readings between 03:00–06:00 UTC
        df["hour"] = pd.to_datetime(
            df["start_time_utc"].astype(str), errors="coerce", utc=True
        ).dt.hour
        resting = (
            df[df["hour"].between(3, 6)]
            .groupby("date")["heart_rate"]
            .min()
            .rename("resting_hr")
        )

        daily = df.groupby("date")["heart_rate"].agg(
            hr_mean="mean", hr_min="min", hr_max="max"
        ).round(1)
        daily = daily.join(resting, how="left")

        daily["hr_mean_7d_avg"] = daily["hr_mean"].rolling(7, min_periods=3).mean()
        daily["resting_hr_7d_avg"] = daily["resting_hr"].rolling(7, min_periods=3).mean()
        return daily.reset_index()

    def _build_blood_oxygen_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("blood_oxygen", pd.DataFrame()).copy()
        if df.empty:
            return df
        df = df.sort_values("date").set_index("date")
        df["spo2_7d_avg"] = df["spo2"].rolling(7, min_periods=3).mean()
        df["low_spo2_flag"] = df["min_spo2"] < 95
        return df.reset_index()

    def _build_stress_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("stress", pd.DataFrame()).copy()
        if df.empty:
            return df
        daily = df.groupby("date")["stress_level"].agg(
            stress_mean="mean", stress_max="max"
        ).round(1)
        daily["stress_7d_avg"] = daily["stress_mean"].rolling(7, min_periods=3).mean()
        daily["high_stress_day"] = daily["stress_mean"] > 70
        return daily.reset_index()

    def _build_running_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("running", pd.DataFrame()).copy()
        if df.empty:
            return df
        # Multiple runs on the same day: aggregate to one row per date.
        daily = df.groupby("date").agg(
            distance_km=("distance_km", "sum"),
            duration_min=("duration_min", "sum"),
            avg_pace_min_per_km=("avg_pace_min_per_km", "mean"),
            avg_hr=("avg_hr", "mean"),
            max_hr=("max_hr", "max"),
            elevation_gain_m=("elevation_gain_m", "sum"),
            runs=("activity_id", "count"),
        ).round(2)
        daily.index = pd.to_datetime(daily.index)
        daily = daily.sort_index()
        # Runs are sparse (gaps between sessions), so use calendar-day offset
        # windows ('7D'/'30D') rather than row-count windows — a row-count
        # window would silently span more than 7/30 actual days.
        daily["distance_7d_avg"] = daily["distance_km"].rolling("7D", min_periods=1).mean().round(2)
        daily["distance_7d_total"] = daily["distance_km"].rolling("7D", min_periods=1).sum().round(2)
        daily["distance_30d_total"] = daily["distance_km"].rolling("30D", min_periods=1).sum().round(2)
        daily["longest_run_km"] = daily["distance_km"].expanding().max().round(2)
        daily["fastest_pace_min_per_km"] = daily["avg_pace_min_per_km"].expanding().min().round(2)
        return daily.reset_index()

    def _build_wellness_score(self, s: dict, g: dict) -> pd.DataFrame:
        parts = {}

        sleep_g = g.get("sleep_gold", pd.DataFrame())
        if not sleep_g.empty and "efficiency" in sleep_g.columns:
            parts["sleep"] = sleep_g.set_index("date")["efficiency"].rename("eff")

        act_g = g.get("activity_gold", pd.DataFrame())
        if not act_g.empty and "steps" in act_g.columns:
            parts["activity"] = act_g.set_index("date")["steps"].rename("steps")

        hr_g = g.get("heart_rate_gold", pd.DataFrame())
        if not hr_g.empty and "resting_hr" in hr_g.columns:
            parts["hr"] = hr_g.set_index("date")["resting_hr"].rename("rhr")

        stress_g = g.get("stress_gold", pd.DataFrame())
        if not stress_g.empty and "stress_mean" in stress_g.columns:
            parts["stress"] = stress_g.set_index("date")["stress_mean"].rename("stress")

        if not parts:
            return pd.DataFrame()

        combined = pd.concat(list(parts.values()), axis=1)
        scores = pd.DataFrame(index=combined.index)
        if "eff" in combined.columns:
            scores["sleep_score"] = np.clip((combined["eff"] - 50) / 50, 0, 1) * 25
        if "steps" in combined.columns:
            scores["activity_score"] = np.clip(combined["steps"] / 10000, 0, 1) * 25
        if "rhr" in combined.columns:
            scores["hr_score"] = np.clip(1 - abs(combined["rhr"] - 60) / 40, 0, 1) * 25
        if "stress" in combined.columns:
            scores["stress_score"] = np.clip(1 - combined["stress"] / 100, 0, 1) * 25

        scores["wellness_score"] = scores.mean(axis=1) * (100 / 25)
        scores["wellness_7d_avg"] = scores["wellness_score"].rolling(7, min_periods=3).mean()
        return scores.reset_index()

    def _build_lab_results_gold(self, s: dict, g: dict) -> pd.DataFrame:
        df = s.get("lab_results", pd.DataFrame()).copy()
        if df.empty:
            return df
        # Latest value per test
        latest = (
            df.sort_values("date")
            .groupby("test_name")
            .last()
            .reset_index()
        )
        return latest

    def _build_cross_domain_sleep_activity(self, s: dict, g: dict) -> pd.DataFrame:
        sleep = s.get("sleep", pd.DataFrame()).copy()
        activity = s.get("activity", pd.DataFrame()).copy()
        if sleep.empty or activity.empty:
            return pd.DataFrame()
        sleep_idx = sleep.set_index("date")[["efficiency", "total_sleep_min"]]
        act_idx = activity.set_index("date")[["steps"]]
        # Sleep on day N → activity on day N+1
        sleep_idx.index = pd.to_datetime(sleep_idx.index)
        act_idx.index = pd.to_datetime(act_idx.index)
        # Shift activity back one day to align with prior night's sleep
        act_shifted = act_idx.copy()
        act_shifted.index = act_shifted.index - pd.Timedelta(days=1)
        joined = sleep_idx.join(act_shifted.rename(columns={"steps": "next_day_steps"}), how="inner")
        return joined.reset_index()

    def _build_daily_summary(self, s: dict, g: dict) -> pd.DataFrame:
        dfs_to_join = {
            "sleep_gold":       ["efficiency", "total_sleep_min"],
            "activity_gold":    ["steps", "distance_km", "active_calories"],
            "heart_rate_gold":  ["hr_mean", "resting_hr"],
            "blood_oxygen_gold":["spo2", "min_spo2"],
            "stress_gold":      ["stress_mean"],
            "running_gold":     ["distance_km", "avg_pace_min_per_km"],
            "wellness_score":   ["wellness_score"],
        }
        base = None
        for table, cols in dfs_to_join.items():
            df = g.get(table, pd.DataFrame()).copy()
            if df.empty or "date" not in df.columns:
                continue
            df["date"] = pd.to_datetime(df["date"])
            available = [c for c in cols if c in df.columns]
            subset = df[["date"] + available].set_index("date")
            base = subset if base is None else base.join(subset, how="outer")
        return pd.DataFrame() if base is None else base.reset_index()

    def _build_weekly_summary(self, s: dict, g: dict) -> pd.DataFrame:
        ds = g.get("daily_summary", pd.DataFrame()).copy()
        if ds.empty:
            return ds
        ds["date"] = pd.to_datetime(ds["date"])
        ds = ds.set_index("date")
        numeric = ds.select_dtypes(include="number")
        return numeric.resample("W-MON").mean().round(2).reset_index()

    def _build_monthly_summary(self, s: dict, g: dict) -> pd.DataFrame:
        ds = g.get("daily_summary", pd.DataFrame()).copy()
        if ds.empty:
            return ds
        ds["date"] = pd.to_datetime(ds["date"])
        ds = ds.set_index("date")
        numeric = ds.select_dtypes(include="number")
        return numeric.resample("MS").mean().round(2).reset_index()


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class ETLPipeline:
    def run_full(self) -> dict:
        log.info("=== ETL Pipeline starting ===")
        bronze_paths = BronzeLayer().run()
        # strava_activities.parquet is written directly by strava_sync.py (API-based,
        # not a local CSV source), so it isn't part of BronzeLayer.SOURCE_MAP.
        strava_bronze = BRONZE_DIR / "strava_activities.parquet"
        if strava_bronze.exists():
            bronze_paths["strava_activities"] = strava_bronze
        silver_paths = SilverLayer().run(bronze_paths)
        gold_paths = GoldLayer().run(silver_paths)
        log.info(
            f"=== ETL complete: {len(bronze_paths)} bronze, "
            f"{len(silver_paths)} silver, {len(gold_paths)} gold tables ==="
        )
        return {"bronze": bronze_paths, "silver": silver_paths, "gold": gold_paths}

    def run_bronze_only(self) -> dict:
        return BronzeLayer().run()

    def run_silver_only(self) -> dict:
        bronze_paths = {p.stem: p for p in BRONZE_DIR.glob("*.parquet")}
        return SilverLayer().run(bronze_paths)

    def run_gold_only(self) -> dict:
        silver_paths = {p.stem: p for p in SILVER_DIR.glob("*.parquet")}
        return GoldLayer().run(silver_paths)


if __name__ == "__main__":
    ETLPipeline().run_full()
