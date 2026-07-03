"""
Approval tools for the ServiceNow MCP server.

This module provides tools for reading and actioning approval records
(``sysapproval_approver``) — the individual approver rows created by workflows,
Flow Designer "Ask For Approval" steps, etc. Only list/get/update are exposed
(approvals are created by the platform, not by this tool). Updating ``state`` to
``approved`` / ``rejected`` drives waiting Flow Designer approvals — used for
end-to-end QA of approval flows.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Table this toolset operates on.
_TABLE = "sysapproval_approver"

# Fields fetched for read operations.
_FIELDS = (
    "sys_id,state,approver,sysapproval,document_id,source_table,order,comments,"
    "sys_created_on,sys_updated_on"
)


class ListApprovalsParams(BaseModel):
    """Parameters for listing approvals."""

    limit: int = Field(50, description="Maximum number of approvals to return")
    offset: int = Field(0, description="Offset for pagination")
    sysapproval: Optional[str] = Field(
        None,
        description="Filter by the approved record sys_id (sysapproval)",
    )
    approver: Optional[str] = Field(
        None, description="Filter by approver (sys_user sys_id)"
    )
    state: Optional[str] = Field(
        None, description="Filter by state (e.g. requested, approved, rejected)"
    )
    query: Optional[str] = Field(
        None, description="Raw ServiceNow encoded query, ANDed with the other filters"
    )


class GetApprovalParams(BaseModel):
    """Parameters for getting an approval."""

    approval_id: str = Field(
        ..., description="Approval sys_id (with or without the 'sys_id:' prefix)"
    )


class UpdateApprovalParams(BaseModel):
    """Parameters for updating (actioning) an approval."""

    approval_id: str = Field(
        ..., description="Approval sys_id (with or without the 'sys_id:' prefix)"
    )
    state: Optional[str] = Field(
        None,
        description="New state: approved, rejected, requested, not_required, no_longer_required",
    )
    comments: Optional[str] = Field(None, description="Approval comments")


class ApprovalResponse(BaseModel):
    """Response from approval operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    approval_id: Optional[str] = Field(
        None, description="sys_id of the affected approval"
    )


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sysapproval_approver record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "state": item.get("state"),
        "approver": item.get("approver"),
        "sysapproval": item.get("sysapproval"),
        "document_id": item.get("document_id"),
        "source_table": item.get("source_table"),
        "order": item.get("order"),
        "comments": item.get("comments"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def _strip_id(value: str) -> str:
    return value.replace("sys_id:", "") if value.startswith("sys_id:") else value


def list_approvals(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListApprovalsParams,
) -> Dict[str, Any]:
    """List approval (sysapproval_approver) records from ServiceNow."""
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
        if params.sysapproval is not None:
            query_parts.append(f"sysapproval={_strip_id(params.sysapproval)}")
        if params.approver is not None:
            query_parts.append(f"approver={_strip_id(params.approver)}")
        if params.state is not None:
            query_parts.append(f"state={params.state}")
        if params.query:
            query_parts.append(params.query)
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        approvals = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(approvals)} approvals",
            "approvals": approvals,
            "total": len(approvals),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing approvals: {e}")
        return {
            "success": False,
            "message": f"Error listing approvals: {str(e)}",
            "approvals": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_approval(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetApprovalParams,
) -> Dict[str, Any]:
    """Get a specific approval (sysapproval_approver) record from ServiceNow."""
    try:
        sys_id = _strip_id(params.approval_id)
        url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data or not data["result"]:
            return {
                "success": False,
                "message": f"Approval not found: {params.approval_id}",
            }

        item = data["result"]
        if isinstance(item, list):
            item = item[0]

        return {
            "success": True,
            "message": f"Found approval: {item.get('sys_id')}",
            "approval": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting approval: {e}")
        return {
            "success": False,
            "message": f"Error getting approval: {str(e)}",
        }


def update_approval(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateApprovalParams,
) -> ApprovalResponse:
    """Update (action) an approval — e.g. set state to approved/rejected."""
    sys_id = _strip_id(params.approval_id)
    url = f"{config.instance_url}/api/now/table/{_TABLE}/{sys_id}"

    body: Dict[str, Any] = {}
    if params.state is not None:
        body["state"] = params.state
    if params.comments is not None:
        body["comments"] = params.comments

    if not body:
        return ApprovalResponse(
            success=True,
            message=f"No changes to update for approval: {sys_id}",
            approval_id=sys_id,
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return ApprovalResponse(
                success=False,
                message=f"Failed to update approval: {sys_id}",
            )

        result = data["result"]
        return ApprovalResponse(
            success=True,
            message=f"Updated approval {sys_id} (state={result.get('state')})",
            approval_id=result.get("sys_id"),
        )

    except Exception as e:
        logger.error(f"Error updating approval: {e}")
        return ApprovalResponse(
            success=False,
            message=f"Error updating approval: {str(e)}",
        )
