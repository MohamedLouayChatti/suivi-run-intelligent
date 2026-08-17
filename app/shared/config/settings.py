from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
	"""Application settings loaded from environment and the project .env file."""

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
		case_sensitive=False,
	)

	database_url: str = Field(..., validation_alias="DATABASE_URL")
	clerk_secret_key: str | None = Field(default=None, validation_alias="CLERK_SECRET_KEY")
	clerk_publishable_key: str | None = Field(
		default=None,
		validation_alias="CLERK_PUBLISHABLE_KEY",
	)
	clerk_jwt_key: str | None = Field(default=None, validation_alias="CLERK_JWT_KEY")
	clerk_issuer: str | None = Field(default=None, validation_alias="CLERK_ISSUER")
	clerk_audience: str | None = Field(default=None, validation_alias="CLERK_AUDIENCE")
	clerk_authorized_parties: Annotated[list[str], NoDecode] = Field(
		default_factory=list,
		validation_alias="CLERK_AUTHORIZED_PARTIES",
	)
	clerk_webhook_signing_secret: str | None = Field(
		default=None,
		validation_alias="CLERK_WEBHOOK_SIGNING_SECRET",
	)
	clerk_swagger_jwt_template: str = Field(
		default="swagger",
		validation_alias="CLERK_SWAGGER_JWT_TEMPLATE",
	)
	cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
		default_factory=list,
		validation_alias="CORS_ALLOWED_ORIGINS",
	)
	storage_root: str = Field(default="storage", validation_alias="STORAGE_ROOT")
	# Host and credential only -- never which model to use. Which embedding model this codebase
	# runs is pinned in code (knowledge_base/infrastructure/embedding_model.py) because it is
	# paired with a calibrated similarity threshold and a fixed vector column dimension; making it
	# an env var would let those three drift apart silently. The host is the one axis that
	# legitimately changes between machines (laptop, GPU box, Ollama Cloud), so it lives here.
	ollama_host: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")
	ollama_api_key: str | None = Field(default=None, validation_alias="OLLAMA_API_KEY")

	@field_validator("clerk_authorized_parties", "cors_allowed_origins", mode="before")
	@classmethod
	def _split_comma_separated(cls, value: str | list[str]) -> list[str]:
		if isinstance(value, str):
			return [item.strip() for item in value.split(",") if item.strip()]
		return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings() # type: ignore[call-arg]
