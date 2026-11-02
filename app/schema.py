from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    """Batch inference payload. Feature count is checked against the model artifact."""

    instances: list[list[float]] = Field(..., min_length=1, max_length=256)

    @field_validator("instances")
    @classmethod
    def rows_must_not_be_empty(cls, value: list[list[float]]) -> list[list[float]]:
        for row in value:
            if not row:
                raise ValueError("instance must not be empty")
        return value


class PredictResponse(BaseModel):
    predictions: list[str]
    model_version: str
