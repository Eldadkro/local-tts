from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
