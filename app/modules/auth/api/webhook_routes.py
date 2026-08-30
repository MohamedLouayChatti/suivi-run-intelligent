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

_APPLICATION_METADATA_KEY = "application"
_FUNCTIONAL_TEAM_METADATA_KEY = "functionalTeam"


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


def _text(value: Any) -> str | None:
	return value if isinstance(value, str) and value else None


def _names(data: dict[str, Any]) -> tuple[str, str]:
	"""The applicant's given name and surname, as the two fields Clerk holds them in.

	Handed on unjoined.  This used to return one string built as `f"{first} {last}"`, which the
	settings form then split apart again on the first space -- and a join and a split on a
	single space are not inverses once either half runs to two words.  All this knows now is
	where in a Clerk payload the two fields live, which is the same division `_signup_declaration`
	makes: how a full name is written from them is the domain's rule, not the transport's.

	The fallback stays here because it is entirely about Clerk's payload: an account can exist
	with neither field set, and something has to name that person.  It is written into the
	surname because that is the half a lone token reads as under this organization's ordering.
	"""
	first = _text(data.get("first_name")) or ""
	last = _text(data.get("last_name")) or ""
	if first or last:
		return first, last
	return "", _text(data.get("username")) or _provider_user_id(data)


def _image_url(data: dict[str, Any]) -> str | None:
	return _text(data.get("image_url"))


def _signup_declaration(data: dict[str, Any]) -> tuple[str | None, str | None]:
	"""The application and team the applicant chose on the signup form, as they arrived.

	The form writes both into `unsafeMetadata` -- the one bag a client that is still signing
	up may write to -- and Clerk echoes it back here verbatim under `unsafe_metadata`.  All
	this knows is where in a Clerk payload to find them and what they are called there; both
	come back out as the raw strings they went in as.  What they mean, what a missing one
	implies and which pairs the domain allows are the application layer's to decide, so that
	the answers do not change with the transport that happened to carry the declaration.
	"""
	metadata = data.get("unsafe_metadata")
	if not isinstance(metadata, dict):
		return None, None
	return _text(metadata.get(_APPLICATION_METADATA_KEY)), _text(metadata.get(_FUNCTIONAL_TEAM_METADATA_KEY))


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
	first_name, last_name = _names(data)
	if event_type == "user.created":
		declared_application, declared_functional_team = _signup_declaration(data)
		result = await create_handler.handle(CreateUserCommand(user_id=uuid4(), auth_provider_user_id=AuthProviderUserId(provider_id), email=_email(data), first_name=first_name, last_name=last_name, avatar_url=_image_url(data), declared_application=declared_application, declared_functional_team=declared_functional_team))
	elif event_type == "user.updated":
		# Profile fields only: the signup metadata is read once, at creation, and never again.
		# `unsafeMetadata` stays writable by the signed-in user, so re-applying it here would
		# let anyone move themselves onto another application -- which is what scopes every
		# ticket and analytics collection they can read -- and would let a stale declaration
		# overwrite an administrator's later correction.
		if local_user_id is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local user was not found.")
		result = await update_handler.handle(UpdateUserCommand(user_id=local_user_id, email=_email(data), first_name=first_name, last_name=last_name, avatar_url=_image_url(data)))
	else:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported webhook event.")
	return UserResponse.from_dto(result)
