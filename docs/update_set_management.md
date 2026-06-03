# Update set Management in ServiceNow MCP

This document provides detailed information about the Update set Management tools available in the ServiceNow MCP server.

## Overview

Update sets in ServiceNow (also known as Update Sets) are collections of customizations and configurations that can be moved between ServiceNow instances. They allow developers to track changes, collaborate on development, and promote changes through different environments (development, test, production).

The ServiceNow MCP server provides tools for managing update sets, allowing Claude to help with:

- Tracking development changes
- Creating and managing update sets
- Committing and publishing update sets
- Adding files to update sets
- Analyzing update set contents

## Available Tools

### 1. list_update_sets

Lists update sets from ServiceNow with various filtering options.

**Parameters:**
- `limit` (optional, default: 10) - Maximum number of records to return
- `offset` (optional, default: 0) - Offset to start from
- `state` (optional) - Filter by state (e.g., "in_progress", "complete", "published")
- `application` (optional) - Filter by application
- `developer` (optional) - Filter by developer
- `timeframe` (optional) - Filter by timeframe ("recent", "last_week", "last_month")
- `query` (optional) - Additional query string

**Example:**
```python
result = list_update_sets({
    "limit": 20,
    "state": "in_progress",
    "developer": "john.doe",
    "timeframe": "recent"
})
```

### 2. get_update_set_details

Gets detailed information about a specific update set, including all changes contained within it.

**Parameters:**
- `update_set_id` (required) - Update set ID or sys_id

**Example:**
```python
result = get_update_set_details({
    "update_set_id": "sys_update_set_123"
})
```

### 3. create_update_set

Creates a new update set in ServiceNow.

**Parameters:**
- `name` (required) - Name of the update set
- `description` (optional) - Description of the update set
- `application` (required) - Application the update set belongs to
- `developer` (optional) - Developer responsible for the update set

**Example:**
```python
result = create_update_set({
    "name": "HR Portal Login Fix",
    "description": "Fixes the login issue on the HR Portal",
    "application": "HR Portal",
    "developer": "john.doe"
})
```

### 4. update_update_set

Updates an existing update set in ServiceNow.

**Parameters:**
- `update_set_id` (required) - Update set ID or sys_id
- `name` (optional) - Name of the update set
- `description` (optional) - Description of the update set
- `state` (optional) - State of the update set
- `developer` (optional) - Developer responsible for the update set

**Example:**
```python
result = update_update_set({
    "update_set_id": "sys_update_set_123",
    "name": "HR Portal Login Fix - Updated",
    "description": "Updated description for the login fix",
    "state": "in_progress"
})
```

### 5. commit_update_set

Commits an update set in ServiceNow, marking it as complete.

**Parameters:**
- `update_set_id` (required) - Update set ID or sys_id
- `commit_message` (optional) - Commit message

**Example:**
```python
result = commit_update_set({
    "update_set_id": "sys_update_set_123",
    "commit_message": "Completed the login fix with all necessary changes"
})
```

### 6. publish_update_set

Publishes an update set in ServiceNow, making it available for deployment to other environments.

**Parameters:**
- `update_set_id` (required) - Update set ID or sys_id
- `publish_notes` (optional) - Notes for publishing

**Example:**
```python
result = publish_update_set({
    "update_set_id": "sys_update_set_123",
    "publish_notes": "Ready for deployment to test environment"
})
```

### 7. add_file_to_update_set

Adds a file to an update set in ServiceNow.

**Parameters:**
- `update_set_id` (required) - Update set ID or sys_id
- `file_path` (required) - Path of the file to add
- `file_content` (required) - Content of the file

**Example:**
```python
result = add_file_to_update_set({
    "update_set_id": "sys_update_set_123",
    "file_path": "scripts/login_fix.js",
    "file_content": "function fixLogin() { ... }"
})
```

## Resources

The ServiceNow MCP server also provides the following resources for accessing update sets:

### 1. update sets://list

URI for listing update sets from ServiceNow.

**Example:**
```
update sets://list
```

### 2. update set://{update_set_id}

URI for getting a specific update set from ServiceNow by ID.

**Example:**
```
update set://sys_update_set_123
```

## Update set States

Update sets in ServiceNow typically go through the following states:

1. **in_progress** - The update set is being actively worked on
2. **complete** - The update set has been completed and is ready for review
3. **published** - The update set has been published and is ready for deployment
4. **deployed** - The update set has been deployed to another environment

## Best Practices

1. **Naming Convention**: Use a consistent naming convention for update sets that includes the application name, feature/fix description, and optionally a ticket number.

2. **Scope**: Keep update sets focused on a single feature, fix, or improvement to make them easier to review and deploy.

3. **Documentation**: Include detailed descriptions for update sets to help reviewers understand the purpose and impact of the changes.

4. **Testing**: Test all changes thoroughly before committing and publishing an update set.

5. **Review**: Have update sets reviewed by another developer before publishing to catch potential issues.

6. **Backup**: Always back up important configurations before deploying update sets to production.

## Example Workflow

1. Create a new update set for a specific feature or fix
2. Make the necessary changes in ServiceNow
3. Add any required files to the update set
4. Test the changes thoroughly
5. Commit the update set with a detailed message
6. Have the update set reviewed
7. Publish the update set
8. Deploy the update set to the target environment

## Troubleshooting

### Common Issues

1. **Update set Conflicts**: When multiple developers modify the same configuration item, conflicts can occur. Resolve these by carefully reviewing and merging the changes.

2. **Missing Dependencies**: Update sets may depend on other configurations that aren't included. Ensure all dependencies are identified and included.

3. **Deployment Failures**: If an update set fails to deploy, check the deployment logs for specific errors and address them before retrying.

4. **Permission Issues**: Ensure the user has the necessary permissions to create, commit, and publish update sets.

### Error Messages

- **"Cannot find update set"**: The specified update set ID does not exist or is not accessible.
- **"Missing required fields"**: One or more required parameters are missing.
- **"Invalid state transition"**: Attempting to change the state of an update set in an invalid way (e.g., from "in_progress" directly to "published").
- **"Application not found"**: The specified application does not exist or is not accessible. 