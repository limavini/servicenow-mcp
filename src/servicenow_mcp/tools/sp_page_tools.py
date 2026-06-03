"""
SpPage tools for the ServiceNow MCP server.

This module provides CRUD tools for Service Portal pages (sp_page) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,id,title,short_description,css,roles,public,internal,draft,category,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListSpPagesParams(BaseModel):
    """Parameters for listing Service Portal pages."""

    limit: int = Field(10, description="Maximum number of Service Portal pages to return")
    offset: int = Field(0, description="Offset for pagination")
    id: Optional[str] = Field(None, description="Filter by Page id (URL id)")
    query: Optional[str] = Field(None, description="Search query matched against id (LIKE)")


class GetSpPageParams(BaseModel):
    """Parameters for getting a Service Portal page."""

    sp_page_id: str = Field(..., description="SpPage sys_id (prefix with 'sys_id:'), or the exact id")


class CreateSpPageParams(BaseModel):
    """Parameters for creating a Service Portal page."""

    id: str = Field(..., description="Page id (URL id)")
    title: Optional[str] = Field(None, description="Page title")
    short_description: Optional[str] = Field(None, description="Short description")
    css: Optional[str] = Field(None, description="Page CSS")
    roles: Optional[str] = Field(None, description="Required roles")
    public: Optional[bool] = Field(None, description="Publicly accessible")
    internal: Optional[bool] = Field(None, description="Internal page")
    draft: Optional[bool] = Field(None, description="Draft")
    category: Optional[str] = Field(None, description="Category")


class UpdateSpPageParams(BaseModel):
    """Parameters for updating a Service Portal page."""

    sp_page_id: str = Field(..., description="SpPage sys_id (prefix with 'sys_id:'), or the exact id")
    id: Optional[str] = Field(None, description="Page id (URL id)")
    title: Optional[str] = Field(None, description="Page title")
    short_description: Optional[str] = Field(None, description="Short description")
    css: Optional[str] = Field(None, description="Page CSS")
    roles: Optional[str] = Field(None, description="Required roles")
    public: Optional[bool] = Field(None, description="Publicly accessible")
    internal: Optional[bool] = Field(None, description="Internal page")
    draft: Optional[bool] = Field(None, description="Draft")
    category: Optional[str] = Field(None, description="Category")


class DeleteSpPageParams(BaseModel):
    """Parameters for deleting a Service Portal page."""

    sp_page_id: str = Field(..., description="SpPage sys_id (prefix with 'sys_id:'), or the exact id")


class SpPageResponse(BaseModel):
    """Response from Service Portal page operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    sp_page_id: Optional[str] = Field(None, description="sys_id of the affected Service Portal page")
    sp_page_name: Optional[str] = Field(None, description="Name of the affected Service Portal page")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sp_page record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "id": item.get("id"),
        "title": _display(item.get("title")),
        "short_description": _display(item.get("short_description")),
        "css": _display(item.get("css")),
        "roles": _display(item.get("roles")),
        "public": item.get("public") == "true",
        "internal": item.get("internal") == "true",
        "draft": item.get("draft") == "true",
        "category": _display(item.get("category")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_sp_pages(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListSpPagesParams,
) -> Dict[str, Any]:
    """List Service Portal pages from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sp_page"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.id:
            query_parts.append(f"id={params.id}")
        if params.query:
            query_parts.append(f"idLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} Service Portal pages",
            "sp_pages": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing Service Portal pages: {e}")
        return {
            "success": False,
            "message": f"Error listing Service Portal pages: {str(e)}",
            "sp_pages": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_sp_page(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetSpPageParams,
) -> Dict[str, Any]:
    """Get a specific Service Portal page from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.sp_page_id.startswith("sys_id:"):
            sys_id = params.sp_page_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sp_page/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sp_page"
            query_params["sysparm_query"] = f"id={params.sp_page_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"SpPage not found: {params.sp_page_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"SpPage not found: {params.sp_page_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found Service Portal page: {item.get('id')}",
            "sp_page": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting Service Portal page: {e}")
        return {"success": False, "message": f"Error getting Service Portal page: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "id", None)
    if value is not None:
        body["id"] = value
    value = getattr(params, "title", None)
    if value is not None:
        body["title"] = value
    value = getattr(params, "short_description", None)
    if value is not None:
        body["short_description"] = value
    value = getattr(params, "css", None)
    if value is not None:
        body["css"] = value
    value = getattr(params, "roles", None)
    if value is not None:
        body["roles"] = value
    value = getattr(params, "category", None)
    if value is not None:
        body["category"] = value
    value = getattr(params, "public", None)
    if value is not None:
        body["public"] = str(value).lower()
    value = getattr(params, "internal", None)
    if value is not None:
        body["internal"] = str(value).lower()
    value = getattr(params, "draft", None)
    if value is not None:
        body["draft"] = str(value).lower()
    return body


def create_sp_page(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateSpPageParams,
) -> SpPageResponse:
    """Create a new Service Portal page in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sp_page"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SpPageResponse(success=False, message="Failed to create Service Portal page")
        result = data["result"]
        return SpPageResponse(
            success=True,
            message=f"Created Service Portal page: {result.get('id') if 'id' != 'sys_id' else result.get('sys_id')}",
            sp_page_id=result.get("sys_id"),
            sp_page_name=result.get("id") if "id" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating Service Portal page: {e}")
        return SpPageResponse(success=False, message=f"Error creating Service Portal page: {str(e)}")


def update_sp_page(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateSpPageParams,
) -> SpPageResponse:
    """Update an existing Service Portal page in ServiceNow."""
    get_result = get_sp_page(config, auth_manager, GetSpPageParams(sp_page_id=params.sp_page_id))
    if not get_result["success"]:
        return SpPageResponse(success=False, message=get_result["message"])
    record = get_result["sp_page"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sp_page/{sys_id}"
    body = _build_body(params)
    if not body:
        return SpPageResponse(
            success=True,
            message=f"No changes to update for Service Portal page",
            sp_page_id=sys_id,
            sp_page_name=record.get("id"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SpPageResponse(success=False, message=f"Failed to update Service Portal page")
        result = data["result"]
        return SpPageResponse(
            success=True,
            message=f"Updated Service Portal page",
            sp_page_id=result.get("sys_id"),
            sp_page_name=result.get("id") if "id" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating Service Portal page: {e}")
        return SpPageResponse(success=False, message=f"Error updating Service Portal page: {str(e)}")


def delete_sp_page(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteSpPageParams,
) -> SpPageResponse:
    """Delete a Service Portal page from ServiceNow."""
    get_result = get_sp_page(config, auth_manager, GetSpPageParams(sp_page_id=params.sp_page_id))
    if not get_result["success"]:
        return SpPageResponse(success=False, message=get_result["message"])
    record = get_result["sp_page"]
    sys_id = record["sys_id"]
    name = record.get("id")

    url = f"{config.instance_url}/api/now/table/sp_page/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return SpPageResponse(success=True, message=f"Deleted Service Portal page", sp_page_id=sys_id, sp_page_name=name)
    except Exception as e:
        logger.error(f"Error deleting Service Portal page: {e}")
        return SpPageResponse(success=False, message=f"Error deleting Service Portal page: {str(e)}")
