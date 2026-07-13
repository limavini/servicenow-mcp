"""
Dictionary override tools for the ServiceNow MCP server.

This module provides tools for managing dictionary overrides
(``sys_dictionary_override``). An override changes how a field *inherited from a
parent table* behaves on one child table only — e.g. giving `effective_date`
(defined on `x_visa_vcna_hr_request`) a default value on a single child process
table without touching the parent or its other children.

Each overridable attribute is a pair: the value column (e.g. ``default_value``)
and a boolean flag that switches the override on (e.g. ``default_value_override``).
Setting the value without the flag has no effect, so `create_dictionary_override`
turns the matching flag on automatically for every value you pass.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FIELDS = (
    "sys_id,name,element,base_table,"
    "default_value,default_value_override,"
    "mandatory,mandatory_override,"
    "read_only,read_only_override,"
    "reference_qual,reference_qual_override,"
    "attributes,attributes_override,"
    "calculation,calculation_override,"
    "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
)

# Value column -> the boolean column that activates the override.
_OVERRIDE_FLAGS = {
    "default_value": "default_value_override",
    "mandatory": "mandatory_override",
    "read_only": "read_only_override",
    "reference_qual": "reference_qual_override",
    "attributes": "attributes_override",
    "calculation": "calculation_override",
}


def _dv(value):
    """Return a reference field's display value whether it came back as a dict
    (sysparm_display_value=all) or a plain string (sysparm_display_value=true
    with exclude_reference_link)."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


class ListDictionaryOverridesParams(BaseModel):
    """Parameters for listing dictionary overrides."""

    limit: int = Field(20, description="Maximum number of overrides to return")
    offset: int = Field(0, description="Offset for pagination")
    table: Optional[str] = Field(
        None, description="Filter by the child table the override applies to (the 'name' column)"
    )
    element: Optional[str] = Field(None, description="Filter by the overridden field (column) name")
    base_table: Optional[str] = Field(
        None, description="Filter by the parent table the field is defined on"
    )


class GetDictionaryOverrideParams(BaseModel):
    """Parameters for getting a dictionary override."""

    override_id: str = Field(
        ..., description="sys_dictionary_override sys_id (optionally prefixed with 'sys_id:')"
    )


class CreateDictionaryOverrideParams(BaseModel):
    """Parameters for creating a dictionary override."""

    table: str = Field(
        ..., description="Child table the override applies to (e.g. 'x_visa_vcna_hr_position_management')"
    )
    element: str = Field(..., description="Field (column) name being overridden (e.g. 'effective_date')")
    base_table: str = Field(
        ..., description="Parent table the field is defined on (e.g. 'x_visa_vcna_hr_request')"
    )
    default_value: Optional[str] = Field(
        None,
        description="Default value for this table only (e.g. 'javascript:gs.now()'); turns default_value_override on",
    )
    mandatory: Optional[bool] = Field(
        None, description="Mandatory for this table only; turns mandatory_override on"
    )
    read_only: Optional[bool] = Field(
        None, description="Read only for this table only; turns read_only_override on"
    )
    reference_qual: Optional[str] = Field(
        None, description="Reference qualifier for this table only; turns reference_qual_override on"
    )
    attributes: Optional[str] = Field(
        None, description="Field attributes for this table only; turns attributes_override on"
    )
    calculation: Optional[str] = Field(
        None, description="Calculation script for this table only; turns calculation_override on"
    )


class UpdateDictionaryOverrideParams(BaseModel):
    """Parameters for updating a dictionary override."""

    override_id: str = Field(
        ..., description="sys_dictionary_override sys_id (optionally prefixed with 'sys_id:')"
    )
    default_value: Optional[str] = Field(None, description="Default value for this table only")
    mandatory: Optional[bool] = Field(None, description="Mandatory for this table only")
    read_only: Optional[bool] = Field(None, description="Read only for this table only")
    reference_qual: Optional[str] = Field(None, description="Reference qualifier for this table only")
    attributes: Optional[str] = Field(None, description="Field attributes for this table only")
    calculation: Optional[str] = Field(None, description="Calculation script for this table only")


class DeleteDictionaryOverrideParams(BaseModel):
    """Parameters for deleting a dictionary override."""

    override_id: str = Field(
        ..., description="sys_dictionary_override sys_id (optionally prefixed with 'sys_id:')"
    )


class DictionaryOverrideResponse(BaseModel):
    """Response from dictionary override operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    override_id: Optional[str] = Field(None, description="sys_id of the affected override")
    override_name: Optional[str] = Field(None, description="Label of the affected override")


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_dictionary_override record to a clean dict."""
    return {
        "sys_id": item.get("sys_id"),
        "table": item.get("name"),
        "element": item.get("element"),
        "base_table": item.get("base_table"),
        "default_value": item.get("default_value"),
        "default_value_override": item.get("default_value_override") == "true",
        "mandatory": item.get("mandatory") == "true",
        "mandatory_override": item.get("mandatory_override") == "true",
        "read_only": item.get("read_only") == "true",
        "read_only_override": item.get("read_only_override") == "true",
        "reference_qual": item.get("reference_qual"),
        "reference_qual_override": item.get("reference_qual_override") == "true",
        "attributes": item.get("attributes"),
        "attributes_override": item.get("attributes_override") == "true",
        "calculation": item.get("calculation"),
        "calculation_override": item.get("calculation_override") == "true",
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
        "created_by": _dv(item.get("sys_created_by")),
        "updated_by": _dv(item.get("sys_updated_by")),
    }


def _build_body(params: BaseModel) -> Dict[str, Any]:
    """Build the request body, including only provided (non-None) fields.

    Every overridable value implies its override flag — the value alone is
    ignored by ServiceNow unless the flag is on.
    """
    body: Dict[str, Any] = {}

    table = getattr(params, "table", None)
    if table is not None:
        body["name"] = table

    for attr in ("element", "base_table"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    for value_field, flag_field in _OVERRIDE_FLAGS.items():
        value = getattr(params, value_field, None)
        if value is None:
            continue
        body[value_field] = str(value).lower() if isinstance(value, bool) else value
        body[flag_field] = "true"

    return body


def list_dictionary_overrides(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListDictionaryOverridesParams,
) -> Dict[str, Any]:
    """List dictionary overrides (sys_dictionary_override) from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the list of dictionary overrides.
    """
    try:
        url = f"{config.instance_url}/api/now/table/sys_dictionary_override"

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        query_parts = []
        if params.table:
            query_parts.append(f"name={params.table}")
        if params.element:
            query_parts.append(f"element={params.element}")
        if params.base_table:
            query_parts.append(f"base_table={params.base_table}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        overrides = [_serialize(item) for item in data.get("result", [])]

        return {
            "success": True,
            "message": f"Found {len(overrides)} dictionary overrides",
            "dictionary_overrides": overrides,
            "total": len(overrides),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing dictionary overrides: {e}")
        return {
            "success": False,
            "message": f"Error listing dictionary overrides: {str(e)}",
            "dictionary_overrides": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_dictionary_override(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDictionaryOverrideParams,
) -> Dict[str, Any]:
    """Get a specific dictionary override from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A dictionary containing the dictionary override data.
    """
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        # There is no meaningful "name" key on this table (name is the table), so
        # resolve by sys_id only.
        if params.override_id.startswith("sys_id:"):
            sys_id = params.override_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sys_dictionary_override/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sys_dictionary_override"
            query_params["sysparm_query"] = f"sys_id={params.override_id}"

        headers = auth_manager.get_headers()
        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Dictionary override not found: {params.override_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Dictionary override not found: {params.override_id}",
                }
            item = result[0]
        else:
            item = result

        return {
            "success": True,
            "message": f"Found dictionary override: {item.get('name')}.{item.get('element')}",
            "dictionary_override": _serialize(item),
        }

    except Exception as e:
        logger.error(f"Error getting dictionary override: {e}")
        return {
            "success": False,
            "message": f"Error getting dictionary override: {str(e)}",
        }


def create_dictionary_override(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateDictionaryOverrideParams,
) -> DictionaryOverrideResponse:
    """Create a new dictionary override in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    url = f"{config.instance_url}/api/now/table/sys_dictionary_override"
    body = _build_body(params)

    headers = auth_manager.get_headers()
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return DictionaryOverrideResponse(
                success=False,
                message="Failed to create dictionary override",
            )

        result = data["result"]
        label = f"{params.table}.{params.element}"
        return DictionaryOverrideResponse(
            success=True,
            message=f"Created dictionary override: {label}",
            override_id=result.get("sys_id"),
            override_name=label,
        )

    except Exception as e:
        logger.error(f"Error creating dictionary override: {e}")
        return DictionaryOverrideResponse(
            success=False,
            message=f"Error creating dictionary override: {str(e)}",
        )


def update_dictionary_override(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateDictionaryOverrideParams,
) -> DictionaryOverrideResponse:
    """Update an existing dictionary override in ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetDictionaryOverrideParams(override_id=params.override_id)
    get_result = get_dictionary_override(config, auth_manager, get_params)

    if not get_result["success"]:
        return DictionaryOverrideResponse(success=False, message=get_result["message"])

    override = get_result["dictionary_override"]
    sys_id = override["sys_id"]
    label = f"{override['table']}.{override['element']}"

    url = f"{config.instance_url}/api/now/table/sys_dictionary_override/{sys_id}"
    body = _build_body(params)

    if not body:
        return DictionaryOverrideResponse(
            success=True,
            message=f"No changes to update for dictionary override: {label}",
            override_id=sys_id,
            override_name=label,
        )

    headers = auth_manager.get_headers()
    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return DictionaryOverrideResponse(
                success=False,
                message=f"Failed to update dictionary override: {label}",
            )

        return DictionaryOverrideResponse(
            success=True,
            message=f"Updated dictionary override: {label}",
            override_id=sys_id,
            override_name=label,
        )

    except Exception as e:
        logger.error(f"Error updating dictionary override: {e}")
        return DictionaryOverrideResponse(
            success=False,
            message=f"Error updating dictionary override: {str(e)}",
        )


def delete_dictionary_override(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteDictionaryOverrideParams,
) -> DictionaryOverrideResponse:
    """Delete a dictionary override from ServiceNow.

    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.

    Returns:
        A response indicating the result of the operation.
    """
    get_params = GetDictionaryOverrideParams(override_id=params.override_id)
    get_result = get_dictionary_override(config, auth_manager, get_params)

    if not get_result["success"]:
        return DictionaryOverrideResponse(success=False, message=get_result["message"])

    override = get_result["dictionary_override"]
    sys_id = override["sys_id"]
    label = f"{override['table']}.{override['element']}"

    url = f"{config.instance_url}/api/now/table/sys_dictionary_override/{sys_id}"

    headers = auth_manager.get_headers()
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return DictionaryOverrideResponse(
            success=True,
            message=f"Deleted dictionary override: {label}",
            override_id=sys_id,
            override_name=label,
        )

    except Exception as e:
        logger.error(f"Error deleting dictionary override: {e}")
        return DictionaryOverrideResponse(
            success=False,
            message=f"Error deleting dictionary override: {str(e)}",
        )
