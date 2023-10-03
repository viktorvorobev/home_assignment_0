from typing import List

import pydantic
import pydantic_settings


class WebsiteSetting(pydantic.BaseModel):
    url: pydantic.AnyUrl
    period: float = pydantic.Field(ge=5, le=300)
    regexp: str = ''


class DbWorkerSettings(pydantic.BaseModel):
    period: float = pydantic.Field(ge=0, le=300)
    max_batch_size: int


class MonitorSettings(pydantic.BaseModel):
    websites: List[WebsiteSetting]
    db: DbWorkerSettings


class DbConnectionSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(env_prefix='postgresql_')

    host: str
    port: str
    username: str
    password: str
    db: str
    ssl: bool = True

    @property
    def dsn(self) -> str:
        dsn = f'postgres://{self.username}:{self.password}@{self.host}:{self.port}/{self.db}'
        if self.ssl:
            dsn += '?sslmode=require'
        return dsn
