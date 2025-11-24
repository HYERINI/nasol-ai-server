from pydantic import BaseModel
from datetime import datetime

class AccountResponse(BaseModel):
    session_id: str
    oauth_id: str
    oauth_type: str
    nickname: str
    name:str
    profile_image: str
    email: str
    phone_number: str
    active_status: str
    role_id: str
    automatic_analysis_cycle: int
    target_period: int
    target_amount: int
    updated_at: datetime
    created_at: datetime