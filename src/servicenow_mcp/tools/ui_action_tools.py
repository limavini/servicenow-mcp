"""
UiAction tools for the ServiceNow MCP server.

This module provides CRUD tools for UI actions (sys_ui_action) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,table,action_name,script,condition,order,active,client,onclick,form_button,form_link,list_button,show_insert,show_update,hint,comments,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListUiActionsParams(BaseModel):
    """Parameters for listing UI actions."""

    limit: int = Field(10, description="Maximum number of UI actions to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Name (button/label)")
    table: Optional[str] = Field(None, description="Filter by Table the action applies to")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetUiActionParams(BaseModel):
    """Parameters for getting a UI action."""

    ui_action_id: str = Field(..., description="UiAction sys_id (prefix with 'sys_id:'), or the exact name")


class CreateUiActionParams(BaseModel):
    """Parameters for creating a UI action."""

    name: str = Field(..., description="Name (button/label)")
    table: Optional[str] = Field(None, description="Table the action applies to")
    action_name: Optional[str] = Field(None, description="Action name (used in scripts)")
    script: Optional[str] = Field(None, description="Server-side script")
    condition: Optional[str] = Field(None, description="Condition script")
    order: Optional[int] = Field(None, description="Order")
    active: bool = Field(True, description="Whether active")
    client: Optional[bool] = Field(None, description="Client-side action")
    onclick: Optional[str] = Field(None, description="Onclick function (client)")
    form_button: Optional[bool] = Field(None, description="Show as form button")
    form_link: Optional[bool] = Field(None, description="Show as form context menu link")
    list_button: Optional[bool] = Field(None, description="Show as list button")
    show_insert: Optional[bool] = Field(None, description="Show on insert")
    show_update: Optional[bool] = Field(None, description="Show on update")
    hint: Optional[str] = Field(None, description="Tooltip hint")
    comments: Optional[str] = Field(None, description="Comments")


class UpdateUiActionParams(BaseModel):
    """Parameters for updating a UI action."""

    ui_action_id: str = Field(..., description="UiAction sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Name (button/label)")
    table: Optional[str] = Field(None, description="Table the action applies to")
    action_name: Optional[str] = Field(None, description="Action name (used in scripts)")
    script: Optional[str] = Field(None, description="Server-side script")
    condition: Optional[str] = Field(None, description="Condition script")
    order: Optional[int] = Field(None, description="Order")
    active: Optional[bool] = Field(None, description="Whether active")
    client: Optional[bool] = Field(None, description="Client-side action")
    onclick: Optional[str] = Field(None, description="Onclick function (client)")
    form_button: Optional[bool] = Field(None, description="Show as form button")
    form_link: Optional[bool] = Field(None, description="Show as form context menu link")
    list_button: Optional[bool] = Field(None, description="Show as list button")
    show_insert: Optional[bool] = Field(None, description="Show on insert")
    show_update: Optional[bool] = Field(None, description="Show on update")
    hint: Optional[str] = Field(None, description="Tooltip hint")
    comments: Optional[str] = Field(None, description="Comments")


class DeleteUiActionParams(BaseModel):
    """Parameters for deleting a UI action."""

    ui_action_id: str = Field(..., description="UiAction sys_id (prefix with 'sys_id:'), or the exact name")


class UiActionResponse(BaseModel):
    """Response from UI action operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    ui_action_id: Optional[str] = Field(None, description="sys_id of the affected UI action")
    ui_action_name: Optional[str] = Field(None, description="Name of the affected UI action")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_ui_action record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "table": _display(item.get("table")),
        "action_name": _display(item.get("action_name")),
        "script": _display(item.get("script")),
        "condition": _display(item.get("condition")),
        "order": _display(item.get("order")),
        "active": item.get("active") == "true",
        "client": item.get("client") == "true",
        "onclick": _display(item.get("onclick")),
        "form_button": item.get("form_button") == "true",
        "form_link": item.get("form_link") == "true",
        "list_button": item.get("list_button") == "true",
        "show_insert": item.get("show_insert") == "true",
        "show_update": item.get("show_update") == "true",
        "hint": _display(item.get("hint")),
        "comments": _display(item.get("comments")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_ui_actions(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiActionsParams,
) -> Dict[str, Any]:
    """List UI actions from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_ui_action"
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
        if params.table:
            query_parts.append(f"table={params.table}")
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
            "message": f"Found {len(items)} UI actions",
            "ui_actions": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI actions: {e}")
        return {
            "success": False,
            "message": f"Error listing UI actions: {str(e)}",
            "ui_actions": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ui_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUiActionParams,
) -> Dict[str, Any]:
    """Get a specific UI action from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.ui_action_id.startswith("sys_id:"):
            sys_id = params.ui_action_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_ui_action/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_ui_action"
            query_params["sysparm_query"] = f"name={params.ui_action_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"UiAction not found: {params.ui_action_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"UiAction not found: {params.ui_action_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found UI action: {item.get('name')}",
            "ui_action": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting UI action: {e}")
        return {"success": False, "message": f"Error getting UI action: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "table", None)
    if value is not None:
        body["table"] = value
    value = getattr(params, "action_name", None)
    if value is not None:
        body["action_name"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "condition", None)
    if value is not None:
        body["condition"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "onclick", None)
    if value is not None:
        body["onclick"] = value
    value = getattr(params, "hint", None)
    if value is not None:
        body["hint"] = value
    value = getattr(params, "comments", None)
    if value is not None:
        body["comments"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "client", None)
    if value is not None:
        body["client"] = str(value).lower()
    value = getattr(params, "form_button", None)
    if value is not None:
        body["form_button"] = str(value).lower()
    value = getattr(params, "form_link", None)
    if value is not None:
        body["form_link"] = str(value).lower()
    value = getattr(params, "list_button", None)
    if value is not None:
        body["list_button"] = str(value).lower()
    value = getattr(params, "show_insert", None)
    if value is not None:
        body["show_insert"] = str(value).lower()
    value = getattr(params, "show_update", None)
    if value is not None:
        body["show_update"] = str(value).lower()
    return body


def create_ui_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiActionParams,
) -> UiActionResponse:
    """Create a new UI action in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_ui_action"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiActionResponse(success=False, message="Failed to create UI action")
        result = data["result"]
        return UiActionResponse(
            success=True,
            message=f"Created UI action: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            ui_action_id=result.get("sys_id"),
            ui_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating UI action: {e}")
        return UiActionResponse(success=False, message=f"Error creating UI action: {str(e)}")


def update_ui_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiActionParams,
) -> UiActionResponse:
    """Update an existing UI action in ServiceNow."""
    get_result = get_ui_action(config, auth_manager, GetUiActionParams(ui_action_id=params.ui_action_id))
    if not get_result["success"]:
        return UiActionResponse(success=False, message=get_result["message"])
    record = get_result["ui_action"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_ui_action/{sys_id}"
    body = _build_body(params)
    if not body:
        return UiActionResponse(
            success=True,
            message=f"No changes to update for UI action",
            ui_action_id=sys_id,
            ui_action_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiActionResponse(success=False, message=f"Failed to update UI action")
        result = data["result"]
        return UiActionResponse(
            success=True,
            message=f"Updated UI action",
            ui_action_id=result.get("sys_id"),
            ui_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating UI action: {e}")
        return UiActionResponse(success=False, message=f"Error updating UI action: {str(e)}")


def delete_ui_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiActionParams,
) -> UiActionResponse:
    """Delete a UI action from ServiceNow."""
    get_result = get_ui_action(config, auth_manager, GetUiActionParams(ui_action_id=params.ui_action_id))
    if not get_result["success"]:
        return UiActionResponse(success=False, message=get_result["message"])
    record = get_result["ui_action"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_ui_action/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return UiActionResponse(success=True, message=f"Deleted UI action", ui_action_id=sys_id, ui_action_name=name)
    except Exception as e:
        logger.error(f"Error deleting UI action: {e}")
        return UiActionResponse(success=False, message=f"Error deleting UI action: {str(e)}")
