"""
DataPolicyRule tools for the ServiceNow MCP server.

This module provides CRUD tools for data policy rules (sys_data_policy_rule) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,sys_data_policy,table,field,mandatory,disabled,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListDataPolicyRulesParams(BaseModel):
    """Parameters for listing data policy rules."""

    limit: int = Field(10, description="Maximum number of data policy rules to return")
    offset: int = Field(0, description="Offset for pagination")
    sys_data_policy: Optional[str] = Field(None, description="Filter by Parent data policy sys_id")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetDataPolicyRuleParams(BaseModel):
    """Parameters for getting a data policy rule."""

    data_policy_rule_id: str = Field(..., description="DataPolicyRule sys_id (prefix with 'sys_id:')")


class CreateDataPolicyRuleParams(BaseModel):
    """Parameters for creating a data policy rule."""

    sys_data_policy: str = Field(..., description="Parent data policy sys_id")
    table: Optional[str] = Field(None, description="Table")
    field: str = Field(..., description="Field the rule targets")
    mandatory: Optional[bool] = Field(None, description="Mandatory")
    disabled: Optional[bool] = Field(None, description="Disabled")


class UpdateDataPolicyRuleParams(BaseModel):
    """Parameters for updating a data policy rule."""

    data_policy_rule_id: str = Field(..., description="DataPolicyRule sys_id (prefix with 'sys_id:')")
    sys_data_policy: Optional[str] = Field(None, description="Parent data policy sys_id")
    table: Optional[str] = Field(None, description="Table")
    field: Optional[str] = Field(None, description="Field the rule targets")
    mandatory: Optional[bool] = Field(None, description="Mandatory")
    disabled: Optional[bool] = Field(None, description="Disabled")


class DeleteDataPolicyRuleParams(BaseModel):
    """Parameters for deleting a data policy rule."""

    data_policy_rule_id: str = Field(..., description="DataPolicyRule sys_id (prefix with 'sys_id:')")


class DataPolicyRuleResponse(BaseModel):
    """Response from data policy rule operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    data_policy_rule_id: Optional[str] = Field(None, description="sys_id of the affected data policy rule")
    data_policy_rule_name: Optional[str] = Field(None, description="Name of the affected data policy rule")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_data_policy_rule record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "sys_data_policy": _display(item.get("sys_data_policy")),
        "table": _display(item.get("table")),
        "field": _display(item.get("field")),
        "mandatory": item.get("mandatory") == "true",
        "disabled": item.get("disabled") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_data_policy_rules(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListDataPolicyRulesParams,
) -> Dict[str, Any]:
    """List data policy rules from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_data_policy_rule"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.sys_data_policy:
            query_parts.append(f"sys_data_policy={params.sys_data_policy}")
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
            "message": f"Found {len(items)} data policy rules",
            "data_policy_rules": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing data policy rules: {e}")
        return {
            "success": False,
            "message": f"Error listing data policy rules: {str(e)}",
            "data_policy_rules": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_data_policy_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDataPolicyRuleParams,
) -> Dict[str, Any]:
    """Get a specific data policy rule from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.data_policy_rule_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_data_policy_rule/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"DataPolicyRule not found: {params.data_policy_rule_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"DataPolicyRule not found: {params.data_policy_rule_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found data policy rule: {item.get('name')}",
            "data_policy_rule": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting data policy rule: {e}")
        return {"success": False, "message": f"Error getting data policy rule: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "sys_data_policy", None)
    if value is not None:
        body["sys_data_policy"] = value
    value = getattr(params, "table", None)
    if value is not None:
        body["table"] = value
    value = getattr(params, "field", None)
    if value is not None:
        body["field"] = value
    value = getattr(params, "mandatory", None)
    if value is not None:
        body["mandatory"] = str(value).lower()
    value = getattr(params, "disabled", None)
    if value is not None:
        body["disabled"] = str(value).lower()
    return body


def create_data_policy_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateDataPolicyRuleParams,
) -> DataPolicyRuleResponse:
    """Create a new data policy rule in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_data_policy_rule"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DataPolicyRuleResponse(success=False, message="Failed to create data policy rule")
        result = data["result"]
        return DataPolicyRuleResponse(
            success=True,
            message=f"Created data policy rule: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            data_policy_rule_id=result.get("sys_id"),
            data_policy_rule_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating data policy rule: {e}")
        return DataPolicyRuleResponse(success=False, message=f"Error creating data policy rule: {str(e)}")


def update_data_policy_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateDataPolicyRuleParams,
) -> DataPolicyRuleResponse:
    """Update an existing data policy rule in ServiceNow."""
    get_result = get_data_policy_rule(config, auth_manager, GetDataPolicyRuleParams(data_policy_rule_id=params.data_policy_rule_id))
    if not get_result["success"]:
        return DataPolicyRuleResponse(success=False, message=get_result["message"])
    record = get_result["data_policy_rule"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_data_policy_rule/{sys_id}"
    body = _build_body(params)
    if not body:
        return DataPolicyRuleResponse(
            success=True,
            message=f"No changes to update for data policy rule",
            data_policy_rule_id=sys_id,
            data_policy_rule_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DataPolicyRuleResponse(success=False, message=f"Failed to update data policy rule")
        result = data["result"]
        return DataPolicyRuleResponse(
            success=True,
            message=f"Updated data policy rule",
            data_policy_rule_id=result.get("sys_id"),
            data_policy_rule_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating data policy rule: {e}")
        return DataPolicyRuleResponse(success=False, message=f"Error updating data policy rule: {str(e)}")


def delete_data_policy_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteDataPolicyRuleParams,
) -> DataPolicyRuleResponse:
    """Delete a data policy rule from ServiceNow."""
    get_result = get_data_policy_rule(config, auth_manager, GetDataPolicyRuleParams(data_policy_rule_id=params.data_policy_rule_id))
    if not get_result["success"]:
        return DataPolicyRuleResponse(success=False, message=get_result["message"])
    record = get_result["data_policy_rule"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_data_policy_rule/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return DataPolicyRuleResponse(success=True, message=f"Deleted data policy rule", data_policy_rule_id=sys_id, data_policy_rule_name=name)
    except Exception as e:
        logger.error(f"Error deleting data policy rule: {e}")
        return DataPolicyRuleResponse(success=False, message=f"Error deleting data policy rule: {str(e)}")
