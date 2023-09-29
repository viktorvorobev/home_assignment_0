from typing import Optional, List

import pydantic


class WebsiteSetting(pydantic.BaseModel):
    url: pydantic.AnyUrl
    period: float = pydantic.Field(ge=5, le=300)
    regexp: Optional[str] = ''


class MonitorSettings(pydantic.BaseModel):
    websites: List[WebsiteSetting]
