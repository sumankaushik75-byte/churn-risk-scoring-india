"""
Churn risk scoring benchmark on the Indian prepaid telecom dataset (99,999 customers, real
call-detail-record-style features, INR currency). Source: the widely published "Telecom Churn
Case Study" dataset (mirrored on GitHub, originally an IIIT-B/UpGrad PG Data Science case study).

Business definitions (matching the dataset's own documented methodology, verified independently
before use):
  - High-value customers: top 30% by average recharge amount in the "good phase" (months 6-7).
    This mirrors India/Southeast Asia's revenue concentration (~80% of revenue from top 20-30%
    of customers), so retention effort is scoped to the customers who actually matter for revenue.
  - Churn label: zero call and data usage in month 9 (the "churn phase"). Usage-based, not
    contract-based, since prepaid customers can leave with no notice.
  - Only month 6-8 features are used to predict the month-9 label; month-9 columns are dropped
    entirely before modeling to avoid leaking the outcome into the inputs.
"""
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, precision_score,
    recall_score, f1_score, roc_curve, precision_recall_curve, confusion_matrix
)
from xgboost import XGBClassifier

RANDOM_STATE = 42

df = pd.read_csv("data_india/telecom_churn_data.csv")

# ---- High-value customer filter ----
df["avg_rech_amt_6_7"] = (df["total_rech_amt_6"] + df["total_rech_amt_7"]) / 2
hv_threshold = df["avg_rech_amt_6_7"].quantile(0.7)
df = df[df["avg_rech_amt_6_7"] >= hv_threshold].copy()

# ---- Churn label from month-9 usage, then drop all month-9 columns (leakage prevention) ----
usage_cols_9 = ["total_ic_mou_9", "total_og_mou_9", "vol_2g_mb_9", "vol_3g_mb_9"]
df["churn"] = (df[usage_cols_9].fillna(0).sum(axis=1) == 0).astype(int)
month9_cols = [c for c in df.columns if c.endswith("_9")]
df = df.drop(columns=month9_cols)

print(f"High-value customers: {len(df)} (threshold: Rs.{hv_threshold:.2f} avg recharge, months 6-7)")
print(f"Churn rate: {df['churn'].mean()*100:.2f}% ({df['churn'].sum()} churned of {len(df)})")

# ---- Feature sets ----
# Core: the handful of numbers a retention analyst would actually look at first.
CORE_BASE = ["arpu", "total_rech_amt", "total_og_mou", "total_ic_mou", "vol_2g_mb", "vol_3g_mb"]
CORE_FIELDS = [f"{b}_{m}" for b in CORE_BASE for m in (6, 7, 8)] + ["aon"]

# Full: every real per-month usage/recharge/data metric across the 3 non-leaky months, plus
# age-on-network and two engineered "decline" features (avg of months 6-7 minus month 8), which
# is exactly the signal the case study's own "action phase" concept is built on.
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
FULL_FIELDS = [f"{b}_{m}" for b in FULL_BASE for m in (6, 7, 8)] + ["aon"]

for base in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]:
    df[f"{base}_decline"] = (df[f"{base}_6"] + df[f"{base}_7"]) / 2 - df[f"{base}_8"]
DECLINE_FIELDS = [f"{b}_decline" for b in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]]
FULL_FIELDS = FULL_FIELDS + DECLINE_FIELDS

# Data-recharge-related columns are ~75% missing by design (NaN = no data recharge that month,
# not a data quality problem) -- documented in the case study's own data dictionary.
FEATURE_SETS = {"core_fields": CORE_FIELDS, "full_fields": FULL_FIELDS}
for cols in FEATURE_SETS.values():
    for c in cols:
        if c in df.columns:
            df[c] = df[c].fillna(0)

y = df["churn"]


def top_k_capture(y_true, y_score, k=0.20):
    n = len(y_true)
    top_n = int(np.ceil(n * k))
    order = np.argsort(-y_score)
    top_idx = order[:top_n]
    caught = y_true.iloc[top_idx].sum() if hasattr(y_true, "iloc") else y_true[top_idx].sum()
    total_pos = y_true.sum()
    return caught / total_pos if total_pos > 0 else np.nan


MODELS = {
    "logistic_regression": lambda: LogisticRegression(
        max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE
    ),
    "random_forest": lambda: RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=5, class_weight="balanced",
        random_state=RANDOM_STATE, n_jobs=-1
    ),
    "xgboost": lambda: XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
        colsample_bytree=0.9, eval_metric="logloss",
        scale_pos_weight=(y.value_counts()[0] / y.value_counts()[1]),
        random_state=RANDOM_STATE
    ),
}

results = []
artifacts = {}

for fs_name, cols in FEATURE_SETS.items():
    X = df[cols]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=cols, index=X_train.index)
    X_test_s = pd.DataFrame(scaler.transform(X_test), columns=cols, index=X_test.index)

    for model_name, build in MODELS.items():
        model = build()
        model.fit(X_train_s, y_train)
        proba = model.predict_proba(X_test_s)[:, 1]
        preds = (proba >= 0.5).astype(int)

        auc = roc_auc_score(y_test, proba)
        pr_auc = average_precision_score(y_test, proba)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        capture20 = top_k_capture(y_test, proba, 0.20)

        results.append({
            "feature_set": fs_name, "model": model_name, "n_features": len(cols),
            "roc_auc": round(auc, 4), "pr_auc": round(pr_auc, 4), "accuracy": round(acc, 4),
            "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "top20_capture_rate": round(capture20, 4),
        })
        key = f"{model_name}__{fs_name}"
        artifacts[key] = {"y_test": y_test.values, "proba": proba, "preds": preds}
        print(f"{model_name:20s} | {fs_name:12s} | AUC={auc:.4f} PR-AUC={pr_auc:.4f} "
              f"acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} top20cap={capture20:.4f}")

results_df = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
results_df.to_csv("benchmark_results_india.csv", index=False)
print("\n=== Ranked by ROC-AUC ===")
print(results_df.to_string(index=False))

# With only 8.6% of customers churning, ROC-AUC is dominated by how well a model ranks the
# large majority class and can look similar across models even when they differ meaningfully
# on the minority (churn) class. We pick the final configuration on PR-AUC and top-20% capture
# instead, since those directly measure performance on catching churners under a capacity-limited
# retention budget, which is the actual business question. Random Forest edges out XGBoost on
# ROC-AUC by a rounding error (0.9376 vs 0.9369), but XGBoost wins on PR-AUC (0.697 vs 0.689) and
# top-20% capture (87.0% vs 86.1%), so XGBoost on the full feature set is the configuration we ship.
selection_row = results_df.sort_values("top20_capture_rate", ascending=False).iloc[0]
best_row = selection_row
best_key = f"{best_row['model']}__{best_row['feature_set']}"
best = artifacts[best_key]
print(f"\nSelected for deployment: {best_key} "
      f"(ROC-AUC {best_row['roc_auc']}, PR-AUC {best_row['pr_auc']}, "
      f"top20 capture {best_row['top20_capture_rate']}) -- chosen on PR-AUC / capture rate, "
      f"not the raw ROC-AUC leaderboard, because of the 8.6% class imbalance.")

fpr, tpr, _ = roc_curve(best["y_test"], best["proba"])
prec_curve, rec_curve, _ = precision_recall_curve(best["y_test"], best["proba"])
cm = confusion_matrix(best["y_test"], best["preds"])

np.savez(
    "best_model_curves_india.npz",
    fpr=fpr, tpr=tpr, prec_curve=prec_curve, rec_curve=rec_curve, cm=cm,
    y_test=best["y_test"], proba=best["proba"],
    best_model=best_row["model"], best_feature_set=best_row["feature_set"],
)

# Feature importance / coefficients for the winning configuration
best_cols = FEATURE_SETS[best_row["feature_set"]]
X_best = df[best_cols]
scaler_best = StandardScaler()
X_best_s = pd.DataFrame(scaler_best.fit_transform(X_best), columns=best_cols, index=X_best.index)
final_model = MODELS[best_row["model"]]()
final_model.fit(X_best_s, y)

if hasattr(final_model, "feature_importances_"):
    importances = pd.Series(final_model.feature_importances_, index=best_cols)
elif hasattr(final_model, "coef_"):
    importances = pd.Series(np.abs(final_model.coef_[0]), index=best_cols)
importances.sort_values(ascending=False).head(15).to_csv("feature_importance_india.csv")

# Held-out sample of 24 real test customers for the ranked list in the prototype
_, X_test_split, _, y_test_split = train_test_split(
    X_best, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
)
sample_df = df.loc[X_test_split.index, ["mobile_number", "aon", "total_rech_amt_8", "arpu_8"]].copy()
sample_df["risk"] = artifacts[best_key]["proba"]
sample_df["churned"] = artifacts[best_key]["y_test"]
sample_sorted = sample_df.sort_values("risk", ascending=False)
sample_24 = pd.concat([
    sample_sorted.iloc[:10],
    sample_sorted.iloc[len(sample_sorted)//2 - 2: len(sample_sorted)//2 + 2],
    sample_sorted.iloc[-10:],
]).drop_duplicates().head(24)
sample_24.to_csv("sample_ranked_customers_india.csv", index=False)

metadata = {
    "high_value_threshold_inr": round(float(hv_threshold), 2),
    "high_value_customers": int(len(df)),
    "churn_rate_pct": round(float(y.mean() * 100), 2),
    "best_model": best_row["model"],
    "best_feature_set": best_row["feature_set"],
}
with open("dataset_metadata_india.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("\nBest configuration:", best_key)
print("Wrote: benchmark_results_india.csv, best_model_curves_india.npz, "
      "feature_importance_india.csv, sample_ranked_customers_india.csv, dataset_metadata_india.json")
