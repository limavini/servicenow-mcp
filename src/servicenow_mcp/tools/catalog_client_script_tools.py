"""
CatalogClientScript tools for the ServiceNow MCP server.

This module provides CRUD tools for catalog client scripts (catalog_script_client) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,cat_item,variable_set,type,script,ui_type,active,applies_to,cat_variable,order,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


def _normalize_io(value: str) -> str:
    """Normalize a variable binding to ServiceNow's 'IO:<sys_id>' form.

    Passes through values that already start with 'IO:'. Wraps a bare
    sys_id (e.g. a 32-char sys_id) as 'IO:<sys_id>'. Empty values are
    returned unchanged.
    """
    if value is None:
        return value
    stripped = value.strip()
    if not stripped or stripped.startswith("IO:"):
        return stripped
    return f"IO:{stripped}"


class ListCatalogClientScriptsParams(BaseModel):
    """Parameters for listing catalog client scripts."""

    limit: int = Field(10, description="Maximum number of catalog client scripts to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Script name")
    cat_item: Optional[str] = Field(None, description="Filter by Catalog item sys_id")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetCatalogClientScriptParams(BaseModel):
    """Parameters for getting a catalog client script."""

    catalog_client_script_id: str = Field(..., description="CatalogClientScript sys_id (prefix with 'sys_id:'), or the exact name")


class CreateCatalogClientScriptParams(BaseModel):
    """Parameters for creating a catalog client script."""

    name: str = Field(..., description="Script name")
    cat_item: Optional[str] = Field(None, description="Catalog item sys_id")
    variable_set: Optional[str] = Field(None, description="Variable set sys_id")
    type: Optional[str] = Field(None, description="Type: onLoad, onChange, onSubmit")
    script: Optional[str] = Field(None, description="Client script")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    active: bool = Field(True, description="Whether active")
    applies_to: Optional[str] = Field(None, description="Applies to: item or set")
    cat_variable: Optional[str] = Field(None, description="Variable the script reacts to (onChange)")
    order: Optional[int] = Field(None, description="Order")


class UpdateCatalogClientScriptParams(BaseModel):
    """Parameters for updating a catalog client script."""

    catalog_client_script_id: str = Field(..., description="CatalogClientScript sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Script name")
    cat_item: Optional[str] = Field(None, description="Catalog item sys_id")
    variable_set: Optional[str] = Field(None, description="Variable set sys_id")
    type: Optional[str] = Field(None, description="Type: onLoad, onChange, onSubmit")
    script: Optional[str] = Field(None, description="Client script")
    ui_type: Optional[str] = Field(None, description="UI type: 0 Desktop, 1 Mobile/SP, 10 All")
    active: Optional[bool] = Field(None, description="Whether active")
    applies_to: Optional[str] = Field(None, description="Applies to: item or set")
    cat_variable: Optional[str] = Field(None, description="Variable the script reacts to (onChange)")
    order: Optional[int] = Field(None, description="Order")


class DeleteCatalogClientScriptParams(BaseModel):
    """Parameters for deleting a catalog client script."""

    catalog_client_script_id: str = Field(..., description="CatalogClientScript sys_id (prefix with 'sys_id:'), or the exact name")


class CatalogClientScriptResponse(BaseModel):
    """Response from catalog client script operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    catalog_client_script_id: Optional[str] = Field(None, description="sys_id of the affected catalog client script")
    catalog_client_script_name: Optional[str] = Field(None, description="Name of the affected catalog client script")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw catalog_script_client record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "cat_item": _display(item.get("cat_item")),
        "variable_set": _display(item.get("variable_set")),
        "type": _display(item.get("type")),
        "script": _display(item.get("script")),
        "ui_type": _display(item.get("ui_type")),
        "active": item.get("active") == "true",
        "applies_to": _display(item.get("applies_to")),
        "cat_variable": _display(item.get("cat_variable")),
        "order": _display(item.get("order")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_catalog_client_scripts(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCatalogClientScriptsParams,
) -> Dict[str, Any]:
    """List catalog client scripts from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/catalog_script_client"
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
        if params.cat_item:
            query_parts.append(f"cat_item={params.cat_item}")
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
            "message": f"Found {len(items)} catalog client scripts",
            "catalog_client_scripts": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing catalog client scripts: {e}")
        return {
            "success": False,
            "message": f"Error listing catalog client scripts: {str(e)}",
            "catalog_client_scripts": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_catalog_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCatalogClientScriptParams,
) -> Dict[str, Any]:
    """Get a specific catalog client script from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.catalog_client_script_id.startswith("sys_id:"):
            sys_id = params.catalog_client_script_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/catalog_script_client/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/catalog_script_client"
            query_params["sysparm_query"] = f"name={params.catalog_client_script_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"CatalogClientScript not found: {params.catalog_client_script_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"CatalogClientScript not found: {params.catalog_client_script_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found catalog client script: {item.get('name')}",
            "catalog_client_script": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting catalog client script: {e}")
        return {"success": False, "message": f"Error getting catalog client script: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "cat_item", None)
    if value is not None:
        body["cat_item"] = value
    value = getattr(params, "variable_set", None)
    if value is not None:
        body["variable_set"] = value
    value = getattr(params, "type", None)
    if value is not None:
        body["type"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "ui_type", None)
    if value is not None:
        body["ui_type"] = value
    value = getattr(params, "applies_to", None)
    if value is not None:
        body["applies_to"] = value
    value = getattr(params, "cat_variable", None)
    if value is not None:
        body["cat_variable"] = _normalize_io(value)
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    return body


def create_catalog_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateCatalogClientScriptParams,
) -> CatalogClientScriptResponse:
    """Create a new catalog client script in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/catalog_script_client"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogClientScriptResponse(success=False, message="Failed to create catalog client script")
        result = data["result"]
        return CatalogClientScriptResponse(
            success=True,
            message=f"Created catalog client script: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            catalog_client_script_id=result.get("sys_id"),
            catalog_client_script_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating catalog client script: {e}")
        return CatalogClientScriptResponse(success=False, message=f"Error creating catalog client script: {str(e)}")


def update_catalog_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateCatalogClientScriptParams,
) -> CatalogClientScriptResponse:
    """Update an existing catalog client script in ServiceNow."""
    get_result = get_catalog_client_script(config, auth_manager, GetCatalogClientScriptParams(catalog_client_script_id=params.catalog_client_script_id))
    if not get_result["success"]:
        return CatalogClientScriptResponse(success=False, message=get_result["message"])
    record = get_result["catalog_client_script"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/catalog_script_client/{sys_id}"
    body = _build_body(params)
    if not body:
        return CatalogClientScriptResponse(
            success=True,
            message=f"No changes to update for catalog client script",
            catalog_client_script_id=sys_id,
            catalog_client_script_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogClientScriptResponse(success=False, message=f"Failed to update catalog client script")
        result = data["result"]
        return CatalogClientScriptResponse(
            success=True,
            message=f"Updated catalog client script",
            catalog_client_script_id=result.get("sys_id"),
            catalog_client_script_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating catalog client script: {e}")
        return CatalogClientScriptResponse(success=False, message=f"Error updating catalog client script: {str(e)}")


def delete_catalog_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteCatalogClientScriptParams,
) -> CatalogClientScriptResponse:
    """Delete a catalog client script from ServiceNow."""
    get_result = get_catalog_client_script(config, auth_manager, GetCatalogClientScriptParams(catalog_client_script_id=params.catalog_client_script_id))
    if not get_result["success"]:
        return CatalogClientScriptResponse(success=False, message=get_result["message"])
    record = get_result["catalog_client_script"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/catalog_script_client/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return CatalogClientScriptResponse(success=True, message=f"Deleted catalog client script", catalog_client_script_id=sys_id, catalog_client_script_name=name)
    except Exception as e:
        logger.error(f"Error deleting catalog client script: {e}")
        return CatalogClientScriptResponse(success=False, message=f"Error deleting catalog client script: {str(e)}")
