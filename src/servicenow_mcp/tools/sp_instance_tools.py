"""
SpInstance tools for the ServiceNow MCP server.

This module provides CRUD tools for Service Portal widget instances (sp_instance) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,title,sp_widget,sp_column,id,short_description,order,css_class,color,glyph,url,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListSpInstancesParams(BaseModel):
    """Parameters for listing Service Portal widget instances."""

    limit: int = Field(10, description="Maximum number of Service Portal widget instances to return")
    offset: int = Field(0, description="Offset for pagination")
    sp_widget: Optional[str] = Field(None, description="Filter by Widget sys_id this instance renders")
    sp_column: Optional[str] = Field(None, description="Filter by Column sys_id the instance sits in")
    query: Optional[str] = Field(None, description="Search query matched against title (LIKE)")


class GetSpInstanceParams(BaseModel):
    """Parameters for getting a Service Portal widget instance."""

    sp_instance_id: str = Field(..., description="SpInstance sys_id (prefix with 'sys_id:')")


class CreateSpInstanceParams(BaseModel):
    """Parameters for creating a Service Portal widget instance."""

    sp_widget: str = Field(..., description="Widget sys_id this instance renders")
    sp_column: Optional[str] = Field(None, description="Column sys_id the instance sits in")
    title: Optional[str] = Field(None, description="Instance title")
    id: Optional[str] = Field(None, description="Instance id")
    short_description: Optional[str] = Field(None, description="Short description")
    order: Optional[int] = Field(None, description="Order within the column")
    css_class: Optional[str] = Field(None, description="CSS class")
    color: Optional[str] = Field(None, description="Color")
    glyph: Optional[str] = Field(None, description="Glyph/icon")
    url: Optional[str] = Field(None, description="URL")


class UpdateSpInstanceParams(BaseModel):
    """Parameters for updating a Service Portal widget instance."""

    sp_instance_id: str = Field(..., description="SpInstance sys_id (prefix with 'sys_id:')")
    sp_widget: Optional[str] = Field(None, description="Widget sys_id this instance renders")
    sp_column: Optional[str] = Field(None, description="Column sys_id the instance sits in")
    title: Optional[str] = Field(None, description="Instance title")
    id: Optional[str] = Field(None, description="Instance id")
    short_description: Optional[str] = Field(None, description="Short description")
    order: Optional[int] = Field(None, description="Order within the column")
    css_class: Optional[str] = Field(None, description="CSS class")
    color: Optional[str] = Field(None, description="Color")
    glyph: Optional[str] = Field(None, description="Glyph/icon")
    url: Optional[str] = Field(None, description="URL")


class DeleteSpInstanceParams(BaseModel):
    """Parameters for deleting a Service Portal widget instance."""

    sp_instance_id: str = Field(..., description="SpInstance sys_id (prefix with 'sys_id:')")


class SpInstanceResponse(BaseModel):
    """Response from Service Portal widget instance operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    sp_instance_id: Optional[str] = Field(None, description="sys_id of the affected Service Portal widget instance")
    sp_instance_name: Optional[str] = Field(None, description="Name of the affected Service Portal widget instance")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sp_instance record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "title": item.get("title"),
        "sp_widget": _display(item.get("sp_widget")),
        "sp_column": _display(item.get("sp_column")),
        "id": _display(item.get("id")),
        "short_description": _display(item.get("short_description")),
        "order": _display(item.get("order")),
        "css_class": _display(item.get("css_class")),
        "color": _display(item.get("color")),
        "glyph": _display(item.get("glyph")),
        "url": _display(item.get("url")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_sp_instances(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListSpInstancesParams,
) -> Dict[str, Any]:
    """List Service Portal widget instances from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sp_instance"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.sp_widget:
            query_parts.append(f"sp_widget={params.sp_widget}")
        if params.sp_column:
            query_parts.append(f"sp_column={params.sp_column}")
        if params.query:
            query_parts.append(f"titleLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} Service Portal widget instances",
            "sp_instances": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing Service Portal widget instances: {e}")
        return {
            "success": False,
            "message": f"Error listing Service Portal widget instances: {str(e)}",
            "sp_instances": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_sp_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetSpInstanceParams,
) -> Dict[str, Any]:
    """Get a specific Service Portal widget instance from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.sp_instance_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sp_instance/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"SpInstance not found: {params.sp_instance_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"SpInstance not found: {params.sp_instance_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found Service Portal widget instance: {item.get('title')}",
            "sp_instance": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting Service Portal widget instance: {e}")
        return {"success": False, "message": f"Error getting Service Portal widget instance: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "sp_widget", None)
    if value is not None:
        body["sp_widget"] = value
    value = getattr(params, "sp_column", None)
    if value is not None:
        body["sp_column"] = value
    value = getattr(params, "title", None)
    if value is not None:
        body["title"] = value
    value = getattr(params, "id", None)
    if value is not None:
        body["id"] = value
    value = getattr(params, "short_description", None)
    if value is not None:
        body["short_description"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "css_class", None)
    if value is not None:
        body["css_class"] = value
    value = getattr(params, "color", None)
    if value is not None:
        body["color"] = value
    value = getattr(params, "glyph", None)
    if value is not None:
        body["glyph"] = value
    value = getattr(params, "url", None)
    if value is not None:
        body["url"] = value
    return body


def create_sp_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateSpInstanceParams,
) -> SpInstanceResponse:
    """Create a new Service Portal widget instance in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sp_instance"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SpInstanceResponse(success=False, message="Failed to create Service Portal widget instance")
        result = data["result"]
        return SpInstanceResponse(
            success=True,
            message=f"Created Service Portal widget instance: {result.get('title') if 'title' != 'sys_id' else result.get('sys_id')}",
            sp_instance_id=result.get("sys_id"),
            sp_instance_name=result.get("title") if "title" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating Service Portal widget instance: {e}")
        return SpInstanceResponse(success=False, message=f"Error creating Service Portal widget instance: {str(e)}")


def update_sp_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateSpInstanceParams,
) -> SpInstanceResponse:
    """Update an existing Service Portal widget instance in ServiceNow."""
    get_result = get_sp_instance(config, auth_manager, GetSpInstanceParams(sp_instance_id=params.sp_instance_id))
    if not get_result["success"]:
        return SpInstanceResponse(success=False, message=get_result["message"])
    record = get_result["sp_instance"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sp_instance/{sys_id}"
    body = _build_body(params)
    if not body:
        return SpInstanceResponse(
            success=True,
            message=f"No changes to update for Service Portal widget instance",
            sp_instance_id=sys_id,
            sp_instance_name=record.get("title"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SpInstanceResponse(success=False, message=f"Failed to update Service Portal widget instance")
        result = data["result"]
        return SpInstanceResponse(
            success=True,
            message=f"Updated Service Portal widget instance",
            sp_instance_id=result.get("sys_id"),
            sp_instance_name=result.get("title") if "title" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating Service Portal widget instance: {e}")
        return SpInstanceResponse(success=False, message=f"Error updating Service Portal widget instance: {str(e)}")


def delete_sp_instance(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteSpInstanceParams,
) -> SpInstanceResponse:
    """Delete a Service Portal widget instance from ServiceNow."""
    get_result = get_sp_instance(config, auth_manager, GetSpInstanceParams(sp_instance_id=params.sp_instance_id))
    if not get_result["success"]:
        return SpInstanceResponse(success=False, message=get_result["message"])
    record = get_result["sp_instance"]
    sys_id = record["sys_id"]
    name = record.get("title")

    url = f"{config.instance_url}/api/now/table/sp_instance/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return SpInstanceResponse(success=True, message=f"Deleted Service Portal widget instance", sp_instance_id=sys_id, sp_instance_name=name)
    except Exception as e:
        logger.error(f"Error deleting Service Portal widget instance: {e}")
        return SpInstanceResponse(success=False, message=f"Error deleting Service Portal widget instance: {str(e)}")
