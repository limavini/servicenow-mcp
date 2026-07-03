"""
VCNA Payout Request tools for the ServiceNow MCP server.

This module provides tools for managing VCNA Payout Request records
(x_visa_vcna_hr_payout_request) in ServiceNow. The Payout Request table is part
of the VCNA HR Processes scope and extends x_visa_vcna_hr_request. The
human-readable identifier for these records is the ``number`` field, not
``name``. Creating a record via the Table API lets the Flow Designer "Created"
trigger fire normally (used for end-to-end QA of the Payout flow).
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Table this toolset operates on.
_TABLE = "x_visa_vcna_hr_payout_request"

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,number,reason,payout_amount,employee_sap,opened_by,assignment_group,"
    "assigned_to,state,canceled_reason,short_description,opened_at,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)

# Fields accepted on create/update.
_WRITABLE = (
    "reason",
    "payout_amount",
    "employee_sap",
    "opened_by",
    "assignment_group",
    "state",
    "canceled_reason",
    "short_description",
)


class ListPayoutRequestsParams(BaseModel):
    """Parameters for listing Payout Requests."""

    limit: int = Field(20, description="Maximum number of Payout Requests to return")
    offset: int = Field(0, description="Offset for pagination")
    reason: Optional[str] = Field(None, description="Filter by reason choice value")
    state: Optional[str] = Field(None, description="Filter by state value")
    query: Optional[str] = Field(
        None,
        description="Search query matched against number and short_description (LIKE)",
    )
    encoded_query: Optional[str] = Field(
        None,
        description="Raw ServiceNow encoded query, ANDed with the other filters",
    )


class GetPayoutRequestParams(BaseModel):
    """Parameters for getting a Payout Request."""

    payout_request_id: str = Field(
        ...,
        description="Payout Request sys_id (prefix with 'sys_id:') or number",
    )


class CreatePayoutRequestParams(BaseModel):
    """Parameters for creating a Payout Request."""

    reason: Optional[str] = Field(
        None,
        description=(
            "Reason choice value: referral_bonus, signing_bonus, retention_bonus, "
            "tuition_pre_enrollment, tuition_after_completion, "
            "safety_boot_reimbursement, other"
        ),
    )
    payout_amount: Optional[str] = Field(None, description="Payout Amount (decimal)")
    employee_sap: Optional[str] = Field(
        None, description="Employee reference (x_visa_vcna_hr_employee sys_id)"
    )
    opened_by: Optional[str] = Field(
        None, description="Opened by reference (sys_user sys_id)"
    )
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    state: Optional[str] = Field(None, description="State value")
    canceled_reason: Optional[str] = Field(None, description="Canceled reason choice value")
    short_description: Optional[str] = Field(
        None, description="Short description of the Payout Request"
    )


class UpdatePayoutRequestParams(BaseModel):
    """Parameters for updating a Payout Request."""

    payout_request_id: str = Field(
        ...,
        description="Payout Request sys_id (prefix with 'sys_id:') or number",
    )
    reason: Optional[str] = Field(None, description="Reason choice value")
    payout_amount: Optional[str] = Field(None, description="Payout Amount (decimal)")
    employee_sap: Optional[str] = Field(
        None, description="Employee reference (x_visa_vcna_hr_employee sys_id)"
    )
    opened_by: Optional[str] = Field(
        None, description="Opened by reference (sys_user sys_id)"
    )
    assignment_group: Optional[str] = Field(
        None, description="Assignment group reference (sys_user_group sys_id)"
    )
    state: Optional[str] = Field(None, description="State value")
    canceled_reason: Optional[str] = Field(None, description="Canceled reason choice value")
    short_description: Optional[str] = Field(
        None, description="Short description of the Payout Request"
    )


class DeletePayoutRequestParams(BaseModel):
    """Parameters for deleting a Payout Request."""

    payout_request_id: str = Field(
        ...,
        description="Payout Request sys_id (prefix with 'sys_id:') or number",
    )


class PayoutRequestResponse(BaseModel):
    """Response from Payout Request operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    payout_request_id: Optional[str] = Field(
        None, description="sys_id of the affected Payout Request"
    )
    payout_request_name: Optional[str] = Field(
        None, description="Number of the affected Payout Request"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw x_visa_vcna_hr_payout_request record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "number": item.get("number"),
        "reason": item.get("reason"),
        "payout_amount": item.get("payout_amount"),
        "employee_sap": item.get("employee_sap"),
        "opened_by": item.get("opened_by"),
        "assignment_group": item.get("assignment_group"),
        "assigned_to": item.get("assigned_to"),
        "state": item.get("state"),
        "canceled_reason": item.get("canceled_reason"),
        "short_description": item.get("short_description"),
        "opened_at": item.get("opened_at"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": item.get("sys_created_by", {}).get("display_value")
        if isinstance(item.get("sys_created_by"), dict)
        else item.get("sys_created_by"),
        "updated_by": item.get("sys_updated_by", {}).get("display_value")
        if isinstance(item.get("sys_updated_by"), dict)
        else item.get("sys_updated_by"),
    }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided non-None fields."""
    body: Dict[str, Any] = {}
    for attr in _WRITABLE:
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value
    return body


def list_payout_requests(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListPayoutRequestsParams,
) -> Dict[str, Any]:
    """List Payout Requests from ServiceNow."""
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
        if params.reason is not None:
            query_parts.append(f"reason={params.reason}")
        if params.state is not None:
            query_parts.append(f"state={params.state}")
        if params.query:
            query_parts.append(
                f"numberLIKE{params.query}^ORshort_descriptionLIKE{params.query}"
            )
        if params.encoded_query:
            query_parts.append(params.encoded_query)
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        payout_requests = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(payout_requests)} Payout Requests",
            "payout_requests": payout_requests,
            "total": len(payout_requests),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing Payout Requests: {e}")
        return {
            "success": False,
            "message": f"Error listing Payout Requests: {str(e)}",
            "payout_requests": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_payout_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetPayoutRequestParams,
) -> Dict[str, Any]:
    """Get a specific Payout Request from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.payout_request_id.startswith("sys_id:"):
            sys_id = params.payout_request_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/{_TABLE}"
            query_params["sysparm_query"] = f"number={params.payout_request_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Payout Request not found: {params.payout_request_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Payout Request not found: {params.payout_request_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found Payout Request: {item.get('number')}",
            "payout_request": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting Payout Request: {e}")
        return {
            "success": False,
            "message": f"Error getting Payout Request: {str(e)}",
        }


def create_payout_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreatePayoutRequestParams,
) -> PayoutRequestResponse:
    """Create a new Payout Request in ServiceNow (fires the Flow Designer trigger)."""
    url = f"{config.instance_url}/api/now/table/{_TABLE}"
    body = _build_body(params)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return PayoutRequestResponse(
                success=False,
                message="Failed to create Payout Request",
            )

        result = data["result"]
        return PayoutRequestResponse(
            success=True,
            message=f"Created Payout Request: {result.get('number')}",
            payout_request_id=result.get("sys_id"),
            payout_request_name=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error creating Payout Request: {e}")
        return PayoutRequestResponse(
            success=False,
            message=f"Error creating Payout Request: {str(e)}",
        )


def update_payout_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdatePayoutRequestParams,
) -> PayoutRequestResponse:
    """Update an existing Payout Request in ServiceNow."""
    get_params = GetPayoutRequestParams(payout_request_id=params.payout_request_id)
    get_result = get_payout_request(config, auth_manager, get_params)

    if not get_result["success"]:
        return PayoutRequestResponse(success=False, message=get_result["message"])

    payout_request = get_result["payout_request"]
    sys_id = payout_request["sys_id"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"
    body = _build_body(params)

    if not body:
        return PayoutRequestResponse(
            success=True,
            message=f"No changes to update for Payout Request: {payout_request['number']}",
            payout_request_id=sys_id,
            payout_request_name=payout_request["number"],
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return PayoutRequestResponse(
                success=False,
                message=f"Failed to update Payout Request: {payout_request['number']}",
            )

        result = data["result"]
        return PayoutRequestResponse(
            success=True,
            message=f"Updated Payout Request: {result.get('number')}",
            payout_request_id=result.get("sys_id"),
            payout_request_name=result.get("number"),
        )

    except Exception as e:
        logger.error(f"Error updating Payout Request: {e}")
        return PayoutRequestResponse(
            success=False,
            message=f"Error updating Payout Request: {str(e)}",
        )


def delete_payout_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeletePayoutRequestParams,
) -> PayoutRequestResponse:
    """Delete a Payout Request from ServiceNow."""
    get_params = GetPayoutRequestParams(payout_request_id=params.payout_request_id)
    get_result = get_payout_request(config, auth_manager, get_params)

    if not get_result["success"]:
        return PayoutRequestResponse(success=False, message=get_result["message"])

    payout_request = get_result["payout_request"]
    sys_id = payout_request["sys_id"]
    number = payout_request["number"]

    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return PayoutRequestResponse(
            success=True,
            message=f"Deleted Payout Request: {number}",
            payout_request_id=sys_id,
            payout_request_name=number,
        )

    except Exception as e:
        logger.error(f"Error deleting Payout Request: {e}")
        return PayoutRequestResponse(
            success=False,
            message=f"Error deleting Payout Request: {str(e)}",
        )
