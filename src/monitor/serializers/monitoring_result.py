from typing import Optional

import pydantic


class MonitoringResult(pydantic.BaseModel):
    timestamp: str
    status_code: int
    response_time: float
    regexp_match: Optional[bool]
