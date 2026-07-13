"""
DbTable tools for the ServiceNow MCP server.

This module provides CRUD tools for tables (sys_db_object) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = (
    "sys_id,name,label,super_class,is_extendable,sys_scope,"
    "access,read_access,create_access,update_access,delete_access,ws_access,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


class ListDbTablesParams(BaseModel):
    """Parameters for listing tables."""

    limit: int = Field(10, description="Maximum number of tables to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Table name (internal)")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetDbTableParams(BaseModel):
    """Parameters for getting a table."""

    db_table_id: str = Field(..., description="DbTable sys_id (prefix with 'sys_id:'), or the exact name")


class CreateDbTableParams(BaseModel):
    """Parameters for creating a table.

    The Application Access flags default to what the ServiceNow UI sets when a table
    is created there. The Table API defaults them to false, which silently breaks the
    table for every non-admin user (admins bypass the check), so they are set here.
    """

    name: str = Field(..., description="Table name (internal)")
    label: Optional[str] = Field(None, description="Table label")
    super_class: Optional[str] = Field(None, description="Parent table sys_id (extends)")
    is_extendable: Optional[bool] = Field(None, description="Whether the table is extendable")
    sys_scope: Optional[str] = Field(None, description="Application scope sys_id")
    access: Optional[str] = Field("public", description="Application access: 'public' or 'package_private'")
    read_access: Optional[bool] = Field(True, description="Application access: Can read")
    create_access: Optional[bool] = Field(True, description="Application access: Can create")
    update_access: Optional[bool] = Field(True, description="Application access: Can update")
    delete_access: Optional[bool] = Field(False, description="Application access: Can delete")
    ws_access: Optional[bool] = Field(True, description="Allow access to this table via web services")


class UpdateDbTableParams(BaseModel):
    """Parameters for updating a table."""

    db_table_id: str = Field(..., description="DbTable sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Table name (internal)")
    label: Optional[str] = Field(None, description="Table label")
    super_class: Optional[str] = Field(None, description="Parent table sys_id (extends)")
    is_extendable: Optional[bool] = Field(None, description="Whether the table is extendable")
    sys_scope: Optional[str] = Field(None, description="Application scope sys_id")
    access: Optional[str] = Field(None, description="Application access: 'public' or 'package_private'")
    read_access: Optional[bool] = Field(None, description="Application access: Can read")
    create_access: Optional[bool] = Field(None, description="Application access: Can create")
    update_access: Optional[bool] = Field(None, description="Application access: Can update")
    delete_access: Optional[bool] = Field(None, description="Application access: Can delete")
    ws_access: Optional[bool] = Field(None, description="Allow access to this table via web services")


class DeleteDbTableParams(BaseModel):
    """Parameters for deleting a table."""

    db_table_id: str = Field(..., description="DbTable sys_id (prefix with 'sys_id:'), or the exact name")


class DbTableResponse(BaseModel):
    """Response from table operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    db_table_id: Optional[str] = Field(None, description="sys_id of the affected table")
    db_table_name: Optional[str] = Field(None, description="Name of the affected table")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_db_object record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "label": _display(item.get("label")),
        "super_class": _display(item.get("super_class")),
        "is_extendable": item.get("is_extendable") == "true",
        "sys_scope": _display(item.get("sys_scope")),
        "access": item.get("access"),
        "read_access": item.get("read_access") == "true",
        "create_access": item.get("create_access") == "true",
        "update_access": item.get("update_access") == "true",
        "delete_access": item.get("delete_access") == "true",
        "ws_access": item.get("ws_access") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_db_tables(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListDbTablesParams,
) -> Dict[str, Any]:
    """List tables from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_db_object"
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
            "message": f"Found {len(items)} tables",
            "db_tables": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return {
            "success": False,
            "message": f"Error listing tables: {str(e)}",
            "db_tables": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_db_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDbTableParams,
) -> Dict[str, Any]:
    """Get a specific table from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.db_table_id.startswith("sys_id:"):
            sys_id = params.db_table_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_db_object/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_db_object"
            query_params["sysparm_query"] = f"name={params.db_table_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"DbTable not found: {params.db_table_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"DbTable not found: {params.db_table_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found table: {item.get('name')}",
            "db_table": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting table: {e}")
        return {"success": False, "message": f"Error getting table: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "label", None)
    if value is not None:
        body["label"] = value
    value = getattr(params, "super_class", None)
    if value is not None:
        body["super_class"] = value
    value = getattr(params, "sys_scope", None)
    if value is not None:
        body["sys_scope"] = value
    value = getattr(params, "is_extendable", None)
    if value is not None:
        body["is_extendable"] = str(value).lower()
    value = getattr(params, "access", None)
    if value is not None:
        body["access"] = value
    for flag in ("read_access", "create_access", "update_access", "delete_access", "ws_access"):
        value = getattr(params, flag, None)
        if value is not None:
            body[flag] = str(value).lower()
    return body


def create_db_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateDbTableParams,
) -> DbTableResponse:
    """Create a new table in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_db_object"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DbTableResponse(success=False, message="Failed to create table")
        result = data["result"]
        return DbTableResponse(
            success=True,
            message=f"Created table: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            db_table_id=result.get("sys_id"),
            db_table_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return DbTableResponse(success=False, message=f"Error creating table: {str(e)}")


def update_db_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateDbTableParams,
) -> DbTableResponse:
    """Update an existing table in ServiceNow."""
    get_result = get_db_table(config, auth_manager, GetDbTableParams(db_table_id=params.db_table_id))
    if not get_result["success"]:
        return DbTableResponse(success=False, message=get_result["message"])
    record = get_result["db_table"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_db_object/{sys_id}"
    body = _build_body(params)
    if not body:
        return DbTableResponse(
            success=True,
            message=f"No changes to update for table",
            db_table_id=sys_id,
            db_table_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DbTableResponse(success=False, message=f"Failed to update table")
        result = data["result"]
        return DbTableResponse(
            success=True,
            message=f"Updated table",
            db_table_id=result.get("sys_id"),
            db_table_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating table: {e}")
        return DbTableResponse(success=False, message=f"Error updating table: {str(e)}")


def delete_db_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteDbTableParams,
) -> DbTableResponse:
    """Delete a table from ServiceNow."""
    get_result = get_db_table(config, auth_manager, GetDbTableParams(db_table_id=params.db_table_id))
    if not get_result["success"]:
        return DbTableResponse(success=False, message=get_result["message"])
    record = get_result["db_table"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_db_object/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return DbTableResponse(success=True, message=f"Deleted table", db_table_id=sys_id, db_table_name=name)
    except Exception as e:
        logger.error(f"Error deleting table: {e}")
        return DbTableResponse(success=False, message=f"Error deleting table: {str(e)}")
