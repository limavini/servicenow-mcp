"""
Form layout tools for the ServiceNow MCP server.

This module provides tools for managing the classic form layout records that
also drive Configurable Workspace record forms:

- ``sys_ui_view``          - the view a form layout belongs to (e.g. a workspace view)
- ``sys_ui_form``          - the form of a (table, view) pair
- ``sys_ui_form_section``  - orders the sections that make up a form
- ``sys_ui_section``       - a section (with its caption) of a form
- ``sys_ui_element``       - a field placed inside a section, at a position

Typical build order for a brand new workspace form:
create_ui_view -> create_ui_section (one per section) -> create_ui_element
(fields inside each section) -> create_ui_form -> create_ui_form_section
(one per section, ordering them on the form).
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

_AUDIT = "sys_created_on,sys_updated_on,sys_created_by,sys_updated_by"
_VIEW_FIELDS = f"sys_id,name,title,hidden,roles,{_AUDIT}"
_FORM_FIELDS = f"sys_id,name,view,roles,{_AUDIT}"
_FORM_SECTION_FIELDS = f"sys_id,sys_ui_form,sys_ui_section,position,{_AUDIT}"
_SECTION_FIELDS = f"sys_id,name,view,caption,title,header,roles,{_AUDIT}"
_ELEMENT_FIELDS = f"sys_id,sys_ui_section,element,position,type,sys_ui_formatter,{_AUDIT}"


def _dv(value):
    """Return a reference field's display value whether it came back as a dict
    (sysparm_display_value=all) or a plain string (sysparm_display_value=true
    with exclude_reference_link)."""
    if isinstance(value, dict):
        return value.get("display_value")
    return value


def _get_by_sys_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    table: str,
    record_id: str,
    fields: str,
) -> Dict[str, Any]:
    """Fetch a single record by sys_id (accepts an optional 'sys_id:' prefix)."""
    sys_id = record_id.replace("sys_id:", "")
    url = f"{config.instance_url}/api/now/table/{table}/{sys_id}"

    response = requests.get(
        url,
        params={
            "sysparm_display_value": "true",
            "sysparm_exclude_reference_link": "true",
            "sysparm_fields": fields,
        },
        headers=auth_manager.get_headers(),
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    result = data.get("result")
    if isinstance(result, list):
        result = result[0] if result else None
    if not result:
        raise ValueError(f"{table} not found: {record_id}")
    return result


def _list_records(
    config: ServerConfig,
    auth_manager: AuthManager,
    table: str,
    fields: str,
    query: Optional[str],
    limit: int,
    offset: int,
    order_by: Optional[str] = None,
) -> list:
    """Run a list query against a table and return the raw records."""
    query_params = {
        "sysparm_limit": limit,
        "sysparm_offset": offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
        "sysparm_fields": fields,
    }

    encoded = query or ""
    if order_by:
        encoded = f"{encoded}^ORDERBY{order_by}" if encoded else f"ORDERBY{order_by}"
    if encoded:
        query_params["sysparm_query"] = encoded

    response = requests.get(
        f"{config.instance_url}/api/now/table/{table}",
        params=query_params,
        headers=auth_manager.get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("result", [])


# ---------------------------------------------------------------------------
# Shared response model
# ---------------------------------------------------------------------------


class FormLayoutResponse(BaseModel):
    """Response from form layout operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    record_id: Optional[str] = Field(None, description="sys_id of the affected record")
    record_name: Optional[str] = Field(None, description="Label of the affected record")


# ---------------------------------------------------------------------------
# sys_ui_view
# ---------------------------------------------------------------------------


class ListUiViewsParams(BaseModel):
    """Parameters for listing UI views."""

    limit: int = Field(20, description="Maximum number of views to return")
    offset: int = Field(0, description="Offset for pagination")
    query: Optional[str] = Field(
        None, description="Search query matched against the view title (LIKE)"
    )


class CreateUiViewParams(BaseModel):
    """Parameters for creating a UI view."""

    name: str = Field(
        ...,
        description="Internal view name, lowercase with underscores (e.g. 'position_management_workspace_view')",
    )
    title: Optional[str] = Field(
        None, description="View title shown in the UI (e.g. 'Position Management Workspace View')"
    )
    hidden: Optional[bool] = Field(None, description="Whether the view is hidden from the view picker")
    roles: Optional[str] = Field(None, description="Comma-separated roles that can use the view")


def _serialize_view(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "name": item.get("name"),
        "title": item.get("title"),
        "hidden": item.get("hidden") == "true",
        "roles": item.get("roles"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def list_ui_views(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiViewsParams,
) -> Dict[str, Any]:
    """List UI views (sys_ui_view) from ServiceNow."""
    try:
        query = f"titleLIKE{params.query}" if params.query else None
        items = _list_records(
            config, auth_manager, "sys_ui_view", _VIEW_FIELDS, query, params.limit, params.offset
        )
        views = [_serialize_view(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(views)} UI views",
            "ui_views": views,
            "total": len(views),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI views: {e}")
        return {
            "success": False,
            "message": f"Error listing UI views: {str(e)}",
            "ui_views": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def create_ui_view(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiViewParams,
) -> FormLayoutResponse:
    """Create a new UI view (sys_ui_view) in ServiceNow."""
    body: Dict[str, Any] = {"name": params.name}
    if params.title is not None:
        body["title"] = params.title
    if params.hidden is not None:
        body["hidden"] = str(params.hidden).lower()
    if params.roles is not None:
        body["roles"] = params.roles

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ui_view",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        return FormLayoutResponse(
            success=True,
            message=f"Created UI view: {result.get('title') or result.get('name')}",
            record_id=result.get("sys_id"),
            record_name=result.get("title") or result.get("name"),
        )
    except Exception as e:
        logger.error(f"Error creating UI view: {e}")
        return FormLayoutResponse(success=False, message=f"Error creating UI view: {str(e)}")


# ---------------------------------------------------------------------------
# sys_ui_form
# ---------------------------------------------------------------------------


class ListUiFormsParams(BaseModel):
    """Parameters for listing UI forms."""

    limit: int = Field(20, description="Maximum number of forms to return")
    offset: int = Field(0, description="Offset for pagination")
    table: Optional[str] = Field(None, description="Filter by table name (the form's 'name' column)")
    view: Optional[str] = Field(None, description="Filter by view sys_id")


class CreateUiFormParams(BaseModel):
    """Parameters for creating a UI form."""

    table: str = Field(..., description="Table the form belongs to (stored in the 'name' column)")
    view: str = Field(..., description="View sys_id (sys_ui_view) the form belongs to")


def _serialize_form(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "table": item.get("name"),
        "view": _dv(item.get("view")),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def list_ui_forms(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiFormsParams,
) -> Dict[str, Any]:
    """List UI forms (sys_ui_form) from ServiceNow."""
    try:
        query_parts = []
        if params.table:
            query_parts.append(f"name={params.table}")
        if params.view:
            query_parts.append(f"view={params.view}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ui_form",
            _FORM_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
        )
        forms = [_serialize_form(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(forms)} UI forms",
            "ui_forms": forms,
            "total": len(forms),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI forms: {e}")
        return {
            "success": False,
            "message": f"Error listing UI forms: {str(e)}",
            "ui_forms": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def create_ui_form(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiFormParams,
) -> FormLayoutResponse:
    """Create a new UI form (sys_ui_form) in ServiceNow."""
    body = {"name": params.table, "view": params.view}

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ui_form",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = f"{params.table} / {params.view}"
        return FormLayoutResponse(
            success=True,
            message=f"Created UI form: {label}",
            record_id=result.get("sys_id"),
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error creating UI form: {e}")
        return FormLayoutResponse(success=False, message=f"Error creating UI form: {str(e)}")


# ---------------------------------------------------------------------------
# sys_ui_form_section
# ---------------------------------------------------------------------------


class ListUiFormSectionsParams(BaseModel):
    """Parameters for listing form-to-section links."""

    limit: int = Field(30, description="Maximum number of links to return")
    offset: int = Field(0, description="Offset for pagination")
    sys_ui_form: Optional[str] = Field(None, description="Filter by form sys_id (sys_ui_form)")
    sys_ui_section: Optional[str] = Field(None, description="Filter by section sys_id (sys_ui_section)")


class CreateUiFormSectionParams(BaseModel):
    """Parameters for adding a section to a form."""

    sys_ui_form: str = Field(..., description="Form sys_id (sys_ui_form)")
    sys_ui_section: str = Field(..., description="Section sys_id (sys_ui_section)")
    position: int = Field(..., description="Position of the section on the form (0-based)")


class UpdateUiFormSectionParams(BaseModel):
    """Parameters for updating a form-to-section link."""

    form_section_id: str = Field(..., description="sys_ui_form_section sys_id")
    position: Optional[int] = Field(None, description="Position of the section on the form")


class DeleteUiFormSectionParams(BaseModel):
    """Parameters for removing a section from a form."""

    form_section_id: str = Field(..., description="sys_ui_form_section sys_id")


def _serialize_form_section(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "sys_ui_form": _dv(item.get("sys_ui_form")),
        "sys_ui_section": _dv(item.get("sys_ui_section")),
        "position": item.get("position"),
    }


def list_ui_form_sections(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiFormSectionsParams,
) -> Dict[str, Any]:
    """List form-to-section links (sys_ui_form_section) from ServiceNow."""
    try:
        query_parts = []
        if params.sys_ui_form:
            query_parts.append(f"sys_ui_form={params.sys_ui_form}")
        if params.sys_ui_section:
            query_parts.append(f"sys_ui_section={params.sys_ui_section}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ui_form_section",
            _FORM_SECTION_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
            order_by="position",
        )
        links = [_serialize_form_section(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(links)} form sections",
            "ui_form_sections": links,
            "total": len(links),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing form sections: {e}")
        return {
            "success": False,
            "message": f"Error listing form sections: {str(e)}",
            "ui_form_sections": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def create_ui_form_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiFormSectionParams,
) -> FormLayoutResponse:
    """Add a section to a form (create a sys_ui_form_section link)."""
    body = {
        "sys_ui_form": params.sys_ui_form,
        "sys_ui_section": params.sys_ui_section,
        "position": str(params.position),
    }

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ui_form_section",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = f"section {params.sys_ui_section} at position {params.position}"
        return FormLayoutResponse(
            success=True,
            message=f"Added {label}",
            record_id=result.get("sys_id"),
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error creating form section: {e}")
        return FormLayoutResponse(success=False, message=f"Error creating form section: {str(e)}")


def update_ui_form_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiFormSectionParams,
) -> FormLayoutResponse:
    """Update a form-to-section link (typically to reorder it)."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_form_section", params.form_section_id, _FORM_SECTION_FIELDS
        )
        sys_id = record["sys_id"]

        body: Dict[str, Any] = {}
        if params.position is not None:
            body["position"] = str(params.position)

        if not body:
            return FormLayoutResponse(
                success=True,
                message=f"No changes to update for form section: {sys_id}",
                record_id=sys_id,
                record_name=sys_id,
            )

        response = requests.patch(
            f"{config.instance_url}/api/now/table/sys_ui_form_section/{sys_id}",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return FormLayoutResponse(
            success=True,
            message=f"Updated form section: {sys_id}",
            record_id=sys_id,
            record_name=sys_id,
        )
    except Exception as e:
        logger.error(f"Error updating form section: {e}")
        return FormLayoutResponse(success=False, message=f"Error updating form section: {str(e)}")


def delete_ui_form_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiFormSectionParams,
) -> FormLayoutResponse:
    """Remove a section from a form (delete the sys_ui_form_section link)."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_form_section", params.form_section_id, _FORM_SECTION_FIELDS
        )
        sys_id = record["sys_id"]

        response = requests.delete(
            f"{config.instance_url}/api/now/table/sys_ui_form_section/{sys_id}",
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return FormLayoutResponse(
            success=True,
            message=f"Deleted form section: {sys_id}",
            record_id=sys_id,
            record_name=sys_id,
        )
    except Exception as e:
        logger.error(f"Error deleting form section: {e}")
        return FormLayoutResponse(success=False, message=f"Error deleting form section: {str(e)}")


# ---------------------------------------------------------------------------
# sys_ui_section
# ---------------------------------------------------------------------------


class ListUiSectionsParams(BaseModel):
    """Parameters for listing form sections."""

    limit: int = Field(30, description="Maximum number of sections to return")
    offset: int = Field(0, description="Offset for pagination")
    table: Optional[str] = Field(None, description="Filter by table name (the section's 'name' column)")
    view: Optional[str] = Field(None, description="Filter by view sys_id")
    caption: Optional[str] = Field(None, description="Filter by section caption (LIKE)")


class GetUiSectionParams(BaseModel):
    """Parameters for getting a form section."""

    section_id: str = Field(..., description="sys_ui_section sys_id (optionally prefixed with 'sys_id:')")


class CreateUiSectionParams(BaseModel):
    """Parameters for creating a form section."""

    table: str = Field(..., description="Table the section belongs to (stored in the 'name' column)")
    view: str = Field(..., description="View sys_id (sys_ui_view) the section belongs to")
    caption: Optional[str] = Field(
        None, description="Section caption / title shown on the form (empty for the primary section)"
    )
    title: Optional[bool] = Field(
        None, description="Whether this is the primary (title) section of the form"
    )
    header: Optional[bool] = Field(None, description="Whether the section renders a header")
    roles: Optional[str] = Field(None, description="Comma-separated roles that can see the section")


class UpdateUiSectionParams(BaseModel):
    """Parameters for updating a form section."""

    section_id: str = Field(..., description="sys_ui_section sys_id (optionally prefixed with 'sys_id:')")
    caption: Optional[str] = Field(None, description="Section caption / title")
    title: Optional[bool] = Field(None, description="Whether this is the primary (title) section")
    header: Optional[bool] = Field(None, description="Whether the section renders a header")
    roles: Optional[str] = Field(None, description="Comma-separated roles that can see the section")


class DeleteUiSectionParams(BaseModel):
    """Parameters for deleting a form section."""

    section_id: str = Field(..., description="sys_ui_section sys_id (optionally prefixed with 'sys_id:')")


def _serialize_section(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "table": item.get("name"),
        "view": _dv(item.get("view")),
        "caption": item.get("caption"),
        "title": item.get("title") == "true",
        "header": item.get("header") == "true",
        "roles": item.get("roles"),
        "created_on": item.get("sys_created_on"),
        "updated_on": item.get("sys_updated_on"),
    }


def _build_section_body(params: BaseModel) -> Dict[str, Any]:
    body: Dict[str, Any] = {}

    table = getattr(params, "table", None)
    if table is not None:
        body["name"] = table

    view = getattr(params, "view", None)
    if view is not None:
        body["view"] = view

    if getattr(params, "caption", None) is not None:
        body["caption"] = params.caption

    for attr in ("title", "header"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = str(value).lower()

    if getattr(params, "roles", None) is not None:
        body["roles"] = params.roles

    return body


def list_ui_sections(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiSectionsParams,
) -> Dict[str, Any]:
    """List form sections (sys_ui_section) from ServiceNow."""
    try:
        query_parts = []
        if params.table:
            query_parts.append(f"name={params.table}")
        if params.view:
            query_parts.append(f"view={params.view}")
        if params.caption:
            query_parts.append(f"captionLIKE{params.caption}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ui_section",
            _SECTION_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
        )
        sections = [_serialize_section(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(sections)} UI sections",
            "ui_sections": sections,
            "total": len(sections),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI sections: {e}")
        return {
            "success": False,
            "message": f"Error listing UI sections: {str(e)}",
            "ui_sections": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_ui_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUiSectionParams,
) -> Dict[str, Any]:
    """Get a specific form section (sys_ui_section) from ServiceNow."""
    try:
        item = _get_by_sys_id(config, auth_manager, "sys_ui_section", params.section_id, _SECTION_FIELDS)
        return {
            "success": True,
            "message": f"Found UI section: {item.get('caption') or item.get('sys_id')}",
            "ui_section": _serialize_section(item),
        }
    except Exception as e:
        logger.error(f"Error getting UI section: {e}")
        return {"success": False, "message": f"Error getting UI section: {str(e)}"}


def create_ui_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiSectionParams,
) -> FormLayoutResponse:
    """Create a new form section (sys_ui_section) in ServiceNow.

    The section still has to be attached to a form via create_ui_form_section
    before it shows up on the form.
    """
    body = _build_section_body(params)

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ui_section",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = params.caption or f"{params.table} (primary section)"
        return FormLayoutResponse(
            success=True,
            message=f"Created UI section: {label}",
            record_id=result.get("sys_id"),
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error creating UI section: {e}")
        return FormLayoutResponse(success=False, message=f"Error creating UI section: {str(e)}")


def update_ui_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiSectionParams,
) -> FormLayoutResponse:
    """Update an existing form section (sys_ui_section) in ServiceNow."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_section", params.section_id, _SECTION_FIELDS
        )
        sys_id = record["sys_id"]
        body = _build_section_body(params)

        if not body:
            return FormLayoutResponse(
                success=True,
                message=f"No changes to update for UI section: {sys_id}",
                record_id=sys_id,
                record_name=record.get("caption") or sys_id,
            )

        response = requests.patch(
            f"{config.instance_url}/api/now/table/sys_ui_section/{sys_id}",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = result.get("caption") or sys_id
        return FormLayoutResponse(
            success=True,
            message=f"Updated UI section: {label}",
            record_id=sys_id,
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error updating UI section: {e}")
        return FormLayoutResponse(success=False, message=f"Error updating UI section: {str(e)}")


def delete_ui_section(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiSectionParams,
) -> FormLayoutResponse:
    """Delete a form section (sys_ui_section) from ServiceNow."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_section", params.section_id, _SECTION_FIELDS
        )
        sys_id = record["sys_id"]
        label = record.get("caption") or sys_id

        response = requests.delete(
            f"{config.instance_url}/api/now/table/sys_ui_section/{sys_id}",
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return FormLayoutResponse(
            success=True,
            message=f"Deleted UI section: {label}",
            record_id=sys_id,
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error deleting UI section: {e}")
        return FormLayoutResponse(success=False, message=f"Error deleting UI section: {str(e)}")


# ---------------------------------------------------------------------------
# sys_ui_element
# ---------------------------------------------------------------------------


class ListUiElementsParams(BaseModel):
    """Parameters for listing fields placed on a section."""

    limit: int = Field(50, description="Maximum number of elements to return")
    offset: int = Field(0, description="Offset for pagination")
    sys_ui_section: Optional[str] = Field(None, description="Filter by section sys_id (sys_ui_section)")
    element: Optional[str] = Field(None, description="Filter by field (column) name")


class CreateUiElementParams(BaseModel):
    """Parameters for placing a field on a section."""

    sys_ui_section: str = Field(..., description="Section sys_id (sys_ui_section) to place the field in")
    element: str = Field(
        ...,
        description="Field (column) name, or '.split' / '.end_split' for column splits, or a formatter name",
    )
    position: int = Field(..., description="Position of the field inside the section (0-based)")
    type: Optional[str] = Field(
        None, description="Element type; leave empty for a normal field, 'formatter' for a formatter"
    )
    sys_ui_formatter: Optional[str] = Field(
        None, description="Formatter sys_id when the element is a formatter"
    )


class UpdateUiElementParams(BaseModel):
    """Parameters for updating a field placement."""

    element_id: str = Field(..., description="sys_ui_element sys_id (optionally prefixed with 'sys_id:')")
    element: Optional[str] = Field(None, description="Field (column) name")
    position: Optional[int] = Field(None, description="Position of the field inside the section")
    sys_ui_section: Optional[str] = Field(None, description="Move the field to another section sys_id")
    type: Optional[str] = Field(None, description="Element type")


class DeleteUiElementParams(BaseModel):
    """Parameters for removing a field from a section."""

    element_id: str = Field(..., description="sys_ui_element sys_id (optionally prefixed with 'sys_id:')")


def _serialize_element(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sys_id": item.get("sys_id"),
        "sys_ui_section": _dv(item.get("sys_ui_section")),
        "element": item.get("element"),
        "position": item.get("position"),
        "type": item.get("type"),
        "sys_ui_formatter": _dv(item.get("sys_ui_formatter")),
    }


def _build_element_body(params: BaseModel) -> Dict[str, Any]:
    body: Dict[str, Any] = {}

    for attr in ("sys_ui_section", "element", "type", "sys_ui_formatter"):
        value = getattr(params, attr, None)
        if value is not None:
            body[attr] = value

    if getattr(params, "position", None) is not None:
        body["position"] = str(params.position)

    return body


def list_ui_elements(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListUiElementsParams,
) -> Dict[str, Any]:
    """List fields placed on form sections (sys_ui_element) from ServiceNow."""
    try:
        query_parts = []
        if params.sys_ui_section:
            query_parts.append(f"sys_ui_section={params.sys_ui_section}")
        if params.element:
            query_parts.append(f"element={params.element}")

        items = _list_records(
            config,
            auth_manager,
            "sys_ui_element",
            _ELEMENT_FIELDS,
            "^".join(query_parts) if query_parts else None,
            params.limit,
            params.offset,
            order_by="position",
        )
        elements = [_serialize_element(item) for item in items]
        return {
            "success": True,
            "message": f"Found {len(elements)} UI elements",
            "ui_elements": elements,
            "total": len(elements),
            "limit": params.limit,
            "offset": params.offset,
        }
    except Exception as e:
        logger.error(f"Error listing UI elements: {e}")
        return {
            "success": False,
            "message": f"Error listing UI elements: {str(e)}",
            "ui_elements": [],
            "total": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def create_ui_element(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateUiElementParams,
) -> FormLayoutResponse:
    """Place a field on a form section (create a sys_ui_element)."""
    body = _build_element_body(params)

    try:
        response = requests.post(
            f"{config.instance_url}/api/now/table/sys_ui_element",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = f"{params.element} @ {params.position}"
        return FormLayoutResponse(
            success=True,
            message=f"Placed field on section: {label}",
            record_id=result.get("sys_id"),
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error creating UI element: {e}")
        return FormLayoutResponse(success=False, message=f"Error creating UI element: {str(e)}")


def update_ui_element(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateUiElementParams,
) -> FormLayoutResponse:
    """Update a field placement (sys_ui_element) in ServiceNow."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_element", params.element_id, _ELEMENT_FIELDS
        )
        sys_id = record["sys_id"]
        body = _build_element_body(params)

        if not body:
            return FormLayoutResponse(
                success=True,
                message=f"No changes to update for UI element: {sys_id}",
                record_id=sys_id,
                record_name=record.get("element") or sys_id,
            )

        response = requests.patch(
            f"{config.instance_url}/api/now/table/sys_ui_element/{sys_id}",
            json=body,
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        label = result.get("element") or sys_id
        return FormLayoutResponse(
            success=True,
            message=f"Updated UI element: {label}",
            record_id=sys_id,
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error updating UI element: {e}")
        return FormLayoutResponse(success=False, message=f"Error updating UI element: {str(e)}")


def delete_ui_element(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteUiElementParams,
) -> FormLayoutResponse:
    """Remove a field from a form section (delete a sys_ui_element)."""
    try:
        record = _get_by_sys_id(
            config, auth_manager, "sys_ui_element", params.element_id, _ELEMENT_FIELDS
        )
        sys_id = record["sys_id"]
        label = record.get("element") or sys_id

        response = requests.delete(
            f"{config.instance_url}/api/now/table/sys_ui_element/{sys_id}",
            headers=auth_manager.get_headers(),
            timeout=30,
        )
        response.raise_for_status()

        return FormLayoutResponse(
            success=True,
            message=f"Deleted UI element: {label}",
            record_id=sys_id,
            record_name=label,
        )
    except Exception as e:
        logger.error(f"Error deleting UI element: {e}")
        return FormLayoutResponse(success=False, message=f"Error deleting UI element: {str(e)}")
