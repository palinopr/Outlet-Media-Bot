"""
Simple configuration settings
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Discord
    discord_bot_token: str = Field(..., env="DISCORD_BOT_TOKEN")
    
    # Meta Ads
    meta_access_token: str = Field(..., env="META_ACCESS_TOKEN")
    meta_ad_account_id: str = Field(..., env="META_AD_ACCOUNT_ID")
    meta_api_version: str = Field(default="v21.0", env="META_API_VERSION")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # App settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings