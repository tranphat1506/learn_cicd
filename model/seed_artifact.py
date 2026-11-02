"""Stand-in for a model artifact produced outside this repo (registry, notebook, vendor).

Week 4 replaces this with a pull from MLflow / DVC. Everything downstream
(evaluate, package, deploy) treats the artifact as read-only input.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import sklearn
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data"
MODEL_PATH = ARTIFACT_DIR / "model.pkl"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"
GOLDEN_PATH = DATA_DIR / "golden.csv"
MODEL_VERSION = "0.1.0"
SEED = 42


def main() -> None:
    dataset = load_iris()
    features = list(dataset.feature_names)
    class_names = [str(name) for name in dataset.target_names]

    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data,
        dataset.target,
        test_size=0.3,
        random_state=SEED,
        stratify=dataset.target,
    )

    model = LogisticRegression(max_iter=500, random_state=SEED).fit(x_train, y_train)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "features": features,
            "class_names": class_names,
            "version": MODEL_VERSION,
            "framework": f"scikit-learn=={sklearn.__version__}",
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        MODEL_PATH,
    )

    header = ",".join([*features, "target"])
    rows = [
        ",".join([*(f"{value:.4f}" for value in row), class_names[int(label)]])
        for row, label in zip(x_test, y_test, strict=True)
    ]
    GOLDEN_PATH.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")

    metadata = {
        "version": MODEL_VERSION,
        "features": features,
        "class_names": class_names,
        "framework": f"scikit-learn=={sklearn.__version__}",
        "golden_rows": len(rows),
        "golden_sha256": hashlib.sha256(GOLDEN_PATH.read_bytes()).hexdigest(),
        "seed": SEED,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"artifact : {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KiB)")
    print(f"golden   : {GOLDEN_PATH} ({len(rows)} rows)")
    print(f"metadata : {METADATA_PATH}")


if __name__ == "__main__":
    main()
