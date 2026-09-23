import os
from dataclasses import dataclass

from dotenv import load_dotenv
import truststore


load_dotenv()
truststore.inject_into_ssl()


@dataclass
class Settings:
    app_name: str = "CWA Temperature Broadcast"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))
    cwa_api_key: str = os.getenv("CWA_API_KEY", "")
    cwa_data_url: str = os.getenv(
        "CWA_DATA_URL",
        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001",
    )
    windy_api_key: str = os.getenv("WINDY_API_KEY", os.getenv("NEXT_PUBLIC_WINDY_API_KEY", ""))
    allow_origins: list[str] = None

    def __post_init__(self):
        if self.allow_origins is None:
            self.allow_origins = ["*"]


settings = Settings()
