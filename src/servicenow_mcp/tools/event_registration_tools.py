"""
EventRegistration tools for the ServiceNow MCP server.

This module provides CRUD tools for event registrations (sysevent_register) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,event_name,table,description,queue,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListEventRegistrationsParams(BaseModel):
    """Parameters for listing event registrations."""

    limit: int = Field(10, description="Maximum number of event registrations to return")
    offset: int = Field(0, description="Offset for pagination")
    event_name: Optional[str] = Field(None, description="Filter by Event name")
    table: Optional[str] = Field(None, description="Filter by Table that fires the event")
    query: Optional[str] = Field(None, description="Search query matched against event_name (LIKE)")


class GetEventRegistrationParams(BaseModel):
    """Parameters for getting a event registration."""

    event_registration_id: str = Field(..., description="EventRegistration sys_id (prefix with 'sys_id:'), or the exact event_name")


class CreateEventRegistrationParams(BaseModel):
    """Parameters for creating a event registration."""

    event_name: str = Field(..., description="Event name")
    table: Optional[str] = Field(None, description="Table that fires the event")
    description: Optional[str] = Field(None, description="Description")
    queue: Optional[str] = Field(None, description="Queue")


class UpdateEventRegistrationParams(BaseModel):
    """Parameters for updating a event registration."""

    event_registration_id: str = Field(..., description="EventRegistration sys_id (prefix with 'sys_id:'), or the exact event_name")
    event_name: Optional[str] = Field(None, description="Event name")
    table: Optional[str] = Field(None, description="Table that fires the event")
    description: Optional[str] = Field(None, description="Description")
    queue: Optional[str] = Field(None, description="Queue")


class DeleteEventRegistrationParams(BaseModel):
    """Parameters for deleting a event registration."""

    event_registration_id: str = Field(..., description="EventRegistration sys_id (prefix with 'sys_id:'), or the exact event_name")


class EventRegistrationResponse(BaseModel):
    """Response from event registration operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    event_registration_id: Optional[str] = Field(None, description="sys_id of the affected event registration")
    event_registration_name: Optional[str] = Field(None, description="Name of the affected event registration")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sysevent_register record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "event_name": item.get("event_name"),
        "table": _display(item.get("table")),
        "description": _display(item.get("description")),
        "queue": _display(item.get("queue")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_event_registrations(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListEventRegistrationsParams,
) -> Dict[str, Any]:
    """List event registrations from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sysevent_register"
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        query_parts = []
        if params.event_name:
            query_parts.append(f"event_name={params.event_name}")
        if params.table:
            query_parts.append(f"table={params.table}")
        if params.query:
            query_parts.append(f"event_nameLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = [_serialize(i) for i in data.get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} event registrations",
            "event_registrations": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing event registrations: {e}")
        return {
            "success": False,
            "message": f"Error listing event registrations: {str(e)}",
            "event_registrations": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_event_registration(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetEventRegistrationParams,
) -> Dict[str, Any]:
    """Get a specific event registration from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.event_registration_id.startswith("sys_id:"):
            sys_id = params.event_registration_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sysevent_register/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sysevent_register"
            query_params["sysparm_query"] = f"event_name={params.event_registration_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"EventRegistration not found: {params.event_registration_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"EventRegistration not found: {params.event_registration_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found event registration: {item.get('event_name')}",
            "event_registration": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting event registration: {e}")
        return {"success": False, "message": f"Error getting event registration: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "event_name", None)
    if value is not None:
        body["event_name"] = value
    value = getattr(params, "table", None)
    if value is not None:
        body["table"] = value
    value = getattr(params, "description", None)
    if value is not None:
        body["description"] = value
    value = getattr(params, "queue", None)
    if value is not None:
        body["queue"] = value
    return body


def create_event_registration(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateEventRegistrationParams,
) -> EventRegistrationResponse:
    """Create a new event registration in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sysevent_register"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return EventRegistrationResponse(success=False, message="Failed to create event registration")
        result = data["result"]
        return EventRegistrationResponse(
            success=True,
            message=f"Created event registration: {result.get('event_name') if 'event_name' != 'sys_id' else result.get('sys_id')}",
            event_registration_id=result.get("sys_id"),
            event_registration_name=result.get("event_name") if "event_name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating event registration: {e}")
        return EventRegistrationResponse(success=False, message=f"Error creating event registration: {str(e)}")


def update_event_registration(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateEventRegistrationParams,
) -> EventRegistrationResponse:
    """Update an existing event registration in ServiceNow."""
    get_result = get_event_registration(config, auth_manager, GetEventRegistrationParams(event_registration_id=params.event_registration_id))
    if not get_result["success"]:
        return EventRegistrationResponse(success=False, message=get_result["message"])
    record = get_result["event_registration"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sysevent_register/{sys_id}"
    body = _build_body(params)
    if not body:
        return EventRegistrationResponse(
            success=True,
            message=f"No changes to update for event registration",
            event_registration_id=sys_id,
            event_registration_name=record.get("event_name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return EventRegistrationResponse(success=False, message=f"Failed to update event registration")
        result = data["result"]
        return EventRegistrationResponse(
            success=True,
            message=f"Updated event registration",
            event_registration_id=result.get("sys_id"),
            event_registration_name=result.get("event_name") if "event_name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating event registration: {e}")
        return EventRegistrationResponse(success=False, message=f"Error updating event registration: {str(e)}")


def delete_event_registration(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteEventRegistrationParams,
) -> EventRegistrationResponse:
    """Delete a event registration from ServiceNow."""
    get_result = get_event_registration(config, auth_manager, GetEventRegistrationParams(event_registration_id=params.event_registration_id))
    if not get_result["success"]:
        return EventRegistrationResponse(success=False, message=get_result["message"])
    record = get_result["event_registration"]
    sys_id = record["sys_id"]
    name = record.get("event_name")

    url = f"{config.instance_url}/api/now/table/sysevent_register/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return EventRegistrationResponse(success=True, message=f"Deleted event registration", event_registration_id=sys_id, event_registration_name=name)
    except Exception as e:
        logger.error(f"Error deleting event registration: {e}")
        return EventRegistrationResponse(success=False, message=f"Error deleting event registration: {str(e)}")
