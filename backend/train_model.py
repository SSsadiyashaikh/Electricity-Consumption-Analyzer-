"""
Train and evaluate the three ML models on the REAL UCI dataset.
Run:  python train_model.py
Nothing is simulated: if the dataset file is missing this script stops with a message.

Outputs
  models/linear_regression.joblib   (scaler + LinearRegression pipeline)
  models/decision_tree.joblib       (tree + thresholds learned from training days only)
  models/kmeans.joblib              (KMeans + StandardScaler + cluster profiles)
  outputs/daily_summary.csv, outputs/monthly_summary.csv, outputs/metrics.json
"""
import json
import sys
from datetime import datetime

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, mean_absolute_error,
                             mean_squared_error, precision_recall_fscore_support,
                             r2_score, silhouette_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import preprocess as pre

RANDOM_STATE = 42


def regression_scores(y_true, y_pred):
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def split_days(daily):
    """Chronological split: earliest 80% of days = train, latest 20% = test."""
    daily = daily.sort_values("date").reset_index(drop=True)
    n_train = int(len(daily) * pre.TRAIN_FRACTION)
    return daily.iloc[:n_train], daily.iloc[n_train:]


# ---------------------------------------------------------------- Linear Regression
def train_linear(daily):
    series = daily.set_index("date")["daily_kwh"].asfreq("D")
    data = pre.make_forecast_features(series).assign(target=series).dropna()
    n_train = int(len(data) * pre.TRAIN_FRACTION)
    train, test = data.iloc[:n_train], data.iloc[n_train:]

    pipe = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
    pipe.fit(train[pre.FORECAST_FEATURES], train["target"])  # scaler sees train only

    pred = pipe.predict(test[pre.FORECAST_FEATURES])
    scores = regression_scores(test["target"], pred)
    baseline = regression_scores(test["target"], test["lag_1"])  # "same as yesterday"

    joblib.dump({"pipeline": pipe, "features": pre.FORECAST_FEATURES}, pre.LINEAR_MODEL_PATH)
    coefs = dict(zip(pre.FORECAST_FEATURES, pipe.named_steps["model"].coef_.tolist()))
    return {
        "task": "Forecast daily electricity consumption (kWh)",
        "features": pre.FORECAST_FEATURES,
        "train_rows": int(len(train)), "test_rows": int(len(test)),
        "train_period": [str(train.index.min().date()), str(train.index.max().date())],
        "test_period": [str(test.index.min().date()), str(test.index.max().date())],
        "test_metrics": scores,
        "baseline_yesterday_metrics": baseline,
        "standardized_coefficients": coefs,
        "intercept": float(pipe.named_steps["model"].intercept_),
    }


# ---------------------------------------------------------------- Decision Tree
def label_from_thresholds(values, low_max, high_min):
    """Low: kWh < low_max | Medium: low_max <= kWh < high_min | High: kWh >= high_min"""
    return np.digitize(values, [low_max, high_min])  # 0,1,2


def train_tree(daily):
    train, test = split_days(daily)
    # Thresholds come from TRAINING days only (33rd and 67th percentile of daily kWh).
    low_max = float(np.percentile(train["daily_kwh"], 100 / 3))
    high_min = float(np.percentile(train["daily_kwh"], 200 / 3))
    y_train = label_from_thresholds(train["daily_kwh"], low_max, high_min)
    y_test = label_from_thresholds(test["daily_kwh"], low_max, high_min)

    # daily_kwh itself is NOT a feature (otherwise the tree would just re-learn the
    # threshold). It predicts the class from peak power, appliance groups and calendar.
    tree = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10,
                                  class_weight="balanced", random_state=RANDOM_STATE)
    tree.fit(train[pre.CLASSIFY_FEATURES], y_train)
    pred = tree.predict(test[pre.CLASSIFY_FEATURES])

    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, pred, labels=[0, 1, 2], average=None, zero_division=0)
    mp, mr, mf, _ = precision_recall_fscore_support(
        y_test, pred, labels=[0, 1, 2], average="macro", zero_division=0)

    joblib.dump({"model": tree, "features": pre.CLASSIFY_FEATURES, "class_names": pre.CLASS_NAMES,
                 "low_max_kwh": low_max, "high_min_kwh": high_min}, pre.TREE_MODEL_PATH)
    return {
        "task": "Classify a day's consumption as Low / Medium / High",
        "features": pre.CLASSIFY_FEATURES,
        "threshold_method": ("Low < 33rd percentile of TRAINING-day kWh; High >= 67th percentile; "
                             "Medium in between. Percentiles use training days only."),
        "thresholds_kwh": {"low_max": low_max, "high_min": high_min},
        "note": ("Labels are derived from thresholds, so they are a convenient grouping, "
                 "not independent ground truth. Accuracy shows how well the tree recovers "
                 "that grouping from other measurements."),
        "train_rows": int(len(train)), "test_rows": int(len(test)),
        "test_class_counts": {n: int((y_test == i).sum()) for i, n in enumerate(pre.CLASS_NAMES)},
        "accuracy": float(accuracy_score(y_test, pred)),
        "macro": {"precision": float(mp), "recall": float(mr), "f1": float(mf)},
        "per_class": {n: {"precision": float(prec[i]), "recall": float(rec[i]), "f1": float(f1[i])}
                      for i, n in enumerate(pre.CLASS_NAMES)},
        "confusion_matrix": {"labels": pre.CLASS_NAMES,
                             "matrix": confusion_matrix(y_test, pred, labels=[0, 1, 2]).tolist()},
        "feature_importances": dict(zip(pre.CLASSIFY_FEATURES, tree.feature_importances_.tolist())),
    }


# ---------------------------------------------------------------- K-Means
def describe_cluster(means, overall):
    """Plain-language description built only from measured averages."""
    parts = []
    for feat, word in [("daily_kwh", "daily use"), ("peak_kw", "peak power"),
                       ("evening_share_pct", "evening share")]:
        ratio = means[feat] / overall[feat] if overall[feat] else 1.0
        level = "higher than" if ratio > 1.15 else "lower than" if ratio < 0.85 else "close to"
        parts.append(f"{word} {level} average")
    return ", ".join(parts)


def train_kmeans(daily):
    train, test = split_days(daily)
    scaler = StandardScaler().fit(train[pre.CLUSTER_FEATURES])
    X_train = scaler.transform(train[pre.CLUSTER_FEATURES])
    X_test = scaler.transform(test[pre.CLUSTER_FEATURES])

    k_scores = []
    best = None
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit(X_train)
        sil = float(silhouette_score(X_train, km.labels_))
        k_scores.append({"k": k, "inertia": float(km.inertia_), "silhouette": sil})
        if best is None or sil > best[0]:
            best = (sil, k, km)
    sil, k, km = best

    labels = km.labels_
    overall = train[pre.CLUSTER_FEATURES].mean().to_dict()
    profiles = []
    for c in range(k):
        rows = train[labels == c]
        means = rows[pre.CLUSTER_FEATURES].mean().to_dict()
        profiles.append({
            "cluster": c, "days": int(len(rows)),
            "share_of_days_pct": float(100 * len(rows) / len(train)),
            "weekend_share_pct": float(100 * rows["is_weekend"].mean()),
            "means": {f: float(v) for f, v in means.items()},
            "description": describe_cluster(means, overall),
        })
    profiles.sort(key=lambda p: p["means"]["daily_kwh"])

    test_sil = float(silhouette_score(X_test, km.predict(X_test)))
    joblib.dump({"kmeans": km, "scaler": scaler, "features": pre.CLUSTER_FEATURES,
                 "profiles": profiles, "overall_means": overall}, pre.KMEANS_MODEL_PATH)
    return {
        "task": "Group days by usage pattern (unsupervised)",
        "features": pre.CLUSTER_FEATURES,
        "chosen_k": int(k),
        "selection_rule": "k from 2 to 6 with the highest silhouette score on training days",
        "inertia": float(km.inertia_),
        "silhouette_train": sil,
        "silhouette_test": test_sil,
        "k_scores": k_scores,
        "profiles": profiles,
        "overall_means": {f: float(v) for f, v in overall.items()},
    }


def main():
    if not pre.dataset_available():
        print("ERROR: dataset not found at", pre.RAW_FILE)
        print("Run `python download_dataset.py`, download it manually (see README.md),")
        print("or run `python generate_sample_data.py` for a synthetic demo file,")
        print("then run `python train_model.py` again. No models were trained.")
        return 2

    source = pre.data_source()
    if source == "sample":
        print("NOTE: training on the SYNTHETIC sample file, not real measurements.")
        print("      Metrics below describe the sample only. Add the real dataset and retrain.")
    print("Loading dataset and aggregating (this can take a minute)...")
    daily, monthly = pre.build_summaries(save=True)
    print(f"Kept {len(daily)} usable days and {len(monthly)} months.")
    if len(daily) < 200:
        print("ERROR: too few usable days to train reliable models.")
        return 3

    pre.MODELS_DIR.mkdir(exist_ok=True)
    metrics = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": {
            "data_source": source,
            "data_file": pre.active_data_file().name,
            "usable_days": int(len(daily)), "months": int(len(monthly)),
            "first_day": str(daily["date"].min().date()), "last_day": str(daily["date"].max().date()),
            "min_valid_minutes_per_day": pre.MIN_VALID_MINUTES_PER_DAY,
            "split": f"chronological, first {int(pre.TRAIN_FRACTION * 100)}% train / rest test",
        },
    }
    print("Training Linear Regression...")
    metrics["linear_regression"] = train_linear(daily)
    print("Training Decision Tree...")
    metrics["decision_tree"] = train_tree(daily)
    print("Training K-Means...")
    metrics["kmeans"] = train_kmeans(daily)

    with open(pre.METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    if source == "sample":  # lets start_project.bat retrain once the real file appears
        pre.SAMPLE_FLAG.write_text("models were trained on synthetic sample data\n")
    else:
        pre.SAMPLE_FLAG.unlink(missing_ok=True)
    print("Saved models to", pre.MODELS_DIR)
    print("Saved metrics to", pre.METRICS_JSON)
    lr = metrics["linear_regression"]["test_metrics"]
    print(f"Linear Regression test: MAE={lr['mae']:.3f} RMSE={lr['rmse']:.3f} R2={lr['r2']:.3f}")
    print(f"Decision Tree test accuracy: {metrics['decision_tree']['accuracy']:.3f}")
    print(f"K-Means: k={metrics['kmeans']['chosen_k']}, silhouette={metrics['kmeans']['silhouette_train']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
