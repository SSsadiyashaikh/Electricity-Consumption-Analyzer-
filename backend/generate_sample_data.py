"""
Create a SYNTHETIC sample dataset in the same format as the UCI file, so you can
demo the whole project without the real download.

!! These numbers are computer-generated, NOT real measurements. !!
Models trained on this file are marked "sample" in the dashboard and in metrics.json,
and their metrics say nothing about real households.

Output: data/sample_household_power_consumption.txt  (two years, one row per minute)
The real file (data/household_power_consumption.txt) always takes priority if present.
Run:  python generate_sample_data.py
"""
import numpy as np
import pandas as pd

from preprocess import DATA_DIR, SAMPLE_FILE


def main():
    rng = np.random.default_rng(42)
    idx = pd.date_range("2007-01-01", "2008-12-31 23:59", freq="min")
    n = len(idx)
    hour, dow, doy = idx.hour.values, idx.dayofweek.values, idx.dayofyear.values
    day_id = np.asarray((idx.normalize() - idx[0].normalize()).days)
    n_days = day_id.max() + 1

    # Typical shape of a household day: quiet night, morning bump, big evening peak.
    profile = np.array([.35, .30, .30, .30, .32, .40, .70, 1.2, 1.3, .9, .7, .7,
                        .9, .8, .7, .7, .8, 1.1, 1.8, 2.0, 1.9, 1.5, .9, .5])
    season = 1 + 0.35 * np.cos(2 * np.pi * (doy - 15) / 365)   # more use in winter
    weekend = np.where(dow >= 5, 1.2, 1.0)
    day_factor = np.exp(rng.normal(0, 0.25, n_days))[day_id]    # some days are just busier

    kw = 0.2 + 0.5 * profile[hour] * season * weekend * day_factor + rng.gamma(2, 0.05, n)
    spike = rng.random(n) < 0.003
    kw[spike] += rng.uniform(1, 3, spike.sum())
    kw = kw.round(3)

    wh = kw * 1000 / 60                                  # Wh available this minute
    meal = np.isin(hour, [7, 8, 12, 13, 18, 19, 20])
    kitchen = wh * rng.random(n) * 0.30 * meal
    laundry = wh * 0.25 * (rng.random(n) < 0.06)
    heater = wh * 0.35 * rng.random(n) * np.isin(hour, [5, 6, 7, 21, 22, 23])  # sums stay < total

    df = pd.DataFrame({
        "Date": idx.strftime("%d/%m/%Y"),
        "Time": idx.strftime("%H:%M:%S"),
        "Global_active_power": kw,
        "Global_reactive_power": rng.uniform(0.05, 0.25, n).round(3),
        "Voltage": (240 + rng.normal(0, 2, n)).round(2),
        "Global_intensity": (kw * 1000 / 240).round(1),
        "Sub_metering_1": kitchen.round(), "Sub_metering_2": laundry.round(),
        "Sub_metering_3": heater.round(),
    })

    # Missing readings, written as '?' like the real file: random minutes + two outages.
    missing = rng.random(n) < 0.001
    missing |= (idx >= "2007-08-10") & (idx < "2007-08-13")
    missing |= (idx >= "2008-04-02") & (idx < "2008-04-09")
    df.loc[missing, df.columns[2:]] = np.nan

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAMPLE_FILE, sep=";", index=False, na_rep="?")
    print("Created SYNTHETIC sample dataset:", SAMPLE_FILE)
    print("These are not real measurements. Add the real file to data/ to replace it.")


if __name__ == "__main__":
    main()
