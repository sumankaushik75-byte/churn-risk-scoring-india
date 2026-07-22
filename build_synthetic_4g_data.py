"""
Synthetic 4G-era data usage transform, grounded in real 2026 operator averages.

The underlying dataset ("Telecom Churn Case Study") is 2G/3G-era: its only data-usage
columns are vol_2g_mb_* and vol_3g_mb_*, with no 4G field at all, meaning it predates
India's 2016 Jio-driven 4G/unlimited-data shift. Everything else in the dataset (recharge
amount, ARPU, voice minutes, tenure, and the real usage-based churn label) is
generation-agnostic and is kept completely unchanged.

Only the data-usage columns for months 6-8 (the model's inputs) are replaced with a
synthetic "data_gb" feature, built as follows:
  1. Compute each real customer's percentile rank in the original vol_2g_mb + vol_3g_mb
     distribution for that month, separately per month, so a customer's real relative
     usage intensity (heavy vs. light user) is preserved.
  2. Map that percentile to a synthetic monthly GB draw from a lognormal mixture grounded
     in real, current per-operator averages (FY26 Q4, publicly reported): Jio 42.3 GB,
     Airtel 31.4 GB, Vodafone Idea (4G/5G users) 20.2 GB, mixed at roughly their reported
     active-subscriber shares (~40/33/18%, remainder BSNL/other at a lower, unlisted
     average assumed near VI's).
This is a distributional resampling, not a linear rescale, so it is not simply undone by
StandardScaler: relative gaps and skew change, not just the units.

Explicitly NOT a claim to real 4G customer behaviour: this is a synthetic stand-in for a
real dataset gap, built for experimentation only. It is intentionally excluded from the
graded submission (docx/pptx) -- it exists as a live, separately-labeled endpoint only.
"""
import numpy as np
import pandas as pd
from scipy.stats import rankdata

RANDOM_STATE = 42
rng = np.random.default_rng(RANDOM_STATE)

# Real, current per-operator average monthly data usage (GB/user), FY26 Q4, publicly
# reported (telecomtalk.info / subkuz.com quarterly results coverage).
OPERATOR_AVG_GB = {"jio": 42.3, "airtel": 31.4, "vi": 20.2, "other": 16.0}
OPERATOR_SHARE = {"jio": 0.40, "airtel": 0.33, "vi": 0.18, "other": 0.09}
# Lognormal shape controlling spread around each operator's mean (coefficient of variation
# roughly 0.5, typical for skewed usage distributions); mu solved so the median maps close
# to the target mean under this sigma.
SIGMA = 0.5


def sample_operator_gb(n, rng):
    """Draw n monthly GB usage values from the operator mixture."""
    ops = rng.choice(list(OPERATOR_SHARE.keys()), size=n, p=list(OPERATOR_SHARE.values()))
    means = np.array([OPERATOR_AVG_GB[o] for o in ops])
    mu = np.log(means) - (SIGMA ** 2) / 2
    return rng.lognormal(mean=mu, sigma=SIGMA)


def rank_preserving_resample(real_values, rng):
    """Map real_values' percentile ranks onto a fresh synthetic-GB distribution draw,
    so a customer who was a heavy 2G/3G user becomes a heavy synthetic-4G user."""
    n = len(real_values)
    ranks = rankdata(real_values, method="average") / (n + 1)  # in (0, 1)
    synthetic_pool = np.sort(sample_operator_gb(n, rng))
    idx = np.clip((ranks * n).astype(int), 0, n - 1)
    return synthetic_pool[idx]


def build_synthetic_dataset(src_csv="data_india/telecom_churn_data.csv"):
    df = pd.read_csv(src_csv)

    # Same real, documented filters as the graded submission -- unchanged.
    df["avg_rech_amt_6_7"] = (df["total_rech_amt_6"] + df["total_rech_amt_7"]) / 2
    hv_threshold = df["avg_rech_amt_6_7"].quantile(0.7)
    df = df[df["avg_rech_amt_6_7"] >= hv_threshold].copy()

    usage_cols_9 = ["total_ic_mou_9", "total_og_mou_9", "vol_2g_mb_9", "vol_3g_mb_9"]
    df["churn"] = (df[usage_cols_9].fillna(0).sum(axis=1) == 0).astype(int)
    df = df.drop(columns=[c for c in df.columns if c.endswith("_9")])

    for m in (6, 7, 8):
        real_total = (df[f"vol_2g_mb_{m}"].fillna(0) + df[f"vol_3g_mb_{m}"].fillna(0)).values
        df[f"data_gb_{m}"] = rank_preserving_resample(real_total, rng)

    df = df.drop(columns=[c for c in df.columns if c.startswith("vol_2g_mb_") or c.startswith("vol_3g_mb_")])

    out_path = "data_india/synthetic_4g_high_value_customers.csv"
    df.to_csv(out_path, index=False)
    print(f"High-value customers: {len(df)} (threshold Rs.{hv_threshold:.2f})")
    print(f"Churn rate: {df['churn'].mean()*100:.2f}%")
    for m in (6, 7, 8):
        col = df[f"data_gb_{m}"]
        print(f"  data_gb_{m}: mean={col.mean():.1f} GB, median={col.median():.1f} GB, "
              f"p90={col.quantile(0.9):.1f} GB")
    print(f"Saved: {out_path}")
    return df


if __name__ == "__main__":
    build_synthetic_dataset()
