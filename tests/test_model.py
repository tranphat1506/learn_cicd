from __future__ import annotations

import joblib
import numpy as np

from app.main import MODEL_PATH


def test_model_predicts_known_class() -> None:
    artifact = joblib.load(MODEL_PATH)
    matrix = np.asarray([[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]])
    predictions = [artifact["class_names"][int(i)] for i in artifact["model"].predict(matrix)]

    assert len(predictions) == 2
    assert set(predictions).issubset(set(artifact["class_names"]))
    assert predictions[0] == "setosa"
