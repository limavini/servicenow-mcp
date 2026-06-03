"""
Record Producer tools for the ServiceNow MCP server.

This module provides tools for managing record producers in ServiceNow.
A record producer is a special catalog item (table ``sc_cat_item_producer``,
which extends ``sc_cat_item``) that creates a record on a target table
(``table_name``) from catalog variables submitted through the Service Catalog
or Service Portal.
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
    "sys_id,name,short_description,description,table_name,category,sc_catalogs,"
    "active,script,redirect,sys_class_name,sys_created_on,sys_updated_on,"
    "sys_created_by,sys_updated_by"
)


class ListRecordProducersParams(BaseModel):
    """Parameters for listing record producers."""

    limit: int = Field(10, description="Maximum number of record producers to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    table_name: Optional[str] = Field(None, description="Filter by target table name (e.g. incident)")
    query: Optional[str] = Field(None, description="Search query matched against the record producer name")


class GetRecordProducerParams(BaseModel):
    """Parameters for getting a record producer."""

    record_producer_id: str = Field(..., description="Record producer sys_id (prefix with 'sys_id:') or name")


class CreateRecordProducerParams(BaseModel):
    """Parameters for creating a record producer."""

    name: str = Field(..., description="Name of the record producer")
    table_name: str = Field(..., description="Target table the record producer creates a record on (e.g. incident)")
    short_description: Optional[str] = Field(None, description="Short description of the record producer")
    description: Optional[str] = Field(None, description="Full description (HTML allowed)")
    category: Optional[str] = Field(None, description="sys_id of the catalog category (sc_category) to file the item under")
    sc_catalogs: Optional[str] = Field(None, description="Comma-separated sys_id(s) of the catalog(s) (sc_catalog) the item belongs to. Required for Service Portal visibility.")
    script: Optional[str] = Field(None, description="Server script that runs on submit (has access to 'current' and 'producer')")
    redirect: Optional[str] = Field(None, description="Optional redirect target after submission")
    active: bool = Field(True, description="Whether the record producer is active")


class UpdateRecordProducerParams(BaseModel):
    """Parameters for updating a record producer."""

    record_producer_id: str = Field(..., description="Record producer sys_id (prefix with 'sys_id:') or name")
    name: Optional[str] = Field(None, description="Name of the record producer")
    table_name: Optional[str] = Field(None, description="Target table the record producer creates a record on")
    short_description: Optional[str] = Field(None, description="Short description of the record producer")
    description: Optional[str] = Field(None, description="Full description (HTML allowed)")
    category: Optional[str] = Field(None, description="sys_id of the catalog category (sc_category)")
    sc_catalogs: Optional[str] = Field(None, description="Comma-separated sys_id(s) of the catalog(s) (sc_catalog)")
    script: Optional[str] = Field(None, description="Server script that runs on submit")
    redirect: Optional[str] = Field(None, description="Optional redirect target after submission")
    active: Optional[bool] = Field(None, description="Whether the record producer is active")


class DeleteRecordProducerParams(BaseModel):
    """Parameters for deleting a record producer."""

    record_producer_id: str = Field(..., description="Record producer sys_id (prefix with 'sys_id:') or name")


class RecordProducerResponse(BaseModel):
    """Response from record producer operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    record_producer_id: Optional[str] = Field(None, description="sys_id of the affected record producer")
    record_producer_name: Optional[str] = Field(None, description="Name of the affected record producer")


def _build_body(params) -> Dict[str, Any]:
    """Build a create/update body including only provided (non-None) fields."""
    body: Dict[str, Any] = {}

    if getattr(params, "name", None) is not None:
        body["name"] = params.name
    if getattr(params, "table_name", None) is not None:
        body["table_name"] = params.table_name
    if getattr(params, "short_description", None) is not None:
        body["short_description"] = params.short_description
    if getattr(params, "description", None) is not None:
        body["description"] = params.description
    if getattr(params, "category", None) is not None:
        body["category"] = params.category
    if getattr(params, "sc_catalogs", None) is not None:
        body["sc_catalogs"] = params.sc_catalogs
    if getattr(params, "script", None) is not None:
        body["script"] = params.script
    if getattr(params, "redirect", None) is not None:
        body["redirect"] = params.redirect
    if getattr(params, "active", None) is not None:
        body["active"] = str(params.active).lower()

    return body


def list_record_producers(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListRecordProducersParams,
) -> Dict[str, Any]:
    """List record producers from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/sc_cat_item_producer"

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
        if params.table_name:
            query_parts.append(f"table_name={params.table_name}")
        if params.query:
            query_parts.append(f"nameLIKE{params.query}")
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        headers = auth_manager.get_headers()

        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        producers = []
        for item in data.get("result", []):
            producers.append(
                {
                    "sys_id": item.get("sys_id"),
                    "name": item.get("name"),
                    "short_description": item.get("short_description"),
                    "table_name": item.get("table_name"),
                    "category": item.get("category"),
                    "sc_catalogs": item.get("sc_catalogs"),
                    "active": item.get("active") == "true",
                    "created_on": item.get("sys_created_on"),
                    "updated_on": item.get("sys_updated_on"),
                }
            )

        return {
            "success": True,
            "message": f"Found {len(producers)} record producers",
            "record_producers": producers,
            "total": len(producers),
            "limit": params.limit,
            "offset": params.offset,
        }

    except Exception as e:
        logger.error(f"Error listing record producers: {e}")
        return {
            "success": False,
            "message": f"Error listing record producers: {str(e)}",
            "record_producers": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_record_producer(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRecordProducerParams,
) -> Dict[str, Any]:
    """Get a specific record producer from ServiceNow."""
    try:
        query_params = {
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FIELDS,
        }

        if params.record_producer_id.startswith("sys_id:"):
            sys_id = params.record_producer_id.replace("sys_id:", "")
            url = f"{config.instance_url}/api/now/table/sc_cat_item_producer/{sys_id}"
        else:
            url = f"{config.instance_url}/api/now/table/sc_cat_item_producer"
            query_params["sysparm_query"] = f"name={params.record_producer_id}"

        headers = auth_manager.get_headers()

        response = requests.get(url, params=query_params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return {
                "success": False,
                "message": f"Record producer not found: {params.record_producer_id}",
            }

        result = data["result"]
        if isinstance(result, list):
            if not result:
                return {
                    "success": False,
                    "message": f"Record producer not found: {params.record_producer_id}",
                }
            item = result[0]
        else:
            item = result

        record_producer = {
            "sys_id": item.get("sys_id"),
            "name": item.get("name"),
            "short_description": item.get("short_description"),
            "description": item.get("description"),
            "table_name": item.get("table_name"),
            "category": item.get("category"),
            "sc_catalogs": item.get("sc_catalogs"),
            "active": item.get("active") == "true",
            "script": item.get("script"),
            "redirect": item.get("redirect"),
            "sys_class_name": item.get("sys_class_name"),
            "created_on": item.get("sys_created_on"),
            "updated_on": item.get("sys_updated_on"),
        }

        return {
            "success": True,
            "message": f"Found record producer: {item.get('name')}",
            "record_producer": record_producer,
        }

    except Exception as e:
        logger.error(f"Error getting record producer: {e}")
        return {
            "success": False,
            "message": f"Error getting record producer: {str(e)}",
        }


def create_record_producer(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateRecordProducerParams,
) -> RecordProducerResponse:
    """Create a new record producer in ServiceNow.

    POSTing to the ``sc_cat_item_producer`` table sets ``sys_class_name`` to
    ``sc_cat_item_producer`` automatically.
    """
    url = f"{config.instance_url}/api/now/table/sc_cat_item_producer"

    body = _build_body(params)

    headers = auth_manager.get_headers()

    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return RecordProducerResponse(
                success=False,
                message="Failed to create record producer",
            )

        result = data["result"]
        return RecordProducerResponse(
            success=True,
            message=f"Created record producer: {result.get('name')}",
            record_producer_id=result.get("sys_id"),
            record_producer_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error creating record producer: {e}")
        return RecordProducerResponse(
            success=False,
            message=f"Error creating record producer: {str(e)}",
        )


def update_record_producer(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateRecordProducerParams,
) -> RecordProducerResponse:
    """Update an existing record producer in ServiceNow."""
    get_params = GetRecordProducerParams(record_producer_id=params.record_producer_id)
    get_result = get_record_producer(config, auth_manager, get_params)

    if not get_result["success"]:
        return RecordProducerResponse(
            success=False,
            message=get_result["message"],
        )

    record_producer = get_result["record_producer"]
    sys_id = record_producer["sys_id"]

    url = f"{config.instance_url}/api/now/table/sc_cat_item_producer/{sys_id}"

    body = _build_body(params)

    if not body:
        return RecordProducerResponse(
            success=True,
            message=f"No changes to update for record producer: {record_producer['name']}",
            record_producer_id=sys_id,
            record_producer_name=record_producer["name"],
        )

    headers = auth_manager.get_headers()

    try:
        response = requests.patch(url, json=body, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if "result" not in data:
            return RecordProducerResponse(
                success=False,
                message=f"Failed to update record producer: {record_producer['name']}",
            )

        result = data["result"]
        return RecordProducerResponse(
            success=True,
            message=f"Updated record producer: {result.get('name')}",
            record_producer_id=result.get("sys_id"),
            record_producer_name=result.get("name"),
        )

    except Exception as e:
        logger.error(f"Error updating record producer: {e}")
        return RecordProducerResponse(
            success=False,
            message=f"Error updating record producer: {str(e)}",
        )


def delete_record_producer(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteRecordProducerParams,
) -> RecordProducerResponse:
    """Delete a record producer from ServiceNow."""
    get_params = GetRecordProducerParams(record_producer_id=params.record_producer_id)
    get_result = get_record_producer(config, auth_manager, get_params)

    if not get_result["success"]:
        return RecordProducerResponse(
            success=False,
            message=get_result["message"],
        )

    record_producer = get_result["record_producer"]
    sys_id = record_producer["sys_id"]
    name = record_producer["name"]

    url = f"{config.instance_url}/api/now/table/sc_cat_item_producer/{sys_id}"

    headers = auth_manager.get_headers()

    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        return RecordProducerResponse(
            success=True,
            message=f"Deleted record producer: {name}",
            record_producer_id=sys_id,
            record_producer_name=name,
        )

    except Exception as e:
        logger.error(f"Error deleting record producer: {e}")
        return RecordProducerResponse(
            success=False,
            message=f"Error deleting record producer: {str(e)}",
        )
