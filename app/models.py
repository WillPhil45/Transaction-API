from pydantic import BaseModel, Field

class SummaryResponse(BaseModel):
    user_id: int
    transaction_count: int
    max_amount: float = Field(..., description="Maximum transaction amount")
    min_amount: float = Field(..., description="Minimum transaction amount")
    mean_amount: float = Field(..., description="Mean transaction amount")
    start_date: str
    end_date: str

class UploadResponse(BaseModel):
    success: bool
    message: str
    rows_processed: int
    processing_time_seconds: float

class ClearResponse(BaseModel):
    success: bool
    message: str