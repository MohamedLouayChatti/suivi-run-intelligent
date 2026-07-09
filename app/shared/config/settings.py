from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Application settings loaded from environment and the project .env file."""

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
		case_sensitive=False,
	)

	database_url: str = Field(..., validation_alias="DATABASE_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings() # Pylance false positive error to ignore.
