FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py .
COPY ["Churn Risk Scoring - Interactive Prototype.html", "./"]
COPY best_model_pipeline_india.joblib .
COPY best_model_metadata_india.json .
COPY best_model_pipeline_4g.joblib .
COPY best_model_metadata_4g.json .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
