"""
TransformEntry tools for the ServiceNow MCP server.

This module provides CRUD tools for transform map fields (sys_transform_entry) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,map,source_field,target_field,coalesce,choice_action,source_script,use_source_script,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListTransformEntrysParams(BaseModel):
    """Parameters for listing transform map fields."""

    limit: int = Field(10, description="Maximum number of transform map fields to return")
    offset: int = Field(0, description="Offset for pagination")
    map: Optional[str] = Field(None, description="Filter by Parent transform map sys_id")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetTransformEntryParams(BaseModel):
    """Parameters for getting a transform map field."""

    transform_entry_id: str = Field(..., description="TransformEntry sys_id (prefix with 'sys_id:')")


class CreateTransformEntryParams(BaseModel):
    """Parameters for creating a transform map field."""

    map: str = Field(..., description="Parent transform map sys_id")
    source_field: Optional[str] = Field(None, description="Source field")
    target_field: Optional[str] = Field(None, description="Target field")
    coalesce: Optional[bool] = Field(None, description="Coalesce on this field")
    choice_action: Optional[str] = Field(None, description="Choice action: create, ignore, reject")
    source_script: Optional[str] = Field(None, description="Source script")
    use_source_script: Optional[bool] = Field(None, description="Use source script")


class UpdateTransformEntryParams(BaseModel):
    """Parameters for updating a transform map field."""

    transform_entry_id: str = Field(..., description="TransformEntry sys_id (prefix with 'sys_id:')")
    map: Optional[str] = Field(None, description="Parent transform map sys_id")
    source_field: Optional[str] = Field(None, description="Source field")
    target_field: Optional[str] = Field(None, description="Target field")
    coalesce: Optional[bool] = Field(None, description="Coalesce on this field")
    choice_action: Optional[str] = Field(None, description="Choice action: create, ignore, reject")
    source_script: Optional[str] = Field(None, description="Source script")
    use_source_script: Optional[bool] = Field(None, description="Use source script")


class DeleteTransformEntryParams(BaseModel):
    """Parameters for deleting a transform map field."""

    transform_entry_id: str = Field(..., description="TransformEntry sys_id (prefix with 'sys_id:')")


class TransformEntryResponse(BaseModel):
    """Response from transform map field operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    transform_entry_id: Optional[str] = Field(None, description="sys_id of the affected transform map field")
    transform_entry_name: Optional[str] = Field(None, description="Name of the affected transform map field")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_transform_entry record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "map": _display(item.get("map")),
        "source_field": _display(item.get("source_field")),
        "target_field": _display(item.get("target_field")),
        "coalesce": item.get("coalesce") == "true",
        "choice_action": _display(item.get("choice_action")),
        "source_script": _display(item.get("source_script")),
        "use_source_script": item.get("use_source_script") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_transform_entries(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListTransformEntrysParams,
) -> Dict[str, Any]:
    """List transform map fields from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_transform_entry"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.map:
            query_parts.append(f"map={params.map}")
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
            "message": f"Found {len(items)} transform map fields",
            "transform_entries": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing transform map fields: {e}")
        return {
            "success": False,
            "message": f"Error listing transform map fields: {str(e)}",
            "transform_entries": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_transform_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetTransformEntryParams,
) -> Dict[str, Any]:
    """Get a specific transform map field from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.transform_entry_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_transform_entry/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"TransformEntry not found: {params.transform_entry_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"TransformEntry not found: {params.transform_entry_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found transform map field: {item.get('name')}",
            "transform_entry": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting transform map field: {e}")
        return {"success": False, "message": f"Error getting transform map field: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "map", None)
    if value is not None:
        body["map"] = value
    value = getattr(params, "source_field", None)
    if value is not None:
        body["source_field"] = value
    value = getattr(params, "target_field", None)
    if value is not None:
        body["target_field"] = value
    value = getattr(params, "choice_action", None)
    if value is not None:
        body["choice_action"] = value
    value = getattr(params, "source_script", None)
    if value is not None:
        body["source_script"] = value
    value = getattr(params, "coalesce", None)
    if value is not None:
        body["coalesce"] = str(value).lower()
    value = getattr(params, "use_source_script", None)
    if value is not None:
        body["use_source_script"] = str(value).lower()
    return body


def create_transform_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateTransformEntryParams,
) -> TransformEntryResponse:
    """Create a new transform map field in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_transform_entry"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return TransformEntryResponse(success=False, message="Failed to create transform map field")
        result = data["result"]
        return TransformEntryResponse(
            success=True,
            message=f"Created transform map field: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            transform_entry_id=result.get("sys_id"),
            transform_entry_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating transform map field: {e}")
        return TransformEntryResponse(success=False, message=f"Error creating transform map field: {str(e)}")


def update_transform_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateTransformEntryParams,
) -> TransformEntryResponse:
    """Update an existing transform map field in ServiceNow."""
    get_result = get_transform_entry(config, auth_manager, GetTransformEntryParams(transform_entry_id=params.transform_entry_id))
    if not get_result["success"]:
        return TransformEntryResponse(success=False, message=get_result["message"])
    record = get_result["transform_entry"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_transform_entry/{sys_id}"
    body = _build_body(params)
    if not body:
        return TransformEntryResponse(
            success=True,
            message=f"No changes to update for transform map field",
            transform_entry_id=sys_id,
            transform_entry_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return TransformEntryResponse(success=False, message=f"Failed to update transform map field")
        result = data["result"]
        return TransformEntryResponse(
            success=True,
            message=f"Updated transform map field",
            transform_entry_id=result.get("sys_id"),
            transform_entry_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating transform map field: {e}")
        return TransformEntryResponse(success=False, message=f"Error updating transform map field: {str(e)}")


def delete_transform_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteTransformEntryParams,
) -> TransformEntryResponse:
    """Delete a transform map field from ServiceNow."""
    get_result = get_transform_entry(config, auth_manager, GetTransformEntryParams(transform_entry_id=params.transform_entry_id))
    if not get_result["success"]:
        return TransformEntryResponse(success=False, message=get_result["message"])
    record = get_result["transform_entry"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_transform_entry/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return TransformEntryResponse(success=True, message=f"Deleted transform map field", transform_entry_id=sys_id, transform_entry_name=name)
    except Exception as e:
        logger.error(f"Error deleting transform map field: {e}")
        return TransformEntryResponse(success=False, message=f"Error deleting transform map field: {str(e)}")
