"""
Generic escape-hatch tools for the ServiceNow MCP server.

This module provides escape-hatch tools that operate on *any* ServiceNow table
via the REST Table API, to cover the long tail of tables/fields that do not have
a dedicated, typed toolset:

- ``query_table``  — read records (read-only).
- ``insert_table`` — insert a record with an arbitrary field map.
- ``update_table`` — patch arbitrary fields on an existing record.

Prefer a dedicated, typed tool when one exists, so the field contract and any
business rules stay explicit and auditable. ``insert_table`` / ``update_table``
exist for fields the typed tools cannot set (e.g. ``catalog_script_client.cat_variable``,
``item_option_new.use_reference_qualifier``) and for tables with no typed toolset
(e.g. m2m and variable-set tables). The same env guard-rails as ``query_table``
apply.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Optional guard-rails. Comma-separated lists of table names.
# Denylist always wins; if an allowlist is set, only those tables are readable.
_DENY_ENV = "SERVICENOW_QUERY_TABLE_DENYLIST"
_ALLOW_ENV = "SERVICENOW_QUERY_TABLE_ALLOWLIST"


class QueryTableParams(BaseModel):
    """Parameters for a generic read-only table query."""

    table: str = Field(
        ...,
        description="Table name to read, e.g. 'cmdb_ci', 'sys_user', 'x_custom_app_table'.",
    )
    query: Optional[str] = Field(
        None,
        description=(
            "ServiceNow encoded query, e.g. 'active=true^priority=1' or "
            "'nameLIKEserver^ORDERBYsys_created_on'. Omit to return all records."
        ),
    )
    fields: Optional[List[str]] = Field(
        None,
        description=(
            "Columns to return. Strongly recommended for wide tables (e.g. CMDB) "
            "to avoid returning hundreds of fields. Omit to return all columns."
        ),
    )
    limit: int = Field(20, description="Maximum number of records to return.")
    offset: int = Field(0, description="Offset for pagination.")
    display_value: bool = Field(
        True,
        description="Return human-readable display values instead of raw sys_ids/codes.",
    )


def _table_blocked(table: str) -> Optional[str]:
    """Return a reason string if the table is blocked by env guard-rails, else None."""
    table = table.strip()
    deny = {t.strip() for t in os.getenv(_DENY_ENV, "").split(",") if t.strip()}
    allow = {t.strip() for t in os.getenv(_ALLOW_ENV, "").split(",") if t.strip()}
    if table in deny:
        return f"Table '{table}' is blocked by {_DENY_ENV}."
    if allow and table not in allow:
        return f"Table '{table}' is not in {_ALLOW_ENV}."
    return None


def query_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: QueryTableParams,
) -> dict:
    """
    Read records from any ServiceNow table via the REST Table API (read-only).

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for the query.

    Returns:
        Dictionary with the matching records (or an error message).
    """
    blocked = _table_blocked(params.table)
    if blocked:
        logger.warning("query_table denied: %s", blocked)
        return {"success": False, "message": blocked, "records": []}

    api_url = f"{config.api_url}/table/{params.table}"

    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": str(params.display_value).lower(),
        "sysparm_exclude_reference_link": "true",
    }
    if params.query:
        query_params["sysparm_query"] = params.query
    if params.fields:
        query_params["sysparm_fields"] = ",".join(params.fields)

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Error querying table '%s': %s", params.table, e)
        return {
            "success": False,
            "message": f"Error querying table '{params.table}': {e}",
            "records": [],
        }

    records = response.json().get("result", [])
    return {
        "success": True,
        "message": f"Found {len(records)} record(s) in '{params.table}'.",
        "table": params.table,
        "count": len(records),
        "records": records,
    }


class InsertTableParams(BaseModel):
    """Parameters for a generic record insert."""

    table: str = Field(
        ...,
        description="Table name to insert into, e.g. 'sc_cat_item_user_criteria_mtom', 'item_option_new_set'.",
    )
    fields: Dict[str, Any] = Field(
        ...,
        description=(
            "Map of column name -> value for the new record, e.g. "
            "{'sc_cat_item': '<sys_id>', 'user_criteria': '<sys_id>'}. "
            "Booleans/numbers are accepted; they are sent to ServiceNow as-is."
        ),
    )


class UpdateTableParams(BaseModel):
    """Parameters for a generic record update (PATCH)."""

    table: str = Field(
        ...,
        description="Table name of the record to update, e.g. 'catalog_script_client', 'item_option_new'.",
    )
    sys_id: str = Field(
        ...,
        description="sys_id of the record to update.",
    )
    fields: Dict[str, Any] = Field(
        ...,
        description=(
            "Map of column name -> value to patch, e.g. "
            "{'use_reference_qualifier': 'advanced', 'reference_qual': 'javascript:...'}. "
            "Only the provided columns are changed."
        ),
    )


def insert_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: InsertTableParams,
) -> dict:
    """
    Insert a record into any ServiceNow table via the REST Table API.

    Escape hatch for tables without a dedicated, typed create tool (e.g. m2m
    tables, variable sets). Prefer a typed tool when one exists.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for the insert (table + field map).

    Returns:
        Dictionary with the created record's sys_id (or an error message).
    """
    blocked = _table_blocked(params.table)
    if blocked:
        logger.warning("insert_table denied: %s", blocked)
        return {"success": False, "message": blocked, "record": None}

    api_url = f"{config.api_url}/table/{params.table}"

    try:
        response = requests.post(
            api_url,
            json=params.fields,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Error inserting into table '%s': %s", params.table, e)
        return {
            "success": False,
            "message": f"Error inserting into table '{params.table}': {e}",
            "record": None,
        }

    try:
        record = response.json().get("result", {})
    except ValueError:
        return {
            "success": False,
            "message": f"Non-JSON response from insert into '{params.table}' (HTTP {response.status_code}).",
            "status_code": response.status_code,
            "body": response.text[:1000],
            "record": None,
        }
    return {
        "success": True,
        "message": f"Inserted record into '{params.table}'.",
        "table": params.table,
        "sys_id": record.get("sys_id"),
        "record": record,
    }


def update_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateTableParams,
) -> dict:
    """
    Patch arbitrary fields on an existing record in any ServiceNow table.

    Escape hatch for fields the dedicated, typed tools cannot set (e.g.
    ``catalog_script_client.cat_variable``, ``item_option_new.use_reference_qualifier``).
    Prefer a typed tool when it covers the field you need.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for the update (table + sys_id + field map).

    Returns:
        Dictionary with the updated record (or an error message).
    """
    blocked = _table_blocked(params.table)
    if blocked:
        logger.warning("update_table denied: %s", blocked)
        return {"success": False, "message": blocked, "record": None}

    api_url = f"{config.api_url}/table/{params.table}/{params.sys_id}"

    # Some ServiceNow front-ends / proxies reject a raw HTTP PATCH. Route the partial
    # update through POST with the standard method override, which follows the same
    # path as the working typed create tools.
    headers = dict(auth_manager.get_headers())
    headers["X-HTTP-Method-Override"] = "PATCH"

    try:
        response = requests.post(
            api_url,
            json=params.fields,
            headers=headers,
            timeout=config.timeout,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Error updating table '%s' record '%s': %s", params.table, params.sys_id, e)
        return {
            "success": False,
            "message": f"Error updating table '{params.table}' record '{params.sys_id}': {e}",
            "record": None,
        }

    try:
        record = response.json().get("result", {})
    except ValueError:
        return {
            "success": False,
            "message": f"Non-JSON response updating '{params.table}' (HTTP {response.status_code}).",
            "status_code": response.status_code,
            "body": response.text[:1000],
            "record": None,
        }
    return {
        "success": True,
        "message": f"Updated record '{params.sys_id}' in '{params.table}'.",
        "table": params.table,
        "sys_id": params.sys_id,
        "record": record,
    }
