"""
Workspace list tools for the ServiceNow MCP server.

This module provides tools for managing the lists shown in a Configurable
Workspace:

- ``sys_ux_list_category`` - a group of lists in the workspace list menu
- ``sys_ux_list``          - one list (title, table, columns, condition) inside a category

Both records belong to a workspace list *configuration*
(``sys_ux_list_configuration``), referenced by the ``configuration`` field. To add
a new process to an existing workspace, reuse that workspace's configuration
sys_id, create a category for the process, then create the lists under it.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_AUDIT = "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
_LIST_FIELDS = (
    "sys_id,title,table,columns,condition,fixed_query,order,active,view,roles,groups,"
    f"category,configuration,group_by_column,{_AUDIT}"
)
_CATEGORY_FIELDS = f"sys_id,title,description,order,active,configuration,{_AUDIT}"


def _dv(value):
    """Return a reference field's display value whether it came back as a dict
    (sysparm_display_value=all) or a plain string (sysparm_display_value=true
    with exclude_reference_link)."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _get_by_sys_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    table: str,
    record_id: str,
    fields: str,
) -> Dict[str, Any]:
    """Fetch a single record by sys_id (accepts an optional 'sys_id:' prefix)."""
    sys_id = record_id.replace("sys_id:", "")
    url = f"{config.instance_url}/api/now/table/{table}/{sys_id}"

    response = requests.get(
        url,
        params={
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": fields,
        },
        headers=auth_manager.get_headers(),
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    result = data.get("result")
    if isinstance(result, list):
        result = result[0] if result else None
    if not result:
        raise ValueError(f"{table} not found: {record_id}")
    return result


def _list_records(
    config: ServerConfig,
    auth_manager: AuthManager,
    table: str,
    fields: str,
    query: Optional[str],
    limit: int,
    offset: int,
) -> list:
    """Run a list query against a table and return the raw records."""
    query_params = {
        "sysparm_limit": limit,
        "sysparm_offset": offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": fields,
    }

    encoded = f"{query}^ORDERBYorder" if query else "ORDERBYorder"
    query_params["sysparm_query"] = encoded

    response = requests.get(
        f"{config.instance_url}/api/now/table/{table}",
        params=query_params,
        headers=auth_manager.get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("result", [])


class UxListResponse(BaseModel):
    """Response from workspace list operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    record_id: Optional[str] = Field(None, description="sys_id of the affected record")
    record_name: Optional[str] = Field(None, description="Title of the affected record")


# ---------------------------------------------------------------------------
# sys_ux_list_category
# ---------------------------------------------------------------------------


class ListUxListCategoriesParams(BaseModel):
    """Parameters for listing workspace list categories."""

    limit: int = Field(20, description="Maximum number of categories to return")
    offset: int = Field(0, description="Offset for pagination")
    configuration: Optional[str] = Field(
        None, description="Filter by workspace list configuration sys_id"
    )
    query: Optional[str] = Field(None, description="Search query matched against the title (LIKE)")


class GetUxListCategoryParams(BaseModel):
    """Parameters for getting a workspace list category."""

    category_id: str = Field(
        ..., description="sys_ux_list_category sys_id (optionally prefixed with 'sys_id:')"
    )


class CreateUxListCategoryParams(BaseModel):
    """Parameters for creating a workspace list category."""

    title: str = Field(..., description="Category title shown in the workspace list menu")
    configuration: str = Field(
        ..., description="Workspace list configuration sys_id (sys_ux_list_configuration)"
    )
    description: Optional[str] = Field(None, description="Category description")
    order: Optional[int] = Field(None, description="Order of the category in the list menu")
    active: Optional[bool] = Field(None, description="Whether the category is active")


class UpdateUxListCategoryParams(BaseModel):
    """Parameters for updating a workspace list category."""

    category_id: str = Field(
        ..., description="sys_ux_list_category sys_id (optionally prefixed with 'sys_id:')"
    )
    title: Optional[str] = Field(None, description="Category title")
    description: Optional[str] = Field(None, description="Category description")
    order: Optional[int] = Field(None, description="Order of the category in the list menu")
    active: Optional[bool] = Field(None, description="Whether the category is active")


class DeleteUxListCategoryParams(BaseModel):
    """Parameters for deleting a workspace list category."""

    category_id: str = Field(
        ..., description="sys_ux_list_category sys_id (optionally prefixed with 'sys_id:')"
    )


def _serialize_category(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "title": item.get("title"),
        "description": item.get("description"),
        "order": item.get("order"),
        "active": item.get("active") == "true",
        "configuration": _dv(item.get("configuration")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def _build_category_body(params: BaseModel) -> Dict[str, Any]:
    body: Dict[str, Any] = {}

    for attr in ("title", "description", "configuration"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    if getattr(params, "order", None) is not None:
        body["order"] = str(params.order)

    if getattr(params, "active", None) is not None:
        body["active"] = str(params.active).lower()

    return body


def list_ux_list_categories(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUxListCategoriesParams,
) -> Dict[str, Any]:
    """List workspace list categories (sys_ux_list_category) from ServiceNow."""
    try:
        query_parts = []
        if params.configuration:
            query_parts.append(f"configuration={params.configuration}")
        if params.query:
            query_parts.append(f"titleLIKE{params.query}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ux_list_category",
            _CATEGORY_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
        )
        categories = [_serialize_category(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(categories)} workspace list categories",
            "ux_list_categories": categories,
            "total": len(categories),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing workspace list categories: {e}")
        return {
            "success": False,
            "message": f"Error listing workspace list categories: {str(e)}",
            "ux_list_categories": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ux_list_category(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUxListCategoryParams,
) -> Dict[str, Any]:
    """Get a specific workspace list category (sys_ux_list_category)."""
    try:
        item = _get_by_sys_id(
            config, auth_manager, "sys_ux_list_category", params.category_id, _CATEGORY_FIELDS
        )
        return {
            "success": True,
            "message": f"Found workspace list category: {item.get('title')}",
            "ux_list_category": _serialize_category(item),
        }
    except Exception as e:
        logger.error(f"Error getting workspace list category: {e}")
        return {"success": False, "message": f"Error getting workspace list category: {str(e)}"}


def create_ux_list_category(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUxListCategoryParams,
) -> UxListResponse:
    """Create a workspace list category (sys_ux_list_category) in ServiceNow."""
    body = _build_category_body(params)

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ux_list_category",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        return UxListResponse(
            success=True,
            message=f"Created workspace list category: {params.title}",
            record_id=result.get("sys_id"),
            record_name=params.title,
        )
    except Exception as e:
        logger.error(f"Error creating workspace list category: {e}")
        return UxListResponse(
            success=False, message=f"Error creating workspace list category: {str(e)}"
        )


def update_ux_list_category(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUxListCategoryParams,
) -> UxListResponse:
    """Update a workspace list category (sys_ux_list_category) in ServiceNow."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ux_list_category", params.category_id, _CATEGORY_FIELDS
        )
        sys_id = record["sys_id"]
        body = _build_category_body(params)

        if not body:
            return UxListResponse(
                success=True,
                message=f"No changes to update for category: {record.get('title')}",
                record_id=sys_id,
                record_name=record.get("title"),
            )

        response = requests.patch(
            f"{config.instance_url}/api/now/table/sys_ux_list_category/{sys_id}",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        title = result.get("title") or record.get("title")
        return UxListResponse(
            success=True,
            message=f"Updated workspace list category: {title}",
            record_id=sys_id,
            record_name=title,
        )
    except Exception as e:
        logger.error(f"Error updating workspace list category: {e}")
        return UxListResponse(
            success=False, message=f"Error updating workspace list category: {str(e)}"
        )


def delete_ux_list_category(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUxListCategoryParams,
) -> UxListResponse:
    """Delete a workspace list category (sys_ux_list_category) from ServiceNow."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ux_list_category", params.category_id, _CATEGORY_FIELDS
        )
        sys_id = record["sys_id"]
        title = record.get("title") or sys_id

        response = requests.delete(
            f"{config.instance_url}/api/now/table/sys_ux_list_category/{sys_id}",
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return UxListResponse(
            success=True,
            message=f"Deleted workspace list category: {title}",
            record_id=sys_id,
            record_name=title,
        )
    except Exception as e:
        logger.error(f"Error deleting workspace list category: {e}")
        return UxListResponse(
            success=False, message=f"Error deleting workspace list category: {str(e)}"
        )


# ---------------------------------------------------------------------------
# sys_ux_list
# ---------------------------------------------------------------------------


class ListUxListsParams(BaseModel):
    """Parameters for listing workspace lists."""

    limit: int = Field(20, description="Maximum number of workspace lists to return")
    offset: int = Field(0, description="Offset for pagination")
    table: Optional[str] = Field(None, description="Filter by the table the list shows")
    category: Optional[str] = Field(None, description="Filter by category sys_id (sys_ux_list_category)")
    configuration: Optional[str] = Field(
        None, description="Filter by workspace list configuration sys_id"
    )


class GetUxListParams(BaseModel):
    """Parameters for getting a workspace list."""

    ux_list_id: str = Field(..., description="sys_ux_list sys_id (optionally prefixed with 'sys_id:')")


class CreateUxListParams(BaseModel):
    """Parameters for creating a workspace list."""

    title: str = Field(..., description="List title shown in the workspace (e.g. 'Assigned to me')")
    table: str = Field(..., description="Table the list shows records from")
    configuration: str = Field(
        ..., description="Workspace list configuration sys_id (sys_ux_list_configuration)"
    )
    category: str = Field(..., description="Category sys_id (sys_ux_list_category) the list belongs to")
    columns: Optional[str] = Field(
        None,
        description="Comma-separated columns shown in the list (e.g. 'number,short_description,state')",
    )
    condition: Optional[str] = Field(
        None, description="Encoded query applied to the list and editable by the user"
    )
    fixed_query: Optional[str] = Field(
        None, description="Encoded query always applied to the list (not editable by the user)"
    )
    order: Optional[int] = Field(None, description="Order of the list inside its category")
    active: Optional[bool] = Field(None, description="Whether the list is active")
    view: Optional[str] = Field(None, description="View used to render the list")
    roles: Optional[str] = Field(None, description="Comma-separated roles that can see the list")
    group_by_column: Optional[str] = Field(None, description="Column used to group the list")


class UpdateUxListParams(BaseModel):
    """Parameters for updating a workspace list."""

    ux_list_id: str = Field(..., description="sys_ux_list sys_id (optionally prefixed with 'sys_id:')")
    title: Optional[str] = Field(None, description="List title")
    table: Optional[str] = Field(None, description="Table the list shows records from")
    category: Optional[str] = Field(None, description="Category sys_id (sys_ux_list_category)")
    columns: Optional[str] = Field(None, description="Comma-separated columns shown in the list")
    condition: Optional[str] = Field(None, description="Encoded query applied to the list")
    fixed_query: Optional[str] = Field(None, description="Encoded query always applied to the list")
    order: Optional[int] = Field(None, description="Order of the list inside its category")
    active: Optional[bool] = Field(None, description="Whether the list is active")
    view: Optional[str] = Field(None, description="View used to render the list")
    roles: Optional[str] = Field(None, description="Comma-separated roles that can see the list")
    group_by_column: Optional[str] = Field(None, description="Column used to group the list")


class DeleteUxListParams(BaseModel):
    """Parameters for deleting a workspace list."""

    ux_list_id: str = Field(..., description="sys_ux_list sys_id (optionally prefixed with 'sys_id:')")


def _serialize_ux_list(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "title": item.get("title"),
        "table": item.get("table"),
        "columns": item.get("columns"),
        "condition": item.get("condition"),
        "fixed_query": item.get("fixed_query"),
        "order": item.get("order"),
        "active": item.get("active") == "true",
        "view": _dv(item.get("view")),
        "roles": item.get("roles"),
        "category": _dv(item.get("category")),
        "configuration": _dv(item.get("configuration")),
        "group_by_column": item.get("group_by_column"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def _build_ux_list_body(params: BaseModel) -> Dict[str, Any]:
    body: Dict[str, Any] = {}

    for attr in (
        "title",
        "table",
        "configuration",
        "category",
        "columns",
        "condition",
        "fixed_query",
        "view",
        "roles",
        "group_by_column",
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    if getattr(params, "order", None) is not None:
        body["order"] = str(params.order)

    if getattr(params, "active", None) is not None:
        body["active"] = str(params.active).lower()

    return body


def list_ux_lists(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUxListsParams,
) -> Dict[str, Any]:
    """List workspace lists (sys_ux_list) from ServiceNow."""
    try:
        query_parts = []
        if params.table:
            query_parts.append(f"table={params.table}")
        if params.category:
            query_parts.append(f"category={params.category}")
        if params.configuration:
            query_parts.append(f"configuration={params.configuration}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ux_list",
            _LIST_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
        )
        ux_lists = [_serialize_ux_list(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(ux_lists)} workspace lists",
            "ux_lists": ux_lists,
            "total": len(ux_lists),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing workspace lists: {e}")
        return {
            "success": False,
            "message": f"Error listing workspace lists: {str(e)}",
            "ux_lists": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ux_list(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUxListParams,
) -> Dict[str, Any]:
    """Get a specific workspace list (sys_ux_list) from ServiceNow."""
    try:
        item = _get_by_sys_id(config, auth_manager, "sys_ux_list", params.ux_list_id, _LIST_FIELDS)
        return {
            "success": True,
            "message": f"Found workspace list: {item.get('title')}",
            "ux_list": _serialize_ux_list(item),
        }
    except Exception as e:
        logger.error(f"Error getting workspace list: {e}")
        return {"success": False, "message": f"Error getting workspace list: {str(e)}"}


def create_ux_list(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUxListParams,
) -> UxListResponse:
    """Create a workspace list (sys_ux_list) in ServiceNow."""
    body = _build_ux_list_body(params)

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ux_list",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        return UxListResponse(
            success=True,
            message=f"Created workspace list: {params.title}",
            record_id=result.get("sys_id"),
            record_name=params.title,
        )
    except Exception as e:
        logger.error(f"Error creating workspace list: {e}")
        return UxListResponse(success=False, message=f"Error creating workspace list: {str(e)}")


def update_ux_list(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUxListParams,
) -> UxListResponse:
    """Update a workspace list (sys_ux_list) in ServiceNow."""
    try:
        record = _get_by_sys_id(config, auth_manager, "sys_ux_list", params.ux_list_id, _LIST_FIELDS)
        sys_id = record["sys_id"]
        body = _build_ux_list_body(params)

        if not body:
            return UxListResponse(
                success=True,
                message=f"No changes to update for workspace list: {record.get('title')}",
                record_id=sys_id,
                record_name=record.get("title"),
            )

        response = requests.patch(
            f"{config.instance_url}/api/now/table/sys_ux_list/{sys_id}",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        title = result.get("title") or record.get("title")
        return UxListResponse(
            success=True,
            message=f"Updated workspace list: {title}",
            record_id=sys_id,
            record_name=title,
        )
    except Exception as e:
        logger.error(f"Error updating workspace list: {e}")
        return UxListResponse(success=False, message=f"Error updating workspace list: {str(e)}")


def delete_ux_list(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUxListParams,
) -> UxListResponse:
    """Delete a workspace list (sys_ux_list) from ServiceNow."""
    try:
        record = _get_by_sys_id(config, auth_manager, "sys_ux_list", params.ux_list_id, _LIST_FIELDS)
        sys_id = record["sys_id"]
        title = record.get("title") or sys_id

        response = requests.delete(
            f"{config.instance_url}/api/now/table/sys_ux_list/{sys_id}",
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return UxListResponse(
            success=True,
            message=f"Deleted workspace list: {title}",
            record_id=sys_id,
            record_name=title,
        )
    except Exception as e:
        logger.error(f"Error deleting workspace list: {e}")
        return UxListResponse(success=False, message=f"Error deleting workspace list: {str(e)}")
