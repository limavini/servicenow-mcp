"""
Instance selection tools for the ServiceNow MCP server.

These tools let a single running MCP server switch between multiple ServiceNow
instances at runtime. All instances live in ONE JSON file (default
`<repo>/instances.json`, override with the SERVICENOW_INSTANCES_FILE env var).
`list_instances` enumerates them (without exposing secrets) and `select_instance`
swaps the active connection for the session by mutating the shared config/auth
manager in place.

The file is a JSON object keyed by instance name, e.g.:

    {
        "dev185907": {
            "instance_url": "https://dev185907.service-now.com",
            "auth_type": "basic",
            "username": "admin",
            "password": "..."
        },
        "prod": {
            "instance_url": "https://acme.service-now.com",
            "auth_type": "oauth",
            "client_id": "...", "client_secret": "...",
            "username": "...", "password": "..."
        }
    }

A top-level "instances" wrapper and a list of objects (each with a "name") are also
accepted. For API key use `"auth_type": "api_key"` with api_key (and optional
api_key_header).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import (
    ApiKeyConfig,
    AuthConfig,
    AuthType,
    BasicAuthConfig,
    OAuthConfig,
    ServerConfig,
)

logger = logging.getLogger(__name__)


class ListInstancesParams(BaseModel):
    """Parameters for listing instances (no inputs required)."""

    random_string: Optional[str] = Field(
        None, description="Unused; present so the tool can be called without arguments"
    )


class GetCurrentInstanceParams(BaseModel):
    """Parameters for getting the current instance (no inputs required)."""

    random_string: Optional[str] = Field(
        None, description="Unused; present so the tool can be called without arguments"
    )


class SelectInstanceParams(BaseModel):
    """Parameters for selecting the active instance."""

    name: str = Field(
        ..., description="Name of the instance to activate (as returned by list_instances)"
    )


class InstanceSelectionResponse(BaseModel):
    """Response from selecting an instance."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    name: Optional[str] = Field(None, description="Name of the now-active instance")
    instance_url: Optional[str] = Field(None, description="URL of the now-active instance")


def _instances_file() -> Path:
    """Resolve the single JSON file holding all instance credentials."""
    env_file = os.getenv("SERVICENOW_INSTANCES_FILE")
    if env_file:
        return Path(env_file).expanduser()
    # Default: <repo_root>/instances.json (this file is src/servicenow_mcp/tools/instance_tools.py)
    return Path(__file__).resolve().parents[3] / "instances.json"


def _load_instances() -> Dict[str, Dict[str, Any]]:
    """Load all instances from the single JSON file, keyed by name."""
    path = _instances_file()
    instances: Dict[str, Dict[str, Any]] = {}
    if not path.is_file():
        return instances
    try:
        raw = json.loads(path.read_text())
    except Exception as e:
        logger.warning(f"Could not parse instances file {path}: {e}")
        return instances

    # Unwrap an optional top-level "instances" key.
    if isinstance(raw, dict) and "instances" in raw:
        raw = raw["instances"]

    if isinstance(raw, dict):
        for name, data in raw.items():
            if isinstance(data, dict):
                instances[name] = {**data, "name": data.get("name") or name}
    elif isinstance(raw, list):
        for data in raw:
            if isinstance(data, dict) and data.get("name"):
                instances[data["name"]] = data
    return instances


def _build_auth_config(data: Dict[str, Any]) -> Tuple[AuthConfig, str]:
    """Build an AuthConfig from an instance file. Returns (auth_config, instance_url)."""
    instance_url = data.get("instance_url")
    if not instance_url:
        raise ValueError("instance file is missing 'instance_url'")

    auth_type = AuthType((data.get("auth_type") or "basic").lower())

    if auth_type == AuthType.BASIC:
        username, password = data.get("username"), data.get("password")
        if not username or not password:
            raise ValueError("basic auth requires 'username' and 'password'")
        return AuthConfig(
            type=auth_type, basic=BasicAuthConfig(username=username, password=password)
        ), instance_url

    if auth_type == AuthType.OAUTH:
        required = ("client_id", "client_secret", "username", "password")
        if not all(data.get(k) for k in required):
            raise ValueError("oauth requires client_id, client_secret, username, password")
        return AuthConfig(
            type=auth_type,
            oauth=OAuthConfig(
                client_id=data["client_id"],
                client_secret=data["client_secret"],
                username=data["username"],
                password=data["password"],
                token_url=data.get("token_url"),
            ),
        ), instance_url

    if auth_type == AuthType.API_KEY:
        api_key = data.get("api_key")
        if not api_key:
            raise ValueError("api_key auth requires 'api_key'")
        return AuthConfig(
            type=auth_type,
            api_key=ApiKeyConfig(
                api_key=api_key,
                header_name=data.get("api_key_header", "X-ServiceNow-API-Key"),
            ),
        ), instance_url

    raise ValueError(f"unsupported auth_type: {auth_type}")


def list_instances(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListInstancesParams,
) -> Dict[str, Any]:
    """List the ServiceNow instances available to connect to.

    Secrets (passwords, client secrets, API keys) are never returned.
    """
    try:
        path = _instances_file()
        files = _load_instances()
        instances: List[Dict[str, Any]] = []
        for name, data in files.items():
            instances.append(
                {
                    "name": name,
                    "instance_url": data.get("instance_url"),
                    "auth_type": (data.get("auth_type") or "basic").lower(),
                    "username": data.get("username"),  # not secret; helps identify
                    "is_current": data.get("instance_url") == config.instance_url,
                }
            )
        message = (
            f"Found {len(instances)} instance(s) in {path}"
            if instances
            else f"No instances found in {path}. Create it from instances.example.json."
        )
        return {
            "success": True,
            "message": message,
            "instances": instances,
            "instances_file": str(path),
            "current_instance_url": config.instance_url,
        }
    except Exception as e:
        logger.error(f"Error listing instances: {e}")
        return {"success": False, "message": f"Error listing instances: {str(e)}", "instances": []}


def get_current_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCurrentInstanceParams,
) -> Dict[str, Any]:
    """Get the instance the server is currently connected to."""
    name = None
    for n, data in _load_instances().items():
        if data.get("instance_url") == config.instance_url:
            name = n
            break
    return {
        "success": True,
        "message": f"Currently connected to: {config.instance_url}",
        "name": name,
        "instance_url": config.instance_url,
        "auth_type": config.auth.type.value if config.auth else None,
    }


def select_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SelectInstanceParams,
) -> InstanceSelectionResponse:
    """Switch the active ServiceNow instance for this session.

    Mutates the shared config and auth manager in place so every subsequent tool
    call targets the selected instance.
    """
    try:
        files = _load_instances()
        if params.name not in files:
            available = ", ".join(files) or "(none)"
            return InstanceSelectionResponse(
                success=False,
                message=f"Instance '{params.name}' not found. Available: {available}",
            )

        auth_config, instance_url = _build_auth_config(files[params.name])

        # Mutate shared state in place — these objects are reused on every call.
        config.instance_url = instance_url
        config.auth = auth_config
        auth_manager.config = auth_config
        auth_manager.instance_url = instance_url
        auth_manager.token = None  # reset any cached OAuth token
        auth_manager.token_type = None

        return InstanceSelectionResponse(
            success=True,
            message=f"Active instance set to '{params.name}' ({instance_url})",
            name=params.name,
            instance_url=instance_url,
        )
    except Exception as e:
        logger.error(f"Error selecting instance: {e}")
        return InstanceSelectionResponse(
            success=False, message=f"Error selecting instance: {str(e)}"
        )
