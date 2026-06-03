"""
EmailNotification tools for the ServiceNow MCP server.

This module provides CRUD tools for email notifications (sysevent_email_action) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,collection,event_name,active,condition,subject,message_html,from,recipient_users,recipient_fields,weight,send_self,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListEmailNotificationsParams(BaseModel):
    """Parameters for listing email notifications."""

    limit: int = Field(10, description="Maximum number of email notifications to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Notification name")
    collection: Optional[str] = Field(None, description="Filter by Table the notification is for")
    event_name: Optional[str] = Field(None, description="Filter by Event that triggers it")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetEmailNotificationParams(BaseModel):
    """Parameters for getting a email notification."""

    email_notification_id: str = Field(..., description="EmailNotification sys_id (prefix with 'sys_id:'), or the exact name")


class CreateEmailNotificationParams(BaseModel):
    """Parameters for creating a email notification."""

    name: str = Field(..., description="Notification name")
    collection: Optional[str] = Field(None, description="Table the notification is for")
    event_name: Optional[str] = Field(None, description="Event that triggers it")
    active: bool = Field(True, description="Whether active")
    condition: Optional[str] = Field(None, description="Condition (encoded query)")
    subject: Optional[str] = Field(None, description="Email subject")
    message_html: Optional[str] = Field(None, description="HTML body")
    from_: Optional[str] = Field(None, alias="from", description="From address")
    recipient_users: Optional[str] = Field(None, description="Recipient users (sys_ids)")
    recipient_fields: Optional[str] = Field(None, description="Recipient fields")
    weight: Optional[int] = Field(None, description="Weight/order")
    send_self: Optional[bool] = Field(None, description="Send to event creator")

    class Config:
        populate_by_name = True


class UpdateEmailNotificationParams(BaseModel):
    """Parameters for updating a email notification."""

    email_notification_id: str = Field(..., description="EmailNotification sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Notification name")
    collection: Optional[str] = Field(None, description="Table the notification is for")
    event_name: Optional[str] = Field(None, description="Event that triggers it")
    active: Optional[bool] = Field(None, description="Whether active")
    condition: Optional[str] = Field(None, description="Condition (encoded query)")
    subject: Optional[str] = Field(None, description="Email subject")
    message_html: Optional[str] = Field(None, description="HTML body")
    from_: Optional[str] = Field(None, alias="from", description="From address")
    recipient_users: Optional[str] = Field(None, description="Recipient users (sys_ids)")
    recipient_fields: Optional[str] = Field(None, description="Recipient fields")
    weight: Optional[int] = Field(None, description="Weight/order")
    send_self: Optional[bool] = Field(None, description="Send to event creator")

    class Config:
        populate_by_name = True


class DeleteEmailNotificationParams(BaseModel):
    """Parameters for deleting a email notification."""

    email_notification_id: str = Field(..., description="EmailNotification sys_id (prefix with 'sys_id:'), or the exact name")


class EmailNotificationResponse(BaseModel):
    """Response from email notification operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    email_notification_id: Optional[str] = Field(None, description="sys_id of the affected email notification")
    email_notification_name: Optional[str] = Field(None, description="Name of the affected email notification")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sysevent_email_action record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "collection": _display(item.get("collection")),
        "event_name": _display(item.get("event_name")),
        "active": item.get("active") == "true",
        "condition": _display(item.get("condition")),
        "subject": _display(item.get("subject")),
        "message_html": _display(item.get("message_html")),
        "from": _display(item.get("from")),
        "recipient_users": _display(item.get("recipient_users")),
        "recipient_fields": _display(item.get("recipient_fields")),
        "weight": _display(item.get("weight")),
        "send_self": item.get("send_self") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_email_notifications(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListEmailNotificationsParams,
) -> Dict[str, Any]:
    """List email notifications from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sysevent_email_action"
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
        if params.event_name:
            query_parts.append(f"event_name={params.event_name}")
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
            "message": f"Found {len(items)} email notifications",
            "email_notifications": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing email notifications: {e}")
        return {
            "success": False,
            "message": f"Error listing email notifications: {str(e)}",
            "email_notifications": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_email_notification(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetEmailNotificationParams,
) -> Dict[str, Any]:
    """Get a specific email notification from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.email_notification_id.startswith("sys_id:"):
            sys_id = params.email_notification_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sysevent_email_action/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sysevent_email_action"
            query_params["sysparm_query"] = f"name={params.email_notification_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"EmailNotification not found: {params.email_notification_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"EmailNotification not found: {params.email_notification_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found email notification: {item.get('name')}",
            "email_notification": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting email notification: {e}")
        return {"success": False, "message": f"Error getting email notification: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "collection", None)
    if value is not None:
        body["collection"] = value
    value = getattr(params, "event_name", None)
    if value is not None:
        body["event_name"] = value
    value = getattr(params, "condition", None)
    if value is not None:
        body["condition"] = value
    value = getattr(params, "subject", None)
    if value is not None:
        body["subject"] = value
    value = getattr(params, "message_html", None)
    if value is not None:
        body["message_html"] = value
    value = getattr(params, "from_", None)
    if value is not None:
        body["from"] = value
    value = getattr(params, "recipient_users", None)
    if value is not None:
        body["recipient_users"] = value
    value = getattr(params, "recipient_fields", None)
    if value is not None:
        body["recipient_fields"] = value
    value = getattr(params, "weight", None)
    if value is not None:
        body["weight"] = str(value)
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "send_self", None)
    if value is not None:
        body["send_self"] = str(value).lower()
    return body


def create_email_notification(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateEmailNotificationParams,
) -> EmailNotificationResponse:
    """Create a new email notification in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sysevent_email_action"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return EmailNotificationResponse(success=False, message="Failed to create email notification")
        result = data["result"]
        return EmailNotificationResponse(
            success=True,
            message=f"Created email notification: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            email_notification_id=result.get("sys_id"),
            email_notification_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating email notification: {e}")
        return EmailNotificationResponse(success=False, message=f"Error creating email notification: {str(e)}")


def update_email_notification(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateEmailNotificationParams,
) -> EmailNotificationResponse:
    """Update an existing email notification in ServiceNow."""
    get_result = get_email_notification(config, auth_manager, GetEmailNotificationParams(email_notification_id=params.email_notification_id))
    if not get_result["success"]:
        return EmailNotificationResponse(success=False, message=get_result["message"])
    record = get_result["email_notification"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sysevent_email_action/{sys_id}"
    body = _build_body(params)
    if not body:
        return EmailNotificationResponse(
            success=True,
            message=f"No changes to update for email notification",
            email_notification_id=sys_id,
            email_notification_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return EmailNotificationResponse(success=False, message=f"Failed to update email notification")
        result = data["result"]
        return EmailNotificationResponse(
            success=True,
            message=f"Updated email notification",
            email_notification_id=result.get("sys_id"),
            email_notification_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating email notification: {e}")
        return EmailNotificationResponse(success=False, message=f"Error updating email notification: {str(e)}")


def delete_email_notification(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteEmailNotificationParams,
) -> EmailNotificationResponse:
    """Delete a email notification from ServiceNow."""
    get_result = get_email_notification(config, auth_manager, GetEmailNotificationParams(email_notification_id=params.email_notification_id))
    if not get_result["success"]:
        return EmailNotificationResponse(success=False, message=get_result["message"])
    record = get_result["email_notification"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sysevent_email_action/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return EmailNotificationResponse(success=True, message=f"Deleted email notification", email_notification_id=sys_id, email_notification_name=name)
    except Exception as e:
        logger.error(f"Error deleting email notification: {e}")
        return EmailNotificationResponse(success=False, message=f"Error deleting email notification: {str(e)}")
