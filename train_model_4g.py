"""
Benchmark on the synthetic 4G dataset (see build_synthetic_4g_data.py for how it's built).
Reference/exploration only -- not part of the graded submission.
"""
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier

RANDOM_STATE = 42

df = pd.read_csv("data_india/synthetic_4g_high_value_customers.csv")

FULL_BASE = [
    "arpu", "onnet_mou", "offnet_mou", "roam_ic_mou", "roam_og_mou",
    "loc_og_t2t_mou", "loc_og_t2m_mou", "loc_og_t2f_mou", "loc_og_mou",
    "std_og_t2t_mou", "std_og_t2m_mou", "std_og_t2f_mou", "std_og_mou",
    "isd_og_mou", "spl_og_mou", "og_others", "total_og_mou",
    "loc_ic_t2t_mou", "loc_ic_t2m_mou", "loc_ic_t2f_mou", "loc_ic_mou",
    "std_ic_t2t_mou", "std_ic_t2m_mou", "std_ic_t2f_mou", "std_ic_mou",
    "spl_ic_mou", "isd_ic_mou", "ic_others", "total_ic_mou",
    "total_rech_num", "total_rech_amt", "max_rech_amt", "last_day_rch_amt",
    "total_rech_data", "max_rech_data", "count_rech_2g", "count_rech_3g", "av_rech_amt_data",
    "data_gb", "arpu_3g", "arpu_2g", "monthly_2g", "sachet_2g", "monthly_3g", "sachet_3g",
]
FULL_FIELDS = [f"{b}_{m}" for b in FULL_BASE for m in (6, 7, 8) if f"{b}_{m}" in df.columns] + ["aon"]

for base in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt", "data_gb"]:
    df[f"{base}_decline"] = (df[f"{base}_6"] + df[f"{base}_7"]) / 2 - df[f"{base}_8"]
DECLINE_FIELDS = [f"{b}_decline" for b in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt", "data_gb"]]
FULL_FIELDS = FULL_FIELDS + DECLINE_FIELDS

for c in FULL_FIELDS:
    if c in df.columns:
        df[c] = df[c].fillna(0)

X = df[FULL_FIELDS]
y = df["churn"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
)
scaler = StandardScaler()
X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=FULL_FIELDS, index=X_train.index)
X_test_s = pd.DataFrame(scaler.transform(X_test), columns=FULL_FIELDS, index=X_test.index)

spw = y_train.value_counts()[0] / y_train.value_counts()[1]
model = XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
    colsample_bytree=0.9, eval_metric="logloss", scale_pos_weight=spw, random_state=RANDOM_STATE
)
model.fit(X_train_s, y_train)
proba = model.predict_proba(X_test_s)[:, 1]
preds = (proba >= 0.5).astype(int)

auc = roc_auc_score(y_test, proba)
pr_auc = average_precision_score(y_test, proba)
acc = accuracy_score(y_test, preds)
prec = precision_score(y_test, preds)
rec = recall_score(y_test, preds)
f1 = f1_score(y_test, preds)

order = np.argsort(-proba)
top_n = int(np.ceil(len(y_test) * 0.20))
capture20 = y_test.iloc[order[:top_n]].sum() / y_test.sum()

print(f"4G-synthetic XGBoost (full fields, n={len(FULL_FIELDS)}): "
      f"ROC-AUC={auc:.4f} PR-AUC={pr_auc:.4f} acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} "
      f"f1={f1:.4f} top20cap={capture20:.4f}")
print("(For reference, the real 2G/3G submission model: ROC-AUC=0.9369 PR-AUC=0.6971 "
      "rec=0.8241 top20cap=0.8704)")

with open("benchmark_results_4g.json", "w") as f:
    json.dump({
        "roc_auc": round(float(auc), 4), "pr_auc": round(float(pr_auc), 4),
        "accuracy": round(float(acc), 4), "precision": round(float(prec), 4),
        "recall": round(float(rec), 4), "f1": round(float(f1), 4),
        "top20_capture_rate": round(float(capture20), 4), "n_features": len(FULL_FIELDS),
    }, f, indent=2)

# Refit on all data for the serving artifact
X_all_s = pd.DataFrame(StandardScaler().fit_transform(X), columns=FULL_FIELDS, index=X.index)
scaler_full = StandardScaler().fit(X)
spw_full = y.value_counts()[0] / y.value_counts()[1]
final_model = XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
    colsample_bytree=0.9, eval_metric="logloss", scale_pos_weight=spw_full, random_state=RANDOM_STATE
)
final_model.fit(pd.DataFrame(scaler_full.transform(X), columns=FULL_FIELDS, index=X.index), y)

import joblib
from sklearn.pipeline import Pipeline
pipeline = Pipeline([("scaler", scaler_full), ("clf", final_model)])
joblib.dump(pipeline, "best_model_pipeline_4g.joblib")

medians = X.median().to_dict()
metadata = {
    "model": "xgboost", "feature_set": "full_fields_4g_synthetic", "n_features": len(FULL_FIELDS),
    "all_fields": FULL_FIELDS, "field_medians": {k: float(v) for k, v in medians.items()},
    "held_out_metrics": {"roc_auc": round(float(auc), 4), "pr_auc": round(float(pr_auc), 4),
                          "recall": round(float(rec), 4), "top20_capture_rate": round(float(capture20), 4)},
    "note": "Synthetic 4G data-usage projection grounded in FY26 Q4 operator averages "
            "(Jio 42.3GB, Airtel 31.4GB, VI 20.2GB); voice/recharge/tenure fields and the "
            "churn label are real. Reference/exploration only, not part of the graded submission.",
}
with open("best_model_metadata_4g.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Saved: best_model_pipeline_4g.joblib, best_model_metadata_4g.json, benchmark_results_4g.json")
