"""
BusinessRule tools for the ServiceNow MCP server.

This module provides CRUD tools for business rules (sys_script) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,collection,when,order,active,advanced,condition,filter_condition,script,action_insert,action_update,action_delete,action_query,description,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListBusinessRulesParams(BaseModel):
    """Parameters for listing business rules."""

    limit: int = Field(10, description="Maximum number of business rules to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Name of the business rule")
    collection: Optional[str] = Field(None, description="Filter by Table the business rule runs on")
    when: Optional[str] = Field(None, description="Filter by When it runs: before, after, async, display")
    active: Optional[bool] = Field(None, description="Filter by Whether the business rule is active")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetBusinessRuleParams(BaseModel):
    """Parameters for getting a business rule."""

    business_rule_id: str = Field(..., description="BusinessRule sys_id (prefix with 'sys_id:'), or the exact name")


class CreateBusinessRuleParams(BaseModel):
    """Parameters for creating a business rule."""

    name: str = Field(..., description="Name of the business rule")
    collection: str = Field(..., description="Table the business rule runs on")
    when: Optional[str] = Field(None, description="When it runs: before, after, async, display")
    order: Optional[int] = Field(None, description="Execution order")
    active: bool = Field(True, description="Whether the business rule is active")
    advanced: bool = Field(True, description="Whether advanced (script) mode is on")
    condition: Optional[str] = Field(None, description="Condition script")
    filter_condition: Optional[str] = Field(None, description="Encoded query condition")
    script: Optional[str] = Field(None, description="Server-side script")
    action_insert: Optional[bool] = Field(None, description="Run on insert")
    action_update: Optional[bool] = Field(None, description="Run on update")
    action_delete: Optional[bool] = Field(None, description="Run on delete")
    action_query: Optional[bool] = Field(None, description="Run on query")
    description: Optional[str] = Field(None, description="Description")


class UpdateBusinessRuleParams(BaseModel):
    """Parameters for updating a business rule."""

    business_rule_id: str = Field(..., description="BusinessRule sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Name of the business rule")
    collection: Optional[str] = Field(None, description="Table the business rule runs on")
    when: Optional[str] = Field(None, description="When it runs: before, after, async, display")
    order: Optional[int] = Field(None, description="Execution order")
    active: Optional[bool] = Field(None, description="Whether the business rule is active")
    advanced: Optional[bool] = Field(None, description="Whether advanced (script) mode is on")
    condition: Optional[str] = Field(None, description="Condition script")
    filter_condition: Optional[str] = Field(None, description="Encoded query condition")
    script: Optional[str] = Field(None, description="Server-side script")
    action_insert: Optional[bool] = Field(None, description="Run on insert")
    action_update: Optional[bool] = Field(None, description="Run on update")
    action_delete: Optional[bool] = Field(None, description="Run on delete")
    action_query: Optional[bool] = Field(None, description="Run on query")
    description: Optional[str] = Field(None, description="Description")


class DeleteBusinessRuleParams(BaseModel):
    """Parameters for deleting a business rule."""

    business_rule_id: str = Field(..., description="BusinessRule sys_id (prefix with 'sys_id:'), or the exact name")


class BusinessRuleResponse(BaseModel):
    """Response from business rule operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    business_rule_id: Optional[str] = Field(None, description="sys_id of the affected business rule")
    business_rule_name: Optional[str] = Field(None, description="Name of the affected business rule")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_script record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "collection": _display(item.get("collection")),
        "when": _display(item.get("when")),
        "order": _display(item.get("order")),
        "active": item.get("active") == "true",
        "advanced": item.get("advanced") == "true",
        "condition": _display(item.get("condition")),
        "filter_condition": _display(item.get("filter_condition")),
        "script": _display(item.get("script")),
        "action_insert": item.get("action_insert") == "true",
        "action_update": item.get("action_update") == "true",
        "action_delete": item.get("action_delete") == "true",
        "action_query": item.get("action_query") == "true",
        "description": _display(item.get("description")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_business_rules(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListBusinessRulesParams,
) -> Dict[str, Any]:
    """List business rules from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_script"
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
        if params.collection:
            query_parts.append(f"collection={params.collection}")
        if params.when:
            query_parts.append(f"when={params.when}")
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
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
            "message": f"Found {len(items)} business rules",
            "business_rules": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing business rules: {e}")
        return {
            "success": False,
            "message": f"Error listing business rules: {str(e)}",
            "business_rules": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_business_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetBusinessRuleParams,
) -> Dict[str, Any]:
    """Get a specific business rule from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.business_rule_id.startswith("sys_id:"):
            sys_id = params.business_rule_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_script/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_script"
            query_params["sysparm_query"] = f"name={params.business_rule_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"BusinessRule not found: {params.business_rule_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"BusinessRule not found: {params.business_rule_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found business rule: {item.get('name')}",
            "business_rule": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting business rule: {e}")
        return {"success": False, "message": f"Error getting business rule: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "collection", None)
    if value is not None:
        body["collection"] = value
    value = getattr(params, "when", None)
    if value is not None:
        body["when"] = value
    value = getattr(params, "order", None)
    if value is not None:
        body["order"] = str(value)
    value = getattr(params, "condition", None)
    if value is not None:
        body["condition"] = value
    value = getattr(params, "filter_condition", None)
    if value is not None:
        body["filter_condition"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "advanced", None)
    if value is not None:
        body["advanced"] = str(value).lower()
    value = getattr(params, "action_insert", None)
    if value is not None:
        body["action_insert"] = str(value).lower()
    value = getattr(params, "action_update", None)
    if value is not None:
        body["action_update"] = str(value).lower()
    value = getattr(params, "action_delete", None)
    if value is not None:
        body["action_delete"] = str(value).lower()
    value = getattr(params, "action_query", None)
    if value is not None:
        body["action_query"] = str(value).lower()
    return body


def create_business_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateBusinessRuleParams,
) -> BusinessRuleResponse:
    """Create a new business rule in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_script"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return BusinessRuleResponse(success=False, message="Failed to create business rule")
        result = data["result"]
        return BusinessRuleResponse(
            success=True,
            message=f"Created business rule: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            business_rule_id=result.get("sys_id"),
            business_rule_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating business rule: {e}")
        return BusinessRuleResponse(success=False, message=f"Error creating business rule: {str(e)}")


def update_business_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateBusinessRuleParams,
) -> BusinessRuleResponse:
    """Update an existing business rule in ServiceNow."""
    get_result = get_business_rule(config, auth_manager, GetBusinessRuleParams(business_rule_id=params.business_rule_id))
    if not get_result["success"]:
        return BusinessRuleResponse(success=False, message=get_result["message"])
    record = get_result["business_rule"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_script/{sys_id}"
    body = _build_body(params)
    if not body:
        return BusinessRuleResponse(
            success=True,
            message=f"No changes to update for business rule",
            business_rule_id=sys_id,
            business_rule_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return BusinessRuleResponse(success=False, message=f"Failed to update business rule")
        result = data["result"]
        return BusinessRuleResponse(
            success=True,
            message=f"Updated business rule",
            business_rule_id=result.get("sys_id"),
            business_rule_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating business rule: {e}")
        return BusinessRuleResponse(success=False, message=f"Error updating business rule: {str(e)}")


def delete_business_rule(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteBusinessRuleParams,
) -> BusinessRuleResponse:
    """Delete a business rule from ServiceNow."""
    get_result = get_business_rule(config, auth_manager, GetBusinessRuleParams(business_rule_id=params.business_rule_id))
    if not get_result["success"]:
        return BusinessRuleResponse(success=False, message=get_result["message"])
    record = get_result["business_rule"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_script/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BusinessRuleResponse(success=True, message=f"Deleted business rule", business_rule_id=sys_id, business_rule_name=name)
    except Exception as e:
        logger.error(f"Error deleting business rule: {e}")
        return BusinessRuleResponse(success=False, message=f"Error deleting business rule: {str(e)}")
