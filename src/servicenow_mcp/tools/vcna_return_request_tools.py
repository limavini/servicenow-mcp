"""
VCNA Return Request tools for the ServiceNow MCP server.

This module provides tools for managing VCNA Return Request records
(x_visa_vcna_hr_return_request) in ServiceNow. The Return Request table is part
of the VCNA HR Processes scope and extends x_visa_vcna_hr_request -> task. The
human-readable identifier for these records is the ``number`` field
(e.g. VCNHR0001119), not ``name``.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Table this toolset operates on.
_TABLE = "x_visa_vcna_hr_return_request"

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,number,short_description,employee_sap,opened_by,assignment_group,"
    "mass_changes,state,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)


class ListVcnaReturnRequestsParams(BaseModel):
    """Parameters for listing VCNA return requests."""

    limit: int = Field(10, description="Maximum number of return requests to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by state value")
    query: Optional[str] = Field(
        None,
        description="Search query matched against number and short_description (LIKE)",
    )


class GetVcnaReturnRequestParams(BaseModel):
    """Parameters for getting a VCNA return request."""

    vcna_return_request_id: str = Field(
        ...,
        description="Return request sys_id (prefix with 'sys_id:') or number (e.g. VCNHR0001119)",
    )


class CreateVcnaReturnRequestParams(BaseModel):
    """Parameters for creating a VCNA return request."""

    short_description: Optional[str] = Field(
        None, description="Short description of the return request"
    )
    employee_sap: Optional[str] = Field(
        None, description="Employee reference (pass the Employee sys_id as-is)"
    )
    opened_by: Optional[str] = Field(
        None, description="Opened by reference (sys_user sys_id)"
    )
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    mass_changes: Optional[str] = Field(
        None, description="Mass changes choice (pass the string value as-is)"
    )
    state: Optional[str] = Field(None, description="State value")


class UpdateVcnaReturnRequestParams(BaseModel):
    """Parameters for updating a VCNA return request."""

    vcna_return_request_id: str = Field(
        ...,
        description="Return request sys_id (prefix with 'sys_id:') or number (e.g. VCNHR0001119)",
    )
    short_description: Optional[str] = Field(
        None, description="Short description of the return request"
    )
    employee_sap: Optional[str] = Field(
        None, description="Employee reference (pass the Employee sys_id as-is)"
    )
    opened_by: Optional[str] = Field(
        None, description="Opened by reference (sys_user sys_id)"
    )
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    mass_changes: Optional[str] = Field(
        None, description="Mass changes choice (pass the string value as-is)"
    )
    state: Optional[str] = Field(None, description="State value")


class DeleteVcnaReturnRequestParams(BaseModel):
    """Parameters for deleting a VCNA return request."""

    vcna_return_request_id: str = Field(
        ...,
        description="Return request sys_id (prefix with 'sys_id:') or number (e.g. VCNHR0001119)",
    )


class VcnaReturnRequestResponse(BaseModel):
    """Response from VCNA return request operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    return_request_id: Optional[str] = Field(
        None, description="sys_id of the affected return request"
    )
    return_request_number: Optional[str] = Field(
        None, description="Number of the affected return request"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw x_visa_vcna_hr_return_request record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "short_description": item.get("short_description"),
        "employee_sap": item.get("employee_sap"),
        "opened_by": item.get("opened_by"),
        "assignment_group": item.get("assignment_group"),
        "mass_changes": item.get("mass_changes"),
        "state": item.get("state"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": item.get("sys_created_by", {}).get("display_value")
        if isinstance(item.get("sys_created_by"), dict)
        else item.get("sys_created_by"),
        "updated_by": item.get("sys_updated_by", {}).get("display_value")
        if isinstance(item.get("sys_updated_by"), dict)
        else item.get("sys_updated_by"),
    }


def list_vcna_return_requests(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListVcnaReturnRequestsParams,
) -> Dict[str, Any]:
    """List VCNA return requests from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of return requests.
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
        return_requests = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(return_requests)} return requests",
            "return_requests": return_requests,
            "total": len(return_requests),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing return requests: {e}")
        return {
            "success": False,
            "message": f"Error listing return requests: {str(e)}",
            "return_requests": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_vcna_return_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetVcnaReturnRequestParams,
) -> Dict[str, Any]:
    """Get a specific VCNA return request from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the return request data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.vcna_return_request_id.startswith("sys_id:"):
            sys_id = params.vcna_return_request_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/{_TABLE}"
            query_params["sysparm_query"] = f"number={params.vcna_return_request_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Return request not found: {params.vcna_return_request_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Return request not found: {params.vcna_return_request_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found return request: {item.get('number')}",
            "return_request": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting return request: {e}")
        return {
            "success": False,
            "message": f"Error getting return request: {str(e)}",
        }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided non-None fields."""
    body: Dict[str, Any] = {}

    for attr in (
        "short_description",
        "employee_sap",
        "opened_by",
        "assignment_group",
        "mass_changes",
        "state",
    ):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    return body


def create_vcna_return_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateVcnaReturnRequestParams,
) -> VcnaReturnRequestResponse:
    """Create a new VCNA return request in ServiceNow.

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
            return VcnaReturnRequestResponse(
                success=False,
                message="Failed to create return request",
            )

        result = data["result"]
        return VcnaReturnRequestResponse(
            success=True,
            message=f"Created return request: {result.get('number')}",
            return_request_id=result.get("sys_id"),
            return_request_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error creating return request: {e}")
        return VcnaReturnRequestResponse(
            success=False,
            message=f"Error creating return request: {str(e)}",
        )


def update_vcna_return_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateVcnaReturnRequestParams,
) -> VcnaReturnRequestResponse:
    """Update an existing VCNA return request in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaReturnRequestParams(
        vcna_return_request_id=params.vcna_return_request_id
    )
    get_result = get_vcna_return_request(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaReturnRequestResponse(success=False, message=get_result["message"])

    return_request = get_result["return_request"]
    sys_id = return_request["sys_id"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
    body = _build_body(params)

    if not body:
        return VcnaReturnRequestResponse(
            success=True,
            message=f"No changes to update for return request: {return_request['number']}",
            return_request_id=sys_id,
            return_request_number=return_request["number"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return VcnaReturnRequestResponse(
                success=False,
                message=f"Failed to update return request: {return_request['number']}",
            )

        result = data["result"]
        return VcnaReturnRequestResponse(
            success=True,
            message=f"Updated return request: {result.get('number')}",
            return_request_id=result.get("sys_id"),
            return_request_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error updating return request: {e}")
        return VcnaReturnRequestResponse(
            success=False,
            message=f"Error updating return request: {str(e)}",
        )


def delete_vcna_return_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteVcnaReturnRequestParams,
) -> VcnaReturnRequestResponse:
    """Delete a VCNA return request from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaReturnRequestParams(
        vcna_return_request_id=params.vcna_return_request_id
    )
    get_result = get_vcna_return_request(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaReturnRequestResponse(success=False, message=get_result["message"])

    return_request = get_result["return_request"]
    sys_id = return_request["sys_id"]
    number = return_request["number"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return VcnaReturnRequestResponse(
            success=True,
            message=f"Deleted return request: {number}",
            return_request_id=sys_id,
            return_request_number=number,
        )

    except Exception as e:
        logger.error(f"Error deleting return request: {e}")
        return VcnaReturnRequestResponse(
            success=False,
            message=f"Error deleting return request: {str(e)}",
        )
