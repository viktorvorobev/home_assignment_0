from typing import Optional
from datetime import datetime
import pydantic


class MonitoringResult(pydantic.BaseModel):
    timestamp: datetime
    status_code: int
    response_time: float
    regexp_match: Optional[bool]
