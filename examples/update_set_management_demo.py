#!/usr/bin/env python3
"""
Update set Management Demo

This script demonstrates how to use the ServiceNow MCP server to manage update sets.
It shows how to create, update, commit, and publish update sets, as well as how to
add files to update sets and retrieve update set details.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the servicenow_mcp package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.update_set_tools import (
    add_file_to_update_set,
    commit_update_set,
    create_update_set,
    get_update_set_details,
    list_update_sets,
    publish_update_set,
    update_update_set,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig

# Load environment variables from .env file
load_dotenv()

# Get ServiceNow credentials from environment variables
instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

if not all([instance_url, username, password]):
    print("Error: Missing required environment variables.")
    print("Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
    sys.exit(1)

# Create server configuration
auth_config = AuthConfig(
    auth_type=AuthType.BASIC,
    basic=BasicAuthConfig(
        username=username,
        password=password,
    ),
)

server_config = ServerConfig(
    instance_url=instance_url,
    auth=auth_config,
)

# Create authentication manager
auth_manager = AuthManager(auth_config)
auth_manager.instance_url = instance_url


def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))


def main():
    """Run the update set management demo."""
    print("\n=== Update set Management Demo ===\n")

    # Step 1: List existing update sets
    print("Step 1: Listing existing update sets...")
    result = list_update_sets(auth_manager, server_config, {
        "limit": 5,
        "timeframe": "recent",
    })
    print_json(result)
    print("\n")

    # Step 2: Create a new update set
    print("Step 2: Creating a new update set...")
    create_result = create_update_set(auth_manager, server_config, {
        "name": "Demo Update set",
        "description": "A demonstration update set created by the MCP demo script",
        "application": "Global",  # Use a valid application name for your instance
        "developer": username,
    })
    print_json(create_result)
    print("\n")

    if not create_result.get("success"):
        print("Failed to create update set. Exiting.")
        sys.exit(1)

    # Get the update set ID from the create result
    update_set_id = create_result["update_set"]["sys_id"]
    print(f"Created update set with ID: {update_set_id}")
    print("\n")

    # Step 3: Update the update set
    print("Step 3: Updating the update set...")
    update_result = update_update_set(auth_manager, server_config, {
        "update_set_id": update_set_id,
        "name": "Demo Update set - Updated",
        "description": "An updated demonstration update set",
    })
    print_json(update_result)
    print("\n")

    # Step 4: Add a file to the update set
    print("Step 4: Adding a file to the update set...")
    file_content = """
function demoFunction() {
    // This is a demonstration function
    gs.info('Hello from the demo update set!');
    return 'Demo function executed successfully';
}
"""
    add_file_result = add_file_to_update_set(auth_manager, server_config, {
        "update_set_id": update_set_id,
        "file_path": "scripts/demo_function.js",
        "file_content": file_content,
    })
    print_json(add_file_result)
    print("\n")

    # Step 5: Get update set details
    print("Step 5: Getting update set details...")
    details_result = get_update_set_details(auth_manager, server_config, {
        "update_set_id": update_set_id,
    })
    print_json(details_result)
    print("\n")

    # Step 6: Commit the update set
    print("Step 6: Committing the update set...")
    commit_result = commit_update_set(auth_manager, server_config, {
        "update_set_id": update_set_id,
        "commit_message": "Completed the demo update set",
    })
    print_json(commit_result)
    print("\n")

    # Step 7: Publish the update set
    print("Step 7: Publishing the update set...")
    publish_result = publish_update_set(auth_manager, server_config, {
        "update_set_id": update_set_id,
        "publish_notes": "Demo update set ready for deployment",
    })
    print_json(publish_result)
    print("\n")

    # Step 8: Get final update set details
    print("Step 8: Getting final update set details...")
    final_details_result = get_update_set_details(auth_manager, server_config, {
        "update_set_id": update_set_id,
    })
    print_json(final_details_result)
    print("\n")

    print("=== Update set Management Demo Completed ===")


if __name__ == "__main__":
    main() 