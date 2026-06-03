"""
Catalog Item Variables tools for the ServiceNow MCP server.

This module provides tools for managing variables (form fields) in ServiceNow catalog items.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class CreateCatalogItemVariableParams(BaseModel):
    """Parameters for creating a catalog item variable."""

    catalog_item_id: str = Field(..., description="The sys_id of the catalog item")
    name: str = Field(..., description="The name of the variable (internal name)")
    type: str = Field(..., description="The variable type. For record producers use the numeric type code as a string: 8=Reference, 5=Select Box, 2=Multi Line Text, 6=Single Line Text, 1=Yes/No, 7=CheckBox, 9=Date, 10=Date/Time.")
    label: str = Field(..., description="The display label for the variable")
    mandatory: bool = Field(False, description="Whether the variable is required")
    help_text: Optional[str] = Field(None, description="Help text to display with the variable")
    default_value: Optional[str] = Field(None, description="Default value for the variable")
    description: Optional[str] = Field(None, description="Description of the variable")
    order: Optional[int] = Field(None, description="Display order of the variable")
    reference_table: Optional[str] = Field(None, description="For reference fields, the table to reference")
    reference_qualifier: Optional[str] = Field(None, description="For reference fields, the query to filter reference options (e.g. 'active=true')")
    max_length: Optional[int] = Field(None, description="Maximum length for string fields")
    min: Optional[int] = Field(None, description="Minimum value for numeric fields")
    max: Optional[int] = Field(None, description="Maximum value for numeric fields")
    # Record-producer field-mapping attributes
    map_to_field: Optional[bool] = Field(None, description="For record producers: whether this variable maps directly to a field on the target table")
    field: Optional[str] = Field(None, description="For record producers: the target table field this variable maps to (e.g. 'caller_id', 'priority', 'description'). Requires map_to_field=True.")
    choice_table: Optional[str] = Field(None, description="For Select Box variables: the table whose choice list backs this variable (e.g. 'incident')")
    choice_field: Optional[str] = Field(None, description="For Select Box variables: the field on choice_table whose choices populate this variable (e.g. 'priority')")
    record_producer_table: Optional[str] = Field(None, description="The record producer's target table (e.g. 'incident'); set to match the producer's table_name")


class CatalogItemVariableResponse(BaseModel):
    """Response from catalog item variable operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    variable_id: Optional[str] = Field(None, description="The sys_id of the created/updated variable")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the variable")


class ListCatalogItemVariablesParams(BaseModel):
    """Parameters for listing catalog item variables."""

    catalog_item_id: str = Field(..., description="The sys_id of the catalog item")
    include_details: bool = Field(True, description="Whether to include detailed information about each variable")
    limit: Optional[int] = Field(None, description="Maximum number of variables to return")
    offset: Optional[int] = Field(None, description="Offset for pagination")


class ListCatalogItemVariablesResponse(BaseModel):
    """Response from listing catalog item variables."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    variables: List[Dict[str, Any]] = Field([], description="List of variables")
    count: int = Field(0, description="Total number of variables found")


class UpdateCatalogItemVariableParams(BaseModel):
    """Parameters for updating a catalog item variable."""

    variable_id: str = Field(..., description="The sys_id of the variable to update")
    label: Optional[str] = Field(None, description="The display label for the variable")
    mandatory: Optional[bool] = Field(None, description="Whether the variable is required")
    help_text: Optional[str] = Field(None, description="Help text to display with the variable")
    default_value: Optional[str] = Field(None, description="Default value for the variable")
    description: Optional[str] = Field(None, description="Description of the variable")
    order: Optional[int] = Field(None, description="Display order of the variable")
    reference_qualifier: Optional[str] = Field(None, description="For reference fields, the query to filter reference options")
    max_length: Optional[int] = Field(None, description="Maximum length for string fields")
    min: Optional[int] = Field(None, description="Minimum value for numeric fields")
    max: Optional[int] = Field(None, description="Maximum value for numeric fields")


def create_catalog_item_variable(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateCatalogItemVariableParams,
) -> CatalogItemVariableResponse:
    """
    Create a new variable (form field) for a catalog item.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating a catalog item variable.

    Returns:
        Response with information about the created variable.
    """
    api_url = f"{config.instance_url}/api/now/table/item_option_new"

    # Build request data
    data = {
        "cat_item": params.catalog_item_id,
        "name": params.name,
        "type": params.type,
        "question_text": params.label,
        "mandatory": str(params.mandatory).lower(),  # ServiceNow expects "true"/"false" strings
    }

    if params.help_text:
        data["help_text"] = params.help_text
    if params.default_value:
        data["default_value"] = params.default_value
    if params.description:
        data["description"] = params.description
    if params.order is not None:
        data["order"] = params.order
    if params.reference_table:
        data["reference"] = params.reference_table
    if params.reference_qualifier:
        data["reference_qual"] = params.reference_qualifier
    if params.max_length:
        data["max_length"] = params.max_length
    if params.min is not None:
        data["min"] = params.min
    if params.max is not None:
        data["max"] = params.max
    # Record-producer field-mapping attributes
    if params.map_to_field is not None:
        data["map_to_field"] = str(params.map_to_field).lower()
    if params.field is not None:
        data["field"] = params.field
    if params.choice_table:
        data["choice_table"] = params.choice_table
    if params.choice_field:
        data["choice_field"] = params.choice_field
    if params.record_producer_table:
        data["record_producer_table"] = params.record_producer_table

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return CatalogItemVariableResponse(
            success=True,
            message="Catalog item variable created successfully",
            variable_id=result.get("sys_id"),
            details=result,
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create catalog item variable: {e}")
        return CatalogItemVariableResponse(
            success=False,
            message=f"Failed to create catalog item variable: {str(e)}",
        )


def list_catalog_item_variables(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCatalogItemVariablesParams,
) -> ListCatalogItemVariablesResponse:
    """
    List all variables (form fields) for a catalog item.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing catalog item variables.

    Returns:
        Response with a list of variables for the catalog item.
    """
    # Build query parameters
    query_params = {
        "sysparm_query": f"cat_item={params.catalog_item_id}^ORDERBYorder",
    }
    
    if params.limit:
        query_params["sysparm_limit"] = params.limit
    if params.offset:
        query_params["sysparm_offset"] = params.offset
    
    # Include all fields if detailed info is requested
    if params.include_details:
        query_params["sysparm_display_value"] = "true"
        query_params["sysparm_exclude_reference_link"] = "false"
    else:
        query_params["sysparm_fields"] = "sys_id,name,type,question_text,order,mandatory"

    api_url = f"{config.instance_url}/api/now/table/item_option_new"

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", [])
        
        return ListCatalogItemVariablesResponse(
            success=True,
            message=f"Retrieved {len(result)} variables for catalog item",
            variables=result,
            count=len(result),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to list catalog item variables: {e}")
        return ListCatalogItemVariablesResponse(
            success=False,
            message=f"Failed to list catalog item variables: {str(e)}",
        )


def update_catalog_item_variable(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateCatalogItemVariableParams,
) -> CatalogItemVariableResponse:
    """
    Update an existing variable (form field) for a catalog item.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating a catalog item variable.

    Returns:
        Response with information about the updated variable.
    """
    api_url = f"{config.instance_url}/api/now/table/item_option_new/{params.variable_id}"

    # Build request data with only parameters that are provided
    data = {}
    
    if params.label is not None:
        data["question_text"] = params.label
    if params.mandatory is not None:
        data["mandatory"] = str(params.mandatory).lower()  # ServiceNow expects "true"/"false" strings
    if params.help_text is not None:
        data["help_text"] = params.help_text
    if params.default_value is not None:
        data["default_value"] = params.default_value
    if params.description is not None:
        data["description"] = params.description
    if params.order is not None:
        data["order"] = params.order
    if params.reference_qualifier is not None:
        data["reference_qual"] = params.reference_qualifier
    if params.max_length is not None:
        data["max_length"] = params.max_length
    if params.min is not None:
        data["min"] = params.min
    if params.max is not None:
        data["max"] = params.max

    # If no fields to update, return early
    if not data:
        return CatalogItemVariableResponse(
            success=False,
            message="No update parameters provided",
        )

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return CatalogItemVariableResponse(
            success=True,
            message="Catalog item variable updated successfully",
            variable_id=params.variable_id,
            details=result,
        )

    except requests.RequestException as e:
        logger.error(f"Failed to update catalog item variable: {e}")
        return CatalogItemVariableResponse(
            success=False,
            message=f"Failed to update catalog item variable: {str(e)}",
        ) 