from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "F1 Telemetry API"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql://f1user:f1pass@localhost:5433/f1telemetry"

    # Ruta local donde fastf1 guarda su caché HTTP.
    # Evita re-descargar datos ya obtenidos entre reinicios del servidor.
    FASTF1_CACHE_PATH: str = "/tmp/fastf1_cache"


settings = Settings()
