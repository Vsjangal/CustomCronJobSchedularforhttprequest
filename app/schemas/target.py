from datetime import datetime

from pydantic import BaseModel, field_validator

ALLOWED_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class TargetCreate(BaseModel):
    """Schema for creating a new Target."""

    name: str
    url: str
    method: str = "GET"
    headers: dict | None = None
    body_template: dict | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        upper = value.upper()
        if upper not in ALLOWED_HTTP_METHODS:
            raise ValueError(f"Method must be one of {ALLOWED_HTTP_METHODS}")
        return upper


class TargetUpdate(BaseModel):
    """Schema for updating an existing Target. All fields optional."""

    name: str | None = None
    url: str | None = None
    method: str | None = None
    headers: dict | None = None
    body_template: dict | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str | None) -> str | None:
        if value is not None and value.upper() not in ALLOWED_HTTP_METHODS:
            raise ValueError(f"Method must be one of {ALLOWED_HTTP_METHODS}")
        return value.upper() if value else value


class TargetResponse(BaseModel):
    """Schema for Target API responses."""

    id: str
    name: str
    url: str
    method: str
    headers: dict | None = None
    body_template: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
