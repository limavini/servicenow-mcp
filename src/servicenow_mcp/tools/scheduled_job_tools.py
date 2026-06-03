"""
ScheduledJob tools for the ServiceNow MCP server.

This module provides CRUD tools for scheduled jobs (sysauto_script) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,script,active,run_type,run_period,run_time,run_dayofweek,conditional,condition,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListScheduledJobsParams(BaseModel):
    """Parameters for listing scheduled jobs."""

    limit: int = Field(10, description="Maximum number of scheduled jobs to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Scheduled job name")
    active: Optional[bool] = Field(None, description="Filter by Whether active")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetScheduledJobParams(BaseModel):
    """Parameters for getting a scheduled job."""

    scheduled_job_id: str = Field(..., description="ScheduledJob sys_id (prefix with 'sys_id:'), or the exact name")


class CreateScheduledJobParams(BaseModel):
    """Parameters for creating a scheduled job."""

    name: str = Field(..., description="Scheduled job name")
    script: Optional[str] = Field(None, description="Script content")
    active: bool = Field(True, description="Whether active")
    run_type: Optional[str] = Field(None, description="Run type: daily, weekly, monthly, periodically, once, on_demand")
    run_period: Optional[str] = Field(None, description="Run period (for periodically)")
    run_time: Optional[str] = Field(None, description="Run time")
    run_dayofweek: Optional[str] = Field(None, description="Day of week")
    conditional: Optional[bool] = Field(None, description="Conditional execution")
    condition: Optional[str] = Field(None, description="Condition script")


class UpdateScheduledJobParams(BaseModel):
    """Parameters for updating a scheduled job."""

    scheduled_job_id: str = Field(..., description="ScheduledJob sys_id (prefix with 'sys_id:'), or the exact name")
    name: Optional[str] = Field(None, description="Scheduled job name")
    script: Optional[str] = Field(None, description="Script content")
    active: Optional[bool] = Field(None, description="Whether active")
    run_type: Optional[str] = Field(None, description="Run type: daily, weekly, monthly, periodically, once, on_demand")
    run_period: Optional[str] = Field(None, description="Run period (for periodically)")
    run_time: Optional[str] = Field(None, description="Run time")
    run_dayofweek: Optional[str] = Field(None, description="Day of week")
    conditional: Optional[bool] = Field(None, description="Conditional execution")
    condition: Optional[str] = Field(None, description="Condition script")


class DeleteScheduledJobParams(BaseModel):
    """Parameters for deleting a scheduled job."""

    scheduled_job_id: str = Field(..., description="ScheduledJob sys_id (prefix with 'sys_id:'), or the exact name")


class ScheduledJobResponse(BaseModel):
    """Response from scheduled job operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    scheduled_job_id: Optional[str] = Field(None, description="sys_id of the affected scheduled job")
    scheduled_job_name: Optional[str] = Field(None, description="Name of the affected scheduled job")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sysauto_script record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "script": _display(item.get("script")),
        "active": item.get("active") == "true",
        "run_type": _display(item.get("run_type")),
        "run_period": _display(item.get("run_period")),
        "run_time": _display(item.get("run_time")),
        "run_dayofweek": _display(item.get("run_dayofweek")),
        "conditional": item.get("conditional") == "true",
        "condition": _display(item.get("condition")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_scheduled_jobs(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListScheduledJobsParams,
) -> Dict[str, Any]:
    """List scheduled jobs from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sysauto_script"
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
            "message": f"Found {len(items)} scheduled jobs",
            "scheduled_jobs": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing scheduled jobs: {e}")
        return {
            "success": False,
            "message": f"Error listing scheduled jobs: {str(e)}",
            "scheduled_jobs": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_scheduled_job(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetScheduledJobParams,
) -> Dict[str, Any]:
    """Get a specific scheduled job from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        if params.scheduled_job_id.startswith("sys_id:"):
            sys_id = params.scheduled_job_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sysauto_script/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sysauto_script"
            query_params["sysparm_query"] = f"name={params.scheduled_job_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"ScheduledJob not found: {params.scheduled_job_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"ScheduledJob not found: {params.scheduled_job_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found scheduled job: {item.get('name')}",
            "scheduled_job": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting scheduled job: {e}")
        return {"success": False, "message": f"Error getting scheduled job: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "script", None)
    if value is not None:
        body["script"] = value
    value = getattr(params, "run_type", None)
    if value is not None:
        body["run_type"] = value
    value = getattr(params, "run_period", None)
    if value is not None:
        body["run_period"] = value
    value = getattr(params, "run_time", None)
    if value is not None:
        body["run_time"] = value
    value = getattr(params, "run_dayofweek", None)
    if value is not None:
        body["run_dayofweek"] = value
    value = getattr(params, "condition", None)
    if value is not None:
        body["condition"] = value
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    value = getattr(params, "conditional", None)
    if value is not None:
        body["conditional"] = str(value).lower()
    return body


def create_scheduled_job(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateScheduledJobParams,
) -> ScheduledJobResponse:
    """Create a new scheduled job in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sysauto_script"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return ScheduledJobResponse(success=False, message="Failed to create scheduled job")
        result = data["result"]
        return ScheduledJobResponse(
            success=True,
            message=f"Created scheduled job: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            scheduled_job_id=result.get("sys_id"),
            scheduled_job_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating scheduled job: {e}")
        return ScheduledJobResponse(success=False, message=f"Error creating scheduled job: {str(e)}")


def update_scheduled_job(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateScheduledJobParams,
) -> ScheduledJobResponse:
    """Update an existing scheduled job in ServiceNow."""
    get_result = get_scheduled_job(config, auth_manager, GetScheduledJobParams(scheduled_job_id=params.scheduled_job_id))
    if not get_result["success"]:
        return ScheduledJobResponse(success=False, message=get_result["message"])
    record = get_result["scheduled_job"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sysauto_script/{sys_id}"
    body = _build_body(params)
    if not body:
        return ScheduledJobResponse(
            success=True,
            message=f"No changes to update for scheduled job",
            scheduled_job_id=sys_id,
            scheduled_job_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return ScheduledJobResponse(success=False, message=f"Failed to update scheduled job")
        result = data["result"]
        return ScheduledJobResponse(
            success=True,
            message=f"Updated scheduled job",
            scheduled_job_id=result.get("sys_id"),
            scheduled_job_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating scheduled job: {e}")
        return ScheduledJobResponse(success=False, message=f"Error updating scheduled job: {str(e)}")


def delete_scheduled_job(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteScheduledJobParams,
) -> ScheduledJobResponse:
    """Delete a scheduled job from ServiceNow."""
    get_result = get_scheduled_job(config, auth_manager, GetScheduledJobParams(scheduled_job_id=params.scheduled_job_id))
    if not get_result["success"]:
        return ScheduledJobResponse(success=False, message=get_result["message"])
    record = get_result["scheduled_job"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sysauto_script/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return ScheduledJobResponse(success=True, message=f"Deleted scheduled job", scheduled_job_id=sys_id, scheduled_job_name=name)
    except Exception as e:
        logger.error(f"Error deleting scheduled job: {e}")
        return ScheduledJobResponse(success=False, message=f"Error deleting scheduled job: {str(e)}")
