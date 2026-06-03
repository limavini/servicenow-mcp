"""
Acl tools for the ServiceNow MCP server.

This module provides CRUD tools for ACLs (sys_security_acl) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,operation,type,admin_overrides,active,script,condition,description,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListAclsParams(BaseModel):
    """Parameters for listing ACLs."""

    limit: int = Field(10, description="Maximum number of ACLs to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by ACL name (table or table.field)")
    operation: Optional[str] = Field(None, description="Filter by Operation: read, write, create, delete, execute")
    type: Optional[str] = Field(None, description="Filter by ACL type: record, field, ...")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetAclParams(BaseModel):
    """Parameters for getting a ACL."""

    acl_id: str = Field(..., description="Acl sys_id (prefix with 'sys_id:'), or the exact name")


class CreateAclParams(BaseModel):
    """Parameters for creating a ACL."""

    name: str = Field(..., description="ACL name (table or table.field)")
    operation: str = Field(..., description="Operation: read, write, create, delete, execute")
    type: Optional[str] = Field(None, description="ACL type: record, field, ...")
    admin_overrides: Optional[bool] = Field(None, description="Admin overrides this ACL")
    active: bool = Field(True, description="Whether active")
    script: Optional[str] = Field(None, description="Script condition")
    condition: Optional[str] = Field(None, description="Encoded query condition")
    description: Optional[str] = Field(None, description="Description")


class UpdateAclParams(BaseModel):
    """Parameters for updating a ACL."""

    acl_id: str = Field(..., description="Acl sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="ACL name (table or table.field)")
    operation: Optional[str] = Field(None, description="Operation: read, write, create, delete, execute")
    type: Optional[str] = Field(None, description="ACL type: record, field, ...")
    admin_overrides: Optional[bool] = Field(None, description="Admin overrides this ACL")
    active: Optional[bool] = Field(None, description="Whether active")
    script: Optional[str] = Field(None, description="Script condition")
    condition: Optional[str] = Field(None, description="Encoded query condition")
    description: Optional[str] = Field(None, description="Description")


class DeleteAclParams(BaseModel):
    """Parameters for deleting a ACL."""

    acl_id: str = Field(..., description="Acl sys_id (prefix with 'sys_id:'), or the exact name")


class AclResponse(BaseModel):
    """Response from ACL operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    acl_id: Optional[str] = Field(None, description="sys_id of the affected ACL")
    acl_name: Optional[str] = Field(None, description="Name of the affected ACL")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_security_acl record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "operation": _display(item.get("operation")),
        "type": _display(item.get("type")),
        "admin_overrides": item.get("admin_overrides") == "true",
        "active": item.get("active") == "true",
        "script": _display(item.get("script")),
        "condition": _display(item.get("condition")),
        "description": _display(item.get("description")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_acls(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListAclsParams,
) -> Dict[str, Any]:
    """List ACLs from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_security_acl"
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
        if params.operation:
            query_parts.append(f"operation={params.operation}")
        if params.type:
            query_parts.append(f"type={params.type}")
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
            "message": f"Found {len(items)} ACLs",
            "acls": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing ACLs: {e}")
        return {
            "success": False,
            "message": f"Error listing ACLs: {str(e)}",
            "acls": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_acl(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetAclParams,
) -> Dict[str, Any]:
    """Get a specific ACL from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.acl_id.startswith("sys_id:"):
            sys_id = params.acl_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_security_acl/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_security_acl"
            query_params["sysparm_query"] = f"name={params.acl_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"Acl not found: {params.acl_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"Acl not found: {params.acl_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found ACL: {item.get('name')}",
            "acl": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting ACL: {e}")
        return {"success": False, "message": f"Error getting ACL: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "operation", None)
    if value is not None:
        body["operation"] = value
    value = getattr(params, "type", None)
    if value is not None:
        body["type"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "condition", None)
    if value is not None:
        body["condition"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "admin_overrides", None)
    if value is not None:
        body["admin_overrides"] = str(value).lower()
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    return body


def create_acl(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateAclParams,
) -> AclResponse:
    """Create a new ACL in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_security_acl"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return AclResponse(success=False, message="Failed to create ACL")
        result = data["result"]
        return AclResponse(
            success=True,
            message=f"Created ACL: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            acl_id=result.get("sys_id"),
            acl_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating ACL: {e}")
        return AclResponse(success=False, message=f"Error creating ACL: {str(e)}")


def update_acl(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateAclParams,
) -> AclResponse:
    """Update an existing ACL in ServiceNow."""
    get_result = get_acl(config, auth_manager, GetAclParams(acl_id=params.acl_id))
    if not get_result["success"]:
        return AclResponse(success=False, message=get_result["message"])
    record = get_result["acl"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_security_acl/{sys_id}"
    body = _build_body(params)
    if not body:
        return AclResponse(
            success=True,
            message=f"No changes to update for ACL",
            acl_id=sys_id,
            acl_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return AclResponse(success=False, message=f"Failed to update ACL")
        result = data["result"]
        return AclResponse(
            success=True,
            message=f"Updated ACL",
            acl_id=result.get("sys_id"),
            acl_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating ACL: {e}")
        return AclResponse(success=False, message=f"Error updating ACL: {str(e)}")


def delete_acl(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteAclParams,
) -> AclResponse:
    """Delete a ACL from ServiceNow."""
    get_result = get_acl(config, auth_manager, GetAclParams(acl_id=params.acl_id))
    if not get_result["success"]:
        return AclResponse(success=False, message=get_result["message"])
    record = get_result["acl"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_security_acl/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return AclResponse(success=True, message=f"Deleted ACL", acl_id=sys_id, acl_name=name)
    except Exception as e:
        logger.error(f"Error deleting ACL: {e}")
        return AclResponse(success=False, message=f"Error deleting ACL: {str(e)}")
