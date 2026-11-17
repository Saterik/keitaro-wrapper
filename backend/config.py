import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Keitaro API settings
    keitaro_api_url: str = "https://tlgk.host"
    keitaro_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///./keitaro_wrapper.db"
    
    # App settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    # Default campaign prefix
    campaign_prefix: str = "test_ivanov_"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()