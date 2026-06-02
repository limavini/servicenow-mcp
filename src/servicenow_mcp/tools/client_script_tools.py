"""
Client Script tools for the ServiceNow MCP server.

This module provides tools for managing client scripts (sys_script_client) in
ServiceNow. Client scripts run in the browser on form/list events such as
onLoad, onChange, onSubmit and onCellEdit.
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
    "sys_id,name,table,type,field,script,description,active,ui_type,global,"
    "order,messages,isolate_script,applies_extended,view,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


class ListClientScriptsParams(BaseModel):
    """Parameters for listing client scripts."""

    limit: int = Field(10, description="Maximum number of client scripts to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    table: Optional[str] = Field(
        None, description="Filter by the table the client script applies to (e.g. 'incident')"
    )
    type: Optional[str] = Field(
        None,
        description="Filter by client script type: onLoad, onChange, onSubmit, or onCellEdit",
    )
    query: Optional[str] = Field(None, description="Search query matched against the name (LIKE)")


class GetClientScriptParams(BaseModel):
    """Parameters for getting a client script."""

    client_script_id: str = Field(
        ...,
        description="Client script sys_id (prefix with 'sys_id:') or exact name to look up",
    )


class CreateClientScriptParams(BaseModel):
    """Parameters for creating a client script."""

    name: str = Field(..., description="Name of the client script")
    table: str = Field(
        ..., description="Table the client script applies to (e.g. 'incident')"
    )
    type: str = Field(
        ...,
        description="Client script type: onLoad, onChange, onSubmit, or onCellEdit",
    )
    script: str = Field(..., description="Client-side script content (JavaScript)")
    description: Optional[str] = Field(None, description="Description of the client script")
    active: bool = Field(True, description="Whether the client script is active")
    ui_type: str = Field(
        "10",
        description="UI type: '0' Desktop, '1' Mobile/Service Portal, '10' All (default)",
    )
    field_name: Optional[str] = Field(
        None,
        description="Field the script reacts to (required for onChange / onCellEdit types)",
    )
    global_: bool = Field(
        True,
        alias="global",
        description="Whether the script applies to all views (Global)",
    )
    order: Optional[int] = Field(None, description="Execution order")
    messages: Optional[str] = Field(None, description="Messages available to the script")
    isolate_script: Optional[bool] = Field(
        None, description="Whether to isolate the script (strict scoping)"
    )
    applies_extended: Optional[bool] = Field(
        None, description="Whether the script applies to extended tables"
    )

    class Config:
        populate_by_name = True


class UpdateClientScriptParams(BaseModel):
    """Parameters for updating a client script."""

    client_script_id: str = Field(
        ..., description="Client script sys_id (prefix with 'sys_id:') or exact name"
    )
    name: Optional[str] = Field(None, description="Name of the client script")
    table: Optional[str] = Field(None, description="Table the client script applies to")
    type: Optional[str] = Field(
        None, description="Client script type: onLoad, onChange, onSubmit, or onCellEdit"
    )
    script: Optional[str] = Field(None, description="Client-side script content (JavaScript)")
    description: Optional[str] = Field(None, description="Description of the client script")
    active: Optional[bool] = Field(None, description="Whether the client script is active")
    ui_type: Optional[str] = Field(
        None, description="UI type: '0' Desktop, '1' Mobile/Service Portal, '10' All"
    )
    field_name: Optional[str] = Field(
        None, description="Field the script reacts to (for onChange / onCellEdit)"
    )
    global_: Optional[bool] = Field(
        None, alias="global", description="Whether the script applies to all views (Global)"
    )
    order: Optional[int] = Field(None, description="Execution order")
    messages: Optional[str] = Field(None, description="Messages available to the script")
    isolate_script: Optional[bool] = Field(None, description="Whether to isolate the script")
    applies_extended: Optional[bool] = Field(
        None, description="Whether the script applies to extended tables"
    )

    class Config:
        populate_by_name = True


class DeleteClientScriptParams(BaseModel):
    """Parameters for deleting a client script."""

    client_script_id: str = Field(
        ..., description="Client script sys_id (prefix with 'sys_id:') or exact name"
    )


class ClientScriptResponse(BaseModel):
    """Response from client script operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    client_script_id: Optional[str] = Field(
        None, description="sys_id of the affected client script"
    )
    client_script_name: Optional[str] = Field(
        None, description="Name of the affected client script"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_script_client record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "table": item.get("table"),
        "type": item.get("type"),
        "field": item.get("field"),
        "script": item.get("script"),
        "description": item.get("description"),
        "active": item.get("active") == "true",
        "ui_type": item.get("ui_type"),
        "global": item.get("global") == "true",
        "order": item.get("order"),
        "messages": item.get("messages"),
        "isolate_script": item.get("isolate_script") == "true",
        "applies_extended": item.get("applies_extended") == "true",
        "view": item.get("view"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": item.get("sys_created_by", {}).get("display_value")
        if isinstance(item.get("sys_created_by"), dict)
        else item.get("sys_created_by"),
        "updated_by": item.get("sys_updated_by", {}).get("display_value")
        if isinstance(item.get("sys_updated_by"), dict)
        else item.get("sys_updated_by"),
    }


def list_client_scripts(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListClientScriptsParams,
) -> Dict[str, Any]:
    """List client scripts from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of client scripts.
    """
    try:
        url = f"{config.instance_url}/api/now/table/sys_script_client"

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        query_parts = []
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
        if params.table:
            query_parts.append(f"table={params.table}")
        if params.type:
            query_parts.append(f"type={params.type}")
        if params.query:
            query_parts.append(f"nameLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        client_scripts = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(client_scripts)} client scripts",
            "client_scripts": client_scripts,
            "total": len(client_scripts),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing client scripts: {e}")
        return {
            "success": False,
            "message": f"Error listing client scripts: {str(e)}",
            "client_scripts": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetClientScriptParams,
) -> Dict[str, Any]:
    """Get a specific client script from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the client script data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.client_script_id.startswith("sys_id:"):
            sys_id = params.client_script_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_script_client/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_script_client"
            query_params["sysparm_query"] = f"name={params.client_script_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Client script not found: {params.client_script_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Client script not found: {params.client_script_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found client script: {item.get('name')}",
            "client_script": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting client script: {e}")
        return {
            "success": False,
            "message": f"Error getting client script: {str(e)}",
        }


def _build_body(params: BaseModel, *, creating: bool) -> Dict[str, Any]:
    """Build the request body, including only provided fields."""
    body: Dict[str, Any] = {}

    # Simple string passthrough fields.
    for attr, field in (
        ("name", "name"),
        ("table", "table"),
        ("type", "type"),
        ("script", "script"),
        ("description", "description"),
        ("ui_type", "ui_type"),
        ("field_name", "field"),
        ("messages", "messages"),
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[field] = value

    # Boolean fields stored as lowercase strings.
    for attr, field in (
        ("active", "active"),
        ("global_", "global"),
        ("isolate_script", "isolate_script"),
        ("applies_extended", "applies_extended"),
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[field] = str(value).lower()

    if getattr(params, "order", None) is not None:
        body["order"] = str(params.order)

    return body


def create_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateClientScriptParams,
) -> ClientScriptResponse:
    """Create a new client script in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    url = f"{config.instance_url}/api/now/table/sys_script_client"
    body = _build_body(params, creating=True)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return ClientScriptResponse(
                success=False,
                message="Failed to create client script",
            )

        result = data["result"]
        return ClientScriptResponse(
            success=True,
            message=f"Created client script: {result.get('name')}",
            client_script_id=result.get("sys_id"),
            client_script_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error creating client script: {e}")
        return ClientScriptResponse(
            success=False,
            message=f"Error creating client script: {str(e)}",
        )


def update_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateClientScriptParams,
) -> ClientScriptResponse:
    """Update an existing client script in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetClientScriptParams(client_script_id=params.client_script_id)
    get_result = get_client_script(config, auth_manager, get_params)

    if not get_result["success"]:
        return ClientScriptResponse(success=False, message=get_result["message"])

    client_script = get_result["client_script"]
    sys_id = client_script["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_script_client/{sys_id}"
    body = _build_body(params, creating=False)

    if not body:
        return ClientScriptResponse(
            success=True,
            message=f"No changes to update for client script: {client_script['name']}",
            client_script_id=sys_id,
            client_script_name=client_script["name"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return ClientScriptResponse(
                success=False,
                message=f"Failed to update client script: {client_script['name']}",
            )

        result = data["result"]
        return ClientScriptResponse(
            success=True,
            message=f"Updated client script: {result.get('name')}",
            client_script_id=result.get("sys_id"),
            client_script_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error updating client script: {e}")
        return ClientScriptResponse(
            success=False,
            message=f"Error updating client script: {str(e)}",
        )


def delete_client_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteClientScriptParams,
) -> ClientScriptResponse:
    """Delete a client script from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetClientScriptParams(client_script_id=params.client_script_id)
    get_result = get_client_script(config, auth_manager, get_params)

    if not get_result["success"]:
        return ClientScriptResponse(success=False, message=get_result["message"])

    client_script = get_result["client_script"]
    sys_id = client_script["sys_id"]
    name = client_script["name"]

    url = f"{config.instance_url}/api/now/table/sys_script_client/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return ClientScriptResponse(
            success=True,
            message=f"Deleted client script: {name}",
            client_script_id=sys_id,
            client_script_name=name,
        )

    except Exception as e:
        logger.error(f"Error deleting client script: {e}")
        return ClientScriptResponse(
            success=False,
            message=f"Error deleting client script: {str(e)}",
        )
