"""
Builds the model artifact served by api.py for the Indian prepaid-churn prototype: a real
scikit-learn Pipeline (StandardScaler + XGBClassifier) for the benchmarked, selected
configuration (XGBoost, full 143-field set, chosen on PR-AUC / top-20% capture rather than
raw ROC-AUC -- see train_model_india.py). Also saves per-feature medians so the live demo can
default the ~127 fields a demo user won't realistically hand-enter, while the ~16 headline
fields (recharge, usage, data, roaming, tenure) stay genuinely live.
"""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

RANDOM_STATE = 42

df = pd.read_csv("data_india/telecom_churn_data.csv")
df["avg_rech_amt_6_7"] = (df["total_rech_amt_6"] + df["total_rech_amt_7"]) / 2
hv_threshold = df["avg_rech_amt_6_7"].quantile(0.7)
df = df[df["avg_rech_amt_6_7"] >= hv_threshold].copy()

usage_cols_9 = ["total_ic_mou_9", "total_og_mou_9", "vol_2g_mb_9", "vol_3g_mb_9"]
df["churn"] = (df[usage_cols_9].fillna(0).sum(axis=1) == 0).astype(int)
df = df.drop(columns=[c for c in df.columns if c.endswith("_9")])

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
    "vol_2g_mb", "vol_3g_mb", "arpu_3g", "arpu_2g", "monthly_2g", "sachet_2g",
    "monthly_3g", "sachet_3g",
]
RAW_FIELDS = [f"{b}_{m}" for b in FULL_BASE for m in (6, 7, 8)] + ["aon"]
for c in RAW_FIELDS:
    if c in df.columns:
        df[c] = df[c].fillna(0)

for base in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]:
    df[f"{base}_decline"] = (df[f"{base}_6"] + df[f"{base}_7"]) / 2 - df[f"{base}_8"]
DECLINE_FIELDS = [f"{b}_decline" for b in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]]
ALL_FIELDS = RAW_FIELDS + DECLINE_FIELDS  # 143 features, matches train_model_india.py full_fields

X = df[ALL_FIELDS]
y = df["churn"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
)
spw = (y_train.value_counts()[0] / y_train.value_counts()[1])

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
        colsample_bytree=0.9, eval_metric="logloss", scale_pos_weight=spw,
        random_state=RANDOM_STATE
    )),
])
pipeline.fit(X_train, y_train)
proba_test = pipeline.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, proba_test)
pr_auc = average_precision_score(y_test, proba_test)
print(f"Sanity check on held-out test split: ROC-AUC={auc:.4f}, PR-AUC={pr_auc:.4f} "
      f"(should match benchmark_results_india.csv's xgboost/full_fields row: 0.9369 / 0.6971)")

# Refit on all high-value customers for the artifact we actually serve.
spw_full = (y.value_counts()[0] / y.value_counts()[1])
final_pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
        colsample_bytree=0.9, eval_metric="logloss", scale_pos_weight=spw_full,
        random_state=RANDOM_STATE
    )),
])
final_pipeline.fit(X, y)
joblib.dump(final_pipeline, "best_model_pipeline_india.joblib")

# Headline fields a demo user can actually type into a form; everything else in the 143-field
# input defaults to its population median so the live demo stays usable without pretending a
# person can hand-enter a full call-detail-record profile.
UI_FIELDS = [
    "arpu_6", "arpu_7", "arpu_8",
    "total_rech_amt_6", "total_rech_amt_7", "total_rech_amt_8",
    "total_og_mou_6", "total_og_mou_7", "total_og_mou_8",
    "total_ic_mou_6", "total_ic_mou_7", "total_ic_mou_8",
    "vol_2g_mb_8", "vol_3g_mb_8", "roam_og_mou_8", "aon",
]
medians = X[RAW_FIELDS].median().to_dict()

metadata = {
    "model": "xgboost", "feature_set": "full_fields", "n_features": len(ALL_FIELDS),
    "all_fields": ALL_FIELDS, "raw_fields": RAW_FIELDS, "decline_fields": DECLINE_FIELDS,
    "ui_fields": UI_FIELDS, "field_medians": {k: float(v) for k, v in medians.items()},
    "high_value_threshold_inr": round(float(hv_threshold), 2),
    "held_out_sanity_check": {"roc_auc": round(float(auc), 4), "pr_auc": round(float(pr_auc), 4)},
    "trained_on_rows": int(len(df)),
    "currency": "INR",
}
with open("best_model_metadata_india.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Saved: best_model_pipeline_india.joblib, best_model_metadata_india.json")
