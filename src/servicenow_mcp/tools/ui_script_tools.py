"""
UiScript tools for the ServiceNow MCP server.

This module provides CRUD tools for UI scripts (sys_ui_script) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,script,description,active,ui_type,use_scoped_format,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListUiScriptsParams(BaseModel):
    """Parameters for listing UI scripts."""

    limit: int = Field(10, description="Maximum number of UI scripts to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by UI script name")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetUiScriptParams(BaseModel):
    """Parameters for getting a UI script."""

    ui_script_id: str = Field(..., description="UiScript sys_id (prefix with 'sys_id:'), or the exact name")


class CreateUiScriptParams(BaseModel):
    """Parameters for creating a UI script."""

    name: str = Field(..., description="UI script name")
    script: Optional[str] = Field(None, description="Script content")
    description: Optional[str] = Field(None, description="Description")
    active: bool = Field(True, description="Whether active")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    use_scoped_format: Optional[bool] = Field(None, description="Use scoped format")


class UpdateUiScriptParams(BaseModel):
    """Parameters for updating a UI script."""

    ui_script_id: str = Field(..., description="UiScript sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="UI script name")
    script: Optional[str] = Field(None, description="Script content")
    description: Optional[str] = Field(None, description="Description")
    active: Optional[bool] = Field(None, description="Whether active")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    use_scoped_format: Optional[bool] = Field(None, description="Use scoped format")


class DeleteUiScriptParams(BaseModel):
    """Parameters for deleting a UI script."""

    ui_script_id: str = Field(..., description="UiScript sys_id (prefix with 'sys_id:'), or the exact name")


class UiScriptResponse(BaseModel):
    """Response from UI script operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    ui_script_id: Optional[str] = Field(None, description="sys_id of the affected UI script")
    ui_script_name: Optional[str] = Field(None, description="Name of the affected UI script")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_ui_script record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "script": _display(item.get("script")),
        "description": _display(item.get("description")),
        "active": item.get("active") == "true",
        "ui_type": _display(item.get("ui_type")),
        "use_scoped_format": item.get("use_scoped_format") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_ui_scripts(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiScriptsParams,
) -> Dict[str, Any]:
    """List UI scripts from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_ui_script"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.name:
            query_parts.append(f"name={params.name}")
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
        if params.query:
            query_parts.append(f"nameLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} UI scripts",
            "ui_scripts": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI scripts: {e}")
        return {
            "success": False,
            "message": f"Error listing UI scripts: {str(e)}",
            "ui_scripts": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ui_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUiScriptParams,
) -> Dict[str, Any]:
    """Get a specific UI script from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.ui_script_id.startswith("sys_id:"):
            sys_id = params.ui_script_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_ui_script/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_ui_script"
            query_params["sysparm_query"] = f"name={params.ui_script_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"UiScript not found: {params.ui_script_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"UiScript not found: {params.ui_script_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found UI script: {item.get('name')}",
            "ui_script": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting UI script: {e}")
        return {"success": False, "message": f"Error getting UI script: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "ui_type", None)
    if value is not None:
        body["ui_type"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "use_scoped_format", None)
    if value is not None:
        body["use_scoped_format"] = str(value).lower()
    return body


def create_ui_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiScriptParams,
) -> UiScriptResponse:
    """Create a new UI script in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_ui_script"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiScriptResponse(success=False, message="Failed to create UI script")
        result = data["result"]
        return UiScriptResponse(
            success=True,
            message=f"Created UI script: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            ui_script_id=result.get("sys_id"),
            ui_script_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating UI script: {e}")
        return UiScriptResponse(success=False, message=f"Error creating UI script: {str(e)}")


def update_ui_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiScriptParams,
) -> UiScriptResponse:
    """Update an existing UI script in ServiceNow."""
    get_result = get_ui_script(config, auth_manager, GetUiScriptParams(ui_script_id=params.ui_script_id))
    if not get_result["success"]:
        return UiScriptResponse(success=False, message=get_result["message"])
    record = get_result["ui_script"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_ui_script/{sys_id}"
    body = _build_body(params)
    if not body:
        return UiScriptResponse(
            success=True,
            message=f"No changes to update for UI script",
            ui_script_id=sys_id,
            ui_script_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiScriptResponse(success=False, message=f"Failed to update UI script")
        result = data["result"]
        return UiScriptResponse(
            success=True,
            message=f"Updated UI script",
            ui_script_id=result.get("sys_id"),
            ui_script_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating UI script: {e}")
        return UiScriptResponse(success=False, message=f"Error updating UI script: {str(e)}")


def delete_ui_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiScriptParams,
) -> UiScriptResponse:
    """Delete a UI script from ServiceNow."""
    get_result = get_ui_script(config, auth_manager, GetUiScriptParams(ui_script_id=params.ui_script_id))
    if not get_result["success"]:
        return UiScriptResponse(success=False, message=get_result["message"])
    record = get_result["ui_script"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_ui_script/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return UiScriptResponse(success=True, message=f"Deleted UI script", ui_script_id=sys_id, ui_script_name=name)
    except Exception as e:
        logger.error(f"Error deleting UI script: {e}")
        return UiScriptResponse(success=False, message=f"Error deleting UI script: {str(e)}")
