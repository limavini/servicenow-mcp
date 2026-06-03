"""
DataPolicy tools for the ServiceNow MCP server.

This module provides CRUD tools for data policies (sys_data_policy2) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,short_description,model_table,active,reverse_if_false,enforce_ui,apply_import_set,conditions,description,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListDataPolicysParams(BaseModel):
    """Parameters for listing data policies."""

    limit: int = Field(10, description="Maximum number of data policies to return")
    offset: int = Field(0, description="Offset for pagination")
    model_table: Optional[str] = Field(None, description="Filter by Table the data policy applies to")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against short_description (LIKE)")


class GetDataPolicyParams(BaseModel):
    """Parameters for getting a data policy."""

    data_policy_id: str = Field(..., description="DataPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class CreateDataPolicyParams(BaseModel):
    """Parameters for creating a data policy."""

    model_table: Optional[str] = Field(None, description="Table the data policy applies to")
    short_description: str = Field(..., description="Short description (name)")
    active: bool = Field(True, description="Whether active")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse if condition false")
    enforce_ui: Optional[bool] = Field(None, description="Use as UI policy on client")
    apply_import_set: Optional[bool] = Field(None, description="Apply to import sets")
    conditions: Optional[str] = Field(None, description="Encoded query conditions")
    description: Optional[str] = Field(None, description="Description")


class UpdateDataPolicyParams(BaseModel):
    """Parameters for updating a data policy."""

    data_policy_id: str = Field(..., description="DataPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")
    model_table: Optional[str] = Field(None, description="Table the data policy applies to")
    short_description: Optional[str] = Field(None, description="Short description (name)")
    active: Optional[bool] = Field(None, description="Whether active")
    reverse_if_false: Optional[bool] = Field(None, description="Reverse if condition false")
    enforce_ui: Optional[bool] = Field(None, description="Use as UI policy on client")
    apply_import_set: Optional[bool] = Field(None, description="Apply to import sets")
    conditions: Optional[str] = Field(None, description="Encoded query conditions")
    description: Optional[str] = Field(None, description="Description")


class DeleteDataPolicyParams(BaseModel):
    """Parameters for deleting a data policy."""

    data_policy_id: str = Field(..., description="DataPolicy sys_id (prefix with 'sys_id:'), or the exact short_description")


class DataPolicyResponse(BaseModel):
    """Response from data policy operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    data_policy_id: Optional[str] = Field(None, description="sys_id of the affected data policy")
    data_policy_name: Optional[str] = Field(None, description="Name of the affected data policy")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_data_policy2 record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "short_description": item.get("short_description"),
        "model_table": _display(item.get("model_table")),
        "active": item.get("active") == "true",
        "reverse_if_false": item.get("reverse_if_false") == "true",
        "enforce_ui": item.get("enforce_ui") == "true",
        "apply_import_set": item.get("apply_import_set") == "true",
        "conditions": _display(item.get("conditions")),
        "description": _display(item.get("description")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_data_policies(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListDataPolicysParams,
) -> Dict[str, Any]:
    """List data policies from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_data_policy2"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.model_table:
            query_parts.append(f"model_table={params.model_table}")
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
            "message": f"Found {len(items)} data policies",
            "data_policies": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing data policies: {e}")
        return {
            "success": False,
            "message": f"Error listing data policies: {str(e)}",
            "data_policies": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_data_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDataPolicyParams,
) -> Dict[str, Any]:
    """Get a specific data policy from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.data_policy_id.startswith("sys_id:"):
            sys_id = params.data_policy_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_data_policy2/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_data_policy2"
            query_params["sysparm_query"] = f"short_description={params.data_policy_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"DataPolicy not found: {params.data_policy_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"DataPolicy not found: {params.data_policy_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found data policy: {item.get('short_description')}",
            "data_policy": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting data policy: {e}")
        return {"success": False, "message": f"Error getting data policy: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "model_table", None)
    if value is not None:
        body["model_table"] = value
    value = getattr(params, "short_description", None)
    if value is not None:
        body["short_description"] = value
    value = getattr(params, "conditions", None)
    if value is not None:
        body["conditions"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "reverse_if_false", None)
    if value is not None:
        body["reverse_if_false"] = str(value).lower()
    value = getattr(params, "enforce_ui", None)
    if value is not None:
        body["enforce_ui"] = str(value).lower()
    value = getattr(params, "apply_import_set", None)
    if value is not None:
        body["apply_import_set"] = str(value).lower()
    return body


def create_data_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateDataPolicyParams,
) -> DataPolicyResponse:
    """Create a new data policy in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_data_policy2"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DataPolicyResponse(success=False, message="Failed to create data policy")
        result = data["result"]
        return DataPolicyResponse(
            success=True,
            message=f"Created data policy: {result.get('short_description') if 'short_description' != 'sys_id' else result.get('sys_id')}",
            data_policy_id=result.get("sys_id"),
            data_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating data policy: {e}")
        return DataPolicyResponse(success=False, message=f"Error creating data policy: {str(e)}")


def update_data_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateDataPolicyParams,
) -> DataPolicyResponse:
    """Update an existing data policy in ServiceNow."""
    get_result = get_data_policy(config, auth_manager, GetDataPolicyParams(data_policy_id=params.data_policy_id))
    if not get_result["success"]:
        return DataPolicyResponse(success=False, message=get_result["message"])
    record = get_result["data_policy"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_data_policy2/{sys_id}"
    body = _build_body(params)
    if not body:
        return DataPolicyResponse(
            success=True,
            message=f"No changes to update for data policy",
            data_policy_id=sys_id,
            data_policy_name=record.get("short_description"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DataPolicyResponse(success=False, message=f"Failed to update data policy")
        result = data["result"]
        return DataPolicyResponse(
            success=True,
            message=f"Updated data policy",
            data_policy_id=result.get("sys_id"),
            data_policy_name=result.get("short_description") if "short_description" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating data policy: {e}")
        return DataPolicyResponse(success=False, message=f"Error updating data policy: {str(e)}")


def delete_data_policy(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteDataPolicyParams,
) -> DataPolicyResponse:
    """Delete a data policy from ServiceNow."""
    get_result = get_data_policy(config, auth_manager, GetDataPolicyParams(data_policy_id=params.data_policy_id))
    if not get_result["success"]:
        return DataPolicyResponse(success=False, message=get_result["message"])
    record = get_result["data_policy"]
    sys_id = record["sys_id"]
    name = record.get("short_description")

    url = f"{config.instance_url}/api/now/table/sys_data_policy2/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return DataPolicyResponse(success=True, message=f"Deleted data policy", data_policy_id=sys_id, data_policy_name=name)
    except Exception as e:
        logger.error(f"Error deleting data policy: {e}")
        return DataPolicyResponse(success=False, message=f"Error deleting data policy: {str(e)}")
