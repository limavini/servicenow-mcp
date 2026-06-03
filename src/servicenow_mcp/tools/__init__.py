"""
Tools module for the ServiceNow MCP server.
"""

# Import tools as they are implemented
from servicenow_mcp.tools.catalog_optimization import (
    get_optimization_recommendations,
    update_catalog_item,
)
from servicenow_mcp.tools.catalog_tools import (
    create_catalog_category,
    get_catalog_item,
    list_catalog_categories,
    list_catalog_items,
    move_catalog_items,
    update_catalog_category,
)
from servicenow_mcp.tools.catalog_variables import (
    create_catalog_item_variable,
    list_catalog_item_variables,
    update_catalog_item_variable,
)
from servicenow_mcp.tools.change_tools import (
    add_change_task,
    approve_change,
    create_change_request,
    get_change_request_details,
    list_change_requests,
    reject_change,
    submit_change_for_approval,
    update_change_request,
)
from servicenow_mcp.tools.update_set_tools import (
    add_file_to_update_set,
    commit_update_set,
    create_update_set,
    get_update_set_details,
    list_update_sets,
    publish_update_set,
    update_update_set,
)
from servicenow_mcp.tools.incident_tools import (
    add_comment,
    create_incident,
    list_incidents,
    resolve_incident,
    update_incident,
    get_incident_by_number,
)
from servicenow_mcp.tools.knowledge_base import (
    create_article,
    create_category,
    create_knowledge_base,
    get_article,
    list_articles,
    list_knowledge_bases,
    publish_article,
    update_article,
    list_categories,
)
from servicenow_mcp.tools.script_include_tools import (
    create_script_include,
    delete_script_include,
    get_script_include,
    list_script_includes,
    update_script_include,
)
from servicenow_mcp.tools.record_producer_tools import (
    create_record_producer,
    delete_record_producer,
    get_record_producer,
    list_record_producers,
    update_record_producer,
)
from servicenow_mcp.tools.client_script_tools import (
    create_client_script,
    delete_client_script,
    get_client_script,
    list_client_scripts,
    update_client_script,
)
from servicenow_mcp.tools.sp_widget_tools import (
    create_sp_widget,
    delete_sp_widget,
    get_sp_widget,
    list_sp_widgets,
    update_sp_widget,
)
from servicenow_mcp.tools.business_rule_tools import (
    create_business_rule,
    delete_business_rule,
    get_business_rule,
    list_business_rules,
    update_business_rule,
)
from servicenow_mcp.tools.system_property_tools import (
    create_system_property,
    delete_system_property,
    get_system_property,
    list_system_properties,
    update_system_property,
)
from servicenow_mcp.tools.ui_policy_tools import (
    create_ui_policy,
    delete_ui_policy,
    get_ui_policy,
    list_ui_policies,
    update_ui_policy,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    create_ui_policy_action,
    delete_ui_policy_action,
    get_ui_policy_action,
    list_ui_policy_actions,
    update_ui_policy_action,
)
from servicenow_mcp.tools.ui_action_tools import (
    create_ui_action,
    delete_ui_action,
    get_ui_action,
    list_ui_actions,
    update_ui_action,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    create_dictionary_entry,
    delete_dictionary_entry,
    get_dictionary_entry,
    list_dictionary_entries,
    update_dictionary_entry,
)
from servicenow_mcp.tools.choice_tools import (
    create_choice,
    delete_choice,
    get_choice,
    list_choices,
    update_choice,
)
from servicenow_mcp.tools.email_notification_tools import (
    create_email_notification,
    delete_email_notification,
    get_email_notification,
    list_email_notifications,
    update_email_notification,
)
from servicenow_mcp.tools.acl_tools import (
    create_acl,
    delete_acl,
    get_acl,
    list_acls,
    update_acl,
)
from servicenow_mcp.tools.sp_instance_tools import (
    create_sp_instance,
    delete_sp_instance,
    get_sp_instance,
    list_sp_instances,
    update_sp_instance,
)
from servicenow_mcp.tools.sp_page_tools import (
    create_sp_page,
    delete_sp_page,
    get_sp_page,
    list_sp_pages,
    update_sp_page,
)
from servicenow_mcp.tools.ui_script_tools import (
    create_ui_script,
    delete_ui_script,
    get_ui_script,
    list_ui_scripts,
    update_ui_script,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    create_scheduled_job,
    delete_scheduled_job,
    get_scheduled_job,
    list_scheduled_jobs,
    update_scheduled_job,
)
from servicenow_mcp.tools.data_policy_tools import (
    create_data_policy,
    delete_data_policy,
    get_data_policy,
    list_data_policies,
    update_data_policy,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    create_data_policy_rule,
    delete_data_policy_rule,
    get_data_policy_rule,
    list_data_policy_rules,
    update_data_policy_rule,
)
from servicenow_mcp.tools.role_tools import (
    create_role,
    delete_role,
    get_role,
    list_roles,
    update_role,
)
from servicenow_mcp.tools.catalog_client_script_tools import (
    create_catalog_client_script,
    delete_catalog_client_script,
    get_catalog_client_script,
    list_catalog_client_scripts,
    update_catalog_client_script,
)
from servicenow_mcp.tools.catalog_ui_policy_tools import (
    create_catalog_ui_policy,
    delete_catalog_ui_policy,
    get_catalog_ui_policy,
    list_catalog_ui_policies,
    update_catalog_ui_policy,
)
from servicenow_mcp.tools.catalog_ui_policy_action_tools import (
    create_catalog_ui_policy_action,
    delete_catalog_ui_policy_action,
    get_catalog_ui_policy_action,
    list_catalog_ui_policy_actions,
    update_catalog_ui_policy_action,
)
from servicenow_mcp.tools.db_table_tools import (
    create_db_table,
    delete_db_table,
    get_db_table,
    list_db_tables,
    update_db_table,
)
from servicenow_mcp.tools.event_registration_tools import (
    create_event_registration,
    delete_event_registration,
    get_event_registration,
    list_event_registrations,
    update_event_registration,
)
from servicenow_mcp.tools.sla_definition_tools import (
    create_sla_definition,
    delete_sla_definition,
    get_sla_definition,
    list_sla_definitions,
    update_sla_definition,
)
from servicenow_mcp.tools.transform_map_tools import (
    create_transform_map,
    delete_transform_map,
    get_transform_map,
    list_transform_maps,
    update_transform_map,
)
from servicenow_mcp.tools.transform_entry_tools import (
    create_transform_entry,
    delete_transform_entry,
    get_transform_entry,
    list_transform_entries,
    update_transform_entry,
)
# __GEN_INIT_IMPORTS__
from servicenow_mcp.tools.current_update_set_tools import (
    get_current_update_set,
    set_current_update_set,
)
from servicenow_mcp.tools.instance_tools import (
    get_current_instance,
    list_instances,
    select_instance,
)
from servicenow_mcp.tools.user_tools import (
    create_user,
    update_user,
    get_user,
    list_users,
    create_group,
    update_group,
    add_group_members,
    remove_group_members,
    list_groups,
)
from servicenow_mcp.tools.workflow_tools import (
    activate_workflow,
    add_workflow_activity,
    create_workflow,
    deactivate_workflow,
    delete_workflow_activity,
    get_workflow_activities,
    get_workflow_details,
    list_workflow_versions,
    list_workflows,
    reorder_workflow_activities,
    update_workflow,
    update_workflow_activity,
)
from servicenow_mcp.tools.story_tools import (
    create_story,
    update_story,
    list_stories,
    list_story_dependencies,
    create_story_dependency,
    delete_story_dependency,
)
from servicenow_mcp.tools.epic_tools import (
    create_epic,
    update_epic,
    list_epics,
)
from servicenow_mcp.tools.scrum_task_tools import (
    create_scrum_task,
    update_scrum_task,
    list_scrum_tasks,
)
from servicenow_mcp.tools.project_tools import (
    create_project,
    update_project,
    list_projects,
)
# from servicenow_mcp.tools.problem_tools import create_problem, update_problem
# from servicenow_mcp.tools.request_tools import create_request, update_request

__all__ = [
    # Incident tools
    "create_incident",
    "update_incident",
    "add_comment",
    "resolve_incident",
    "list_incidents",
    "get_incident_by_number",
    
    # Catalog tools
    "list_catalog_items",
    "get_catalog_item",
    "list_catalog_categories",
    "create_catalog_category",
    "update_catalog_category",
    "move_catalog_items",
    "get_optimization_recommendations",
    "update_catalog_item",
    "create_catalog_item_variable",
    "list_catalog_item_variables",
    "update_catalog_item_variable",
    
    # Change management tools
    "create_change_request",
    "update_change_request",
    "list_change_requests",
    "get_change_request_details",
    "add_change_task",
    "submit_change_for_approval",
    "approve_change",
    "reject_change",
    
    # Workflow management tools
    "list_workflows",
    "get_workflow_details",
    "list_workflow_versions",
    "get_workflow_activities",
    "create_workflow",
    "update_workflow",
    "activate_workflow",
    "deactivate_workflow",
    "add_workflow_activity",
    "update_workflow_activity",
    "delete_workflow_activity",
    "reorder_workflow_activities",
    
    # Update set tools
    "list_update_sets",
    "get_update_set_details",
    "create_update_set",
    "update_update_set",
    "commit_update_set",
    "publish_update_set",
    "add_file_to_update_set",
    
    # Script Include tools
    "list_script_includes",
    "get_script_include",
    "create_script_include",
    "update_script_include",
    "delete_script_include",
    # Record Producer Tools
    "list_record_producers",
    "get_record_producer",
    "create_record_producer",
    "update_record_producer",
    "delete_record_producer",

    # Client Script tools
    "list_client_scripts",
    "get_client_script",
    "create_client_script",
    "update_client_script",
    "delete_client_script",

    # Service Portal Widget tools
    "list_sp_widgets",
    "get_sp_widget",
    "create_sp_widget",
    "update_sp_widget",
    "delete_sp_widget",
    # Business Rule tools
    "list_business_rules",
    "get_business_rule",
    "create_business_rule",
    "update_business_rule",
    "delete_business_rule",
    # System Property tools
    "list_system_properties",
    "get_system_property",
    "create_system_property",
    "update_system_property",
    "delete_system_property",
    # UI Policy tools
    "list_ui_policies",
    "get_ui_policy",
    "create_ui_policy",
    "update_ui_policy",
    "delete_ui_policy",
    # UI Policy Action tools
    "list_ui_policy_actions",
    "get_ui_policy_action",
    "create_ui_policy_action",
    "update_ui_policy_action",
    "delete_ui_policy_action",
    # UI Action tools
    "list_ui_actions",
    "get_ui_action",
    "create_ui_action",
    "update_ui_action",
    "delete_ui_action",
    # Dictionary Entry tools
    "list_dictionary_entries",
    "get_dictionary_entry",
    "create_dictionary_entry",
    "update_dictionary_entry",
    "delete_dictionary_entry",
    # Choice tools
    "list_choices",
    "get_choice",
    "create_choice",
    "update_choice",
    "delete_choice",
    # Email Notification tools
    "list_email_notifications",
    "get_email_notification",
    "create_email_notification",
    "update_email_notification",
    "delete_email_notification",
    # ACL tools
    "list_acls",
    "get_acl",
    "create_acl",
    "update_acl",
    "delete_acl",
    # Service Portal Widget Instance tools
    "list_sp_instances",
    "get_sp_instance",
    "create_sp_instance",
    "update_sp_instance",
    "delete_sp_instance",
    # Service Portal Page tools
    "list_sp_pages",
    "get_sp_page",
    "create_sp_page",
    "update_sp_page",
    "delete_sp_page",
    # UI Script tools
    "list_ui_scripts",
    "get_ui_script",
    "create_ui_script",
    "update_ui_script",
    "delete_ui_script",
    # Scheduled Job tools
    "list_scheduled_jobs",
    "get_scheduled_job",
    "create_scheduled_job",
    "update_scheduled_job",
    "delete_scheduled_job",
    # Data Policy tools
    "list_data_policies",
    "get_data_policy",
    "create_data_policy",
    "update_data_policy",
    "delete_data_policy",
    # Data Policy Rule tools
    "list_data_policy_rules",
    "get_data_policy_rule",
    "create_data_policy_rule",
    "update_data_policy_rule",
    "delete_data_policy_rule",
    # Role tools
    "list_roles",
    "get_role",
    "create_role",
    "update_role",
    "delete_role",
    # Catalog Client Script tools
    "list_catalog_client_scripts",
    "get_catalog_client_script",
    "create_catalog_client_script",
    "update_catalog_client_script",
    "delete_catalog_client_script",
    # Catalog UI Policy tools
    "list_catalog_ui_policies",
    "get_catalog_ui_policy",
    "create_catalog_ui_policy",
    "update_catalog_ui_policy",
    "delete_catalog_ui_policy",
    # Catalog UI Policy Action tools
    "list_catalog_ui_policy_actions",
    "get_catalog_ui_policy_action",
    "create_catalog_ui_policy_action",
    "update_catalog_ui_policy_action",
    "delete_catalog_ui_policy_action",
    # Table (sys_db_object) tools
    "list_db_tables",
    "get_db_table",
    "create_db_table",
    "update_db_table",
    "delete_db_table",
    # Event Registration tools
    "list_event_registrations",
    "get_event_registration",
    "create_event_registration",
    "update_event_registration",
    "delete_event_registration",
    # SLA Definition tools
    "list_sla_definitions",
    "get_sla_definition",
    "create_sla_definition",
    "update_sla_definition",
    "delete_sla_definition",
    # Transform Map tools
    "list_transform_maps",
    "get_transform_map",
    "create_transform_map",
    "update_transform_map",
    "delete_transform_map",
    # Transform Entry tools
    "list_transform_entries",
    "get_transform_entry",
    "create_transform_entry",
    "update_transform_entry",
    "delete_transform_entry",
    # __GEN_INIT_ALL__

    # Current Update Set tools
    "get_current_update_set",
    "set_current_update_set",

    # Instance selection tools
    "list_instances",
    "get_current_instance",
    "select_instance",
    
    # Knowledge Base tools
    "create_knowledge_base",
    "list_knowledge_bases",
    "create_category",
    "list_categories",
    "create_article",
    "update_article",
    "publish_article",
    "list_articles",
    "get_article",
    
    # User management tools
    "create_user",
    "update_user",
    "get_user",
    "list_users",
    "create_group",
    "update_group",
    "add_group_members",
    "remove_group_members",
    "list_groups",

    # Story tools
    "create_story",
    "update_story",
    "list_stories",
    "list_story_dependencies",
    "create_story_dependency",
    "delete_story_dependency",
    
    # Epic tools
    "create_epic",
    "update_epic",
    "list_epics",

    # Scrum Task tools
    "create_scrum_task",
    "update_scrum_task",
    "list_scrum_tasks",

    # Project tools
    "create_project",
    "update_project",
    "list_projects",

    
    # Future tools
    # "create_problem",
    # "update_problem",
    # "create_request",
    # "update_request",
] 