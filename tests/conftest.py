from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "model" / "artifacts" / "model.pkl"


@pytest.fixture(scope="session", autouse=True)
def seed_artifact_once() -> None:
    """Keep tests runnable on a fresh clone without a manual `make seed`."""
    if not ARTIFACT.exists():
        subprocess.run(
            [sys.executable, "-m", "model.seed_artifact"],
            cwd=ROOT,
            check=True,
        )
