"""
CatalogUiPolicyAction tools for the ServiceNow MCP server.

This module provides CRUD tools for catalog UI policy actions (catalog_ui_policy_action) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,ui_policy,catalog_variable,mandatory,visible,disabled,cleared,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListCatalogUiPolicyActionsParams(BaseModel):
    """Parameters for listing catalog UI policy actions."""

    limit: int = Field(10, description="Maximum number of catalog UI policy actions to return")
    offset: int = Field(0, description="Offset for pagination")
    ui_policy: Optional[str] = Field(None, description="Filter by Parent catalog UI policy sys_id")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetCatalogUiPolicyActionParams(BaseModel):
    """Parameters for getting a catalog UI policy action."""

    catalog_ui_policy_action_id: str = Field(..., description="CatalogUiPolicyAction sys_id (prefix with 'sys_id:')")


class CreateCatalogUiPolicyActionParams(BaseModel):
    """Parameters for creating a catalog UI policy action."""

    ui_policy: str = Field(..., description="Parent catalog UI policy sys_id")
    catalog_variable: str = Field(..., description="Variable the action targets")
    mandatory: Optional[str] = Field(None, description="Mandatory: true, false, ignore")
    visible: Optional[str] = Field(None, description="Visible: true, false, ignore")
    disabled: Optional[str] = Field(None, description="Disabled: true, false, ignore")
    cleared: Optional[str] = Field(None, description="Cleared: true, false, ignore")


class UpdateCatalogUiPolicyActionParams(BaseModel):
    """Parameters for updating a catalog UI policy action."""

    catalog_ui_policy_action_id: str = Field(..., description="CatalogUiPolicyAction sys_id (prefix with 'sys_id:')")
    ui_policy: Optional[str] = Field(None, description="Parent catalog UI policy sys_id")
    catalog_variable: Optional[str] = Field(None, description="Variable the action targets")
    mandatory: Optional[str] = Field(None, description="Mandatory: true, false, ignore")
    visible: Optional[str] = Field(None, description="Visible: true, false, ignore")
    disabled: Optional[str] = Field(None, description="Disabled: true, false, ignore")
    cleared: Optional[str] = Field(None, description="Cleared: true, false, ignore")


class DeleteCatalogUiPolicyActionParams(BaseModel):
    """Parameters for deleting a catalog UI policy action."""

    catalog_ui_policy_action_id: str = Field(..., description="CatalogUiPolicyAction sys_id (prefix with 'sys_id:')")


class CatalogUiPolicyActionResponse(BaseModel):
    """Response from catalog UI policy action operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    catalog_ui_policy_action_id: Optional[str] = Field(None, description="sys_id of the affected catalog UI policy action")
    catalog_ui_policy_action_name: Optional[str] = Field(None, description="Name of the affected catalog UI policy action")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw catalog_ui_policy_action record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "ui_policy": _display(item.get("ui_policy")),
        "catalog_variable": _display(item.get("catalog_variable")),
        "mandatory": _display(item.get("mandatory")),
        "visible": _display(item.get("visible")),
        "disabled": _display(item.get("disabled")),
        "cleared": _display(item.get("cleared")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_catalog_ui_policy_actions(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCatalogUiPolicyActionsParams,
) -> Dict[str, Any]:
    """List catalog UI policy actions from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/catalog_ui_policy_action"
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
            "message": f"Found {len(items)} catalog UI policy actions",
            "catalog_ui_policy_actions": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing catalog UI policy actions: {e}")
        return {
            "success": False,
            "message": f"Error listing catalog UI policy actions: {str(e)}",
            "catalog_ui_policy_actions": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_catalog_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCatalogUiPolicyActionParams,
) -> Dict[str, Any]:
    """Get a specific catalog UI policy action from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.catalog_ui_policy_action_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/catalog_ui_policy_action/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"CatalogUiPolicyAction not found: {params.catalog_ui_policy_action_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"CatalogUiPolicyAction not found: {params.catalog_ui_policy_action_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found catalog UI policy action: {item.get('name')}",
            "catalog_ui_policy_action": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting catalog UI policy action: {e}")
        return {"success": False, "message": f"Error getting catalog UI policy action: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "ui_policy", None)
    if value is not None:
        body["ui_policy"] = value
    value = getattr(params, "catalog_variable", None)
    if value is not None:
        body["catalog_variable"] = value
    value = getattr(params, "mandatory", None)
    if value is not None:
        body["mandatory"] = value
    value = getattr(params, "visible", None)
    if value is not None:
        body["visible"] = value
    value = getattr(params, "disabled", None)
    if value is not None:
        body["disabled"] = value
    value = getattr(params, "cleared", None)
    if value is not None:
        body["cleared"] = value
    return body


def create_catalog_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateCatalogUiPolicyActionParams,
) -> CatalogUiPolicyActionResponse:
    """Create a new catalog UI policy action in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/catalog_ui_policy_action"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogUiPolicyActionResponse(success=False, message="Failed to create catalog UI policy action")
        result = data["result"]
        return CatalogUiPolicyActionResponse(
            success=True,
            message=f"Created catalog UI policy action: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            catalog_ui_policy_action_id=result.get("sys_id"),
            catalog_ui_policy_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating catalog UI policy action: {e}")
        return CatalogUiPolicyActionResponse(success=False, message=f"Error creating catalog UI policy action: {str(e)}")


def update_catalog_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateCatalogUiPolicyActionParams,
) -> CatalogUiPolicyActionResponse:
    """Update an existing catalog UI policy action in ServiceNow."""
    get_result = get_catalog_ui_policy_action(config, auth_manager, GetCatalogUiPolicyActionParams(catalog_ui_policy_action_id=params.catalog_ui_policy_action_id))
    if not get_result["success"]:
        return CatalogUiPolicyActionResponse(success=False, message=get_result["message"])
    record = get_result["catalog_ui_policy_action"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/catalog_ui_policy_action/{sys_id}"
    body = _build_body(params)
    if not body:
        return CatalogUiPolicyActionResponse(
            success=True,
            message=f"No changes to update for catalog UI policy action",
            catalog_ui_policy_action_id=sys_id,
            catalog_ui_policy_action_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogUiPolicyActionResponse(success=False, message=f"Failed to update catalog UI policy action")
        result = data["result"]
        return CatalogUiPolicyActionResponse(
            success=True,
            message=f"Updated catalog UI policy action",
            catalog_ui_policy_action_id=result.get("sys_id"),
            catalog_ui_policy_action_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating catalog UI policy action: {e}")
        return CatalogUiPolicyActionResponse(success=False, message=f"Error updating catalog UI policy action: {str(e)}")


def delete_catalog_ui_policy_action(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteCatalogUiPolicyActionParams,
) -> CatalogUiPolicyActionResponse:
    """Delete a catalog UI policy action from ServiceNow."""
    get_result = get_catalog_ui_policy_action(config, auth_manager, GetCatalogUiPolicyActionParams(catalog_ui_policy_action_id=params.catalog_ui_policy_action_id))
    if not get_result["success"]:
        return CatalogUiPolicyActionResponse(success=False, message=get_result["message"])
    record = get_result["catalog_ui_policy_action"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/catalog_ui_policy_action/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return CatalogUiPolicyActionResponse(success=True, message=f"Deleted catalog UI policy action", catalog_ui_policy_action_id=sys_id, catalog_ui_policy_action_name=name)
    except Exception as e:
        logger.error(f"Error deleting catalog UI policy action: {e}")
        return CatalogUiPolicyActionResponse(success=False, message=f"Error deleting catalog UI policy action: {str(e)}")
