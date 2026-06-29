"""
io_set_item tools for the ServiceNow MCP server.

This module provides tools for managing io_set_item records in ServiceNow. The
io_set_item table is the many-to-many link between a catalog item / record
producer (sc_cat_item) and a variable set (item_option_new_set). Creating a
record here attaches an existing shared variable set to a catalog item or
record producer.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,sc_cat_item,variable_set,order,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


def _dv(value):
    """Return a reference field's display value whether it came back as a dict
    (sysparm_display_value=all) or a plain string (sysparm_display_value=true
    with exclude_reference_link)."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


class ListIoSetItemsParams(BaseModel):
    """Parameters for listing io_set_item records."""

    limit: int = Field(10, description="Maximum number of io_set_item records to return")
    offset: int = Field(0, description="Offset for pagination")
    sc_cat_item: Optional[str] = Field(
        None, description="Filter by catalog item / record producer sys_id (sc_cat_item)"
    )
    variable_set: Optional[str] = Field(
        None, description="Filter by variable set sys_id (item_option_new_set)"
    )


class GetIoSetItemParams(BaseModel):
    """Parameters for getting an io_set_item record."""

    io_set_item_id: str = Field(
        ...,
        description="io_set_item sys_id (optionally prefixed with 'sys_id:')",
    )


class CreateIoSetItemParams(BaseModel):
    """Parameters for creating an io_set_item record."""

    sc_cat_item: str = Field(
        ..., description="Catalog item / record producer sys_id (sc_cat_item)"
    )
    variable_set: str = Field(
        ..., description="Variable set sys_id (item_option_new_set)"
    )
    order: Optional[int] = Field(
        None, description="Display order of the variable set on the item"
    )


class UpdateIoSetItemParams(BaseModel):
    """Parameters for updating an io_set_item record."""

    io_set_item_id: str = Field(
        ..., description="io_set_item sys_id (optionally prefixed with 'sys_id:')"
    )
    sc_cat_item: Optional[str] = Field(
        None, description="Catalog item / record producer sys_id (sc_cat_item)"
    )
    variable_set: Optional[str] = Field(
        None, description="Variable set sys_id (item_option_new_set)"
    )
    order: Optional[int] = Field(
        None, description="Display order of the variable set on the item"
    )


class DeleteIoSetItemParams(BaseModel):
    """Parameters for deleting an io_set_item record."""

    io_set_item_id: str = Field(
        ..., description="io_set_item sys_id (optionally prefixed with 'sys_id:')"
    )


class IoSetItemResponse(BaseModel):
    """Response from io_set_item operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    io_set_item_id: Optional[str] = Field(
        None, description="sys_id of the affected io_set_item record"
    )
    io_set_item_name: Optional[str] = Field(
        None, description="Composed label of the affected io_set_item record"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw io_set_item record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "sc_cat_item": _dv(item.get("sc_cat_item")),
        "variable_set": _dv(item.get("variable_set")),
        "order": item.get("order"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _dv(item.get("sys_created_by")),
        "updated_by": _dv(item.get("sys_updated_by")),
    }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}

    for attr in ("sc_cat_item", "variable_set"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    if getattr(params, "order", None) is not None:
        body["order"] = str(params.order)

    return body


def list_io_set_items(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListIoSetItemsParams,
) -> Dict[str, Any]:
    """List io_set_item records from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of io_set_item records.
    """
    try:
        url = f"{config.instance_url}/api/now/table/io_set_item"

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        query_parts = []
        if params.sc_cat_item:
            query_parts.append(f"sc_cat_item={params.sc_cat_item}")
        if params.variable_set:
            query_parts.append(f"variable_set={params.variable_set}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        io_set_items = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(io_set_items)} io_set_item records",
            "io_set_items": io_set_items,
            "total": len(io_set_items),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing io_set_item records: {e}")
        return {
            "success": False,
            "message": f"Error listing io_set_item records: {str(e)}",
            "io_set_items": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_io_set_item(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetIoSetItemParams,
) -> Dict[str, Any]:
    """Get a specific io_set_item record from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the io_set_item data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        # There is no meaningful "name" column on this M2M table, so resolve by
        # sys_id only. A leading 'sys_id:' prefix is stripped; any other string
        # is treated as a sys_id equality query.
        if params.io_set_item_id.startswith("sys_id:"):
            sys_id = params.io_set_item_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/io_set_item/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/io_set_item"
            query_params["sysparm_query"] = f"sys_id={params.io_set_item_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"io_set_item not found: {params.io_set_item_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"io_set_item not found: {params.io_set_item_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found io_set_item: {item.get('sys_id')}",
            "io_set_item": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting io_set_item: {e}")
        return {
            "success": False,
            "message": f"Error getting io_set_item: {str(e)}",
        }


def create_io_set_item(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateIoSetItemParams,
) -> IoSetItemResponse:
    """Create a new io_set_item record in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    url = f"{config.instance_url}/api/now/table/io_set_item"
    body = _build_body(params)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return IoSetItemResponse(
                success=False,
                message="Failed to create io_set_item",
            )

        result = data["result"]
        sys_id = result.get("sys_id")
        label = f"{params.sc_cat_item} / {params.variable_set}"
        return IoSetItemResponse(
            success=True,
            message=f"Created io_set_item: {label}",
            io_set_item_id=sys_id,
            io_set_item_name=label,
        )

    except Exception as e:
        logger.error(f"Error creating io_set_item: {e}")
        return IoSetItemResponse(
            success=False,
            message=f"Error creating io_set_item: {str(e)}",
        )


def update_io_set_item(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateIoSetItemParams,
) -> IoSetItemResponse:
    """Update an existing io_set_item record in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetIoSetItemParams(io_set_item_id=params.io_set_item_id)
    get_result = get_io_set_item(config, auth_manager, get_params)

    if not get_result["success"]:
        return IoSetItemResponse(success=False, message=get_result["message"])

    io_set_item = get_result["io_set_item"]
    sys_id = io_set_item["sys_id"]

    url = f"{config.instance_url}/api/now/table/io_set_item/{sys_id}"
    body = _build_body(params)

    if not body:
        return IoSetItemResponse(
            success=True,
            message=f"No changes to update for io_set_item: {sys_id}",
            io_set_item_id=sys_id,
            io_set_item_name=sys_id,
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return IoSetItemResponse(
                success=False,
                message=f"Failed to update io_set_item: {sys_id}",
            )

        result = data["result"]
        new_sys_id = result.get("sys_id")
        label = f"{_dv(result.get('sc_cat_item'))} / {_dv(result.get('variable_set'))}"
        return IoSetItemResponse(
            success=True,
            message=f"Updated io_set_item: {new_sys_id}",
            io_set_item_id=new_sys_id,
            io_set_item_name=label,
        )

    except Exception as e:
        logger.error(f"Error updating io_set_item: {e}")
        return IoSetItemResponse(
            success=False,
            message=f"Error updating io_set_item: {str(e)}",
        )


def delete_io_set_item(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteIoSetItemParams,
) -> IoSetItemResponse:
    """Delete an io_set_item record from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetIoSetItemParams(io_set_item_id=params.io_set_item_id)
    get_result = get_io_set_item(config, auth_manager, get_params)

    if not get_result["success"]:
        return IoSetItemResponse(success=False, message=get_result["message"])

    io_set_item = get_result["io_set_item"]
    sys_id = io_set_item["sys_id"]

    url = f"{config.instance_url}/api/now/table/io_set_item/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return IoSetItemResponse(
            success=True,
            message=f"Deleted io_set_item: {sys_id}",
            io_set_item_id=sys_id,
            io_set_item_name=sys_id,
        )

    except Exception as e:
        logger.error(f"Error deleting io_set_item: {e}")
        return IoSetItemResponse(
            success=False,
            message=f"Error deleting io_set_item: {str(e)}",
        )
