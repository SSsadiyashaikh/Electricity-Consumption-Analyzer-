"""
Data loading, energy conversion, aggregation and feature engineering.

Dataset: UCI "Individual household electric power consumption".
  * One row per minute, columns separated by ';'.
  * Missing values are written as '?'.
  * Date is dd/mm/yyyy, Time is hh:mm:ss.
  * Global_active_power is in kilowatts (kW).
  * Sub_metering_1/2/3 are in watt-hours (Wh) of active energy for that minute
    (kitchen, laundry room, electric water-heater + air-conditioner).

ENERGY CONVERSION (the most important formula in this project)
  Each record covers about one minute = 1/60 hour.
      energy (kWh) = power (kW) x time (h) = Global_active_power x (1/60)
  Daily energy = sum of the per-minute energies of that day.
  Sub-metering columns are already Wh, so kWh = sum(Wh) / 1000.

MISSING DATA
  Minutes with '?' are NOT filled with invented numbers. A day is kept only if
  at least MIN_VALID_MINUTES_PER_DAY of its 1440 minutes have a real reading,
  otherwise its total would be badly under-counted. A month is flagged
  "complete" when at least 90% of its calendar days are kept.
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

RAW_FILE = DATA_DIR / "household_power_consumption.txt"            # the real UCI file
SAMPLE_FILE = DATA_DIR / "sample_household_power_consumption.txt"  # synthetic demo file
SAMPLE_FLAG = OUTPUT_DIR / "trained_on_sample.flag"
DAILY_CSV = OUTPUT_DIR / "daily_summary.csv"
MONTHLY_CSV = OUTPUT_DIR / "monthly_summary.csv"
METRICS_JSON = OUTPUT_DIR / "metrics.json"

LINEAR_MODEL_PATH = MODELS_DIR / "linear_regression.joblib"
TREE_MODEL_PATH = MODELS_DIR / "decision_tree.joblib"
KMEANS_MODEL_PATH = MODELS_DIR / "kmeans.joblib"

MIN_VALID_MINUTES_PER_DAY = 1296  # 90% of 1440
MIN_VALID_MONTH_FRACTION = 0.90
TRAIN_FRACTION = 0.80  # chronological split: first 80% of days train, last 20% test

# Feature lists shared by training and the Flask API (keeps them consistent).
FORECAST_FEATURES = [
    "lag_1", "lag_2", "lag_7", "roll_mean_7",
    "is_weekend", "dow_sin", "dow_cos", "month_sin", "month_cos",
]
CLASSIFY_FEATURES = [
    "peak_kw", "kitchen_kwh", "laundry_kwh", "water_heater_ac_kwh",
    "is_weekend", "month",
]
CLUSTER_FEATURES = ["daily_kwh", "peak_kw", "evening_share_pct"]
CLASS_NAMES = ["Low", "Medium", "High"]


def active_data_file():
    """The real dataset always wins; the synthetic sample is only a fallback."""
    if RAW_FILE.exists():
        return RAW_FILE
    if SAMPLE_FILE.exists():
        return SAMPLE_FILE
    return None


def data_source():
    f = active_data_file()
    return None if f is None else ("real" if f == RAW_FILE else "sample")


def dataset_available():
    return active_data_file() is not None


def load_raw(path=None):
    """Read the semicolon-separated file, convert '?' to NaN, parse timestamps."""
    path = path or active_data_file()
    df = pd.read_csv(path, sep=";", na_values=["?", ""], low_memory=False)
    df["datetime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )
    numeric_cols = [
        "Global_active_power", "Global_reactive_power", "Voltage",
        "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["datetime"])


def build_daily(df):
    """Aggregate minute-level rows into one row per day (kWh)."""
    df = df.copy()
    df["energy_kwh"] = df["Global_active_power"] * (1.0 / 60.0)  # kW x 1 minute
    df["date"] = df["datetime"].dt.normalize()
    # Energy used from 18:00 to 23:59 (NaN stays NaN so missing minutes are skipped).
    df["evening_kwh"] = df["energy_kwh"].where(df["datetime"].dt.hour >= 18, 0.0)

    g = df.groupby("date")
    daily = pd.DataFrame({
        "daily_kwh": g["energy_kwh"].sum(),
        "valid_minutes": g["Global_active_power"].count(),
        "peak_kw": g["Global_active_power"].max(),
        "avg_voltage": g["Voltage"].mean(),
        "kitchen_kwh": g["Sub_metering_1"].sum() / 1000.0,
        "laundry_kwh": g["Sub_metering_2"].sum() / 1000.0,
        "water_heater_ac_kwh": g["Sub_metering_3"].sum() / 1000.0,
        "evening_kwh": g["evening_kwh"].sum(),
    })
    daily = daily[daily["valid_minutes"] >= MIN_VALID_MINUTES_PER_DAY].copy()
    metered = daily["kitchen_kwh"] + daily["laundry_kwh"] + daily["water_heater_ac_kwh"]
    daily["other_kwh"] = (daily["daily_kwh"] - metered).clip(lower=0.0)
    daily["evening_share_pct"] = 100.0 * daily["evening_kwh"] / daily["daily_kwh"]
    daily["is_weekend"] = (daily.index.dayofweek >= 5).astype(int)
    daily["month"] = daily.index.month
    daily = daily.drop(columns=["evening_kwh"]).reset_index()
    num_cols = daily.columns.drop("date")
    daily[num_cols] = daily[num_cols].round(4)
    return daily


def build_monthly(daily):
    """Sum the kept days of each month; report coverage so partial months are visible."""
    d = daily.copy()
    d["month_start"] = d["date"].dt.to_period("M").dt.to_timestamp()
    g = d.groupby("month_start")
    monthly = pd.DataFrame({
        "total_kwh": g["daily_kwh"].sum(),
        "avg_daily_kwh": g["daily_kwh"].mean(),
        "valid_days": g["daily_kwh"].count(),
        "kitchen_kwh": g["kitchen_kwh"].sum(),
        "laundry_kwh": g["laundry_kwh"].sum(),
        "water_heater_ac_kwh": g["water_heater_ac_kwh"].sum(),
        "other_kwh": g["other_kwh"].sum(),
    })
    monthly["days_in_month"] = monthly.index.days_in_month
    monthly["complete"] = monthly["valid_days"] >= MIN_VALID_MONTH_FRACTION * monthly["days_in_month"]
    monthly = monthly.reset_index().rename(columns={"month_start": "month"})
    monthly["month"] = monthly["month"].dt.strftime("%Y-%m")
    num_cols = monthly.columns.drop("month")
    monthly[num_cols] = monthly[num_cols].round(4)
    return monthly


def build_summaries(save=True):
    """Full pipeline: raw file -> daily table + monthly table (saved as CSV)."""
    raw = load_raw()
    daily = build_daily(raw)
    monthly = build_monthly(daily)
    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = daily.copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        out.to_csv(DAILY_CSV, index=False)
        monthly.to_csv(MONTHLY_CSV, index=False)
    return daily, monthly


def load_daily():
    return pd.read_csv(DAILY_CSV, parse_dates=["date"])


def load_monthly():
    return pd.read_csv(MONTHLY_CSV)


def make_forecast_features(series):
    """
    Build features for the Linear Regression forecaster from a daily kWh series.
    Every feature for day t uses ONLY days before t (shift) or the calendar, so
    there is no leakage of the value being predicted. Training and inference both
    call this exact function, so they cannot drift apart.
    """
    s = series.asfreq("D")  # missing days become NaN (never invented)
    f = pd.DataFrame(index=s.index)
    f["lag_1"] = s.shift(1)
    f["lag_2"] = s.shift(2)
    f["lag_7"] = s.shift(7)
    f["roll_mean_7"] = s.shift(1).rolling(7).mean()
    dow = s.index.dayofweek
    month = s.index.month
    f["is_weekend"] = (dow >= 5).astype(int)
    f["dow_sin"] = np.sin(2 * np.pi * dow / 7)
    f["dow_cos"] = np.cos(2 * np.pi * dow / 7)
    f["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12)
    f["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12)
    return f[FORECAST_FEATURES]
