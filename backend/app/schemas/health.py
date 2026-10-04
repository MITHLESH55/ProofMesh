from typing import Dict
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "proofmesh-api"
    version: str = "0.1.0"


class ReadyResponse(BaseModel):
    status: str
    dependencies: Dict[str, str]
