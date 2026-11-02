from __future__ import annotations

import joblib
import pytest

from app.schema import PredictRequest

ARTIFACT = "model/artifacts/model.pkl"


def test_accepts_valid_rows() -> None:
    payload = PredictRequest(instances=[[5.1, 3.5, 1.4, 0.2]])
    assert len(payload.instances) == 1


def test_rejects_empty_batch() -> None:
    with pytest.raises(ValueError):
        PredictRequest(instances=[])


def test_rejects_empty_row() -> None:
    with pytest.raises(ValueError):
        PredictRequest(instances=[[]])


def test_artifact_contract() -> None:
    artifact = joblib.load(ARTIFACT)
    assert artifact["features"]
    assert artifact["class_names"]
    assert artifact["version"]
    assert hasattr(artifact["model"], "predict")
