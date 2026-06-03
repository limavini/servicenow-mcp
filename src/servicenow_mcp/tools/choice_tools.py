"""
Choice tools for the ServiceNow MCP server.

This module provides CRUD tools for choices (sys_choice) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,label,name,element,value,sequence,inactive,dependent_value,language,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListChoicesParams(BaseModel):
    """Parameters for listing choices."""

    limit: int = Field(10, description="Maximum number of choices to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Table the choice belongs to")
    element: Optional[str] = Field(None, description="Filter by Field the choice belongs to")
    query: Optional[str] = Field(None, description="Search query matched against label (LIKE)")


class GetChoiceParams(BaseModel):
    """Parameters for getting a choice."""

    choice_id: str = Field(..., description="Choice sys_id (prefix with 'sys_id:')")


class CreateChoiceParams(BaseModel):
    """Parameters for creating a choice."""

    name: str = Field(..., description="Table the choice belongs to")
    element: str = Field(..., description="Field the choice belongs to")
    value: str = Field(..., description="Stored value")
    label: str = Field(..., description="Display label")
    sequence: Optional[int] = Field(None, description="Order sequence")
    inactive: Optional[bool] = Field(None, description="Whether inactive")
    dependent_value: Optional[str] = Field(None, description="Dependent value")
    language: Optional[str] = Field(None, description="Language code")


class UpdateChoiceParams(BaseModel):
    """Parameters for updating a choice."""

    choice_id: str = Field(..., description="Choice sys_id (prefix with 'sys_id:')")
    name: Optional[str] = Field(None, description="Table the choice belongs to")
    element: Optional[str] = Field(None, description="Field the choice belongs to")
    value: Optional[str] = Field(None, description="Stored value")
    label: Optional[str] = Field(None, description="Display label")
    sequence: Optional[int] = Field(None, description="Order sequence")
    inactive: Optional[bool] = Field(None, description="Whether inactive")
    dependent_value: Optional[str] = Field(None, description="Dependent value")
    language: Optional[str] = Field(None, description="Language code")


class DeleteChoiceParams(BaseModel):
    """Parameters for deleting a choice."""

    choice_id: str = Field(..., description="Choice sys_id (prefix with 'sys_id:')")


class ChoiceResponse(BaseModel):
    """Response from choice operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    choice_id: Optional[str] = Field(None, description="sys_id of the affected choice")
    choice_name: Optional[str] = Field(None, description="Name of the affected choice")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_choice record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "label": item.get("label"),
        "name": _display(item.get("name")),
        "element": _display(item.get("element")),
        "value": _display(item.get("value")),
        "sequence": _display(item.get("sequence")),
        "inactive": item.get("inactive") == "true",
        "dependent_value": _display(item.get("dependent_value")),
        "language": _display(item.get("language")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_choices(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListChoicesParams,
) -> Dict[str, Any]:
    """List choices from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_choice"
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
        if params.element:
            query_parts.append(f"element={params.element}")
        if params.query:
            query_parts.append(f"labelLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} choices",
            "choices": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing choices: {e}")
        return {
            "success": False,
            "message": f"Error listing choices: {str(e)}",
            "choices": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_choice(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetChoiceParams,
) -> Dict[str, Any]:
    """Get a specific choice from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.choice_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_choice/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"Choice not found: {params.choice_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"Choice not found: {params.choice_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found choice: {item.get('label')}",
            "choice": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting choice: {e}")
        return {"success": False, "message": f"Error getting choice: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "element", None)
    if value is not None:
        body["element"] = value
    value = getattr(params, "value", None)
    if value is not None:
        body["value"] = value
    value = getattr(params, "label", None)
    if value is not None:
        body["label"] = value
    value = getattr(params, "sequence", None)
    if value is not None:
        body["sequence"] = str(value)
    value = getattr(params, "dependent_value", None)
    if value is not None:
        body["dependent_value"] = value
    value = getattr(params, "language", None)
    if value is not None:
        body["language"] = value
    value = getattr(params, "inactive", None)
    if value is not None:
        body["inactive"] = str(value).lower()
    return body


def create_choice(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateChoiceParams,
) -> ChoiceResponse:
    """Create a new choice in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_choice"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return ChoiceResponse(success=False, message="Failed to create choice")
        result = data["result"]
        return ChoiceResponse(
            success=True,
            message=f"Created choice: {result.get('label') if 'label' != 'sys_id' else result.get('sys_id')}",
            choice_id=result.get("sys_id"),
            choice_name=result.get("label") if "label" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating choice: {e}")
        return ChoiceResponse(success=False, message=f"Error creating choice: {str(e)}")


def update_choice(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateChoiceParams,
) -> ChoiceResponse:
    """Update an existing choice in ServiceNow."""
    get_result = get_choice(config, auth_manager, GetChoiceParams(choice_id=params.choice_id))
    if not get_result["success"]:
        return ChoiceResponse(success=False, message=get_result["message"])
    record = get_result["choice"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_choice/{sys_id}"
    body = _build_body(params)
    if not body:
        return ChoiceResponse(
            success=True,
            message=f"No changes to update for choice",
            choice_id=sys_id,
            choice_name=record.get("label"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return ChoiceResponse(success=False, message=f"Failed to update choice")
        result = data["result"]
        return ChoiceResponse(
            success=True,
            message=f"Updated choice",
            choice_id=result.get("sys_id"),
            choice_name=result.get("label") if "label" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating choice: {e}")
        return ChoiceResponse(success=False, message=f"Error updating choice: {str(e)}")


def delete_choice(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteChoiceParams,
) -> ChoiceResponse:
    """Delete a choice from ServiceNow."""
    get_result = get_choice(config, auth_manager, GetChoiceParams(choice_id=params.choice_id))
    if not get_result["success"]:
        return ChoiceResponse(success=False, message=get_result["message"])
    record = get_result["choice"]
    sys_id = record["sys_id"]
    name = record.get("label")

    url = f"{config.instance_url}/api/now/table/sys_choice/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return ChoiceResponse(success=True, message=f"Deleted choice", choice_id=sys_id, choice_name=name)
    except Exception as e:
        logger.error(f"Error deleting choice: {e}")
        return ChoiceResponse(success=False, message=f"Error deleting choice: {str(e)}")
