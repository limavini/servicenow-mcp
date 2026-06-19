"""
Generic read-only tools for the ServiceNow MCP server.

This module provides a single escape-hatch tool, ``query_table``, that reads
records from *any* ServiceNow table via the REST Table API. It exists to cover
the long tail of tables that do not have a dedicated, typed toolset.

It is intentionally **read-only**: there is no generic create/update/delete.
Writes should go through a dedicated, typed tool so the field contract and any
business rules stay explicit and auditable.
"""

import logging
import os
from typing import List, Optional

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
