"""
Live scoring API for the Indian prepaid churn risk prototype.
Loads the fitted sklearn pipeline (best_model_pipeline_india.joblib: XGBoost on the full
143-field set, selected on PR-AUC / top-20% capture -- see train_model_india.py) and scores
customers sent from the browser prototype. Run with:

    uvicorn api:app --reload --port 8000
"""
import json

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Churn risk scoring API (India)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROTOTYPE_HTML = "Churn Risk Scoring - Interactive Prototype.html"


@app.get("/")
def serve_prototype():
    # Once deployed, the same service serves both the API and the demo page, so the browser
    # calls /score on its own origin instead of a hardcoded localhost address.
    return FileResponse(PROTOTYPE_HTML)

pipeline = joblib.load("best_model_pipeline_india.joblib")
with open("best_model_metadata_india.json") as f:
    METADATA = json.load(f)

ALL_FIELDS = METADATA["all_fields"]
RAW_FIELDS = METADATA["raw_fields"]
DECLINE_FIELDS = METADATA["decline_fields"]
MEDIANS = METADATA["field_medians"]

# Experimental: same model, retrained on a synthetic 4G-era data-usage projection (the
# underlying dataset only has 2G/3G fields). See build_synthetic_4g_data.py for how this
# is grounded in real FY26 operator averages. Reference/exploration endpoint only -- not
# part of the graded submission, kept fully separate from the /score path above.
pipeline_4g = joblib.load("best_model_pipeline_4g.joblib")
with open("best_model_metadata_4g.json") as f:
    METADATA_4G = json.load(f)

ALL_FIELDS_4G = METADATA_4G["all_fields"]
MEDIANS_4G = METADATA_4G["field_medians"]


class Customer(BaseModel):
    arpu_6: float
    arpu_7: float
    arpu_8: float
    total_rech_amt_6: float
    total_rech_amt_7: float
    total_rech_amt_8: float
    total_og_mou_6: float
    total_og_mou_7: float
    total_og_mou_8: float
    total_ic_mou_6: float
    total_ic_mou_7: float
    total_ic_mou_8: float
    vol_2g_mb_8: float
    vol_3g_mb_8: float
    roam_og_mou_8: float
    aon: int


def build_feature_row(customer: Customer) -> pd.DataFrame:
    row = dict(MEDIANS)  # start every one of the 127 non-exposed fields at its dataset median
    row.update(customer.model_dump())  # overlay the ~16 fields the demo actually sent
    for base in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]:
        row[f"{base}_decline"] = (row[f"{base}_6"] + row[f"{base}_7"]) / 2 - row[f"{base}_8"]
    return pd.DataFrame([{f: row[f] for f in ALL_FIELDS}])


def tier_and_action(risk: float, rech_decline: float, usage_decline: float) -> tuple[str, str]:
    if risk < 0.25:
        return "Low risk", "No action needed right now."
    tier = "High risk" if risk >= 0.5 else "Medium risk"
    if rech_decline > 0 and usage_decline > 0:
        action = "Recharge and usage both falling. Likely price-sensitive or trying a competitor SIM -- call with a matching recharge offer."
    elif usage_decline > 0:
        action = "Usage falling while recharge holds steady. Possible service or network-quality complaint -- route to a care callback, not a discount."
    else:
        action = "Flagged on other behavior signals. Proactive retention call before the next recharge cycle."
    return tier, action


@app.get("/health")
def health():
    return {"status": "ok", "model": METADATA["model"], "feature_set": METADATA["feature_set"],
            "currency": METADATA["currency"]}


@app.get("/model-info")
def model_info():
    return {k: v for k, v in METADATA.items() if k not in ("field_medians", "all_fields", "raw_fields")}


@app.post("/score")
def score(customer: Customer):
    X = build_feature_row(customer)
    risk = float(pipeline.predict_proba(X)[:, 1][0])
    rech_decline = X["total_rech_amt_decline"].iloc[0]
    usage_decline = X["total_og_mou_decline"].iloc[0]
    tier, action = tier_and_action(risk, rech_decline, usage_decline)
    return {"risk": round(risk, 4), "tier": tier, "action": action}


class Customer4G(BaseModel):
    arpu_6: float
    arpu_7: float
    arpu_8: float
    total_rech_amt_6: float
    total_rech_amt_7: float
    total_rech_amt_8: float
    total_og_mou_6: float
    total_og_mou_7: float
    total_og_mou_8: float
    total_ic_mou_6: float
    total_ic_mou_7: float
    total_ic_mou_8: float
    data_gb_8: float
    roam_og_mou_8: float
    aon: int


def build_feature_row_4g(customer: Customer4G) -> pd.DataFrame:
    row = dict(MEDIANS_4G)
    row.update(customer.model_dump())
    for base in ["arpu", "total_og_mou", "total_ic_mou", "total_rech_amt"]:
        row[f"{base}_decline"] = (row[f"{base}_6"] + row[f"{base}_7"]) / 2 - row[f"{base}_8"]
    # data_gb_decline needs months 6/7, which aren't exposed in the demo form; hold them at
    # their median and only vary month 8 with what the caller actually sent.
    row["data_gb_decline"] = (row["data_gb_6"] + row["data_gb_7"]) / 2 - row["data_gb_8"]
    return pd.DataFrame([{f: row[f] for f in ALL_FIELDS_4G}])


@app.get("/health-4g")
def health_4g():
    return {"status": "ok", "model": METADATA_4G["model"], "feature_set": METADATA_4G["feature_set"],
            "note": METADATA_4G["note"]}


@app.get("/model-info-4g")
def model_info_4g():
    return {k: v for k, v in METADATA_4G.items() if k not in ("field_medians", "all_fields")}


@app.post("/score-4g")
def score_4g(customer: Customer4G):
    """Experimental: XGBoost retrained on a synthetic 4G/GB-scale data-usage projection
    instead of the dataset's real 2G/3G MB fields. Voice, recharge, and tenure signals are
    real and unchanged; only the data-usage feature is a grounded synthetic stand-in.
    Reference endpoint, not part of the graded submission."""
    X = build_feature_row_4g(customer)
    risk = float(pipeline_4g.predict_proba(X)[:, 1][0])
    rech_decline = X["total_rech_amt_decline"].iloc[0]
    usage_decline = X["total_og_mou_decline"].iloc[0]
    tier, action = tier_and_action(risk, rech_decline, usage_decline)
    return {"risk": round(risk, 4), "tier": tier, "action": action, "experimental": True,
            "note": "Synthetic 4G-projected data usage; voice/recharge/tenure fields are real."}
