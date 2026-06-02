"""
Service Portal Widget tools for the ServiceNow MCP server.

This module provides tools for managing Service Portal widgets (sp_widget) in
ServiceNow. A widget bundles an HTML template, CSS, a server-side script, a
client controller and an option schema, and is rendered inside Service Portal
pages (e.g. the "Standard Ticket Header" widget).
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,id,name,description,template,css,script,client_script,link,"
    "option_schema,demo_data,controller_as,field_list,data_table,docs,"
    "public,has_preview,servicenow,roles,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


class ListSpWidgetsParams(BaseModel):
    """Parameters for listing Service Portal widgets."""

    limit: int = Field(10, description="Maximum number of widgets to return")
    offset: int = Field(0, description="Offset for pagination")
    public: Optional[bool] = Field(None, description="Filter by public (unauthenticated) access")
    query: Optional[str] = Field(
        None, description="Search query matched against the widget name and id (LIKE)"
    )


class GetSpWidgetParams(BaseModel):
    """Parameters for getting a Service Portal widget."""

    widget_id: str = Field(
        ...,
        description=(
            "Widget sys_id (prefix with 'sys_id:'), or the widget id "
            "(e.g. 'standard_ticket_header'), or the exact widget name"
        ),
    )


class CreateSpWidgetParams(BaseModel):
    """Parameters for creating a Service Portal widget."""

    id: str = Field(..., description="Unique widget id (e.g. 'my_custom_widget')")
    name: str = Field(..., description="Human-readable name of the widget")
    template: Optional[str] = Field(None, description="HTML template (AngularJS)")
    css: Optional[str] = Field(None, description="CSS / SCSS styles for the widget")
    script: Optional[str] = Field(None, description="Server-side script (server controller)")
    client_script: Optional[str] = Field(None, description="Client-side controller script")
    link: Optional[str] = Field(None, description="Link function (directive link)")
    option_schema: Optional[str] = Field(None, description="Option schema JSON")
    demo_data: Optional[str] = Field(None, description="Demo data JSON")
    controller_as: Optional[str] = Field(None, description="Controller alias (default 'c')")
    field_list: Optional[str] = Field(None, description="Comma-separated field list")
    data_table: Optional[str] = Field(None, description="Data table the widget operates on")
    docs: Optional[str] = Field(None, description="Documentation for the widget")
    description: Optional[str] = Field(None, description="Description of the widget")
    public: Optional[bool] = Field(None, description="Whether the widget is publicly accessible")
    has_preview: Optional[bool] = Field(None, description="Whether the widget has a preview")


class UpdateSpWidgetParams(BaseModel):
    """Parameters for updating a Service Portal widget."""

    widget_id: str = Field(
        ...,
        description=(
            "Widget sys_id (prefix with 'sys_id:'), or the widget id, or the exact name"
        ),
    )
    name: Optional[str] = Field(None, description="Human-readable name of the widget")
    template: Optional[str] = Field(None, description="HTML template (AngularJS)")
    css: Optional[str] = Field(None, description="CSS / SCSS styles for the widget")
    script: Optional[str] = Field(None, description="Server-side script (server controller)")
    client_script: Optional[str] = Field(None, description="Client-side controller script")
    link: Optional[str] = Field(None, description="Link function (directive link)")
    option_schema: Optional[str] = Field(None, description="Option schema JSON")
    demo_data: Optional[str] = Field(None, description="Demo data JSON")
    controller_as: Optional[str] = Field(None, description="Controller alias (default 'c')")
    field_list: Optional[str] = Field(None, description="Comma-separated field list")
    data_table: Optional[str] = Field(None, description="Data table the widget operates on")
    docs: Optional[str] = Field(None, description="Documentation for the widget")
    description: Optional[str] = Field(None, description="Description of the widget")
    public: Optional[bool] = Field(None, description="Whether the widget is publicly accessible")
    has_preview: Optional[bool] = Field(None, description="Whether the widget has a preview")


class DeleteSpWidgetParams(BaseModel):
    """Parameters for deleting a Service Portal widget."""

    widget_id: str = Field(
        ...,
        description="Widget sys_id (prefix with 'sys_id:'), or the widget id, or the exact name",
    )


class SpWidgetResponse(BaseModel):
    """Response from Service Portal widget operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    sp_widget_id: Optional[str] = Field(None, description="sys_id of the affected widget")
    sp_widget_name: Optional[str] = Field(None, description="Name of the affected widget")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sp_widget record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "id": item.get("id"),
        "name": item.get("name"),
        "description": item.get("description"),
        "template": item.get("template"),
        "css": item.get("css"),
        "script": item.get("script"),
        "client_script": item.get("client_script"),
        "link": item.get("link"),
        "option_schema": item.get("option_schema"),
        "demo_data": item.get("demo_data"),
        "controller_as": item.get("controller_as"),
        "field_list": item.get("field_list"),
        "data_table": item.get("data_table"),
        "docs": item.get("docs"),
        "public": item.get("public") == "true",
        "has_preview": item.get("has_preview") == "true",
        "servicenow": item.get("servicenow") == "true",
        "roles": item.get("roles"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_sp_widgets(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListSpWidgetsParams,
) -> Dict[str, Any]:
    """List Service Portal widgets from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of widgets.
    """
    try:
        url = f"{config.instance_url}/api/now/table/sp_widget"

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        query_parts = []
        if params.public is not None:
            query_parts.append(f"public={str(params.public).lower()}")
        if params.query:
            query_parts.append(f"nameLIKE{params.query}^ORidLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        widgets = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(widgets)} widgets",
            "sp_widgets": widgets,
            "total": len(widgets),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing widgets: {e}")
        return {
            "success": False,
            "message": f"Error listing widgets: {str(e)}",
            "sp_widgets": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_sp_widget(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetSpWidgetParams,
) -> Dict[str, Any]:
    """Get a specific Service Portal widget from ServiceNow.

    The widget can be looked up by sys_id (prefix with 'sys_id:'), by its widget
    id (e.g. 'standard_ticket_header'), or by its exact name.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the widget data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.widget_id.startswith("sys_id:"):
            sys_id = params.widget_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sp_widget/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sp_widget"
            query_params["sysparm_query"] = (
                f"id={params.widget_id}^ORname={params.widget_id}"
            )

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Widget not found: {params.widget_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Widget not found: {params.widget_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found widget: {item.get('name')}",
            "sp_widget": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting widget: {e}")
        return {
            "success": False,
            "message": f"Error getting widget: {str(e)}",
        }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}

    # Simple string passthrough fields.
    for attr in (
        "id",
        "name",
        "template",
        "css",
        "script",
        "client_script",
        "link",
        "option_schema",
        "demo_data",
        "controller_as",
        "field_list",
        "data_table",
        "docs",
        "description",
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    # Boolean fields stored as lowercase strings.
    for attr in ("public", "has_preview"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = str(value).lower()

    return body


def create_sp_widget(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateSpWidgetParams,
) -> SpWidgetResponse:
    """Create a new Service Portal widget in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    url = f"{config.instance_url}/api/now/table/sp_widget"
    body = _build_body(params)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return SpWidgetResponse(
                success=False,
                message="Failed to create widget",
            )

        result = data["result"]
        return SpWidgetResponse(
            success=True,
            message=f"Created widget: {result.get('name')}",
            sp_widget_id=result.get("sys_id"),
            sp_widget_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error creating widget: {e}")
        return SpWidgetResponse(
            success=False,
            message=f"Error creating widget: {str(e)}",
        )


def update_sp_widget(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateSpWidgetParams,
) -> SpWidgetResponse:
    """Update an existing Service Portal widget in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetSpWidgetParams(widget_id=params.widget_id)
    get_result = get_sp_widget(config, auth_manager, get_params)

    if not get_result["success"]:
        return SpWidgetResponse(success=False, message=get_result["message"])

    widget = get_result["sp_widget"]
    sys_id = widget["sys_id"]

    url = f"{config.instance_url}/api/now/table/sp_widget/{sys_id}"
    body = _build_body(params)

    if not body:
        return SpWidgetResponse(
            success=True,
            message=f"No changes to update for widget: {widget['name']}",
            sp_widget_id=sys_id,
            sp_widget_name=widget["name"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return SpWidgetResponse(
                success=False,
                message=f"Failed to update widget: {widget['name']}",
            )

        result = data["result"]
        return SpWidgetResponse(
            success=True,
            message=f"Updated widget: {result.get('name')}",
            sp_widget_id=result.get("sys_id"),
            sp_widget_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error updating widget: {e}")
        return SpWidgetResponse(
            success=False,
            message=f"Error updating widget: {str(e)}",
        )


def delete_sp_widget(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteSpWidgetParams,
) -> SpWidgetResponse:
    """Delete a Service Portal widget from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetSpWidgetParams(widget_id=params.widget_id)
    get_result = get_sp_widget(config, auth_manager, get_params)

    if not get_result["success"]:
        return SpWidgetResponse(success=False, message=get_result["message"])

    widget = get_result["sp_widget"]
    sys_id = widget["sys_id"]
    name = widget["name"]

    url = f"{config.instance_url}/api/now/table/sp_widget/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return SpWidgetResponse(
            success=True,
            message=f"Deleted widget: {name}",
            sp_widget_id=sys_id,
            sp_widget_name=name,
        )

    except Exception as e:
        logger.error(f"Error deleting widget: {e}")
        return SpWidgetResponse(
            success=False,
            message=f"Error deleting widget: {str(e)}",
        )
