from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.api.dependencies import (
	get_create_user_handler,
	get_update_user_handler,
	get_user_read_repository,
	get_verified_webhook_payload,
)
from app.modules.auth.api.schemas.user import UserResponse
from app.modules.auth.application.commands.create_user.command import CreateUserCommand
from app.modules.auth.application.commands.update_user.command import UpdateUserCommand
from app.modules.auth.application.commands.create_user.handler import CreateUserHandler
from app.modules.auth.application.commands.update_user.handler import UpdateUserHandler
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository

router = APIRouter(prefix="/auth/webhooks", tags=["auth-webhooks"])


def _data(payload: dict[str, Any]) -> dict[str, Any]:
	value = payload.get("data")
	if not isinstance(value, dict):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook data is invalid.")
	return value


def _provider_user_id(data: dict[str, Any]) -> str:
	value = data.get("id")
	if not isinstance(value, str) or not value:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook user ID is missing.")
	return value


def _email(data: dict[str, Any]) -> str:
	addresses = data.get("email_addresses")
	primary_id = data.get("primary_email_address_id")
	if isinstance(addresses, list):
		for address in addresses:
			if isinstance(address, dict) and address.get("id") == primary_id and isinstance(address.get("email_address"), str):
				return address["email_address"]
		for address in addresses:
			if isinstance(address, dict) and isinstance(address.get("email_address"), str):
				return address["email_address"]
	value = data.get("email")
	if isinstance(value, str) and value:
		return value
	return ""


def _display_name(data: dict[str, Any]) -> str:
	first = data.get("first_name") or ""
	last = data.get("last_name") or ""
	name = f"{first} {last}".strip()
	return name or data.get("username") or _provider_user_id(data)


def _image_url(data: dict[str, Any]) -> str | None:
	value = data.get("image_url")
	return value if isinstance(value, str) and value else None


async def _local_user_id(
	payload: Annotated[dict[str, Any], Depends(get_verified_webhook_payload)],
	repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
) -> UUID | None:
	user = await repository.get_user_by_auth_provider_user_id(_provider_user_id(_data(payload)))
	return None if user is None else user.id


@router.post("", response_model=UserResponse)
async def receive_webhook(
	payload: Annotated[dict[str, Any], Depends(get_verified_webhook_payload)],
	create_handler: Annotated[CreateUserHandler, Depends(get_create_user_handler)],
	update_handler: Annotated[UpdateUserHandler, Depends(get_update_user_handler)],
	local_user_id: Annotated[UUID, Depends(_local_user_id)],
) -> UserResponse:
	event_type = payload.get("type")
	data = _data(payload)
	provider_id = _provider_user_id(data)
	if event_type == "user.created":
		result = await create_handler.handle(CreateUserCommand(user_id=uuid4(), auth_provider_user_id=AuthProviderUserId(provider_id), email=_email(data), display_name=_display_name(data), avatar_url=_image_url(data)))
	elif event_type == "user.updated":
		if local_user_id is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local user was not found.")
		result = await update_handler.handle(UpdateUserCommand(user_id=local_user_id, email=_email(data), display_name=_display_name(data), avatar_url=_image_url(data)))
	else:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported webhook event.")
	return UserResponse.from_dto(result)
