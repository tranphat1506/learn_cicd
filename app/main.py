from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException

from app.schema import PredictRequest, PredictResponse

MODEL_PATH = Path(os.getenv("MODEL_PATH", "model/artifacts/model.pkl"))
STATE = {"predictions": 0, "errors": 0, "started_at": time.time()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.exists():
        raise RuntimeError(f"model artifact not found at {MODEL_PATH}. Run `make seed` first.")
    app.state.artifact = joblib.load(MODEL_PATH)
    yield


app = FastAPI(title="model-api", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    artifact = app.state.artifact
    return {"status": "ok", "model_version": artifact.get("version", "unknown")}


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    artifact = app.state.artifact
    n_features = len(artifact["features"])
    for row in payload.instances:
        if len(row) != n_features:
            STATE["errors"] += 1
            raise HTTPException(
                status_code=422,
                detail=f"each instance must have {n_features} features",
            )

    matrix = np.asarray(payload.instances, dtype=float)
    class_names = artifact["class_names"]
    predictions = [class_names[int(idx)] for idx in artifact["model"].predict(matrix)]
    STATE["predictions"] += len(predictions)
    return PredictResponse(
        predictions=predictions,
        model_version=artifact.get("version", "unknown"),
    )


@app.get("/metrics")
def metrics() -> dict[str, object]:
    artifact = app.state.artifact
    return {
        "predictions_total": STATE["predictions"],
        "errors_total": STATE["errors"],
        "uptime_seconds": round(time.time() - STATE["started_at"], 1),
        "model_version": artifact.get("version", "unknown"),
    }
