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
