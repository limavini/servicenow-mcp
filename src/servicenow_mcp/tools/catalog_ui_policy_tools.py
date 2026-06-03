"""
CatalogUiPolicy tools for the ServiceNow MCP server.

This module provides CRUD tools for catalog UI policies (catalog_ui_policy) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,short_description,catalog_item,variable_set,active,order,on_load,reverse_if_false,applies_to,catalog_conditions,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListCatalogUiPolicysParams(BaseModel):
    """Parameters for listing catalog UI policies."""

    limit: int = Field(10, description="Maximum number of catalog UI policies to return")
    offset: int = Field(0, description="Offset for pagination")
    catalog_item: Optional[str] = Field(None, description="Filter by Catalog item sys_id")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against short_description (LIKE)")


class GetCatalogUiPolicyParams(BaseModel):
    """Parameters for getting a catalog UI policy."""

    catalog_ui_policy_id: str = Field(..., description="CatalogUiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class CreateCatalogUiPolicyParams(BaseModel):
    """Parameters for creating a catalog UI policy."""

    short_description: str = Field(..., description="Short description (name)")
    catalog_item: Optional[str] = Field(None, description="Catalog item sys_id")
    variable_set: Optional[str] = Field(None, description="Variable set sys_id")
    active: bool = Field(True, description="Whether active")
    order: Optional[int] = Field(None, description="Order")
    on_load: Optional[bool] = Field(None, description="Run on load")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse if false")
    applies_to: Optional[str] = Field(None, description="Applies to: item or set")
    catalog_conditions: Optional[str] = Field(None, description="Conditions")


class UpdateCatalogUiPolicyParams(BaseModel):
    """Parameters for updating a catalog UI policy."""

    catalog_ui_policy_id: str = Field(..., description="CatalogUiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")
    short_description: Optional[str] = Field(None, description="Short description (name)")
    catalog_item: Optional[str] = Field(None, description="Catalog item sys_id")
    variable_set: Optional[str] = Field(None, description="Variable set sys_id")
    active: Optional[bool] = Field(None, description="Whether active")
    order: Optional[int] = Field(None, description="Order")
    on_load: Optional[bool] = Field(None, description="Run on load")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse if false")
    applies_to: Optional[str] = Field(None, description="Applies to: item or set")
    catalog_conditions: Optional[str] = Field(None, description="Conditions")


class DeleteCatalogUiPolicyParams(BaseModel):
    """Parameters for deleting a catalog UI policy."""

    catalog_ui_policy_id: str = Field(..., description="CatalogUiPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class CatalogUiPolicyResponse(BaseModel):
    """Response from catalog UI policy operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    catalog_ui_policy_id: Optional[str] = Field(None, description="sys_id of the affected catalog UI policy")
    catalog_ui_policy_name: Optional[str] = Field(None, description="Name of the affected catalog UI policy")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw catalog_ui_policy record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "short_description": item.get("short_description"),
        "catalog_item": _display(item.get("catalog_item")),
        "variable_set": _display(item.get("variable_set")),
        "active": item.get("active") == "true",
        "order": _display(item.get("order")),
        "on_load": item.get("on_load") == "true",
        "reverse_if_false": item.get("reverse_if_false") == "true",
        "applies_to": _display(item.get("applies_to")),
        "catalog_conditions": _display(item.get("catalog_conditions")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_catalog_ui_policies(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCatalogUiPolicysParams,
) -> Dict[str, Any]:
    """List catalog UI policies from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/catalog_ui_policy"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.catalog_item:
            query_parts.append(f"catalog_item={params.catalog_item}")
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
        if params.query:
            query_parts.append(f"short_descriptionLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} catalog UI policies",
            "catalog_ui_policies": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing catalog UI policies: {e}")
        return {
            "success": False,
            "message": f"Error listing catalog UI policies: {str(e)}",
            "catalog_ui_policies": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_catalog_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCatalogUiPolicyParams,
) -> Dict[str, Any]:
    """Get a specific catalog UI policy from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.catalog_ui_policy_id.startswith("sys_id:"):
            sys_id = params.catalog_ui_policy_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/catalog_ui_policy/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/catalog_ui_policy"
            query_params["sysparm_query"] = f"short_description={params.catalog_ui_policy_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"CatalogUiPolicy not found: {params.catalog_ui_policy_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"CatalogUiPolicy not found: {params.catalog_ui_policy_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found catalog UI policy: {item.get('short_description')}",
            "catalog_ui_policy": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting catalog UI policy: {e}")
        return {"success": False, "message": f"Error getting catalog UI policy: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "short_description", None)
    if value is not None:
        body["short_description"] = value
    value = getattr(params, "catalog_item", None)
    if value is not None:
        body["catalog_item"] = value
    value = getattr(params, "variable_set", None)
    if value is not None:
        body["variable_set"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "applies_to", None)
    if value is not None:
        body["applies_to"] = value
    value = getattr(params, "catalog_conditions", None)
    if value is not None:
        body["catalog_conditions"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "on_load", None)
    if value is not None:
        body["on_load"] = str(value).lower()
    value = getattr(params, "reverse_if_false", None)
    if value is not None:
        body["reverse_if_false"] = str(value).lower()
    return body


def create_catalog_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateCatalogUiPolicyParams,
) -> CatalogUiPolicyResponse:
    """Create a new catalog UI policy in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/catalog_ui_policy"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogUiPolicyResponse(success=False, message="Failed to create catalog UI policy")
        result = data["result"]
        return CatalogUiPolicyResponse(
            success=True,
            message=f"Created catalog UI policy: {result.get('short_description') if 'short_description' != 'sys_id' else result.get('sys_id')}",
            catalog_ui_policy_id=result.get("sys_id"),
            catalog_ui_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating catalog UI policy: {e}")
        return CatalogUiPolicyResponse(success=False, message=f"Error creating catalog UI policy: {str(e)}")


def update_catalog_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateCatalogUiPolicyParams,
) -> CatalogUiPolicyResponse:
    """Update an existing catalog UI policy in ServiceNow."""
    get_result = get_catalog_ui_policy(config, auth_manager, GetCatalogUiPolicyParams(catalog_ui_policy_id=params.catalog_ui_policy_id))
    if not get_result["success"]:
        return CatalogUiPolicyResponse(success=False, message=get_result["message"])
    record = get_result["catalog_ui_policy"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/catalog_ui_policy/{sys_id}"
    body = _build_body(params)
    if not body:
        return CatalogUiPolicyResponse(
            success=True,
            message=f"No changes to update for catalog UI policy",
            catalog_ui_policy_id=sys_id,
            catalog_ui_policy_name=record.get("short_description"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return CatalogUiPolicyResponse(success=False, message=f"Failed to update catalog UI policy")
        result = data["result"]
        return CatalogUiPolicyResponse(
            success=True,
            message=f"Updated catalog UI policy",
            catalog_ui_policy_id=result.get("sys_id"),
            catalog_ui_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating catalog UI policy: {e}")
        return CatalogUiPolicyResponse(success=False, message=f"Error updating catalog UI policy: {str(e)}")


def delete_catalog_ui_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteCatalogUiPolicyParams,
) -> CatalogUiPolicyResponse:
    """Delete a catalog UI policy from ServiceNow."""
    get_result = get_catalog_ui_policy(config, auth_manager, GetCatalogUiPolicyParams(catalog_ui_policy_id=params.catalog_ui_policy_id))
    if not get_result["success"]:
        return CatalogUiPolicyResponse(success=False, message=get_result["message"])
    record = get_result["catalog_ui_policy"]
    sys_id = record["sys_id"]
    name = record.get("short_description")

    url = f"{config.instance_url}/api/now/table/catalog_ui_policy/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return CatalogUiPolicyResponse(success=True, message=f"Deleted catalog UI policy", catalog_ui_policy_id=sys_id, catalog_ui_policy_name=name)
    except Exception as e:
        logger.error(f"Error deleting catalog UI policy: {e}")
        return CatalogUiPolicyResponse(success=False, message=f"Error deleting catalog UI policy: {str(e)}")
