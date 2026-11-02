from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_version"]


def test_predict_batch() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={"instances": [[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]]},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["predictions"]) == 2
    assert body["predictions"][0] == "setosa"


def test_predict_wrong_feature_count() -> None:
    with TestClient(app) as client:
        response = client.post("/predict", json={"instances": [[1.0, 2.0]]})
    assert response.status_code == 422


def test_predict_invalid_type() -> None:
    with TestClient(app) as client:
        response = client.post("/predict", json={"instances": [["a", "b", "c", "d"]]})
    assert response.status_code == 422


def test_metrics() -> None:
    with TestClient(app) as client:
        client.post("/predict", json={"instances": [[5.1, 3.5, 1.4, 0.2]]})
        response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["predictions_total"] >= 1
