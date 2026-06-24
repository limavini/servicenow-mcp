"""
VCNA HR Task tools for the ServiceNow MCP server.

This module provides tools for managing VCNA HR Task records
(x_visa_vcna_hr_task) in ServiceNow. The HR Task table is part of the VCNA HR
Processes scope and extends task. The human-readable identifier for these
records is the ``number`` field, not ``name``.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Table this toolset operates on.
_TABLE = "x_visa_vcna_hr_task"

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,number,short_description,state,assignment_group,assigned_to,parent,"
    "hr_request,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


class ListVcnaHrTasksParams(BaseModel):
    """Parameters for listing VCNA HR tasks."""

    limit: int = Field(10, description="Maximum number of HR tasks to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by state value")
    query: Optional[str] = Field(
        None,
        description="Search query matched against number and short_description (LIKE)",
    )


class GetVcnaHrTaskParams(BaseModel):
    """Parameters for getting a VCNA HR task."""

    vcna_hr_task_id: str = Field(
        ...,
        description="HR task sys_id (prefix with 'sys_id:') or number",
    )


class CreateVcnaHrTaskParams(BaseModel):
    """Parameters for creating a VCNA HR task."""

    short_description: Optional[str] = Field(
        None, description="Short description of the HR task"
    )
    state: Optional[str] = Field(None, description="State value")
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    assigned_to: Optional[str] = Field(
        None, description="Assigned to reference (sys_user sys_id)"
    )
    parent: Optional[str] = Field(
        None, description="Parent task reference (task sys_id)"
    )
    hr_request: Optional[str] = Field(
        None, description="HR request reference (pass the sys_id as-is)"
    )


class UpdateVcnaHrTaskParams(BaseModel):
    """Parameters for updating a VCNA HR task."""

    vcna_hr_task_id: str = Field(
        ...,
        description="HR task sys_id (prefix with 'sys_id:') or number",
    )
    short_description: Optional[str] = Field(
        None, description="Short description of the HR task"
    )
    state: Optional[str] = Field(None, description="State value")
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    assigned_to: Optional[str] = Field(
        None, description="Assigned to reference (sys_user sys_id)"
    )
    parent: Optional[str] = Field(
        None, description="Parent task reference (task sys_id)"
    )
    hr_request: Optional[str] = Field(
        None, description="HR request reference (pass the sys_id as-is)"
    )


class DeleteVcnaHrTaskParams(BaseModel):
    """Parameters for deleting a VCNA HR task."""

    vcna_hr_task_id: str = Field(
        ...,
        description="HR task sys_id (prefix with 'sys_id:') or number",
    )


class VcnaHrTaskResponse(BaseModel):
    """Response from VCNA HR task operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    vcna_hr_task_id: Optional[str] = Field(
        None, description="sys_id of the affected HR task"
    )
    vcna_hr_task_number: Optional[str] = Field(
        None, description="Number of the affected HR task"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw x_visa_vcna_hr_task record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "short_description": item.get("short_description"),
        "state": item.get("state"),
        "assignment_group": item.get("assignment_group"),
        "assigned_to": item.get("assigned_to"),
        "parent": item.get("parent"),
        "hr_request": item.get("hr_request"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": item.get("sys_created_by", {}).get("display_value")
        if isinstance(item.get("sys_created_by"), dict)
        else item.get("sys_created_by"),
        "updated_by": item.get("sys_updated_by", {}).get("display_value")
        if isinstance(item.get("sys_updated_by"), dict)
        else item.get("sys_updated_by"),
    }


def list_vcna_hr_tasks(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListVcnaHrTasksParams,
) -> Dict[str, Any]:
    """List VCNA HR tasks from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of HR tasks.
    """
    try:
        url = f"{config.instance_url}/api/now/table/{_TABLE}"

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        query_parts = []
        if params.state is not None:
            query_parts.append(f"state={params.state}")
        if params.query:
            query_parts.append(
                f"numberLIKE{params.query}^ORshort_descriptionLIKE{params.query}"
            )
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        hr_tasks = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(hr_tasks)} HR tasks",
            "hr_tasks": hr_tasks,
            "total": len(hr_tasks),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing HR tasks: {e}")
        return {
            "success": False,
            "message": f"Error listing HR tasks: {str(e)}",
            "hr_tasks": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_vcna_hr_task(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetVcnaHrTaskParams,
) -> Dict[str, Any]:
    """Get a specific VCNA HR task from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the HR task data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.vcna_hr_task_id.startswith("sys_id:"):
            sys_id = params.vcna_hr_task_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/{_TABLE}"
            query_params["sysparm_query"] = f"number={params.vcna_hr_task_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"HR task not found: {params.vcna_hr_task_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"HR task not found: {params.vcna_hr_task_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found HR task: {item.get('number')}",
            "hr_task": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting HR task: {e}")
        return {
            "success": False,
            "message": f"Error getting HR task: {str(e)}",
        }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided non-None fields."""
    body: Dict[str, Any] = {}

    for attr in (
        "short_description",
        "state",
        "assignment_group",
        "assigned_to",
        "parent",
        "hr_request",
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    return body


def create_vcna_hr_task(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateVcnaHrTaskParams,
) -> VcnaHrTaskResponse:
    """Create a new VCNA HR task in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    url = f"{config.instance_url}/api/now/table/{_TABLE}"
    body = _build_body(params)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return VcnaHrTaskResponse(
                success=False,
                message="Failed to create HR task",
            )

        result = data["result"]
        return VcnaHrTaskResponse(
            success=True,
            message=f"Created HR task: {result.get('number')}",
            vcna_hr_task_id=result.get("sys_id"),
            vcna_hr_task_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error creating HR task: {e}")
        return VcnaHrTaskResponse(
            success=False,
            message=f"Error creating HR task: {str(e)}",
        )


def update_vcna_hr_task(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateVcnaHrTaskParams,
) -> VcnaHrTaskResponse:
    """Update an existing VCNA HR task in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaHrTaskParams(vcna_hr_task_id=params.vcna_hr_task_id)
    get_result = get_vcna_hr_task(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaHrTaskResponse(success=False, message=get_result["message"])

    hr_task = get_result["hr_task"]
    sys_id = hr_task["sys_id"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
    body = _build_body(params)

    if not body:
        return VcnaHrTaskResponse(
            success=True,
            message=f"No changes to update for HR task: {hr_task['number']}",
            vcna_hr_task_id=sys_id,
            vcna_hr_task_number=hr_task["number"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return VcnaHrTaskResponse(
                success=False,
                message=f"Failed to update HR task: {hr_task['number']}",
            )

        result = data["result"]
        return VcnaHrTaskResponse(
            success=True,
            message=f"Updated HR task: {result.get('number')}",
            vcna_hr_task_id=result.get("sys_id"),
            vcna_hr_task_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error updating HR task: {e}")
        return VcnaHrTaskResponse(
            success=False,
            message=f"Error updating HR task: {str(e)}",
        )


def delete_vcna_hr_task(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteVcnaHrTaskParams,
) -> VcnaHrTaskResponse:
    """Delete a VCNA HR task from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaHrTaskParams(vcna_hr_task_id=params.vcna_hr_task_id)
    get_result = get_vcna_hr_task(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaHrTaskResponse(success=False, message=get_result["message"])

    hr_task = get_result["hr_task"]
    sys_id = hr_task["sys_id"]
    number = hr_task["number"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return VcnaHrTaskResponse(
            success=True,
            message=f"Deleted HR task: {number}",
            vcna_hr_task_id=sys_id,
            vcna_hr_task_number=number,
        )

    except Exception as e:
        logger.error(f"Error deleting HR task: {e}")
        return VcnaHrTaskResponse(
            success=False,
            message=f"Error deleting HR task: {str(e)}",
        )
