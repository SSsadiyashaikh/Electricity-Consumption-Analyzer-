"""Flask API for the AI-Based Electricity Consumption Analyzer.
Run:  python app.py   (serves on http://127.0.0.1:5000)"""
import json
import math
from datetime import timedelta

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

import preprocess as pre

app = Flask(__name__)

ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": ORIGINS}})
except ImportError:  # minimal fallback so the app still works without Flask-CORS
    @app.after_request
    def add_cors(resp):
        origin = request.headers.get("Origin")
        if origin in ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp


class ApiError(Exception):
    def __init__(self, message, status=400, hint=None):
        super().__init__(message)
        self.message, self.status, self.hint = message, status, hint


@app.errorhandler(ApiError)
def handle_api_error(err):
    body = {"error": err.message}
    if err.hint:
        body["hint"] = err.hint
    return jsonify(body), err.status


@app.errorhandler(404)
def handle_404(_):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(Exception)
def handle_unexpected(err):
    app.logger.exception(err)
    return jsonify({"error": "Unexpected server error.", "detail": str(err)}), 500


TRAIN_HINT = "Place the dataset in backend/data/ and run: python train_model.py"
_model_cache = {}


def load_model(path, name):
    """Load a saved model once; give a clear error if it was never trained."""
    if path in _model_cache:
        return _model_cache[path]
    if not path.exists():
        raise ApiError(f"The {name} model has not been trained yet.", 503, TRAIN_HINT)
    try:
        _model_cache[path] = joblib.load(path)  # files are produced locally by train_model.py
    except Exception as exc:
        raise ApiError(f"The {name} model file could not be loaded: {exc}", 500, TRAIN_HINT)
    return _model_cache[path]


def require_file(path, what):
    if not path.exists():
        raise ApiError(f"{what} is not available.", 503, TRAIN_HINT)


def records(df):
    return json.loads(df.to_json(orient="records", date_format="iso"))


def read_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object.")
    return data


def num(data, key, lo, hi, required=True):
    value = data.get(key)
    if value is None or value == "":
        if required:
            raise ApiError(f"'{key}' is required.")
        return None
    if isinstance(value, bool):
        raise ApiError(f"'{key}' must be a number.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ApiError(f"'{key}' must be a number.")
    if not math.isfinite(value) or value < lo or value > hi:
        raise ApiError(f"'{key}' must be between {lo} and {hi}.")
    return value


# ------------------------------------------------------------------ endpoints
def current_data_source():
    """'real' or 'sample', as recorded when the models were trained."""
    if pre.METRICS_JSON.exists():
        with open(pre.METRICS_JSON, encoding="utf-8") as f:
            return json.load(f).get("dataset", {}).get("data_source")
    return None


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "dataset_present": pre.dataset_available(),
        "data_source": pre.data_source(),
        "summaries_present": pre.DAILY_CSV.exists() and pre.MONTHLY_CSV.exists(),
        "models": {
            "linear_regression": pre.LINEAR_MODEL_PATH.exists(),
            "decision_tree": pre.TREE_MODEL_PATH.exists(),
            "kmeans": pre.KMEANS_MODEL_PATH.exists(),
        },
    })


@app.get("/api/history")
def history():
    require_file(pre.MONTHLY_CSV, "Consumption history")
    gran = request.args.get("granularity", "monthly")
    if gran == "monthly":
        return jsonify({"granularity": "monthly", "unit": "kWh", "data": records(pre.load_monthly())})
    if gran == "daily":
        try:
            limit = int(request.args.get("limit", 365))
        except ValueError:
            raise ApiError("'limit' must be an integer.")
        df = pre.load_daily().tail(max(1, min(limit, 5000)))
        df = df.assign(date=df["date"].dt.strftime("%Y-%m-%d"))
        return jsonify({"granularity": "daily", "unit": "kWh", "data": records(df)})
    raise ApiError("'granularity' must be 'monthly' or 'daily'.")


@app.get("/api/summary")
def summary():
    require_file(pre.DAILY_CSV, "Consumption summary")
    daily, monthly = pre.load_daily(), pre.load_monthly()
    complete = monthly[monthly["complete"]]
    top_day = daily.loc[daily["daily_kwh"].idxmax()]
    parts = {k: float(daily[k].sum()) for k in
             ["kitchen_kwh", "laundry_kwh", "water_heater_ac_kwh", "other_kwh"]}
    total = float(daily["daily_kwh"].sum())
    out = {
        "data_source": current_data_source(),
        "usable_days": int(len(daily)),
        "first_day": daily["date"].min().strftime("%Y-%m-%d"),
        "last_day": daily["date"].max().strftime("%Y-%m-%d"),
        "total_kwh": total,
        "avg_daily_kwh": float(daily["daily_kwh"].mean()),
        "avg_peak_kw": float(daily["peak_kw"].mean()),
        "highest_day": {"date": top_day["date"].strftime("%Y-%m-%d"), "kwh": float(top_day["daily_kwh"])},
        "end_use_kwh": parts,
        "end_use_share_pct": {k: (100 * v / total if total else 0.0) for k, v in parts.items()},
    }
    if len(complete):
        hi = complete.loc[complete["total_kwh"].idxmax()]
        lo = complete.loc[complete["total_kwh"].idxmin()]
        out["highest_month"] = {"month": hi["month"], "kwh": float(hi["total_kwh"])}
        out["lowest_month"] = {"month": lo["month"], "kwh": float(lo["total_kwh"])}
        out["avg_monthly_kwh"] = float(complete["total_kwh"].mean())
    return jsonify(out)


@app.get("/api/model-metrics")
def model_metrics():
    require_file(pre.METRICS_JSON, "Model metrics")
    with open(pre.METRICS_JSON, encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.post("/api/predict")
def predict():
    data = read_json_body()
    bundle = load_model(pre.LINEAR_MODEL_PATH, "Linear Regression")
    pipe, feats = bundle["pipeline"], bundle["features"]
    days_ahead = int(num(data, "days_ahead", 1, 30, required=False) or 7)

    recent = data.get("recent_daily_kwh")
    if recent is not None:
        if not isinstance(recent, list) or len(recent) != 7:
            raise ApiError("'recent_daily_kwh' must be a list of exactly 7 numbers (oldest first).")
        history_vals = [num({"v": v}, "v", 0, 200) for v in recent]
        start_raw = data.get("start_date")
        if not start_raw:
            raise ApiError("'start_date' (YYYY-MM-DD, the day after your 7 values) is required with 'recent_daily_kwh'.")
        try:
            start = pd.Timestamp(start_raw).normalize()
        except Exception:
            raise ApiError("'start_date' must look like YYYY-MM-DD.")
        source = "your 7 recent daily values"
    else:
        require_file(pre.DAILY_CSV, "Daily history")
        s = pre.load_daily().set_index("date")["daily_kwh"].asfreq("D")
        ok = (s.rolling(7).count() == 7)
        if not ok.any():
            raise ApiError("The dataset has no 7 consecutive usable days to forecast from.", 503)
        end = ok[ok].index.max()
        history_vals = s.loc[end - timedelta(days=6):end].tolist()
        start = end + timedelta(days=1)
        source = f"the last 7 consecutive usable days in the dataset (ending {end.date()})"

    hist, out = list(history_vals), []
    for i in range(days_ahead):
        day = start + timedelta(days=i)
        idx = pd.date_range(day - timedelta(days=7), day, freq="D")
        series = pd.Series(hist[-7:] + [np.nan], index=idx)
        row = pre.make_forecast_features(series).iloc[[-1]][feats]  # same code as training
        value = max(float(pipe.predict(row)[0]), 0.0)  # electricity use cannot be negative
        hist.append(value)
        out.append({"date": day.strftime("%Y-%m-%d"), "predicted_kwh": round(value, 3)})

    metrics = None
    if pre.METRICS_JSON.exists():
        with open(pre.METRICS_JSON, encoding="utf-8") as f:
            metrics = json.load(f).get("linear_regression", {}).get("test_metrics")
    return jsonify({
        "model": "Linear Regression", "based_on": source,
        "note": "Multi-day forecasts feed earlier predictions back in, so error grows with distance.",
        "test_metrics": metrics, "predictions": out,
    })


@app.post("/api/classify")
def classify():
    data = read_json_body()
    bundle = load_model(pre.TREE_MODEL_PATH, "Decision Tree")
    row = {
        "peak_kw": num(data, "peak_kw", 0, 20),
        "kitchen_kwh": num(data, "kitchen_kwh", 0, 50),
        "laundry_kwh": num(data, "laundry_kwh", 0, 50),
        "water_heater_ac_kwh": num(data, "water_heater_ac_kwh", 0, 50),
        "is_weekend": int(num(data, "is_weekend", 0, 1)),
        "month": int(num(data, "month", 1, 12)),
    }
    X = pd.DataFrame([row])[bundle["features"]]
    model = bundle["model"]
    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    classes = [int(c) for c in model.classes_]
    resp = {
        "prediction": bundle["class_names"][pred],
        "probabilities": {bundle["class_names"][c]: round(float(p), 4) for c, p in zip(classes, proba)},
        "thresholds_kwh": {"low_max": bundle["low_max_kwh"], "high_min": bundle["high_min_kwh"]},
        "note": "Low/Medium/High come from percentile thresholds on historical daily kWh; they are not independent ground truth.",
    }
    daily_kwh = num(data, "daily_kwh", 0, 200, required=False)
    if daily_kwh is not None:
        idx = int(np.digitize([daily_kwh], [bundle["low_max_kwh"], bundle["high_min_kwh"]])[0])
        resp["threshold_label_for_daily_kwh"] = bundle["class_names"][idx]
    return jsonify(resp)


@app.post("/api/cluster")
def cluster():
    data = read_json_body()
    bundle = load_model(pre.KMEANS_MODEL_PATH, "K-Means")
    row = {
        "daily_kwh": num(data, "daily_kwh", 0, 200),
        "peak_kw": num(data, "peak_kw", 0, 20),
        "evening_share_pct": num(data, "evening_share_pct", 0, 100),
    }
    X = pd.DataFrame([row])[bundle["features"]]
    Z = bundle["scaler"].transform(X)
    km = bundle["kmeans"]
    c = int(km.predict(Z)[0])
    dist = float(np.linalg.norm(Z[0] - km.cluster_centers_[c]))
    profile = next((p for p in bundle["profiles"] if p["cluster"] == c), None)
    return jsonify({"cluster": c, "distance_to_centre": round(dist, 4),
                    "input": row, "profile": profile})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
