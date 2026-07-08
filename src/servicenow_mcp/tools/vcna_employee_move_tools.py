"""
VCNA Employee Move (Other Employee Change) tools for the ServiceNow MCP server.

This module provides tools for managing VCNA Employee Move records
(x_visa_vcna_hr_other_employee_change_request) in ServiceNow. The Employee Move
table is part of the VCNA HR Processes scope and extends x_visa_vcna_hr_request ->
task. The human-readable identifier for these records is the ``number`` field
(e.g. VCNOE0001064), not ``name``.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Table this toolset operates on.
_TABLE = "x_visa_vcna_hr_other_employee_change_request"

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,number,short_description,employee_sap,opened_by,assignment_group,"
    "change_type,effective_date,offer_letter_required,state,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)

# Create/update body fields that map 1:1 to string columns.
_STRING_FIELDS = (
    "short_description",
    "employee_sap",
    "opened_by",
    "assignment_group",
    "change_type",
    "effective_date",
    "state",
)


class ListVcnaEmployeeMovesParams(BaseModel):
    """Parameters for listing VCNA employee moves."""

    limit: int = Field(10, description="Maximum number of employee moves to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by state value")
    query: Optional[str] = Field(
        None,
        description="Search query matched against number and short_description (LIKE)",
    )


class GetVcnaEmployeeMoveParams(BaseModel):
    """Parameters for getting a VCNA employee move."""

    vcna_employee_move_id: str = Field(
        ...,
        description="Employee move sys_id (prefix with 'sys_id:') or number (e.g. VCNOE0001064)",
    )


class CreateVcnaEmployeeMoveParams(BaseModel):
    """Parameters for creating a VCNA employee move."""

    short_description: Optional[str] = Field(
        None, description="Short description of the employee move"
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
    change_type: Optional[str] = Field(
        None,
        description="Change type choice value as-is (e.g. 'lateral_transfer', 'promotion')",
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date (YYYY-MM-DD)"
    )
    offer_letter_required: Optional[bool] = Field(
        None,
        description="Whether an offer letter is required (drives the DocuSign branch)",
    )
    state: Optional[str] = Field(None, description="State value")


class UpdateVcnaEmployeeMoveParams(BaseModel):
    """Parameters for updating a VCNA employee move."""

    vcna_employee_move_id: str = Field(
        ...,
        description="Employee move sys_id (prefix with 'sys_id:') or number (e.g. VCNOE0001064)",
    )
    short_description: Optional[str] = Field(
        None, description="Short description of the employee move"
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
    change_type: Optional[str] = Field(
        None,
        description="Change type choice value as-is (e.g. 'lateral_transfer', 'promotion')",
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date (YYYY-MM-DD)"
    )
    offer_letter_required: Optional[bool] = Field(
        None,
        description="Whether an offer letter is required (drives the DocuSign branch)",
    )
    state: Optional[str] = Field(None, description="State value")


class DeleteVcnaEmployeeMoveParams(BaseModel):
    """Parameters for deleting a VCNA employee move."""

    vcna_employee_move_id: str = Field(
        ...,
        description="Employee move sys_id (prefix with 'sys_id:') or number (e.g. VCNOE0001064)",
    )


class VcnaEmployeeMoveResponse(BaseModel):
    """Response from VCNA employee move operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    employee_move_id: Optional[str] = Field(
        None, description="sys_id of the affected employee move"
    )
    employee_move_number: Optional[str] = Field(
        None, description="Number of the affected employee move"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw x_visa_vcna_hr_other_employee_change_request record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "short_description": item.get("short_description"),
        "employee_sap": item.get("employee_sap"),
        "opened_by": item.get("opened_by"),
        "assignment_group": item.get("assignment_group"),
        "change_type": item.get("change_type"),
        "effective_date": item.get("effective_date"),
        "offer_letter_required": item.get("offer_letter_required") == "true",
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


def list_vcna_employee_moves(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListVcnaEmployeeMovesParams,
) -> Dict[str, Any]:
    """List VCNA employee moves from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of employee moves.
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
        employee_moves = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(employee_moves)} employee moves",
            "employee_moves": employee_moves,
            "total": len(employee_moves),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing employee moves: {e}")
        return {
            "success": False,
            "message": f"Error listing employee moves: {str(e)}",
            "employee_moves": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_vcna_employee_move(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetVcnaEmployeeMoveParams,
) -> Dict[str, Any]:
    """Get a specific VCNA employee move from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the employee move data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.vcna_employee_move_id.startswith("sys_id:"):
            sys_id = params.vcna_employee_move_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/{_TABLE}"
            query_params["sysparm_query"] = f"number={params.vcna_employee_move_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Employee move not found: {params.vcna_employee_move_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Employee move not found: {params.vcna_employee_move_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found employee move: {item.get('number')}",
            "employee_move": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting employee move: {e}")
        return {
            "success": False,
            "message": f"Error getting employee move: {str(e)}",
        }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided non-None fields."""
    body: Dict[str, Any] = {}

    for attr in _STRING_FIELDS:
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    # Booleans are sent to the Table API as lowercase strings.
    offer_letter_required = getattr(params, "offer_letter_required", None)
    if offer_letter_required is not None:
        body["offer_letter_required"] = str(offer_letter_required).lower()

    return body


def create_vcna_employee_move(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateVcnaEmployeeMoveParams,
) -> VcnaEmployeeMoveResponse:
    """Create a new VCNA employee move in ServiceNow.

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
            return VcnaEmployeeMoveResponse(
                success=False,
                message="Failed to create employee move",
            )

        result = data["result"]
        return VcnaEmployeeMoveResponse(
            success=True,
            message=f"Created employee move: {result.get('number')}",
            employee_move_id=result.get("sys_id"),
            employee_move_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error creating employee move: {e}")
        return VcnaEmployeeMoveResponse(
            success=False,
            message=f"Error creating employee move: {str(e)}",
        )


def update_vcna_employee_move(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateVcnaEmployeeMoveParams,
) -> VcnaEmployeeMoveResponse:
    """Update an existing VCNA employee move in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaEmployeeMoveParams(
        vcna_employee_move_id=params.vcna_employee_move_id
    )
    get_result = get_vcna_employee_move(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaEmployeeMoveResponse(success=False, message=get_result["message"])

    employee_move = get_result["employee_move"]
    sys_id = employee_move["sys_id"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
    body = _build_body(params)

    if not body:
        return VcnaEmployeeMoveResponse(
            success=True,
            message=f"No changes to update for employee move: {employee_move['number']}",
            employee_move_id=sys_id,
            employee_move_number=employee_move["number"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return VcnaEmployeeMoveResponse(
                success=False,
                message=f"Failed to update employee move: {employee_move['number']}",
            )

        result = data["result"]
        return VcnaEmployeeMoveResponse(
            success=True,
            message=f"Updated employee move: {result.get('number')}",
            employee_move_id=result.get("sys_id"),
            employee_move_number=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error updating employee move: {e}")
        return VcnaEmployeeMoveResponse(
            success=False,
            message=f"Error updating employee move: {str(e)}",
        )


def delete_vcna_employee_move(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteVcnaEmployeeMoveParams,
) -> VcnaEmployeeMoveResponse:
    """Delete a VCNA employee move from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetVcnaEmployeeMoveParams(
        vcna_employee_move_id=params.vcna_employee_move_id
    )
    get_result = get_vcna_employee_move(config, auth_manager, get_params)

    if not get_result["success"]:
        return VcnaEmployeeMoveResponse(success=False, message=get_result["message"])

    employee_move = get_result["employee_move"]
    sys_id = employee_move["sys_id"]
    number = employee_move["number"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return VcnaEmployeeMoveResponse(
            success=True,
            message=f"Deleted employee move: {number}",
            employee_move_id=sys_id,
            employee_move_number=number,
        )

    except Exception as e:
        logger.error(f"Error deleting employee move: {e}")
        return VcnaEmployeeMoveResponse(
            success=False,
            message=f"Error deleting employee move: {str(e)}",
        )
