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

	@field_validator("clerk_authorized_parties", mode="before")
	@classmethod
	def _split_authorized_parties(cls, value: str | list[str]) -> list[str]:
		if isinstance(value, str):
			return [party.strip() for party in value.split(",") if party.strip()]
		return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings() # type: ignore[call-arg]
