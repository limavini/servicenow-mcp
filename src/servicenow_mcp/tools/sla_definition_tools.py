"""
SlaDefinition tools for the ServiceNow MCP server.

This module provides CRUD tools for SLA definitions (contract_sla) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,collection,type,duration_type,duration,schedule,start_condition,stop_condition,active,description,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListSlaDefinitionsParams(BaseModel):
    """Parameters for listing SLA definitions."""

    limit: int = Field(10, description="Maximum number of SLA definitions to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by SLA name")
    collection: Optional[str] = Field(None, description="Filter by Table the SLA applies to")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetSlaDefinitionParams(BaseModel):
    """Parameters for getting a SLA definition."""

    sla_definition_id: str = Field(..., description="SlaDefinition sys_id (prefix with 'sys_id:'), or the exact name")


class CreateSlaDefinitionParams(BaseModel):
    """Parameters for creating a SLA definition."""

    name: str = Field(..., description="SLA name")
    collection: Optional[str] = Field(None, description="Table the SLA applies to")
    type: Optional[str] = Field(None, description="Type: SLA, OLA, Underpinning Contract")
    duration_type: Optional[str] = Field(None, description="Duration type")
    duration: Optional[str] = Field(None, description="Duration")
    schedule: Optional[str] = Field(None, description="Schedule sys_id")
    start_condition: Optional[str] = Field(None, description="Start condition")
    stop_condition: Optional[str] = Field(None, description="Stop condition")
    active: bool = Field(True, description="Whether active")
    description: Optional[str] = Field(None, description="Description")


class UpdateSlaDefinitionParams(BaseModel):
    """Parameters for updating a SLA definition."""

    sla_definition_id: str = Field(..., description="SlaDefinition sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="SLA name")
    collection: Optional[str] = Field(None, description="Table the SLA applies to")
    type: Optional[str] = Field(None, description="Type: SLA, OLA, Underpinning Contract")
    duration_type: Optional[str] = Field(None, description="Duration type")
    duration: Optional[str] = Field(None, description="Duration")
    schedule: Optional[str] = Field(None, description="Schedule sys_id")
    start_condition: Optional[str] = Field(None, description="Start condition")
    stop_condition: Optional[str] = Field(None, description="Stop condition")
    active: Optional[bool] = Field(None, description="Whether active")
    description: Optional[str] = Field(None, description="Description")


class DeleteSlaDefinitionParams(BaseModel):
    """Parameters for deleting a SLA definition."""

    sla_definition_id: str = Field(..., description="SlaDefinition sys_id (prefix with 'sys_id:'), or the exact name")


class SlaDefinitionResponse(BaseModel):
    """Response from SLA definition operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    sla_definition_id: Optional[str] = Field(None, description="sys_id of the affected SLA definition")
    sla_definition_name: Optional[str] = Field(None, description="Name of the affected SLA definition")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw contract_sla record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "collection": _display(item.get("collection")),
        "type": _display(item.get("type")),
        "duration_type": _display(item.get("duration_type")),
        "duration": _display(item.get("duration")),
        "schedule": _display(item.get("schedule")),
        "start_condition": _display(item.get("start_condition")),
        "stop_condition": _display(item.get("stop_condition")),
        "active": item.get("active") == "true",
        "description": _display(item.get("description")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_sla_definitions(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListSlaDefinitionsParams,
) -> Dict[str, Any]:
    """List SLA definitions from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/contract_sla"
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
            "message": f"Found {len(items)} SLA definitions",
            "sla_definitions": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing SLA definitions: {e}")
        return {
            "success": False,
            "message": f"Error listing SLA definitions: {str(e)}",
            "sla_definitions": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_sla_definition(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetSlaDefinitionParams,
) -> Dict[str, Any]:
    """Get a specific SLA definition from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.sla_definition_id.startswith("sys_id:"):
            sys_id = params.sla_definition_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/contract_sla/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/contract_sla"
            query_params["sysparm_query"] = f"name={params.sla_definition_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"SlaDefinition not found: {params.sla_definition_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"SlaDefinition not found: {params.sla_definition_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found SLA definition: {item.get('name')}",
            "sla_definition": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting SLA definition: {e}")
        return {"success": False, "message": f"Error getting SLA definition: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "collection", None)
    if value is not None:
        body["collection"] = value
    value = getattr(params, "type", None)
    if value is not None:
        body["type"] = value
    value = getattr(params, "duration_type", None)
    if value is not None:
        body["duration_type"] = value
    value = getattr(params, "duration", None)
    if value is not None:
        body["duration"] = value
    value = getattr(params, "schedule", None)
    if value is not None:
        body["schedule"] = value
    value = getattr(params, "start_condition", None)
    if value is not None:
        body["start_condition"] = value
    value = getattr(params, "stop_condition", None)
    if value is not None:
        body["stop_condition"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    return body


def create_sla_definition(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateSlaDefinitionParams,
) -> SlaDefinitionResponse:
    """Create a new SLA definition in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/contract_sla"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SlaDefinitionResponse(success=False, message="Failed to create SLA definition")
        result = data["result"]
        return SlaDefinitionResponse(
            success=True,
            message=f"Created SLA definition: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            sla_definition_id=result.get("sys_id"),
            sla_definition_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating SLA definition: {e}")
        return SlaDefinitionResponse(success=False, message=f"Error creating SLA definition: {str(e)}")


def update_sla_definition(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateSlaDefinitionParams,
) -> SlaDefinitionResponse:
    """Update an existing SLA definition in ServiceNow."""
    get_result = get_sla_definition(config, auth_manager, GetSlaDefinitionParams(sla_definition_id=params.sla_definition_id))
    if not get_result["success"]:
        return SlaDefinitionResponse(success=False, message=get_result["message"])
    record = get_result["sla_definition"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/contract_sla/{sys_id}"
    body = _build_body(params)
    if not body:
        return SlaDefinitionResponse(
            success=True,
            message=f"No changes to update for SLA definition",
            sla_definition_id=sys_id,
            sla_definition_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return SlaDefinitionResponse(success=False, message=f"Failed to update SLA definition")
        result = data["result"]
        return SlaDefinitionResponse(
            success=True,
            message=f"Updated SLA definition",
            sla_definition_id=result.get("sys_id"),
            sla_definition_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating SLA definition: {e}")
        return SlaDefinitionResponse(success=False, message=f"Error updating SLA definition: {str(e)}")


def delete_sla_definition(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteSlaDefinitionParams,
) -> SlaDefinitionResponse:
    """Delete a SLA definition from ServiceNow."""
    get_result = get_sla_definition(config, auth_manager, GetSlaDefinitionParams(sla_definition_id=params.sla_definition_id))
    if not get_result["success"]:
        return SlaDefinitionResponse(success=False, message=get_result["message"])
    record = get_result["sla_definition"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/contract_sla/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return SlaDefinitionResponse(success=True, message=f"Deleted SLA definition", sla_definition_id=sys_id, sla_definition_name=name)
    except Exception as e:
        logger.error(f"Error deleting SLA definition: {e}")
        return SlaDefinitionResponse(success=False, message=f"Error deleting SLA definition: {str(e)}")
