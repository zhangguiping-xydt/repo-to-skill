from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class WorkloadRequest(BaseModel):
    employee_info: str
    bill_type: int
    is_container_holiday: bool = False


class WorkloadResponse(BaseModel):
    days: float
    hours: float


@app.post("/workload", response_model=WorkloadResponse)
def compute_workload(payload: WorkloadRequest):
    return WorkloadResponse(days=1.0, hours=8.0)
