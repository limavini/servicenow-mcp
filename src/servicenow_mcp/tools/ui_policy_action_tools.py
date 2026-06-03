"""
UiPolicyAction tools for the ServiceNow MCP server.

This module provides CRUD tools for UI policy actions (sys_ui_policy_action) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,ui_policy,field,mandatory,visible,disabled,read_only,order,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListUiPolicyActionsParams(BaseModel):
    """Parameters for listing UI policy actions."""

    limit: int = Field(10, description="Maximum number of UI policy actions to return")
    offset: int = Field(0, description="Offset for pagination")
    ui_policy: Optional[str] = Field(None, description="Filter by Parent UI policy sys_id")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetUiPolicyActionParams(BaseModel):
    """Parameters for getting a UI policy action."""

    ui_policy_action_id: str = Field(..., description="UiPolicyAction sys_id (prefix with 'sys_id:')")


class CreateUiPolicyActionParams(BaseModel):
    """Parameters for creating a UI policy action."""

    ui_policy: str = Field(..., description="Parent UI policy sys_id")
    field: str = Field(..., description="Field the action targets")
    mandatory: Optional[str] = Field(None, description="Mandatory: true, false, ignore")
    visible: Optional[str] = Field(None, description="Visible: true, false, ignore")
    disabled: Optional[str] = Field(None, description="Disabled: true, false, ignore")
    read_only: Optional[str] = Field(None, description="Read only: true, false, ignore")
    order: Optional[int] = Field(None, description="Order")


class UpdateUiPolicyActionParams(BaseModel):
    """Parameters for updating a UI policy action."""

    ui_policy_action_id: str = Field(..., description="UiPolicyAction sys_id (prefix with 'sys_id:')")
    ui_policy: Optional[str] = Field(None, description="Parent UI policy sys_id")
    field: Optional[str] = Field(None, description="Field the action targets")
    mandatory: Optional[str] = Field(None, description="Mandatory: true, false, ignore")
    visible: Optional[str] = Field(None, description="Visible: true, false, ignore")
    disabled: Optional[str] = Field(None, description="Disabled: true, false, ignore")
    read_only: Optional[str] = Field(None, description="Read only: true, false, ignore")
    order: Optional[int] = Field(None, description="Order")


class DeleteUiPolicyActionParams(BaseModel):
    """Parameters for deleting a UI policy action."""

    ui_policy_action_id: str = Field(..., description="UiPolicyAction sys_id (prefix with 'sys_id:')")


class UiPolicyActionResponse(BaseModel):
    """Response from UI policy action operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    ui_policy_action_id: Optional[str] = Field(None, description="sys_id of the affected UI policy action")
    ui_policy_action_name: Optional[str] = Field(None, description="Name of the affected UI policy action")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_ui_policy_action record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "ui_policy": _display(item.get("ui_policy")),
        "field": _display(item.get("field")),
        "mandatory": _display(item.get("mandatory")),
        "visible": _display(item.get("visible")),
        "disabled": _display(item.get("disabled")),
        "read_only": _display(item.get("read_only")),
        "order": _display(item.get("order")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_ui_policy_actions(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiPolicyActionsParams,
) -> Dict[str, Any]:
    """List UI policy actions from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_ui_policy_action"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.ui_policy:
            query_parts.append(f"ui_policy={params.ui_policy}")
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
            "message": f"Found {len(items)} UI policy actions",
            "ui_policy_actions": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI policy actions: {e}")
        return {
            "success": False,
            "message": f"Error listing UI policy actions: {str(e)}",
            "ui_policy_actions": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUiPolicyActionParams,
) -> Dict[str, Any]:
    """Get a specific UI policy action from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.ui_policy_action_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_ui_policy_action/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"UiPolicyAction not found: {params.ui_policy_action_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"UiPolicyAction not found: {params.ui_policy_action_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found UI policy action: {item.get('name')}",
            "ui_policy_action": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting UI policy action: {e}")
        return {"success": False, "message": f"Error getting UI policy action: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "ui_policy", None)
    if value is not None:
        body["ui_policy"] = value
    value = getattr(params, "field", None)
    if value is not None:
        body["field"] = value
    value = getattr(params, "mandatory", None)
    if value is not None:
        body["mandatory"] = value
    value = getattr(params, "visible", None)
    if value is not None:
        body["visible"] = value
    value = getattr(params, "disabled", None)
    if value is not None:
        body["disabled"] = value
    value = getattr(params, "read_only", None)
    if value is not None:
        body["read_only"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    return body


def create_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiPolicyActionParams,
) -> UiPolicyActionResponse:
    """Create a new UI policy action in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_ui_policy_action"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiPolicyActionResponse(success=False, message="Failed to create UI policy action")
        result = data["result"]
        return UiPolicyActionResponse(
            success=True,
            message=f"Created UI policy action: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            ui_policy_action_id=result.get("sys_id"),
            ui_policy_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating UI policy action: {e}")
        return UiPolicyActionResponse(success=False, message=f"Error creating UI policy action: {str(e)}")


def update_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiPolicyActionParams,
) -> UiPolicyActionResponse:
    """Update an existing UI policy action in ServiceNow."""
    get_result = get_ui_policy_action(config, auth_manager, GetUiPolicyActionParams(ui_policy_action_id=params.ui_policy_action_id))
    if not get_result["success"]:
        return UiPolicyActionResponse(success=False, message=get_result["message"])
    record = get_result["ui_policy_action"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_ui_policy_action/{sys_id}"
    body = _build_body(params)
    if not body:
        return UiPolicyActionResponse(
            success=True,
            message=f"No changes to update for UI policy action",
            ui_policy_action_id=sys_id,
            ui_policy_action_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiPolicyActionResponse(success=False, message=f"Failed to update UI policy action")
        result = data["result"]
        return UiPolicyActionResponse(
            success=True,
            message=f"Updated UI policy action",
            ui_policy_action_id=result.get("sys_id"),
            ui_policy_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating UI policy action: {e}")
        return UiPolicyActionResponse(success=False, message=f"Error updating UI policy action: {str(e)}")


def delete_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiPolicyActionParams,
) -> UiPolicyActionResponse:
    """Delete a UI policy action from ServiceNow."""
    get_result = get_ui_policy_action(config, auth_manager, GetUiPolicyActionParams(ui_policy_action_id=params.ui_policy_action_id))
    if not get_result["success"]:
        return UiPolicyActionResponse(success=False, message=get_result["message"])
    record = get_result["ui_policy_action"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_ui_policy_action/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return UiPolicyActionResponse(success=True, message=f"Deleted UI policy action", ui_policy_action_id=sys_id, ui_policy_action_name=name)
    except Exception as e:
        logger.error(f"Error deleting UI policy action: {e}")
        return UiPolicyActionResponse(success=False, message=f"Error deleting UI policy action: {str(e)}")
