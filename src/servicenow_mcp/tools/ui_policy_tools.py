"""
UiPolicy tools for the ServiceNow MCP server.

This module provides CRUD tools for UI policies (sys_ui_policy) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,short_description,table,active,order,conditions,on_load,reverse_if_false,run_scripts,ui_type,global,script_true,script_false,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListUiPolicysParams(BaseModel):
    """Parameters for listing UI policies."""

    limit: int = Field(10, description="Maximum number of UI policies to return")
    offset: int = Field(0, description="Offset for pagination")
    table: Optional[str] = Field(None, description="Filter by Table the UI policy applies to")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against short_description (LIKE)")


class GetUiPolicyParams(BaseModel):
    """Parameters for getting a UI policy."""

    ui_policy_id: str = Field(..., description="UiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class CreateUiPolicyParams(BaseModel):
    """Parameters for creating a UI policy."""

    table: str = Field(..., description="Table the UI policy applies to")
    short_description: str = Field(..., description="Short description (name)")
    active: bool = Field(True, description="Whether active")
    order: Optional[int] = Field(None, description="Execution order")
    conditions: Optional[str] = Field(None, description="Encoded query conditions")
    on_load: Optional[bool] = Field(None, description="Run on form load")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse actions if condition false")
    run_scripts: Optional[bool] = Field(None, description="Run scripts")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    global_: Optional[bool] = Field(None, alias="global", description="Applies to all views (Global)")
    script_true: Optional[str] = Field(None, description="Script when condition true")
    script_false: Optional[str] = Field(None, description="Script when condition false")

    class Config:
        populate_by_name = True


class UpdateUiPolicyParams(BaseModel):
    """Parameters for updating a UI policy."""

    ui_policy_id: str = Field(..., description="UiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")
    table: Optional[str] = Field(None, description="Table the UI policy applies to")
    short_description: Optional[str] = Field(None, description="Short description (name)")
    active: Optional[bool] = Field(None, description="Whether active")
    order: Optional[int] = Field(None, description="Execution order")
    conditions: Optional[str] = Field(None, description="Encoded query conditions")
    on_load: Optional[bool] = Field(None, description="Run on form load")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse actions if condition false")
    run_scripts: Optional[bool] = Field(None, description="Run scripts")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    global_: Optional[bool] = Field(None, alias="global", description="Applies to all views (Global)")
    script_true: Optional[str] = Field(None, description="Script when condition true")
    script_false: Optional[str] = Field(None, description="Script when condition false")

    class Config:
        populate_by_name = True


class DeleteUiPolicyParams(BaseModel):
    """Parameters for deleting a UI policy."""

    ui_policy_id: str = Field(..., description="UiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class UiPolicyResponse(BaseModel):
    """Response from UI policy operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    ui_policy_id: Optional[str] = Field(None, description="sys_id of the affected UI policy")
    ui_policy_name: Optional[str] = Field(None, description="Name of the affected UI policy")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_ui_policy record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "short_description": item.get("short_description"),
        "table": _display(item.get("table")),
        "active": item.get("active") == "true",
        "order": _display(item.get("order")),
        "conditions": _display(item.get("conditions")),
        "on_load": item.get("on_load") == "true",
        "reverse_if_false": item.get("reverse_if_false") == "true",
        "run_scripts": item.get("run_scripts") == "true",
        "ui_type": _display(item.get("ui_type")),
        "global": item.get("global") == "true",
        "script_true": _display(item.get("script_true")),
        "script_false": _display(item.get("script_false")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_ui_policies(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiPolicysParams,
) -> Dict[str, Any]:
    """List UI policies from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_ui_policy"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.table:
            query_parts.append(f"table={params.table}")
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
        if params.query:
            query_parts.append(f"short_descriptionLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} UI policies",
            "ui_policies": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI policies: {e}")
        return {
            "success": False,
            "message": f"Error listing UI policies: {str(e)}",
            "ui_policies": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUiPolicyParams,
) -> Dict[str, Any]:
    """Get a specific UI policy from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.ui_policy_id.startswith("sys_id:"):
            sys_id = params.ui_policy_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_ui_policy/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_ui_policy"
            query_params["sysparm_query"] = f"short_description={params.ui_policy_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"UiPolicy not found: {params.ui_policy_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"UiPolicy not found: {params.ui_policy_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found UI policy: {item.get('short_description')}",
            "ui_policy": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting UI policy: {e}")
        return {"success": False, "message": f"Error getting UI policy: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "table", None)
    if value is not None:
        body["table"] = value
    value = getattr(params, "short_description", None)
    if value is not None:
        body["short_description"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "conditions", None)
    if value is not None:
        body["conditions"] = value
    value = getattr(params, "ui_type", None)
    if value is not None:
        body["ui_type"] = value
    value = getattr(params, "script_true", None)
    if value is not None:
        body["script_true"] = value
    value = getattr(params, "script_false", None)
    if value is not None:
        body["script_false"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "on_load", None)
    if value is not None:
        body["on_load"] = str(value).lower()
    value = getattr(params, "reverse_if_false", None)
    if value is not None:
        body["reverse_if_false"] = str(value).lower()
    value = getattr(params, "run_scripts", None)
    if value is not None:
        body["run_scripts"] = str(value).lower()
    value = getattr(params, "global_", None)
    if value is not None:
        body["global"] = str(value).lower()
    return body


def create_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiPolicyParams,
) -> UiPolicyResponse:
    """Create a new UI policy in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_ui_policy"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiPolicyResponse(success=False, message="Failed to create UI policy")
        result = data["result"]
        return UiPolicyResponse(
            success=True,
            message=f"Created UI policy: {result.get('short_description') if 'short_description' != 'sys_id' else result.get('sys_id')}",
            ui_policy_id=result.get("sys_id"),
            ui_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating UI policy: {e}")
        return UiPolicyResponse(success=False, message=f"Error creating UI policy: {str(e)}")


def update_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiPolicyParams,
) -> UiPolicyResponse:
    """Update an existing UI policy in ServiceNow."""
    get_result = get_ui_policy(config, auth_manager, GetUiPolicyParams(ui_policy_id=params.ui_policy_id))
    if not get_result["success"]:
        return UiPolicyResponse(success=False, message=get_result["message"])
    record = get_result["ui_policy"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_ui_policy/{sys_id}"
    body = _build_body(params)
    if not body:
        return UiPolicyResponse(
            success=True,
            message=f"No changes to update for UI policy",
            ui_policy_id=sys_id,
            ui_policy_name=record.get("short_description"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return UiPolicyResponse(success=False, message=f"Failed to update UI policy")
        result = data["result"]
        return UiPolicyResponse(
            success=True,
            message=f"Updated UI policy",
            ui_policy_id=result.get("sys_id"),
            ui_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating UI policy: {e}")
        return UiPolicyResponse(success=False, message=f"Error updating UI policy: {str(e)}")


def delete_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiPolicyParams,
) -> UiPolicyResponse:
    """Delete a UI policy from ServiceNow."""
    get_result = get_ui_policy(config, auth_manager, GetUiPolicyParams(ui_policy_id=params.ui_policy_id))
    if not get_result["success"]:
        return UiPolicyResponse(success=False, message=get_result["message"])
    record = get_result["ui_policy"]
    sys_id = record["sys_id"]
    name = record.get("short_description")

    url = f"{config.instance_url}/api/now/table/sys_ui_policy/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return UiPolicyResponse(success=True, message=f"Deleted UI policy", ui_policy_id=sys_id, ui_policy_name=name)
    except Exception as e:
        logger.error(f"Error deleting UI policy: {e}")
        return UiPolicyResponse(success=False, message=f"Error deleting UI policy: {str(e)}")
