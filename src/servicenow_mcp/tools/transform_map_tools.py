"""
TransformMap tools for the ServiceNow MCP server.

This module provides CRUD tools for transform maps (sys_transform_map) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,source_table,target_table,active,order,run_business_rules,enforce_mandatory_fields,copy_empty_fields,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListTransformMapsParams(BaseModel):
    """Parameters for listing transform maps."""

    limit: int = Field(10, description="Maximum number of transform maps to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Transform map name")
    source_table: Optional[str] = Field(None, description="Filter by Source (import set) table")
    target_table: Optional[str] = Field(None, description="Filter by Target table")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetTransformMapParams(BaseModel):
    """Parameters for getting a transform map."""

    transform_map_id: str = Field(..., description="TransformMap sys_id (prefix with 'sys_id:'), or the exact name")


class CreateTransformMapParams(BaseModel):
    """Parameters for creating a transform map."""

    name: str = Field(..., description="Transform map name")
    source_table: Optional[str] = Field(None, description="Source (import set) table")
    target_table: Optional[str] = Field(None, description="Target table")
    active: bool = Field(True, description="Whether active")
    order: Optional[int] = Field(None, description="Order")
    run_business_rules: Optional[bool] = Field(None, description="Run business rules on transform")
    enforce_mandatory_fields: Optional[str] = Field(None, description="Enforce mandatory fields")
    copy_empty_fields: Optional[bool] = Field(None, description="Copy empty fields")


class UpdateTransformMapParams(BaseModel):
    """Parameters for updating a transform map."""

    transform_map_id: str = Field(..., description="TransformMap sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Transform map name")
    source_table: Optional[str] = Field(None, description="Source (import set) table")
    target_table: Optional[str] = Field(None, description="Target table")
    active: Optional[bool] = Field(None, description="Whether active")
    order: Optional[int] = Field(None, description="Order")
    run_business_rules: Optional[bool] = Field(None, description="Run business rules on transform")
    enforce_mandatory_fields: Optional[str] = Field(None, description="Enforce mandatory fields")
    copy_empty_fields: Optional[bool] = Field(None, description="Copy empty fields")


class DeleteTransformMapParams(BaseModel):
    """Parameters for deleting a transform map."""

    transform_map_id: str = Field(..., description="TransformMap sys_id (prefix with 'sys_id:'), or the exact name")


class TransformMapResponse(BaseModel):
    """Response from transform map operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    transform_map_id: Optional[str] = Field(None, description="sys_id of the affected transform map")
    transform_map_name: Optional[str] = Field(None, description="Name of the affected transform map")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_transform_map record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "source_table": _display(item.get("source_table")),
        "target_table": _display(item.get("target_table")),
        "active": item.get("active") == "true",
        "order": _display(item.get("order")),
        "run_business_rules": item.get("run_business_rules") == "true",
        "enforce_mandatory_fields": _display(item.get("enforce_mandatory_fields")),
        "copy_empty_fields": item.get("copy_empty_fields") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_transform_maps(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListTransformMapsParams,
) -> Dict[str, Any]:
    """List transform maps from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_transform_map"
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
        if params.source_table:
            query_parts.append(f"source_table={params.source_table}")
        if params.target_table:
            query_parts.append(f"target_table={params.target_table}")
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
            "message": f"Found {len(items)} transform maps",
            "transform_maps": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing transform maps: {e}")
        return {
            "success": False,
            "message": f"Error listing transform maps: {str(e)}",
            "transform_maps": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_transform_map(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetTransformMapParams,
) -> Dict[str, Any]:
    """Get a specific transform map from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.transform_map_id.startswith("sys_id:"):
            sys_id = params.transform_map_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_transform_map/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_transform_map"
            query_params["sysparm_query"] = f"name={params.transform_map_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"TransformMap not found: {params.transform_map_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"TransformMap not found: {params.transform_map_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found transform map: {item.get('name')}",
            "transform_map": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting transform map: {e}")
        return {"success": False, "message": f"Error getting transform map: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "source_table", None)
    if value is not None:
        body["source_table"] = value
    value = getattr(params, "target_table", None)
    if value is not None:
        body["target_table"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "enforce_mandatory_fields", None)
    if value is not None:
        body["enforce_mandatory_fields"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "run_business_rules", None)
    if value is not None:
        body["run_business_rules"] = str(value).lower()
    value = getattr(params, "copy_empty_fields", None)
    if value is not None:
        body["copy_empty_fields"] = str(value).lower()
    return body


def create_transform_map(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateTransformMapParams,
) -> TransformMapResponse:
    """Create a new transform map in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_transform_map"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return TransformMapResponse(success=False, message="Failed to create transform map")
        result = data["result"]
        return TransformMapResponse(
            success=True,
            message=f"Created transform map: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            transform_map_id=result.get("sys_id"),
            transform_map_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating transform map: {e}")
        return TransformMapResponse(success=False, message=f"Error creating transform map: {str(e)}")


def update_transform_map(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateTransformMapParams,
) -> TransformMapResponse:
    """Update an existing transform map in ServiceNow."""
    get_result = get_transform_map(config, auth_manager, GetTransformMapParams(transform_map_id=params.transform_map_id))
    if not get_result["success"]:
        return TransformMapResponse(success=False, message=get_result["message"])
    record = get_result["transform_map"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_transform_map/{sys_id}"
    body = _build_body(params)
    if not body:
        return TransformMapResponse(
            success=True,
            message=f"No changes to update for transform map",
            transform_map_id=sys_id,
            transform_map_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return TransformMapResponse(success=False, message=f"Failed to update transform map")
        result = data["result"]
        return TransformMapResponse(
            success=True,
            message=f"Updated transform map",
            transform_map_id=result.get("sys_id"),
            transform_map_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating transform map: {e}")
        return TransformMapResponse(success=False, message=f"Error updating transform map: {str(e)}")


def delete_transform_map(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteTransformMapParams,
) -> TransformMapResponse:
    """Delete a transform map from ServiceNow."""
    get_result = get_transform_map(config, auth_manager, GetTransformMapParams(transform_map_id=params.transform_map_id))
    if not get_result["success"]:
        return TransformMapResponse(success=False, message=get_result["message"])
    record = get_result["transform_map"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_transform_map/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return TransformMapResponse(success=True, message=f"Deleted transform map", transform_map_id=sys_id, transform_map_name=name)
    except Exception as e:
        logger.error(f"Error deleting transform map: {e}")
        return TransformMapResponse(success=False, message=f"Error deleting transform map: {str(e)}")
