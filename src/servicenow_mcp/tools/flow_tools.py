"""
Flow Designer (read-only) tools for the ServiceNow MCP server.

Flow Designer flows are stored across several ``sys_hub_*`` tables (the flow
record, its trigger, action instances and flow-logic instances), and the engine
runs a *compiled snapshot* rather than these design-time rows. Creating a runnable
flow purely through the Table API is impractical and unsupported (see
``docs/flow_designer.md``), so this module is intentionally **read-only**: it lists
flows and assembles a single flow's design-time structure for inspection/auditing.

Two storage models exist and this module transparently handles both:

* **Flow Engine V1** (pre-Washington DC): ``sys_hub_action_instance``,
  ``sys_hub_trigger_instance``, ``sys_hub_flow_logic``.
* **Flow Engine V2** (Washington DC+): ``sys_hub_action_instance_v2``,
  ``sys_hub_trigger_instance_v2``, ``sys_hub_flow_logic_instance_v2``.

For each component group it queries the V2 table first and falls back to V1, and
reports the detected ``engine_version``. The large compressed ``values`` /
``trigger_inputs`` / ``trigger_outputs`` blobs are deliberately **not** fetched —
they would bloat the response and are opaque (gzip+base64 JSON on V2). Use the
generic ``query_table`` tool if you need the raw blob for a specific row.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_FLOW_TABLE = "sys_hub_flow"
_FLOW_FIELDS = (
    "sys_id,name,internal_name,sys_name,type,active,status,description,"
    "sys_scope,master_snapshot,latest_snapshot,sys_class_name,"
    "sys_updated_on,sys_updated_by"
)

# (v2 table, v1 table) pairs for each component group.
_TRIGGER_TABLES = ("sys_hub_trigger_instance_v2", "sys_hub_trigger_instance")
_ACTION_TABLES = ("sys_hub_action_instance_v2", "sys_hub_action_instance")
_LOGIC_TABLES = ("sys_hub_flow_logic_instance_v2", "sys_hub_flow_logic")

_TRIGGER_FIELDS = (
    "sys_id,name,trigger_type,trigger_definition,display_text,comment,"
    "order,sys_class_name"
)
_ACTION_FIELDS = (
    "sys_id,order,action_type,action_type_parent,ui_id,parent_ui_id,"
    "display_text,comment,sys_class_name"
)
_LOGIC_FIELDS = (
    "sys_id,order,logic_definition,connected_to,ui_id,parent_ui_id,"
    "display_text,comment,sys_class_name"
)


class ListFlowsParams(BaseModel):
    """Parameters for listing Flow Designer flows (sys_hub_flow)."""

    limit: int = Field(20, description="Maximum number of flows to return")
    offset: int = Field(0, description="Offset for pagination")
    name: Optional[str] = Field(None, description="Filter by name (LIKE match)")
    active: Optional[bool] = Field(None, description="Filter by active status")
    flow_type: Optional[str] = Field(
        None,
        description="Filter by Flow Type, e.g. 'flow' or 'subflow' (the stored 'type' value).",
    )
    query: Optional[str] = Field(
        None, description="Additional raw ServiceNow encoded query, ANDed with the other filters."
    )


class GetFlowParams(BaseModel):
    """Parameters for getting a single flow and its design-time structure."""

    flow_id: str = Field(
        ...,
        description=(
            "Flow sys_id (prefix with 'sys_id:') or a flow name / internal_name. "
            "When a name is given the first matching sys_hub_flow record is used."
        ),
    )
    include_components: bool = Field(
        True,
        description="Also fetch the trigger, action instances and flow-logic instances (in order).",
    )


def _display(value: Any) -> Any:
    """Return display_value if the field is a reference dict, else the raw value."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _serialize_flow(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map a raw sys_hub_flow record to a clean dict."""
    master = _display(item.get("master_snapshot"))
    return {
        "sys_id": item.get("sys_id"),
        "name": _display(item.get("name")) or _display(item.get("sys_name")),
        "internal_name": item.get("internal_name"),
        "type": _display(item.get("type")),
        "active": item.get("active") == "true",
        "status": _display(item.get("status")),
        "description": item.get("description"),
        "scope": _display(item.get("sys_scope")),
        "master_snapshot": master,
        "latest_snapshot": _display(item.get("latest_snapshot")),
        # The runtime executes the compiled master snapshot; if absent the flow
        # has never been published/compiled and will not run.
        "has_snapshot": bool(master),
        "updated_on": item.get("sys_updated_on"),
        "updated_by": _display(item.get("sys_updated_by")),
    }


def _serialize_trigger(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "name": _display(item.get("name")),
        "trigger_type": _display(item.get("trigger_type")),
        "trigger_definition": _display(item.get("trigger_definition")),
        "label": _display(item.get("display_text")),
        "comment": item.get("comment"),
    }


def _serialize_action(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "order": item.get("order"),
        "action_type": _display(item.get("action_type")),
        "action_type_parent": _display(item.get("action_type_parent")),
        "label": _display(item.get("display_text")),
        "ui_id": item.get("ui_id"),
        "parent_ui_id": item.get("parent_ui_id"),
        "comment": item.get("comment"),
    }


def _serialize_logic(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "order": item.get("order"),
        "logic_definition": _display(item.get("logic_definition")),
        "connected_to": item.get("connected_to"),
        "label": _display(item.get("display_text")),
        "ui_id": item.get("ui_id"),
        "parent_ui_id": item.get("parent_ui_id"),
        "comment": item.get("comment"),
    }


def _query(
    config: ServerConfig,
    auth_manager: AuthManager,
    table: str,
    query: str,
    fields: str,
    order_by: Optional[str] = None,
    limit: int = 500,
) -> Optional[List[Dict[str, Any]]]:
    """GET rows from a table. Returns a list, or None if the request failed.

    A None result (HTTP error) typically means the table does not exist on this
    instance's Flow Engine version — the caller uses that to fall back V2 -> V1.
    """
    url = f"{config.instance_url}/api/now/table/{table}"
    full_query = query
    if order_by:
        full_query = f"{query}^ORDERBY{order_by}"
    query_params = {
        "sysparm_limit": limit,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": fields,
        "sysparm_query": full_query,
    }
    try:
        response = requests.get(
            url, params=query_params, headers=auth_manager.get_headers(), timeout=30
        )
        response.raise_for_status()
        return response.json().get("result", [])
    except requests.RequestException as e:
        logger.info("Flow query on '%s' failed (engine version mismatch?): %s", table, e)
        return None


def _fetch_components(
    config: ServerConfig,
    auth_manager: AuthManager,
    tables: tuple,
    query: str,
    fields: str,
    order_by: Optional[str] = None,
) -> tuple:
    """Try the V2 table then the V1 table. Returns (rows, engine) where engine is
    'v2', 'v1', or 'unknown' (neither table had any rows)."""
    v2_table, v1_table = tables
    v2_rows = _query(config, auth_manager, v2_table, query, fields, order_by)
    if v2_rows:
        return v2_rows, "v2"
    v1_rows = _query(config, auth_manager, v1_table, query, fields, order_by)
    if v1_rows:
        return v1_rows, "v1"
    # Neither had rows; preserve an empty list if either table actually exists.
    if v2_rows is not None:
        return [], "v2"
    if v1_rows is not None:
        return [], "v1"
    return [], "unknown"


def list_flows(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListFlowsParams,
) -> Dict[str, Any]:
    """List Flow Designer flows (and subflows) from ServiceNow."""
    try:
        url = f"{config.instance_url}/api/now/table/{_FLOW_TABLE}"
        query_parts: List[str] = []
        if params.name:
            query_parts.append(f"nameLIKE{params.name}")
        if params.active is not None:
            query_parts.append(f"active={str(params.active).lower()}")
        if params.flow_type:
            query_parts.append(f"type={params.flow_type}")
        if params.query:
            query_parts.append(params.query)

        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": _FLOW_FIELDS,
        }
        if query_parts:
            query_params["sysparm_query"] = "^".join(query_parts)

        response = requests.get(
            url, params=query_params, headers=auth_manager.get_headers(), timeout=30
        )
        response.raise_for_status()
        items = [_serialize_flow(i) for i in response.json().get("result", [])]
        return {
            "success": True,
            "message": f"Found {len(items)} flow(s)",
            "flows": items,
            "total": len(items),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing flows: {e}")
        return {
            "success": False,
            "message": f"Error listing flows: {str(e)}",
            "flows": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def _resolve_flow(
    config: ServerConfig,
    auth_manager: AuthManager,
    flow_id: str,
) -> Optional[Dict[str, Any]]:
    """Resolve a flow record by 'sys_id:<id>' or by name / internal_name."""
    headers = auth_manager.get_headers()
    base = f"{config.instance_url}/api/now/table/{_FLOW_TABLE}"
    common = {
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": _FLOW_FIELDS,
    }
    if flow_id.startswith("sys_id:"):
        sys_id = flow_id.replace("sys_id:", "")
        response = requests.get(f"{base}/{sys_id}", params=common, headers=headers, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        result = response.json().get("result")
        return result if result else None

    params = dict(common)
    params["sysparm_query"] = f"name={flow_id}^ORinternal_name={flow_id}"
    params["sysparm_limit"] = 1
    response = requests.get(base, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json().get("result", [])
    return result[0] if result else None


def get_flow(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetFlowParams,
) -> Dict[str, Any]:
    """Get a single flow and assemble its design-time structure (trigger, actions,
    flow-logic) in order. Read-only — see docs/flow_designer.md for the model."""
    try:
        record = _resolve_flow(config, auth_manager, params.flow_id)
    except requests.RequestException as e:
        logger.error(f"Error resolving flow '{params.flow_id}': {e}")
        return {"success": False, "message": f"Error resolving flow: {str(e)}"}

    if not record:
        return {"success": False, "message": f"Flow not found: {params.flow_id}"}

    flow = _serialize_flow(record)
    sys_id = flow["sys_id"]
    result: Dict[str, Any] = {
        "success": True,
        "message": f"Found flow: {flow['name']}",
        "flow": flow,
        "notes": (
            "Design-time view. The runtime executes the compiled snapshot "
            "(master_snapshot); component rows alone are not runnable without a "
            "publish/compile. Input/output values are omitted here (V2 stores them "
            "as a compressed blob in 'values'/'trigger_inputs'/'trigger_outputs'). "
            "See docs/flow_designer.md."
        ),
    }

    if not params.include_components:
        return result

    flow_query = f"flow={sys_id}"
    triggers, t_engine = _fetch_components(
        config, auth_manager, _TRIGGER_TABLES, flow_query, _TRIGGER_FIELDS, order_by="order"
    )
    actions, a_engine = _fetch_components(
        config, auth_manager, _ACTION_TABLES, flow_query, _ACTION_FIELDS, order_by="order"
    )
    logic, l_engine = _fetch_components(
        config, auth_manager, _LOGIC_TABLES, flow_query, _LOGIC_FIELDS, order_by="order"
    )

    engine = next((e for e in (a_engine, t_engine, l_engine) if e != "unknown"), "unknown")
    result["engine_version"] = engine
    result["trigger"] = _serialize_trigger(triggers[0]) if triggers else None
    result["actions"] = [_serialize_action(a) for a in actions]
    result["logic"] = [_serialize_logic(x) for x in logic]
    result["component_counts"] = {
        "triggers": len(triggers),
        "actions": len(actions),
        "logic": len(logic),
    }
    return result
