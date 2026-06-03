"""
Role tools for the ServiceNow MCP server.

This module provides CRUD tools for roles (sys_user_role) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,description,suffix,elevated_privilege,assignable_by,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListRolesParams(BaseModel):
    """Parameters for listing roles."""

    limit: int = Field(10, description="Maximum number of roles to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Role name")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetRoleParams(BaseModel):
    """Parameters for getting a role."""

    role_id: str = Field(..., description="Role sys_id (prefix with 'sys_id:'), or the exact name")


class CreateRoleParams(BaseModel):
    """Parameters for creating a role."""

    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Description")
    suffix: Optional[str] = Field(None, description="Suffix")
    elevated_privilege: Optional[bool] = Field(None, description="Elevated privilege (security admin)")
    assignable_by: Optional[str] = Field(None, description="Role that can assign this role")


class UpdateRoleParams(BaseModel):
    """Parameters for updating a role."""

    role_id: str = Field(..., description="Role sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Role name")
    description: Optional[str] = Field(None, description="Description")
    suffix: Optional[str] = Field(None, description="Suffix")
    elevated_privilege: Optional[bool] = Field(None, description="Elevated privilege (security admin)")
    assignable_by: Optional[str] = Field(None, description="Role that can assign this role")


class DeleteRoleParams(BaseModel):
    """Parameters for deleting a role."""

    role_id: str = Field(..., description="Role sys_id (prefix with 'sys_id:'), or the exact name")


class RoleResponse(BaseModel):
    """Response from role operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    role_id: Optional[str] = Field(None, description="sys_id of the affected role")
    role_name: Optional[str] = Field(None, description="Name of the affected role")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_user_role record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "description": _display(item.get("description")),
        "suffix": _display(item.get("suffix")),
        "elevated_privilege": item.get("elevated_privilege") == "true",
        "assignable_by": _display(item.get("assignable_by")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_roles(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListRolesParams,
) -> Dict[str, Any]:
    """List roles from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_user_role"
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
            "message": f"Found {len(items)} roles",
            "roles": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        return {
            "success": False,
            "message": f"Error listing roles: {str(e)}",
            "roles": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_role(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRoleParams,
) -> Dict[str, Any]:
    """Get a specific role from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.role_id.startswith("sys_id:"):
            sys_id = params.role_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_user_role/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_user_role"
            query_params["sysparm_query"] = f"name={params.role_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"Role not found: {params.role_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"Role not found: {params.role_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found role: {item.get('name')}",
            "role": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        return {"success": False, "message": f"Error getting role: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "suffix", None)
    if value is not None:
        body["suffix"] = value
    value = getattr(params, "assignable_by", None)
    if value is not None:
        body["assignable_by"] = value
    value = getattr(params, "elevated_privilege", None)
    if value is not None:
        body["elevated_privilege"] = str(value).lower()
    return body


def create_role(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateRoleParams,
) -> RoleResponse:
    """Create a new role in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_user_role"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return RoleResponse(success=False, message="Failed to create role")
        result = data["result"]
        return RoleResponse(
            success=True,
            message=f"Created role: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            role_id=result.get("sys_id"),
            role_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        return RoleResponse(success=False, message=f"Error creating role: {str(e)}")


def update_role(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateRoleParams,
) -> RoleResponse:
    """Update an existing role in ServiceNow."""
    get_result = get_role(config, auth_manager, GetRoleParams(role_id=params.role_id))
    if not get_result["success"]:
        return RoleResponse(success=False, message=get_result["message"])
    record = get_result["role"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_user_role/{sys_id}"
    body = _build_body(params)
    if not body:
        return RoleResponse(
            success=True,
            message=f"No changes to update for role",
            role_id=sys_id,
            role_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return RoleResponse(success=False, message=f"Failed to update role")
        result = data["result"]
        return RoleResponse(
            success=True,
            message=f"Updated role",
            role_id=result.get("sys_id"),
            role_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        return RoleResponse(success=False, message=f"Error updating role: {str(e)}")


def delete_role(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteRoleParams,
) -> RoleResponse:
    """Delete a role from ServiceNow."""
    get_result = get_role(config, auth_manager, GetRoleParams(role_id=params.role_id))
    if not get_result["success"]:
        return RoleResponse(success=False, message=get_result["message"])
    record = get_result["role"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_user_role/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return RoleResponse(success=True, message=f"Deleted role", role_id=sys_id, role_name=name)
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        return RoleResponse(success=False, message=f"Error deleting role: {str(e)}")
