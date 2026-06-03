"""
DictionaryEntry tools for the ServiceNow MCP server.

This module provides CRUD tools for dictionary entries (sys_dictionary) in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = "sys_id,name,element,column_label,internal_type,max_length,reference,mandatory,read_only,default_value,active,comments,sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"


class ListDictionaryEntrysParams(BaseModel):
    """Parameters for listing dictionary entries."""

    limit: int = Field(10, description="Maximum number of dictionary entries to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by Table the field belongs to")
    element: Optional[str] = Field(None, description="Filter by Field (column) name")
    query: Optional[str] = Field(None, description="Search query matched against name (LIKE)")


class GetDictionaryEntryParams(BaseModel):
    """Parameters for getting a dictionary entry."""

    dictionary_entry_id: str = Field(..., description="DictionaryEntry sys_id (prefix with 'sys_id:')")


class CreateDictionaryEntryParams(BaseModel):
    """Parameters for creating a dictionary entry."""

    name: str = Field(..., description="Table the field belongs to")
    element: str = Field(..., description="Field (column) name")
    column_label: Optional[str] = Field(None, description="Field label")
    internal_type: Optional[str] = Field(None, description="Field type (string, integer, reference, boolean, ...)")
    max_length: Optional[int] = Field(None, description="Max length")
    reference: Optional[str] = Field(None, description="Referenced table (for reference fields)")
    mandatory: Optional[bool] = Field(None, description="Mandatory")
    read_only: Optional[bool] = Field(None, description="Read only")
    default_value: Optional[str] = Field(None, description="Default value")
    active: Optional[bool] = Field(None, description="Active")
    comments: Optional[str] = Field(None, description="Comments")


class UpdateDictionaryEntryParams(BaseModel):
    """Parameters for updating a dictionary entry."""

    dictionary_entry_id: str = Field(..., description="DictionaryEntry sys_id (prefix with 'sys_id:')")
    name: Optional[str] = Field(None, description="Table the field belongs to")
    element: Optional[str] = Field(None, description="Field (column) name")
    column_label: Optional[str] = Field(None, description="Field label")
    internal_type: Optional[str] = Field(None, description="Field type (string, integer, reference, boolean, ...)")
    max_length: Optional[int] = Field(None, description="Max length")
    reference: Optional[str] = Field(None, description="Referenced table (for reference fields)")
    mandatory: Optional[bool] = Field(None, description="Mandatory")
    read_only: Optional[bool] = Field(None, description="Read only")
    default_value: Optional[str] = Field(None, description="Default value")
    active: Optional[bool] = Field(None, description="Active")
    comments: Optional[str] = Field(None, description="Comments")


class DeleteDictionaryEntryParams(BaseModel):
    """Parameters for deleting a dictionary entry."""

    dictionary_entry_id: str = Field(..., description="DictionaryEntry sys_id (prefix with 'sys_id:')")


class DictionaryEntryResponse(BaseModel):
    """Response from dictionary entry operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    dictionary_entry_id: Optional[str] = Field(None, description="sys_id of the affected dictionary entry")
    dictionary_entry_name: Optional[str] = Field(None, description="Name of the affected dictionary entry")


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_dictionary record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "element": _display(item.get("element")),
        "column_label": _display(item.get("column_label")),
        "internal_type": _display(item.get("internal_type")),
        "max_length": _display(item.get("max_length")),
        "reference": _display(item.get("reference")),
        "mandatory": item.get("mandatory") == "true",
        "read_only": item.get("read_only") == "true",
        "default_value": _display(item.get("default_value")),
        "active": item.get("active") == "true",
        "comments": _display(item.get("comments")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _display(item.get("sys_created_by")),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def list_dictionary_entries(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListDictionaryEntrysParams,
) -> Dict[str, Any]:
    """List dictionary entries from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sys_dictionary"
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
        if params.element:
            query_parts.append(f"element={params.element}")
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
            "message": f"Found {len(items)} dictionary entries",
            "dictionary_entries": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing dictionary entries: {e}")
        return {
            "success": False,
            "message": f"Error listing dictionary entries: {str(e)}",
            "dictionary_entries": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_dictionary_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDictionaryEntryParams,
) -> Dict[str, Any]:
    """Get a specific dictionary entry from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }
        sys_id = params.dictionary_entry_id.replace("sys_id:", "")
        url = f"{config.instance_url}/api/now/table/sys_dictionary/{sys_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {"success": False, "message": f"DictionaryEntry not found: {params.dictionary_entry_id}"}
        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {"success": False, "message": f"DictionaryEntry not found: {params.dictionary_entry_id}"}
            item = result[0]
        else:
            item = result
        return {
            "success": True,
            "message": f"Found dictionary entry: {item.get('name')}",
            "dictionary_entry": _serialize(item),
        }
    except Exception as e:
        logger.error(f"Error getting dictionary entry: {e}")
        return {"success": False, "message": f"Error getting dictionary entry: {str(e)}"}


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields."""
    body: Dict[str, Any] = {}
    value = getattr(params, "name", None)
    if value is not None:
        body["name"] = value
    value = getattr(params, "element", None)
    if value is not None:
        body["element"] = value
    value = getattr(params, "column_label", None)
    if value is not None:
        body["column_label"] = value
    value = getattr(params, "internal_type", None)
    if value is not None:
        body["internal_type"] = value
    value = getattr(params, "max_length", None)
    if value is not None:
        body["max_length"] = str(value)
    value = getattr(params, "reference", None)
    if value is not None:
        body["reference"] = value
    value = getattr(params, "default_value", None)
    if value is not None:
        body["default_value"] = value
    value = getattr(params, "comments", None)
    if value is not None:
        body["comments"] = value
    value = getattr(params, "mandatory", None)
    if value is not None:
        body["mandatory"] = str(value).lower()
    value = getattr(params, "read_only", None)
    if value is not None:
        body["read_only"] = str(value).lower()
    value = getattr(params, "active", None)
    if value is not None:
        body["active"] = str(value).lower()
    return body


def create_dictionary_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateDictionaryEntryParams,
) -> DictionaryEntryResponse:
    """Create a new dictionary entry in ServiceNow."""
    url = f"{config.instance_url}/api/now/table/sys_dictionary"
    body = _build_body(params)
    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DictionaryEntryResponse(success=False, message="Failed to create dictionary entry")
        result = data["result"]
        return DictionaryEntryResponse(
            success=True,
            message=f"Created dictionary entry: {result.get('name') if 'name' != 'sys_id' else result.get('sys_id')}",
            dictionary_entry_id=result.get("sys_id"),
            dictionary_entry_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error creating dictionary entry: {e}")
        return DictionaryEntryResponse(success=False, message=f"Error creating dictionary entry: {str(e)}")


def update_dictionary_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateDictionaryEntryParams,
) -> DictionaryEntryResponse:
    """Update an existing dictionary entry in ServiceNow."""
    get_result = get_dictionary_entry(config, auth_manager, GetDictionaryEntryParams(dictionary_entry_id=params.dictionary_entry_id))
    if not get_result["success"]:
        return DictionaryEntryResponse(success=False, message=get_result["message"])
    record = get_result["dictionary_entry"]
    sys_id = record["sys_id"]

    url = f"{config.instance_url}/api/now/table/sys_dictionary/{sys_id}"
    body = _build_body(params)
    if not body:
        return DictionaryEntryResponse(
            success=True,
            message=f"No changes to update for dictionary entry",
            dictionary_entry_id=sys_id,
            dictionary_entry_name=record.get("name"),
        )
    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            return DictionaryEntryResponse(success=False, message=f"Failed to update dictionary entry")
        result = data["result"]
        return DictionaryEntryResponse(
            success=True,
            message=f"Updated dictionary entry",
            dictionary_entry_id=result.get("sys_id"),
            dictionary_entry_name=result.get("name") if "name" != "sys_id" else result.get("sys_id"),
        )
    except Exception as e:
        logger.error(f"Error updating dictionary entry: {e}")
        return DictionaryEntryResponse(success=False, message=f"Error updating dictionary entry: {str(e)}")


def delete_dictionary_entry(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteDictionaryEntryParams,
) -> DictionaryEntryResponse:
    """Delete a dictionary entry from ServiceNow."""
    get_result = get_dictionary_entry(config, auth_manager, GetDictionaryEntryParams(dictionary_entry_id=params.dictionary_entry_id))
    if not get_result["success"]:
        return DictionaryEntryResponse(success=False, message=get_result["message"])
    record = get_result["dictionary_entry"]
    sys_id = record["sys_id"]
    name = record.get("name")

    url = f"{config.instance_url}/api/now/table/sys_dictionary/{sys_id}"
    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        return DictionaryEntryResponse(success=True, message=f"Deleted dictionary entry", dictionary_entry_id=sys_id, dictionary_entry_name=name)
    except Exception as e:
        logger.error(f"Error deleting dictionary entry: {e}")
        return DictionaryEntryResponse(success=False, message=f"Error deleting dictionary entry: {str(e)}")
