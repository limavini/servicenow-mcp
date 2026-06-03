"""
SystemProperty tools for the ServiceNow MCP server.

This module provides CRUD tools for system properties (sys_properties) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,value,type,description,is_private,ignore_cache,read_roles,write_roles,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListSystemPropertysParams(BaseModel):
    """Parameters for listing system properties."""

    limit: int = Field(10, description="Maximum number of system properties to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Property name (e.g. x.y.z)")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetSystemPropertyParams(BaseModel):
    """Parameters for getting a system property."""

    system_property_id: str = Field(..., description="SystemProperty sys_id (prefix with 'sys_id:'), or the exact name")


class CreateSystemPropertyParams(BaseModel):
    """Parameters for creating a system property."""

    name: str = Field(..., description="Property name (e.g. x.y.z)")
    value: Optional[str] = Field(None, description="Property value")
    type: Optional[str] = Field(None, description="Value type: string, integer, boolean, ...")
    description: Optional[str] = Field(None, description="Description")
    is_private: Optional[bool] = Field(None, description="Whether the property is private")
    ignore_cache: Optional[bool] = Field(None, description="Ignore cache on change")
    read_roles: Optional[str] = Field(None, description="Roles allowed to read")
    write_roles: Optional[str] = Field(None, description="Roles allowed to write")


class UpdateSystemPropertyParams(BaseModel):
    """Parameters for updating a system property."""

    system_property_id: str = Field(..., description="SystemProperty sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Property name (e.g. x.y.z)")
    value: Optional[str] = Field(None, description="Property value")
    type: Optional[str] = Field(None, description="Value type: string, integer, boolean, ...")
    description: Optional[str] = Field(None, description="Description")
    is_private: Optional[bool] = Field(None, description="Whether the property is private")
    ignore_cache: Optional[bool] = Field(None, description="Ignore cache on change")
    read_roles: Optional[str] = Field(None, description="Roles allowed to read")
    write_roles: Optional[str] = Field(None, description="Roles allowed to write")


class DeleteSystemPropertyParams(BaseModel):
    """Parameters for deleting a system property."""

    system_property_id: str = Field(..., description="SystemProperty sys_id (prefix with 'sys_id:'), or the exact name")


class SystemPropertyResponse(BaseModel):
    """Response from system property operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    system_property_id: Optional[str] = Field(None, description="sys_id of the affected system property")
    system_property_name: Optional[str] = Field(None, description="Name of the affected system property")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_properties record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "value": _display(item.get("value")),
        "type": _display(item.get("type")),
        "description": _display(item.get("description")),
        "is_private": item.get("is_private") == "true",
        "ignore_cache": item.get("ignore_cache") == "true",
        "read_roles": _display(item.get("read_roles")),
        "write_roles": _display(item.get("write_roles")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_system_properties(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListSystemPropertysParams,
) -> Dict[str, Any]:
    """List system properties from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_properties"
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
            "message": f"Found {len(items)} system properties",
            "system_properties": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing system properties: {e}")
        return {
            "success": False,
            "message": f"Error listing system properties: {str(e)}",
            "system_properties": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_system_property(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetSystemPropertyParams,
) -> Dict[str, Any]:
    """Get a specific system property from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.system_property_id.startswith("sys_id:"):
            sys_id = params.system_property_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_properties/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_properties"
            query_params["sysparm_query"] = f"name={params.system_property_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"SystemProperty not found: {params.system_property_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"SystemProperty not found: {params.system_property_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found system property: {item.get('name')}",
            "system_property": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting system property: {e}")
        return {"success": False, "message": f"Error getting system property: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "value", None)
    if value is not None:
        body["value"] = value
    value = getattr(params, "type", None)
    if value is not None:
        body["type"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "read_roles", None)
    if value is not None:
        body["read_roles"] = value
    value = getattr(params, "write_roles", None)
    if value is not None:
        body["write_roles"] = value
    value = getattr(params, "is_private", None)
    if value is not None:
        body["is_private"] = str(value).lower()
    value = getattr(params, "ignore_cache", None)
    if value is not None:
        body["ignore_cache"] = str(value).lower()
    return body


def create_system_property(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateSystemPropertyParams,
) -> SystemPropertyResponse:
    """Create a new system property in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_properties"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SystemPropertyResponse(success=False, message="Failed to create system property")
        result = data["result"]
        return SystemPropertyResponse(
            success=True,
            message=f"Created system property: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            system_property_id=result.get("sys_id"),
            system_property_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating system property: {e}")
        return SystemPropertyResponse(success=False, message=f"Error creating system property: {str(e)}")


def update_system_property(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateSystemPropertyParams,
) -> SystemPropertyResponse:
    """Update an existing system property in ServiceNow."""
    get_result = get_system_property(config, auth_manager, GetSystemPropertyParams(system_property_id=params.system_property_id))
    if not get_result["success"]:
        return SystemPropertyResponse(success=False, message=get_result["message"])
    record = get_result["system_property"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_properties/{sys_id}"
    body = _build_body(params)
    if not body:
        return SystemPropertyResponse(
            success=True,
            message=f"No changes to update for system property",
            system_property_id=sys_id,
            system_property_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SystemPropertyResponse(success=False, message=f"Failed to update system property")
        result = data["result"]
        return SystemPropertyResponse(
            success=True,
            message=f"Updated system property",
            system_property_id=result.get("sys_id"),
            system_property_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating system property: {e}")
        return SystemPropertyResponse(success=False, message=f"Error updating system property: {str(e)}")


def delete_system_property(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteSystemPropertyParams,
) -> SystemPropertyResponse:
    """Delete a system property from ServiceNow."""
    get_result = get_system_property(config, auth_manager, GetSystemPropertyParams(system_property_id=params.system_property_id))
    if not get_result["success"]:
        return SystemPropertyResponse(success=False, message=get_result["message"])
    record = get_result["system_property"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_properties/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return SystemPropertyResponse(success=True, message=f"Deleted system property", system_property_id=sys_id, system_property_name=name)
    except Exception as e:
        logger.error(f"Error deleting system property: {e}")
        return SystemPropertyResponse(success=False, message=f"Error deleting system property: {str(e)}")
