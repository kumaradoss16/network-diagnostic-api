"""Checks and organizes data sent by users before the network diagnostic API processes it."""
from typing import Any, Self

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from ..utils.validators import is_valid_target

_TARGET_DESCRIPTION = "Hostname or IP address to check (e.g. 'example.com' or '93.184.216.34')."

# Model describes the input for a ping endpoint.
class PingRequest(BaseModel):
    host: str = Field(..., description=_TARGET_DESCRIPTION, examples=["example.com"])
    count: int = Field(default=4, ge=1, le=10, description="Number of ping packets to send.")
    timeout: float = Field(default=2.0, gt=0, le=10, description="Timeout per packet, in seconds.")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        value = value.strip()
        if not is_valid_target(value):
            raise ValueError("host must be valid hostname or IP address")
        return value


# Model describes input for a DNS lookup endpoint
class DNSRequest(BaseModel):
    hostname: str = Field(..., description="Hostname to resolve.", examples=["example.com"])

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value:str) -> str:
        value = value.strip()
        if not is_valid_target(value):
            raise ValueError("hostname must be a valid DNS hostname or IP address")
        return value

#  Model represents a TCP port-check request
class PortCheckRequest(BaseModel):
    host: str = Field(..., description=_TARGET_DESCRIPTION, examples=["example.com"])
    port: int = Field(..., ge=1, le=65535, description="TCP port number to check.")
    timeout: float = Field(default=3.0, gt=0, le=10, description="Connection timeout, in seconds.")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        value = value.strip()
        if not is_valid_target(value):
            raise ValueError("host must be a valid hostname or IP address")
        return value

#  Model represents an HTTP or HTTPS check
class HTTPCheckRequest(BaseModel):
    url: AnyHttpUrl = Field(..., description="Full URL to check, including scheme.", examples=["https://example.com"])
    timeout: float = Field(default=5.0, gt=0, le=30, description="Request timeout, in seconds.")
    follow_redirects: bool = Field(default=True, description="Whether to follow HTTP redirects.")

#  Model represents a latency-measurement request
class LatencyRequest(BaseModel):
    host: str = Field(..., description=_TARGET_DESCRIPTION, examples=["example.com"])
    count: int = Field(default=5, ge=2, le=20, description="Number of latency samples to take.")
    timeout: float = Field(default=2.0, gt=0, le=10, description="Timeout per sample, in seconds.")

    @field_validator("host")
    @classmethod
    def validate(cls, value: str) -> str:
        value = value.strip()
        if not is_valid_target(value):
            raise ValueError("host must be a valid hostname or Ip address")
        return value

#  Model represents a combined diagnostic request
class DiagnosticRunRequest(BaseModel):
    host: str = Field(..., description=_TARGET_DESCRIPTION, examples=["examples.com"])
    port: int | None = Field(default=None, ge=1, le=65535, description="optional TCP port to also check.")
    url: AnyHttpUrl | None = Field(default=None, description="Optional URL to also check over HTTP(s).")
    ping_count: int = Field(default=4, ge=1, le=10, description="Number of ping packets to send.")
    timeout: float = Field(default=3.0, gt=0, le=10, description="Timeout used for each individual check, in seconds.")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        value = value.strip()
        if not is_valid_target(value):
            raise ValueError("host must be valid hostname or IP address")
        return value
