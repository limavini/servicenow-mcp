"""
Update set tools for the ServiceNow MCP server.

This module provides tools for managing update sets in ServiceNow.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


class ListUpdateSetsParams(BaseModel):
    """Parameters for listing update sets."""

    limit: Optional[int] = Field(10, description="Maximum number of records to return")
    offset: Optional[int] = Field(0, description="Offset to start from")
    state: Optional[str] = Field(None, description="Filter by state")
    application: Optional[str] = Field(None, description="Filter by application")
    developer: Optional[str] = Field(None, description="Filter by developer")
    timeframe: Optional[str] = Field(None, description="Filter by timeframe (recent, last_week, last_month)")
    query: Optional[str] = Field(None, description="Additional query string")


class GetUpdateSetDetailsParams(BaseModel):
    """Parameters for getting update set details."""

    update_set_id: str = Field(..., description="Update set ID or sys_id")


class CreateUpdateSetParams(BaseModel):
    """Parameters for creating an update set."""

    name: str = Field(..., description="Name of the update set")
    description: Optional[str] = Field(None, description="Description of the update set")
    application: str = Field(..., description="Application the update set belongs to")
    developer: Optional[str] = Field(None, description="Developer responsible for the update set")


class UpdateUpdateSetParams(BaseModel):
    """Parameters for updating an update set."""

    update_set_id: str = Field(..., description="Update set ID or sys_id")
    name: Optional[str] = Field(None, description="Name of the update set")
    description: Optional[str] = Field(None, description="Description of the update set")
    state: Optional[str] = Field(None, description="State of the update set")
    developer: Optional[str] = Field(None, description="Developer responsible for the update set")


class CommitUpdateSetParams(BaseModel):
    """Parameters for committing an update set."""

    update_set_id: str = Field(..., description="Update set ID or sys_id")
    commit_message: Optional[str] = Field(None, description="Commit message")


class PublishUpdateSetParams(BaseModel):
    """Parameters for publishing an update set."""

    update_set_id: str = Field(..., description="Update set ID or sys_id")
    publish_notes: Optional[str] = Field(None, description="Notes for publishing")


class AddFileToUpdateSetParams(BaseModel):
    """Parameters for adding a file to an update set."""

    update_set_id: str = Field(..., description="Update set ID or sys_id")
    file_path: str = Field(..., description="Path of the file to add")
    file_content: str = Field(..., description="Content of the file")


def _unwrap_and_validate_params(
    params: Union[Dict[str, Any], BaseModel], 
    model_class: Type[T], 
    required_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Unwrap and validate parameters.

    Args:
        params: The parameters to unwrap and validate. Can be a dictionary or a Pydantic model.
        model_class: The Pydantic model class to validate against.
        required_fields: List of fields that must be present.

    Returns:
        A dictionary with success status and validated parameters or error message.
    """
    try:
        # Handle case where params is already a Pydantic model
        if isinstance(params, BaseModel):
            # If it's already the correct model class, use it directly
            if isinstance(params, model_class):
                model_instance = params
            # Otherwise, convert to dict and create new instance
            else:
                model_instance = model_class(**params.dict())
        # Handle dictionary case
        else:
            # Create model instance
            model_instance = model_class(**params)
        
        # Check required fields
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if getattr(model_instance, field, None) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "success": False,
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                }
        
        return {
            "success": True,
            "params": model_instance,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Invalid parameters: {str(e)}",
        }


def _get_instance_url(auth_manager: AuthManager, server_config: ServerConfig) -> Optional[str]:
    """
    Get the instance URL from either auth_manager or server_config.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.

    Returns:
        The instance URL or None if not found.
    """
    # Try to get instance_url from server_config
    if hasattr(server_config, 'instance_url'):
        return server_config.instance_url
    
    # Try to get instance_url from auth_manager
    if hasattr(auth_manager, 'instance_url'):
        return auth_manager.instance_url
    
    # If neither has instance_url, check if auth_manager is actually a ServerConfig
    # and server_config is actually an AuthManager (parameters swapped)
    if hasattr(server_config, 'get_headers') and not hasattr(auth_manager, 'get_headers'):
        if hasattr(auth_manager, 'instance_url'):
            return auth_manager.instance_url
    
    logger.error("Cannot find instance_url in either auth_manager or server_config")
    return None


def _get_headers(auth_manager: AuthManager, server_config: ServerConfig) -> Optional[Dict[str, str]]:
    """
    Get the headers from either auth_manager or server_config.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.

    Returns:
        The headers or None if not found.
    """
    # Try to get headers from auth_manager
    if hasattr(auth_manager, 'get_headers'):
        return auth_manager.get_headers()
    
    # Try to get headers from server_config
    if hasattr(server_config, 'get_headers'):
        return server_config.get_headers()
    
    # If neither has get_headers, check if auth_manager is actually a ServerConfig
    # and server_config is actually an AuthManager (parameters swapped)
    if hasattr(server_config, 'get_headers') and not hasattr(auth_manager, 'get_headers'):
        return server_config.get_headers()
    
    logger.error("Cannot find get_headers method in either auth_manager or server_config")
    return None


def list_update_sets(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], ListUpdateSetsParams],
) -> Dict[str, Any]:
    """
    List update sets from ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for listing update sets. Can be a dictionary or a ListUpdateSetsParams object.

    Returns:
        A list of update sets.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(params, ListUpdateSetsParams)
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Build query parameters
    query_params = {
        "sysparm_limit": validated_params.limit,
        "sysparm_offset": validated_params.offset,
    }
    
    # Build sysparm_query
    query_parts = []
    
    if validated_params.state:
        query_parts.append(f"state={validated_params.state}")
    
    if validated_params.application:
        query_parts.append(f"application={validated_params.application}")
    
    if validated_params.developer:
        query_parts.append(f"developer={validated_params.developer}")
    
    if validated_params.timeframe:
        if validated_params.timeframe == "recent":
            query_parts.append("sys_created_onONLast 7 days@javascript:gs.beginningOfLast7Days()@javascript:gs.endOfToday()")
        elif validated_params.timeframe == "last_week":
            query_parts.append("sys_created_onONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()")
        elif validated_params.timeframe == "last_month":
            query_parts.append("sys_created_onONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()")
    
    if validated_params.query:
        query_parts.append(validated_params.query)
    
    if query_parts:
        query_params["sysparm_query"] = "^".join(query_parts)
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set"
    
    try:
        response = requests.get(url, params=query_params, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "update_sets": result.get("result", []),
            "count": len(result.get("result", [])),
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error listing update sets: {e}")
        return {
            "success": False,
            "message": f"Error listing update sets: {str(e)}",
        }


def get_update_set_details(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], GetUpdateSetDetailsParams],
) -> Dict[str, Any]:
    """
    Get detailed information about a specific update set.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for getting update set details. Can be a dictionary or a GetUpdateSetDetailsParams object.

    Returns:
        Detailed information about the update set.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        GetUpdateSetDetailsParams, 
        required_fields=["update_set_id"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set/{validated_params.update_set_id}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        # Get the update set details
        update_set = result.get("result", {})
        
        # Get the changes in this update set
        changes_url = f"{instance_url}/api/now/table/sys_update_xml"
        changes_params = {
            "sysparm_query": f"update_set={validated_params.update_set_id}",
        }
        
        changes_response = requests.get(changes_url, params=changes_params, headers=headers)
        changes_response.raise_for_status()
        
        changes_result = changes_response.json()
        changes = changes_result.get("result", [])
        
        return {
            "success": True,
            "update_set": update_set,
            "changes": changes,
            "change_count": len(changes),
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting update set details: {e}")
        return {
            "success": False,
            "message": f"Error getting update set details: {str(e)}",
        }


def create_update_set(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], CreateUpdateSetParams],
) -> Dict[str, Any]:
    """
    Create a new update set in ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for creating an update set. Can be a dictionary or a CreateUpdateSetParams object.

    Returns:
        The created update set.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        CreateUpdateSetParams, 
        required_fields=["name", "application"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Prepare the request data
    data = {
        "name": validated_params.name,
        "application": validated_params.application,
    }
    
    # Add optional fields if provided
    if validated_params.description:
        data["description"] = validated_params.description
    if validated_params.developer:
        data["developer"] = validated_params.developer
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Add Content-Type header
    headers["Content-Type"] = "application/json"
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set"
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Update set created successfully",
            "update_set": result["result"],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating update set: {e}")
        return {
            "success": False,
            "message": f"Error creating update set: {str(e)}",
        }


def update_update_set(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], UpdateUpdateSetParams],
) -> Dict[str, Any]:
    """
    Update an existing update set in ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for updating an update set. Can be a dictionary or a UpdateUpdateSetParams object.

    Returns:
        The updated update set.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        UpdateUpdateSetParams, 
        required_fields=["update_set_id"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Prepare the request data
    data = {}
    
    # Add optional fields if provided
    if validated_params.name:
        data["name"] = validated_params.name
    if validated_params.description:
        data["description"] = validated_params.description
    if validated_params.state:
        data["state"] = validated_params.state
    if validated_params.developer:
        data["developer"] = validated_params.developer
    
    # If no fields to update, return error
    if not data:
        return {
            "success": False,
            "message": "No fields to update",
        }
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Add Content-Type header
    headers["Content-Type"] = "application/json"
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set/{validated_params.update_set_id}"
    
    try:
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Update set updated successfully",
            "update_set": result["result"],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating update set: {e}")
        return {
            "success": False,
            "message": f"Error updating update set: {str(e)}",
        }


def commit_update_set(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], CommitUpdateSetParams],
) -> Dict[str, Any]:
    """
    Commit an update set in ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for committing an update set. Can be a dictionary or a CommitUpdateSetParams object.

    Returns:
        The committed update set.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        CommitUpdateSetParams, 
        required_fields=["update_set_id"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Prepare the request data
    data = {
        "state": "complete",
    }
    
    # Add commit message if provided
    if validated_params.commit_message:
        data["description"] = validated_params.commit_message
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Add Content-Type header
    headers["Content-Type"] = "application/json"
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set/{validated_params.update_set_id}"
    
    try:
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Update set committed successfully",
            "update_set": result["result"],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error committing update set: {e}")
        return {
            "success": False,
            "message": f"Error committing update set: {str(e)}",
        }


def publish_update_set(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], PublishUpdateSetParams],
) -> Dict[str, Any]:
    """
    Publish an update set in ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for publishing an update set. Can be a dictionary or a PublishUpdateSetParams object.

    Returns:
        The published update set.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        PublishUpdateSetParams, 
        required_fields=["update_set_id"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Add Content-Type header
    headers["Content-Type"] = "application/json"
    
    # Prepare the request data for the publish action
    data = {
        "state": "published",
    }
    
    # Add publish notes if provided
    if validated_params.publish_notes:
        data["description"] = validated_params.publish_notes
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_set/{validated_params.update_set_id}"
    
    try:
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Update set published successfully",
            "update_set": result["result"],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error publishing update set: {e}")
        return {
            "success": False,
            "message": f"Error publishing update set: {str(e)}",
        }


def add_file_to_update_set(
    auth_manager: AuthManager,
    server_config: ServerConfig,
    params: Union[Dict[str, Any], AddFileToUpdateSetParams],
) -> Dict[str, Any]:
    """
    Add a file to an update set in ServiceNow.

    Args:
        auth_manager: The authentication manager.
        server_config: The server configuration.
        params: The parameters for adding a file to an update set. Can be a dictionary or a AddFileToUpdateSetParams object.

    Returns:
        The result of the add file operation.
    """
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        params, 
        AddFileToUpdateSetParams, 
        required_fields=["update_set_id", "file_path", "file_content"]
    )
    
    if not result["success"]:
        return result
    
    validated_params = result["params"]
    
    # Get the instance URL
    instance_url = _get_instance_url(auth_manager, server_config)
    if not instance_url:
        return {
            "success": False,
            "message": "Cannot find instance_url in either server_config or auth_manager",
        }
    
    # Get the headers
    headers = _get_headers(auth_manager, server_config)
    if not headers:
        return {
            "success": False,
            "message": "Cannot find get_headers method in either auth_manager or server_config",
        }
    
    # Add Content-Type header
    headers["Content-Type"] = "application/json"
    
    # Prepare the request data for adding a file
    data = {
        "update_set": validated_params.update_set_id,
        "name": validated_params.file_path,
        "payload": validated_params.file_content,
        "type": "file",
    }
    
    # Make the API request
    url = f"{instance_url}/api/now/table/sys_update_xml"
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "File added to update set successfully",
            "file": result["result"],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding file to update set: {e}")
        return {
            "success": False,
            "message": f"Error adding file to update set: {str(e)}",
        } 