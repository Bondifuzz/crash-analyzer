from pydantic import BaseModel, root_validator
from pydantic import Field, AnyHttpUrl, AnyUrl
from pydantic import BaseSettings as _BaseSettings
from typing import Dict, Any, Optional
from contextlib import suppress
from functools import lru_cache

# fmt: off
with suppress(ModuleNotFoundError):
    import dotenv; dotenv.load_dotenv()
# fmt: on


class BaseSettings(_BaseSettings):
    @root_validator
    def check_empty_strings(cls, data: Dict[str, Any]):
        for name, value in data.items():
            if isinstance(value, str):
                if len(value) == 0:
                    var = f"{cls.__name__}.{name}"
                    raise ValueError(f"Variable '{var}': empty string not allowed")

        return data


class EnvironmentSettings(BaseSettings):
    name: str = Field(env="ENVIRONMENT", regex=r"^(dev|prod|test)$")
    shutdown_timeout: int = Field(env="SHUTDOWN_TIMEOUT")
    service_name: Optional[str] = Field(env="SERVICE_NAME")
    service_version: Optional[str] = Field(env="SERVICE_VERSION")
    commit_id: Optional[str] = Field(env="COMMIT_ID")
    build_date: Optional[str] = Field(env="BUILD_DATE")
    commit_date: Optional[str] = Field(env="COMMIT_DATE")
    git_branch: Optional[str] = Field(env="GIT_BRANCH")

    @root_validator(skip_on_failure=True)
    def check_values_for_production(cls, data: Dict[str, Any]):

        if data["name"] != "prod":
            return data

        vars = []
        for name, value in data.items():
            if value is None:
                vars.append(name.upper())

        if vars:
            raise ValueError(f"Variables must be set in production mode: {vars}")

        return data


class DatabaseSettings(BaseSettings):

    engine: str = Field(regex=r"^arangodb$")
    url: AnyHttpUrl
    username: str
    password: str
    name: str

    class Config:
        env_prefix = "DB_"


class CollectionSettings(BaseSettings):
    crashes: str = "Crashes"
    unsent_messages: str = "UnsentMessages"


class MessageQueues(BaseSettings):
    crash_analyzer: str
    api_gateway: str
    dlq: str

    class Config:
        env_prefix = "MQ_QUEUE_"


class MessageQueueSettings(BaseSettings):

    queues: MessageQueues
    broker: str = Field(regex="^sqs$")
    url: AnyUrl
    region: str
    username: str
    password: str

    class Config:
        env_prefix = "MQ_"


class ServerSettings(BaseSettings):

    host: str
    port: str

    class Config:
        env_prefix = "SERVER_"


class CrashAnalyzerSettings(BaseSettings):

    preview_max_size: int

    class Config:
        env_prefix = "CRASH_ANALYZER_"


class S3Buckets(BaseSettings):
    fuzzers: str
    data: str

    class Config:
        env_prefix = "S3_BUCKET_"


class ObjectStorageSettings(BaseSettings):

    url: AnyHttpUrl
    buckets: S3Buckets
    access_key: str
    secret_key: str

    class Config:
        env_prefix = "S3_"


class AppSettings(BaseModel):
    environment: EnvironmentSettings
    object_storage: ObjectStorageSettings
    message_queue: MessageQueueSettings
    collections: CollectionSettings
    database: DatabaseSettings
    server: ServerSettings
    crash_analyzer: CrashAnalyzerSettings


_app_settings = None


def get_app_settings() -> AppSettings:

    global _app_settings

    if _app_settings is None:
        _app_settings = AppSettings(
        database=DatabaseSettings(),
        collections=CollectionSettings(),
        object_storage=ObjectStorageSettings(buckets=S3Buckets()),
        message_queue=MessageQueueSettings(queues=MessageQueues()),
        environment=EnvironmentSettings(),
        server=ServerSettings(),
        crash_analyzer=CrashAnalyzerSettings(),
    )

    return _app_settings
