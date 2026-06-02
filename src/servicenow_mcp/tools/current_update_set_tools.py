"""
Current Update Set tools for the ServiceNow MCP server.

The "current update set" is not a property of the update set itself: it is stored
as a per-user preference (`sys_user_preference` with name `sys_update_set`). When
records are created/updated through the API, customization changes are captured
into whichever update set is current for the authenticated user. These tools read
and set that preference so changes land in the intended (non-global) update set.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_PREF_NAME = "sys_update_set"
_UPDATE_SET_FIELDS = "sys_id,name,state,application,is_default"


class GetCurrentUpdateSetParams(BaseModel):
    """Parameters for getting the current update set (no inputs required)."""

    random_string: Optional[str] = Field(
        None, description="Unused; present so the tool can be called without arguments"
    )


class SetCurrentUpdateSetParams(BaseModel):
    """Parameters for setting the current update set."""

    update_set_id: str = Field(
        ...,
        description="Update set sys_id (prefix with 'sys_id:') or exact name to make current",
    )


class CurrentUpdateSetResponse(BaseModel):
    """Response from current update set operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    update_set_id: Optional[str] = Field(None, description="sys_id of the current update set")
    update_set_name: Optional[str] = Field(None, description="Name of the current update set")
    scope: Optional[str] = Field(None, description="Application scope of the update set")
    is_global: Optional[bool] = Field(
        None, description="Whether the update set is in the Global scope"
    )


def _get_current_user_sys_id(config: ServerConfig, auth_manager: AuthManager) -> Optional[str]:
    """Resolve the sys_id of the authenticated user via gs.getUserID()."""
    url = f"{config.instance_url}/api/now/table/sys_user"
    query_params = {
        "sysparm_query": "sys_id=javascript:gs.getUserID()",
        "sysparm_limit": 1,
        "sysparm_fields": "sys_id,user_name",
    }
    response = requests.get(
        url, params=query_params, headers=auth_manager.get_headers(), timeout=30
    )
    response.raise_for_status()
    result = response.json().get("result", [])
    if not result:
        return None
    return result[0].get("sys_id")


def _get_update_set(
    config: ServerConfig, auth_manager: AuthManager, update_set_id: str
) -> Optional[Dict[str, Any]]:
    """Fetch an update set record by sys_id (sys_id: prefix) or exact name."""
    query_params = {
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": _UPDATE_SET_FIELDS,
    }
    if update_set_id.startswith("sys_id:"):
        sys_id = update_set_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_update_set/{sys_id}"
    else:
        url = f"{config.instance_url}/api/now/table/sys_update_set"
        query_params["sysparm_query"] = f"name={update_set_id}"

    response = requests.get(
        url, params=query_params, headers=auth_manager.get_headers(), timeout=30
    )
    response.raise_for_status()
    result = response.json().get("result")
    if isinstance(result, list):
        return result[0] if result else None
    return result


def _scope_info(update_set: Dict[str, Any]) -> Dict[str, Any]:
    """Extract scope/global info from an update set record (display values)."""
    application = update_set.get("application")
    if isinstance(application, dict):
        scope = application.get("display_value")
    else:
        scope = application
    is_global = (scope or "").strip().lower() in ("global", "")
    return {"scope": scope, "is_global": is_global}


def get_current_update_set(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCurrentUpdateSetParams,
) -> Dict[str, Any]:
    """Get the update set currently active for the authenticated user.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary describing the current update set (name, scope, global flag).
    """
    try:
        user_id = _get_current_user_sys_id(config, auth_manager)
        if not user_id:
            return {"success": False, "message": "Could not resolve the authenticated user"}

        # Per-user preference first; fall back to the system-wide default.
        pref_url = f"{config.instance_url}/api/now/table/sys_user_preference"
        pref_params = {
            "sysparm_query": f"name={_PREF_NAME}^user={user_id}",
            "sysparm_fields": "sys_id,value",
            "sysparm_limit": 1,
        }
        resp = requests.get(
            pref_url, params=pref_params, headers=auth_manager.get_headers(), timeout=30
        )
        resp.raise_for_status()
        prefs = resp.json().get("result", [])

        if not prefs:
            # System default preference (user empty).
            pref_params["sysparm_query"] = f"name={_PREF_NAME}^userISEMPTY"
            resp = requests.get(
                pref_url, params=pref_params, headers=auth_manager.get_headers(), timeout=30
            )
            resp.raise_for_status()
            prefs = resp.json().get("result", [])

        if not prefs or not prefs[0].get("value"):
            return {
                "success": True,
                "message": "No current update set preference found; the instance default applies",
                "update_set_id": None,
                "update_set_name": None,
            }

        update_set = _get_update_set(config, auth_manager, f"sys_id:{prefs[0]['value']}")
        if not update_set:
            return {
                "success": True,
                "message": "Current update set preference points to a missing update set",
                "update_set_id": prefs[0]["value"],
            }

        info = _scope_info(update_set)
        return {
            "success": True,
            "message": f"Current update set: {update_set.get('name')}",
            "update_set_id": update_set.get("sys_id"),
            "update_set_name": update_set.get("name"),
            "state": update_set.get("state"),
            "scope": info["scope"],
            "is_global": info["is_global"],
            "is_default": update_set.get("is_default") == "true",
        }

    except Exception as e:
        logger.error(f"Error getting current update set: {e}")
        return {"success": False, "message": f"Error getting current update set: {str(e)}"}


def set_current_update_set(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SetCurrentUpdateSetParams,
) -> CurrentUpdateSetResponse:
    """Set the current update set for the authenticated user.

    Writes the `sys_update_set` user preference so that subsequent customization
    changes are captured into the given update set.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result, including the update set scope.
    """
    try:
        update_set = _get_update_set(config, auth_manager, params.update_set_id)
        if not update_set:
            return CurrentUpdateSetResponse(
                success=False,
                message=f"Update set not found: {params.update_set_id}",
            )

        sys_id = update_set.get("sys_id")
        name = update_set.get("name")
        info = _scope_info(update_set)

        user_id = _get_current_user_sys_id(config, auth_manager)
        if not user_id:
            return CurrentUpdateSetResponse(
                success=False, message="Could not resolve the authenticated user"
            )

        headers = auth_manager.get_headers()
        pref_url = f"{config.instance_url}/api/now/table/sys_user_preference"

        # Look for an existing per-user preference to update; otherwise create one.
        lookup = requests.get(
            pref_url,
            params={
                "sysparm_query": f"name={_PREF_NAME}^user={user_id}",
                "sysparm_fields": "sys_id",
                "sysparm_limit": 1,
            },
            headers=headers,
            timeout=30,
        )
        lookup.raise_for_status()
        existing = lookup.json().get("result", [])

        if existing:
            pref_sys_id = existing[0]["sys_id"]
            upd = requests.patch(
                f"{pref_url}/{pref_sys_id}",
                json={"value": sys_id},
                headers=headers,
                timeout=30,
            )
            upd.raise_for_status()
        else:
            body = {
                "name": _PREF_NAME,
                "value": sys_id,
                "user": user_id,
                "type": "string",
            }
            crt = requests.post(pref_url, json=body, headers=headers, timeout=30)
            crt.raise_for_status()

        message = f"Current update set set to: {name}"
        if info["is_global"]:
            message += " (WARNING: this update set is in the Global scope)"

        return CurrentUpdateSetResponse(
            success=True,
            message=message,
            update_set_id=sys_id,
            update_set_name=name,
            scope=info["scope"],
            is_global=info["is_global"],
        )

    except Exception as e:
        logger.error(f"Error setting current update set: {e}")
        return CurrentUpdateSetResponse(
            success=False,
            message=f"Error setting current update set: {str(e)}",
        )
