from typing import Any, Callable, Dict, Tuple, Type

# Import all necessary tool implementation functions and params models
# (This list needs to be kept complete and up-to-date)
from servicenow_mcp.tools.catalog_optimization import (
    OptimizationRecommendationsParams,
    UpdateCatalogItemParams,
)
from servicenow_mcp.tools.catalog_optimization import (
    get_optimization_recommendations as get_optimization_recommendations_tool,
)
from servicenow_mcp.tools.catalog_optimization import (
    update_catalog_item as update_catalog_item_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    CreateCatalogCategoryParams,
    GetCatalogItemParams,
    ListCatalogCategoriesParams,
    ListCatalogItemsParams,
    MoveCatalogItemsParams,
    UpdateCatalogCategoryParams,
)
from servicenow_mcp.tools.catalog_tools import (
    create_catalog_category as create_catalog_category_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    get_catalog_item as get_catalog_item_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    list_catalog_categories as list_catalog_categories_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    list_catalog_items as list_catalog_items_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    move_catalog_items as move_catalog_items_tool,
)
from servicenow_mcp.tools.catalog_tools import (
    update_catalog_category as update_catalog_category_tool,
)
from servicenow_mcp.tools.catalog_variables import (
    CreateCatalogItemVariableParams,
    ListCatalogItemVariablesParams,
    UpdateCatalogItemVariableParams,
)
from servicenow_mcp.tools.catalog_variables import (
    create_catalog_item_variable as create_catalog_item_variable_tool,
)
from servicenow_mcp.tools.catalog_variables import (
    list_catalog_item_variables as list_catalog_item_variables_tool,
)
from servicenow_mcp.tools.catalog_variables import (
    update_catalog_item_variable as update_catalog_item_variable_tool,
)
from servicenow_mcp.tools.change_tools import (
    AddChangeTaskParams,
    ApproveChangeParams,
    CreateChangeRequestParams,
    GetChangeRequestDetailsParams,
    ListChangeRequestsParams,
    RejectChangeParams,
    SubmitChangeForApprovalParams,
    UpdateChangeRequestParams,
)
from servicenow_mcp.tools.change_tools import (
    add_change_task as add_change_task_tool,
)
from servicenow_mcp.tools.change_tools import (
    approve_change as approve_change_tool,
)
from servicenow_mcp.tools.change_tools import (
    create_change_request as create_change_request_tool,
)
from servicenow_mcp.tools.change_tools import (
    get_change_request_details as get_change_request_details_tool,
)
from servicenow_mcp.tools.change_tools import (
    list_change_requests as list_change_requests_tool,
)
from servicenow_mcp.tools.change_tools import (
    reject_change as reject_change_tool,
)
from servicenow_mcp.tools.change_tools import (
    submit_change_for_approval as submit_change_for_approval_tool,
)
from servicenow_mcp.tools.change_tools import (
    update_change_request as update_change_request_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    AddFileToUpdateSetParams,
    CommitUpdateSetParams,
    CreateUpdateSetParams,
    GetUpdateSetDetailsParams,
    ListUpdateSetsParams,
    PublishUpdateSetParams,
    UpdateUpdateSetParams,
)
from servicenow_mcp.tools.update_set_tools import (
    add_file_to_update_set as add_file_to_update_set_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    commit_update_set as commit_update_set_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    create_update_set as create_update_set_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    get_update_set_details as get_update_set_details_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    list_update_sets as list_update_sets_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    publish_update_set as publish_update_set_tool,
)
from servicenow_mcp.tools.update_set_tools import (
    update_update_set as update_update_set_tool,
)
from servicenow_mcp.tools.incident_tools import (
    AddCommentParams,
    CreateIncidentParams,
    ListIncidentsParams,
    ResolveIncidentParams,
    UpdateIncidentParams,
    GetIncidentByNumberParams,
)
from servicenow_mcp.tools.incident_tools import (
    add_comment as add_comment_tool,
)
from servicenow_mcp.tools.incident_tools import (
    create_incident as create_incident_tool,
)
from servicenow_mcp.tools.incident_tools import (
    list_incidents as list_incidents_tool,
)
from servicenow_mcp.tools.incident_tools import (
    resolve_incident as resolve_incident_tool,
)
from servicenow_mcp.tools.incident_tools import (
    update_incident as update_incident_tool,
)
from servicenow_mcp.tools.incident_tools import (
    get_incident_by_number as get_incident_by_number_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    CreateArticleParams,
    CreateKnowledgeBaseParams,
    GetArticleParams,
    ListArticlesParams,
    ListKnowledgeBasesParams,
    PublishArticleParams,
    UpdateArticleParams,
)
from servicenow_mcp.tools.knowledge_base import (
    CreateCategoryParams as CreateKBCategoryParams,  # Aliased
)
from servicenow_mcp.tools.knowledge_base import (
    ListCategoriesParams as ListKBCategoriesParams,  # Aliased
)
from servicenow_mcp.tools.knowledge_base import (
    create_article as create_article_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    # create_category aliased in function call
    create_knowledge_base as create_knowledge_base_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    get_article as get_article_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    list_articles as list_articles_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    # list_categories aliased in function call
    list_knowledge_bases as list_knowledge_bases_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    publish_article as publish_article_tool,
)
from servicenow_mcp.tools.knowledge_base import (
    update_article as update_article_tool,
)
from servicenow_mcp.tools.script_include_tools import (
    CreateScriptIncludeParams,
    DeleteScriptIncludeParams,
    GetScriptIncludeParams,
    ListScriptIncludesParams,
    ScriptIncludeResponse,
    UpdateScriptIncludeParams,
)
from servicenow_mcp.tools.script_include_tools import (
    create_script_include as create_script_include_tool,
)
from servicenow_mcp.tools.script_include_tools import (
    delete_script_include as delete_script_include_tool,
)
from servicenow_mcp.tools.script_include_tools import (
    get_script_include as get_script_include_tool,
)
from servicenow_mcp.tools.script_include_tools import (
    list_script_includes as list_script_includes_tool,
)
from servicenow_mcp.tools.script_include_tools import (
    update_script_include as update_script_include_tool,
)
from servicenow_mcp.tools.record_producer_tools import (
    CreateRecordProducerParams,
    DeleteRecordProducerParams,
    GetRecordProducerParams,
    ListRecordProducersParams,
    RecordProducerResponse,
    UpdateRecordProducerParams,
)
from servicenow_mcp.tools.record_producer_tools import (
    create_record_producer as create_record_producer_tool,
)
from servicenow_mcp.tools.record_producer_tools import (
    delete_record_producer as delete_record_producer_tool,
)
from servicenow_mcp.tools.record_producer_tools import (
    get_record_producer as get_record_producer_tool,
)
from servicenow_mcp.tools.record_producer_tools import (
    list_record_producers as list_record_producers_tool,
)
from servicenow_mcp.tools.record_producer_tools import (
    update_record_producer as update_record_producer_tool,
)
from servicenow_mcp.tools.client_script_tools import (
    ClientScriptResponse,
    CreateClientScriptParams,
    DeleteClientScriptParams,
    GetClientScriptParams,
    ListClientScriptsParams,
    UpdateClientScriptParams,
)
from servicenow_mcp.tools.client_script_tools import (
    create_client_script as create_client_script_tool,
)
from servicenow_mcp.tools.client_script_tools import (
    delete_client_script as delete_client_script_tool,
)
from servicenow_mcp.tools.client_script_tools import (
    get_client_script as get_client_script_tool,
)
from servicenow_mcp.tools.client_script_tools import (
    list_client_scripts as list_client_scripts_tool,
)
from servicenow_mcp.tools.client_script_tools import (
    update_client_script as update_client_script_tool,
)
from servicenow_mcp.tools.sp_widget_tools import (
    CreateSpWidgetParams,
    DeleteSpWidgetParams,
    GetSpWidgetParams,
    ListSpWidgetsParams,
    SpWidgetResponse,
    UpdateSpWidgetParams,
)
from servicenow_mcp.tools.sp_widget_tools import (
    create_sp_widget as create_sp_widget_tool,
)
from servicenow_mcp.tools.sp_widget_tools import (
    delete_sp_widget as delete_sp_widget_tool,
)
from servicenow_mcp.tools.sp_widget_tools import (
    get_sp_widget as get_sp_widget_tool,
)
from servicenow_mcp.tools.sp_widget_tools import (
    list_sp_widgets as list_sp_widgets_tool,
)
from servicenow_mcp.tools.sp_widget_tools import (
    update_sp_widget as update_sp_widget_tool,
)
from servicenow_mcp.tools.business_rule_tools import (
    BusinessRuleResponse, CreateBusinessRuleParams, DeleteBusinessRuleParams, GetBusinessRuleParams, ListBusinessRulesParams, UpdateBusinessRuleParams,
)
from servicenow_mcp.tools.business_rule_tools import (
    create_business_rule as create_business_rule_tool,
)
from servicenow_mcp.tools.business_rule_tools import (
    delete_business_rule as delete_business_rule_tool,
)
from servicenow_mcp.tools.business_rule_tools import (
    get_business_rule as get_business_rule_tool,
)
from servicenow_mcp.tools.business_rule_tools import (
    list_business_rules as list_business_rules_tool,
)
from servicenow_mcp.tools.business_rule_tools import (
    update_business_rule as update_business_rule_tool,
)
from servicenow_mcp.tools.system_property_tools import (
    SystemPropertyResponse, CreateSystemPropertyParams, DeleteSystemPropertyParams, GetSystemPropertyParams, ListSystemPropertysParams, UpdateSystemPropertyParams,
)
from servicenow_mcp.tools.system_property_tools import (
    create_system_property as create_system_property_tool,
)
from servicenow_mcp.tools.system_property_tools import (
    delete_system_property as delete_system_property_tool,
)
from servicenow_mcp.tools.system_property_tools import (
    get_system_property as get_system_property_tool,
)
from servicenow_mcp.tools.system_property_tools import (
    list_system_properties as list_system_properties_tool,
)
from servicenow_mcp.tools.system_property_tools import (
    update_system_property as update_system_property_tool,
)
from servicenow_mcp.tools.ui_policy_tools import (
    UiPolicyResponse, CreateUiPolicyParams, DeleteUiPolicyParams, GetUiPolicyParams, ListUiPolicysParams, UpdateUiPolicyParams,
)
from servicenow_mcp.tools.ui_policy_tools import (
    create_ui_policy as create_ui_policy_tool,
)
from servicenow_mcp.tools.ui_policy_tools import (
    delete_ui_policy as delete_ui_policy_tool,
)
from servicenow_mcp.tools.ui_policy_tools import (
    get_ui_policy as get_ui_policy_tool,
)
from servicenow_mcp.tools.ui_policy_tools import (
    list_ui_policies as list_ui_policies_tool,
)
from servicenow_mcp.tools.ui_policy_tools import (
    update_ui_policy as update_ui_policy_tool,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    UiPolicyActionResponse, CreateUiPolicyActionParams, DeleteUiPolicyActionParams, GetUiPolicyActionParams, ListUiPolicyActionsParams, UpdateUiPolicyActionParams,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    create_ui_policy_action as create_ui_policy_action_tool,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    delete_ui_policy_action as delete_ui_policy_action_tool,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    get_ui_policy_action as get_ui_policy_action_tool,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    list_ui_policy_actions as list_ui_policy_actions_tool,
)
from servicenow_mcp.tools.ui_policy_action_tools import (
    update_ui_policy_action as update_ui_policy_action_tool,
)
from servicenow_mcp.tools.ui_action_tools import (
    UiActionResponse, CreateUiActionParams, DeleteUiActionParams, GetUiActionParams, ListUiActionsParams, UpdateUiActionParams,
)
from servicenow_mcp.tools.ui_action_tools import (
    create_ui_action as create_ui_action_tool,
)
from servicenow_mcp.tools.ui_action_tools import (
    delete_ui_action as delete_ui_action_tool,
)
from servicenow_mcp.tools.ui_action_tools import (
    get_ui_action as get_ui_action_tool,
)
from servicenow_mcp.tools.ui_action_tools import (
    list_ui_actions as list_ui_actions_tool,
)
from servicenow_mcp.tools.ui_action_tools import (
    update_ui_action as update_ui_action_tool,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    DictionaryEntryResponse, CreateDictionaryEntryParams, DeleteDictionaryEntryParams, GetDictionaryEntryParams, ListDictionaryEntrysParams, UpdateDictionaryEntryParams,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    create_dictionary_entry as create_dictionary_entry_tool,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    delete_dictionary_entry as delete_dictionary_entry_tool,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    get_dictionary_entry as get_dictionary_entry_tool,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    list_dictionary_entries as list_dictionary_entries_tool,
)
from servicenow_mcp.tools.dictionary_entry_tools import (
    update_dictionary_entry as update_dictionary_entry_tool,
)
from servicenow_mcp.tools.choice_tools import (
    ChoiceResponse, CreateChoiceParams, DeleteChoiceParams, GetChoiceParams, ListChoicesParams, UpdateChoiceParams,
)
from servicenow_mcp.tools.choice_tools import (
    create_choice as create_choice_tool,
)
from servicenow_mcp.tools.choice_tools import (
    delete_choice as delete_choice_tool,
)
from servicenow_mcp.tools.choice_tools import (
    get_choice as get_choice_tool,
)
from servicenow_mcp.tools.choice_tools import (
    list_choices as list_choices_tool,
)
from servicenow_mcp.tools.choice_tools import (
    update_choice as update_choice_tool,
)
from servicenow_mcp.tools.email_notification_tools import (
    EmailNotificationResponse, CreateEmailNotificationParams, DeleteEmailNotificationParams, GetEmailNotificationParams, ListEmailNotificationsParams, UpdateEmailNotificationParams,
)
from servicenow_mcp.tools.email_notification_tools import (
    create_email_notification as create_email_notification_tool,
)
from servicenow_mcp.tools.email_notification_tools import (
    delete_email_notification as delete_email_notification_tool,
)
from servicenow_mcp.tools.email_notification_tools import (
    get_email_notification as get_email_notification_tool,
)
from servicenow_mcp.tools.email_notification_tools import (
    list_email_notifications as list_email_notifications_tool,
)
from servicenow_mcp.tools.email_notification_tools import (
    update_email_notification as update_email_notification_tool,
)
from servicenow_mcp.tools.acl_tools import (
    AclResponse, CreateAclParams, DeleteAclParams, GetAclParams, ListAclsParams, UpdateAclParams,
)
from servicenow_mcp.tools.acl_tools import (
    create_acl as create_acl_tool,
)
from servicenow_mcp.tools.acl_tools import (
    delete_acl as delete_acl_tool,
)
from servicenow_mcp.tools.acl_tools import (
    get_acl as get_acl_tool,
)
from servicenow_mcp.tools.acl_tools import (
    list_acls as list_acls_tool,
)
from servicenow_mcp.tools.acl_tools import (
    update_acl as update_acl_tool,
)
from servicenow_mcp.tools.sp_instance_tools import (
    SpInstanceResponse, CreateSpInstanceParams, DeleteSpInstanceParams, GetSpInstanceParams, ListSpInstancesParams, UpdateSpInstanceParams,
)
from servicenow_mcp.tools.sp_instance_tools import (
    create_sp_instance as create_sp_instance_tool,
)
from servicenow_mcp.tools.sp_instance_tools import (
    delete_sp_instance as delete_sp_instance_tool,
)
from servicenow_mcp.tools.sp_instance_tools import (
    get_sp_instance as get_sp_instance_tool,
)
from servicenow_mcp.tools.sp_instance_tools import (
    list_sp_instances as list_sp_instances_tool,
)
from servicenow_mcp.tools.sp_instance_tools import (
    update_sp_instance as update_sp_instance_tool,
)
from servicenow_mcp.tools.sp_page_tools import (
    SpPageResponse, CreateSpPageParams, DeleteSpPageParams, GetSpPageParams, ListSpPagesParams, UpdateSpPageParams,
)
from servicenow_mcp.tools.sp_page_tools import (
    create_sp_page as create_sp_page_tool,
)
from servicenow_mcp.tools.sp_page_tools import (
    delete_sp_page as delete_sp_page_tool,
)
from servicenow_mcp.tools.sp_page_tools import (
    get_sp_page as get_sp_page_tool,
)
from servicenow_mcp.tools.sp_page_tools import (
    list_sp_pages as list_sp_pages_tool,
)
from servicenow_mcp.tools.sp_page_tools import (
    update_sp_page as update_sp_page_tool,
)
from servicenow_mcp.tools.ui_script_tools import (
    UiScriptResponse, CreateUiScriptParams, DeleteUiScriptParams, GetUiScriptParams, ListUiScriptsParams, UpdateUiScriptParams,
)
from servicenow_mcp.tools.ui_script_tools import (
    create_ui_script as create_ui_script_tool,
)
from servicenow_mcp.tools.ui_script_tools import (
    delete_ui_script as delete_ui_script_tool,
)
from servicenow_mcp.tools.ui_script_tools import (
    get_ui_script as get_ui_script_tool,
)
from servicenow_mcp.tools.ui_script_tools import (
    list_ui_scripts as list_ui_scripts_tool,
)
from servicenow_mcp.tools.ui_script_tools import (
    update_ui_script as update_ui_script_tool,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    ScheduledJobResponse, CreateScheduledJobParams, DeleteScheduledJobParams, GetScheduledJobParams, ListScheduledJobsParams, UpdateScheduledJobParams,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    create_scheduled_job as create_scheduled_job_tool,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    delete_scheduled_job as delete_scheduled_job_tool,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    get_scheduled_job as get_scheduled_job_tool,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    list_scheduled_jobs as list_scheduled_jobs_tool,
)
from servicenow_mcp.tools.scheduled_job_tools import (
    update_scheduled_job as update_scheduled_job_tool,
)
from servicenow_mcp.tools.data_policy_tools import (
    DataPolicyResponse, CreateDataPolicyParams, DeleteDataPolicyParams, GetDataPolicyParams, ListDataPolicysParams, UpdateDataPolicyParams,
)
from servicenow_mcp.tools.data_policy_tools import (
    create_data_policy as create_data_policy_tool,
)
from servicenow_mcp.tools.data_policy_tools import (
    delete_data_policy as delete_data_policy_tool,
)
from servicenow_mcp.tools.data_policy_tools import (
    get_data_policy as get_data_policy_tool,
)
from servicenow_mcp.tools.data_policy_tools import (
    list_data_policies as list_data_policies_tool,
)
from servicenow_mcp.tools.data_policy_tools import (
    update_data_policy as update_data_policy_tool,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    DataPolicyRuleResponse, CreateDataPolicyRuleParams, DeleteDataPolicyRuleParams, GetDataPolicyRuleParams, ListDataPolicyRulesParams, UpdateDataPolicyRuleParams,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    create_data_policy_rule as create_data_policy_rule_tool,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    delete_data_policy_rule as delete_data_policy_rule_tool,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    get_data_policy_rule as get_data_policy_rule_tool,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    list_data_policy_rules as list_data_policy_rules_tool,
)
from servicenow_mcp.tools.data_policy_rule_tools import (
    update_data_policy_rule as update_data_policy_rule_tool,
)
from servicenow_mcp.tools.role_tools import (
    RoleResponse, CreateRoleParams, DeleteRoleParams, GetRoleParams, ListRolesParams, UpdateRoleParams,
)
from servicenow_mcp.tools.role_tools import (
    create_role as create_role_tool,
)
from servicenow_mcp.tools.role_tools import (
    delete_role as delete_role_tool,
)
from servicenow_mcp.tools.role_tools import (
    get_role as get_role_tool,
)
from servicenow_mcp.tools.role_tools import (
    list_roles as list_roles_tool,
)
from servicenow_mcp.tools.role_tools import (
    update_role as update_role_tool,
)
# __GEN_TU_IMPORTS__
from servicenow_mcp.tools.current_update_set_tools import (
    CurrentUpdateSetResponse,
    GetCurrentUpdateSetParams,
    SetCurrentUpdateSetParams,
)
from servicenow_mcp.tools.current_update_set_tools import (
    get_current_update_set as get_current_update_set_tool,
)
from servicenow_mcp.tools.current_update_set_tools import (
    set_current_update_set as set_current_update_set_tool,
)
from servicenow_mcp.tools.instance_tools import (
    GetCurrentInstanceParams,
    InstanceSelectionResponse,
    ListInstancesParams,
    SelectInstanceParams,
)
from servicenow_mcp.tools.instance_tools import (
    get_current_instance as get_current_instance_tool,
)
from servicenow_mcp.tools.instance_tools import (
    list_instances as list_instances_tool,
)
from servicenow_mcp.tools.instance_tools import (
    select_instance as select_instance_tool,
)
from servicenow_mcp.tools.user_tools import (
    AddGroupMembersParams,
    CreateGroupParams,
    CreateUserParams,
    GetUserParams,
    ListGroupsParams,
    ListUsersParams,
    RemoveGroupMembersParams,
    UpdateGroupParams,
    UpdateUserParams,
)
from servicenow_mcp.tools.user_tools import (
    add_group_members as add_group_members_tool,
)
from servicenow_mcp.tools.user_tools import (
    create_group as create_group_tool,
)
from servicenow_mcp.tools.user_tools import (
    create_user as create_user_tool,
)
from servicenow_mcp.tools.user_tools import (
    get_user as get_user_tool,
)
from servicenow_mcp.tools.user_tools import (
    list_groups as list_groups_tool,
)
from servicenow_mcp.tools.user_tools import (
    list_users as list_users_tool,
)
from servicenow_mcp.tools.user_tools import (
    remove_group_members as remove_group_members_tool,
)
from servicenow_mcp.tools.user_tools import (
    update_group as update_group_tool,
)
from servicenow_mcp.tools.user_tools import (
    update_user as update_user_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    ActivateWorkflowParams,
    AddWorkflowActivityParams,
    CreateWorkflowParams,
    DeactivateWorkflowParams,
    DeleteWorkflowActivityParams,
    GetWorkflowActivitiesParams,
    GetWorkflowDetailsParams,
    ListWorkflowsParams,
    ListWorkflowVersionsParams,
    ReorderWorkflowActivitiesParams,
    UpdateWorkflowActivityParams,
    UpdateWorkflowParams,
)
from servicenow_mcp.tools.workflow_tools import (
    activate_workflow as activate_workflow_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    add_workflow_activity as add_workflow_activity_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    create_workflow as create_workflow_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    deactivate_workflow as deactivate_workflow_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    delete_workflow_activity as delete_workflow_activity_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    get_workflow_activities as get_workflow_activities_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    get_workflow_details as get_workflow_details_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    list_workflow_versions as list_workflow_versions_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    list_workflows as list_workflows_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    reorder_workflow_activities as reorder_workflow_activities_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    update_workflow as update_workflow_tool,
)
from servicenow_mcp.tools.workflow_tools import (
    update_workflow_activity as update_workflow_activity_tool,
)
from servicenow_mcp.tools.story_tools import (
    CreateStoryParams,
    UpdateStoryParams,
    ListStoriesParams,
    ListStoryDependenciesParams,
    CreateStoryDependencyParams,
    DeleteStoryDependencyParams,
)
from servicenow_mcp.tools.story_tools import (
    create_story as create_story_tool,
    update_story as update_story_tool,
    list_stories as list_stories_tool,
    list_story_dependencies as list_story_dependencies_tool,
    create_story_dependency as create_story_dependency_tool,
    delete_story_dependency as delete_story_dependency_tool,
)
from servicenow_mcp.tools.epic_tools import (
    CreateEpicParams,
    UpdateEpicParams,
    ListEpicsParams,
)
from servicenow_mcp.tools.epic_tools import (
    create_epic as create_epic_tool,
    update_epic as update_epic_tool,
    list_epics as list_epics_tool,
)
from servicenow_mcp.tools.scrum_task_tools import (
    CreateScrumTaskParams,
    UpdateScrumTaskParams,
    ListScrumTasksParams,
)
from servicenow_mcp.tools.scrum_task_tools import (
    create_scrum_task as create_scrum_task_tool,
    update_scrum_task as update_scrum_task_tool,
    list_scrum_tasks as list_scrum_tasks_tool,
)
from servicenow_mcp.tools.project_tools import (
    CreateProjectParams,
    UpdateProjectParams,
    ListProjectsParams,
)
from servicenow_mcp.tools.project_tools import (
    create_project as create_project_tool,
    update_project as update_project_tool,
    list_projects as list_projects_tool,
)

# Define a type alias for the Pydantic models or dataclasses used for params
ParamsModel = Type[Any]  # Use Type[Any] for broader compatibility initially

# Define the structure of the tool definition tuple
ToolDefinition = Tuple[
    Callable,  # Implementation function
    ParamsModel,  # Pydantic model for parameters
    Type,  # Return type annotation (used for hints, not strictly enforced by low-level server)
    str,  # Description
    str,  # Serialization method ('str', 'json', 'dict', 'model_dump', etc.)
]


def get_tool_definitions(
    create_kb_category_tool_impl: Callable, list_kb_categories_tool_impl: Callable
) -> Dict[str, ToolDefinition]:
    """
    Returns a dictionary containing definitions for all available ServiceNow tools.

    This centralizes the tool definitions for use in the server implementation.
    Pass aliased functions for KB categories directly.

    Returns:
        Dict[str, ToolDefinition]: A dictionary mapping tool names to their definitions.
    """
    tool_definitions: Dict[str, ToolDefinition] = {
        # Incident Tools
        "create_incident": (
            create_incident_tool,
            CreateIncidentParams,
            str,
            "Create a new incident in ServiceNow",
            "str",
        ),
        "update_incident": (
            update_incident_tool,
            UpdateIncidentParams,
            str,
            "Update an existing incident in ServiceNow",
            "str",
        ),
        "add_comment": (
            add_comment_tool,
            AddCommentParams,
            str,
            "Add a comment to an incident in ServiceNow",
            "str",
        ),
        "resolve_incident": (
            resolve_incident_tool,
            ResolveIncidentParams,
            str,
            "Resolve an incident in ServiceNow",
            "str",
        ),
        "list_incidents": (
            list_incidents_tool,
            ListIncidentsParams,
            str,  # Expects JSON string
            "List incidents from ServiceNow",
            "json",  # Tool returns list/dict, needs JSON dump
        ),
        "get_incident_by_number":(
            get_incident_by_number_tool,
            GetIncidentByNumberParams,
            str,
            "Incident details from ServiceNow",
            "json_dict"
        ),
        # Catalog Tools
        "list_catalog_items": (
            list_catalog_items_tool,
            ListCatalogItemsParams,
            str,  # Expects JSON string
            "List service catalog items.",
            "json",  # Tool returns list/dict
        ),
        "get_catalog_item": (
            get_catalog_item_tool,
            GetCatalogItemParams,
            str,  # Expects JSON string
            "Get a specific service catalog item.",
            "json_dict",  # Tool returns Pydantic model
        ),
        "list_catalog_categories": (
            list_catalog_categories_tool,
            ListCatalogCategoriesParams,
            str,  # Expects JSON string
            "List service catalog categories.",
            "json",  # Tool returns list/dict
        ),
        "create_catalog_category": (
            create_catalog_category_tool,
            CreateCatalogCategoryParams,
            str,  # Expects JSON string
            "Create a new service catalog category.",
            "json_dict",  # Tool returns Pydantic model
        ),
        "update_catalog_category": (
            update_catalog_category_tool,
            UpdateCatalogCategoryParams,
            str,  # Expects JSON string
            "Update an existing service catalog category.",
            "json_dict",  # Tool returns Pydantic model
        ),
        "move_catalog_items": (
            move_catalog_items_tool,
            MoveCatalogItemsParams,
            str,  # Expects JSON string
            "Move catalog items to a different category.",
            "json_dict",  # Tool returns Pydantic model
        ),
        "get_optimization_recommendations": (
            get_optimization_recommendations_tool,
            OptimizationRecommendationsParams,
            str,  # Expects JSON string
            "Get optimization recommendations for the service catalog.",
            "json",  # Tool returns list/dict
        ),
        "update_catalog_item": (
            update_catalog_item_tool,
            UpdateCatalogItemParams,
            str,  # Expects JSON string
            "Update a service catalog item.",
            "json",  # Tool returns Pydantic model
        ),
        # Catalog Variables
        "create_catalog_item_variable": (
            create_catalog_item_variable_tool,
            CreateCatalogItemVariableParams,
            Dict[str, Any],  # Expects dict
            "Create a new catalog item variable",
            "dict",  # Tool returns Pydantic model
        ),
        "list_catalog_item_variables": (
            list_catalog_item_variables_tool,
            ListCatalogItemVariablesParams,
            Dict[str, Any],  # Expects dict
            "List catalog item variables",
            "dict",  # Tool returns Pydantic model
        ),
        "update_catalog_item_variable": (
            update_catalog_item_variable_tool,
            UpdateCatalogItemVariableParams,
            Dict[str, Any],  # Expects dict
            "Update a catalog item variable",
            "dict",  # Tool returns Pydantic model
        ),
        # Change Management Tools
        "create_change_request": (
            create_change_request_tool,
            CreateChangeRequestParams,
            str,
            "Create a new change request in ServiceNow",
            "str",
        ),
        "update_change_request": (
            update_change_request_tool,
            UpdateChangeRequestParams,
            str,
            "Update an existing change request in ServiceNow",
            "str",
        ),
        "list_change_requests": (
            list_change_requests_tool,
            ListChangeRequestsParams,
            str,  # Expects JSON string
            "List change requests from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "get_change_request_details": (
            get_change_request_details_tool,
            GetChangeRequestDetailsParams,
            str,  # Expects JSON string
            "Get detailed information about a specific change request",
            "json",  # Tool returns list/dict
        ),
        "add_change_task": (
            add_change_task_tool,
            AddChangeTaskParams,
            str,  # Expects JSON string
            "Add a task to a change request",
            "json_dict",  # Tool returns Pydantic model
        ),
        "submit_change_for_approval": (
            submit_change_for_approval_tool,
            SubmitChangeForApprovalParams,
            str,
            "Submit a change request for approval",
            "str",  # Tool returns simple message
        ),
        "approve_change": (
            approve_change_tool,
            ApproveChangeParams,
            str,
            "Approve a change request",
            "str",  # Tool returns simple message
        ),
        "reject_change": (
            reject_change_tool,
            RejectChangeParams,
            str,
            "Reject a change request",
            "str",  # Tool returns simple message
        ),
        # Workflow Management Tools
        "list_workflows": (
            list_workflows_tool,
            ListWorkflowsParams,
            str,  # Expects JSON string
            "List workflows from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "get_workflow_details": (
            get_workflow_details_tool,
            GetWorkflowDetailsParams,
            str,  # Expects JSON string
            "Get detailed information about a specific workflow",
            "json",  # Tool returns list/dict
        ),
        "list_workflow_versions": (
            list_workflow_versions_tool,
            ListWorkflowVersionsParams,
            str,  # Expects JSON string
            "List workflow versions from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "get_workflow_activities": (
            get_workflow_activities_tool,
            GetWorkflowActivitiesParams,
            str,  # Expects JSON string
            "Get activities for a specific workflow",
            "json",  # Tool returns list/dict
        ),
        "create_workflow": (
            create_workflow_tool,
            CreateWorkflowParams,
            str,  # Expects JSON string
            "Create a new workflow in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "update_workflow": (
            update_workflow_tool,
            UpdateWorkflowParams,
            str,  # Expects JSON string
            "Update an existing workflow in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "activate_workflow": (
            activate_workflow_tool,
            ActivateWorkflowParams,
            str,
            "Activate a workflow in ServiceNow",
            "str",  # Tool returns simple message
        ),
        "deactivate_workflow": (
            deactivate_workflow_tool,
            DeactivateWorkflowParams,
            str,
            "Deactivate a workflow in ServiceNow",
            "str",  # Tool returns simple message
        ),
        "add_workflow_activity": (
            add_workflow_activity_tool,
            AddWorkflowActivityParams,
            str,  # Expects JSON string
            "Add a new activity to a workflow in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "update_workflow_activity": (
            update_workflow_activity_tool,
            UpdateWorkflowActivityParams,
            str,  # Expects JSON string
            "Update an existing activity in a workflow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "delete_workflow_activity": (
            delete_workflow_activity_tool,
            DeleteWorkflowActivityParams,
            str,
            "Delete an activity from a workflow",
            "str",  # Tool returns simple message
        ),
        "reorder_workflow_activities": (
            reorder_workflow_activities_tool,
            ReorderWorkflowActivitiesParams,
            str,
            "Reorder activities in a workflow",
            "str",  # Tool returns simple message
        ),
        # Update set Management Tools
        "list_update_sets": (
            list_update_sets_tool,
            ListUpdateSetsParams,
            str,  # Expects JSON string
            "List update sets from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "get_update_set_details": (
            get_update_set_details_tool,
            GetUpdateSetDetailsParams,
            str,  # Expects JSON string
            "Get detailed information about a specific update set",
            "json",  # Tool returns list/dict
        ),
        "create_update_set": (
            create_update_set_tool,
            CreateUpdateSetParams,
            str,  # Expects JSON string
            "Create a new update set in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "update_update_set": (
            update_update_set_tool,
            UpdateUpdateSetParams,
            str,  # Expects JSON string
            "Update an existing update set in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "commit_update_set": (
            commit_update_set_tool,
            CommitUpdateSetParams,
            str,
            "Commit an update set in ServiceNow",
            "str",  # Tool returns simple message
        ),
        "publish_update_set": (
            publish_update_set_tool,
            PublishUpdateSetParams,
            str,
            "Publish an update set in ServiceNow",
            "str",  # Tool returns simple message
        ),
        "add_file_to_update_set": (
            add_file_to_update_set_tool,
            AddFileToUpdateSetParams,
            str,
            "Add a file to an update set in ServiceNow",
            "str",  # Tool returns simple message
        ),
        # Script Include Tools
        "list_script_includes": (
            list_script_includes_tool,
            ListScriptIncludesParams,
            Dict[str, Any],  # Expects dict
            "List script includes from ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        "get_script_include": (
            get_script_include_tool,
            GetScriptIncludeParams,
            Dict[str, Any],  # Expects dict
            "Get a specific script include from ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        "create_script_include": (
            create_script_include_tool,
            CreateScriptIncludeParams,
            ScriptIncludeResponse,  # Expects Pydantic model
            "Create a new script include in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "update_script_include": (
            update_script_include_tool,
            UpdateScriptIncludeParams,
            ScriptIncludeResponse,  # Expects Pydantic model
            "Update an existing script include in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "delete_script_include": (
            delete_script_include_tool,
            DeleteScriptIncludeParams,
            str,  # Expects JSON string
            "Delete a script include in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        # Record Producer Tools
        "list_record_producers": (
            list_record_producers_tool,
            ListRecordProducersParams,
            Dict[str, Any],
            "List record producers (sc_cat_item_producer) from ServiceNow",
            "raw_dict",
        ),
        "get_record_producer": (
            get_record_producer_tool,
            GetRecordProducerParams,
            Dict[str, Any],
            "Get a specific record producer from ServiceNow",
            "raw_dict",
        ),
        "create_record_producer": (
            create_record_producer_tool,
            CreateRecordProducerParams,
            RecordProducerResponse,
            "Create a new record producer (sc_cat_item_producer) pointing at a target table",
            "raw_pydantic",
        ),
        "update_record_producer": (
            update_record_producer_tool,
            UpdateRecordProducerParams,
            RecordProducerResponse,
            "Update an existing record producer in ServiceNow",
            "raw_pydantic",
        ),
        "delete_record_producer": (
            delete_record_producer_tool,
            DeleteRecordProducerParams,
            str,
            "Delete a record producer in ServiceNow",
            "json_dict",
        ),
        # Client Script Tools
        "list_client_scripts": (
            list_client_scripts_tool,
            ListClientScriptsParams,
            Dict[str, Any],  # Expects dict
            "List client scripts (sys_script_client) from ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        "get_client_script": (
            get_client_script_tool,
            GetClientScriptParams,
            Dict[str, Any],  # Expects dict
            "Get a specific client script from ServiceNow by sys_id or name",
            "raw_dict",  # Tool returns raw dict
        ),
        "create_client_script": (
            create_client_script_tool,
            CreateClientScriptParams,
            ClientScriptResponse,  # Expects Pydantic model
            "Create a new client script (e.g. onLoad alert on a form) in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "update_client_script": (
            update_client_script_tool,
            UpdateClientScriptParams,
            ClientScriptResponse,  # Expects Pydantic model
            "Update an existing client script in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "delete_client_script": (
            delete_client_script_tool,
            DeleteClientScriptParams,
            str,  # Expects JSON string
            "Delete a client script in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        # Service Portal Widget Tools
        "list_sp_widgets": (
            list_sp_widgets_tool,
            ListSpWidgetsParams,
            Dict[str, Any],  # Expects dict
            "List Service Portal widgets (sp_widget) from ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        "get_sp_widget": (
            get_sp_widget_tool,
            GetSpWidgetParams,
            Dict[str, Any],  # Expects dict
            "Get a Service Portal widget from ServiceNow by sys_id, widget id, or name",
            "raw_dict",  # Tool returns raw dict
        ),
        "create_sp_widget": (
            create_sp_widget_tool,
            CreateSpWidgetParams,
            SpWidgetResponse,  # Expects Pydantic model
            "Create a new Service Portal widget in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "update_sp_widget": (
            update_sp_widget_tool,
            UpdateSpWidgetParams,
            SpWidgetResponse,  # Expects Pydantic model
            "Update an existing Service Portal widget (template, css, scripts, etc.) in ServiceNow",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        "delete_sp_widget": (
            delete_sp_widget_tool,
            DeleteSpWidgetParams,
            str,  # Expects JSON string
            "Delete a Service Portal widget in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        # Current Update Set Tools
        "get_current_update_set": (
            get_current_update_set_tool,
            GetCurrentUpdateSetParams,
            Dict[str, Any],  # Expects dict
            "Get the update set currently active for the authenticated user",
            "raw_dict",  # Tool returns raw dict
        ),
        "set_current_update_set": (
            set_current_update_set_tool,
            SetCurrentUpdateSetParams,
            CurrentUpdateSetResponse,  # Expects Pydantic model
            "Set the current update set so changes are captured into it (not Global)",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        # Instance Selection Tools
        "list_instances": (
            list_instances_tool,
            ListInstancesParams,
            Dict[str, Any],  # Expects dict
            "List the ServiceNow instances available to connect to (no secrets)",
            "raw_dict",  # Tool returns raw dict
        ),
        "get_current_instance": (
            get_current_instance_tool,
            GetCurrentInstanceParams,
            Dict[str, Any],  # Expects dict
            "Get the ServiceNow instance the server is currently connected to",
            "raw_dict",  # Tool returns raw dict
        ),
        "select_instance": (
            select_instance_tool,
            SelectInstanceParams,
            InstanceSelectionResponse,  # Expects Pydantic model
            "Switch the active ServiceNow instance for this session",
            "raw_pydantic",  # Tool returns Pydantic model
        ),
        # Knowledge Base Tools
        "create_knowledge_base": (
            create_knowledge_base_tool,
            CreateKnowledgeBaseParams,
            str,  # Expects JSON string
            "Create a new knowledge base in ServiceNow",
            "json_dict",  # Tool returns Pydantic model
        ),
        "list_knowledge_bases": (
            list_knowledge_bases_tool,
            ListKnowledgeBasesParams,
            Dict[str, Any],  # Expects dict
            "List knowledge bases from ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        # Use the passed-in implementations for aliased KB category tools
        "create_category": (
            create_kb_category_tool_impl,  # Use passed function
            CreateKBCategoryParams,
            str,  # Expects JSON string
            "Create a new category in a knowledge base",
            "json_dict",  # Tool returns Pydantic model
        ),
        "create_article": (
            create_article_tool,
            CreateArticleParams,
            str,  # Expects JSON string
            "Create a new knowledge article",
            "json_dict",  # Tool returns Pydantic model
        ),
        "update_article": (
            update_article_tool,
            UpdateArticleParams,
            str,  # Expects JSON string
            "Update an existing knowledge article",
            "json_dict",  # Tool returns Pydantic model
        ),
        "publish_article": (
            publish_article_tool,
            PublishArticleParams,
            str,  # Expects JSON string
            "Publish a knowledge article",
            "json_dict",  # Tool returns Pydantic model
        ),
        "list_articles": (
            list_articles_tool,
            ListArticlesParams,
            Dict[str, Any],  # Expects dict
            "List knowledge articles",
            "raw_dict",  # Tool returns raw dict
        ),
        "get_article": (
            get_article_tool,
            GetArticleParams,
            Dict[str, Any],  # Expects dict
            "Get a specific knowledge article by ID",
            "raw_dict",  # Tool returns raw dict
        ),
        # Use the passed-in implementations for aliased KB category tools
        "list_categories": (
            list_kb_categories_tool_impl,  # Use passed function
            ListKBCategoriesParams,
            Dict[str, Any],  # Expects dict
            "List categories in a knowledge base",
            "raw_dict",  # Tool returns raw dict
        ),
        # User Management Tools
        "create_user": (
            create_user_tool,
            CreateUserParams,
            Dict[str, Any],  # Expects dict
            "Create a new user in ServiceNow",
            "raw_dict",  # Tool returns raw dict
        ),
        "update_user": (
            update_user_tool,
            UpdateUserParams,
            Dict[str, Any],  # Expects dict
            "Update an existing user in ServiceNow",
            "raw_dict",
        ),
        "get_user": (
            get_user_tool,
            GetUserParams,
            Dict[str, Any],  # Expects dict
            "Get a specific user in ServiceNow",
            "raw_dict",
        ),
        "list_users": (
            list_users_tool,
            ListUsersParams,
            Dict[str, Any],  # Expects dict
            "List users in ServiceNow",
            "raw_dict",
        ),
        "create_group": (
            create_group_tool,
            CreateGroupParams,
            Dict[str, Any],  # Expects dict
            "Create a new group in ServiceNow",
            "raw_dict",
        ),
        "update_group": (
            update_group_tool,
            UpdateGroupParams,
            Dict[str, Any],  # Expects dict
            "Update an existing group in ServiceNow",
            "raw_dict",
        ),
        "add_group_members": (
            add_group_members_tool,
            AddGroupMembersParams,
            Dict[str, Any],  # Expects dict
            "Add members to an existing group in ServiceNow",
            "raw_dict",
        ),
        "remove_group_members": (
            remove_group_members_tool,
            RemoveGroupMembersParams,
            Dict[str, Any],  # Expects dict
            "Remove members from an existing group in ServiceNow",
            "raw_dict",
        ),
        "list_groups": (
            list_groups_tool,
            ListGroupsParams,
            Dict[str, Any],  # Expects dict
            "List groups from ServiceNow with optional filtering",
            "raw_dict",
        ),
        # Story Management Tools
        "create_story": (
            create_story_tool,
            CreateStoryParams,
            str,
            "Create a new story in ServiceNow",
            "str",
        ),
        "update_story": (
            update_story_tool,
            UpdateStoryParams,
            str,
            "Update an existing story in ServiceNow",
            "str",
        ),
        "list_stories": (
            list_stories_tool,
            ListStoriesParams,
            str,  # Expects JSON string
            "List stories from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "list_story_dependencies": (
            list_story_dependencies_tool,
            ListStoryDependenciesParams,
            str,  # Expects JSON string
            "List story dependencies from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        "create_story_dependency": (
            create_story_dependency_tool,
            CreateStoryDependencyParams,
            str,
            "Create a dependency between two stories in ServiceNow",
            "str",
        ),
        "delete_story_dependency": (
            delete_story_dependency_tool,
            DeleteStoryDependencyParams,
            str,
            "Delete a story dependency in ServiceNow",
            "str",
        ),
        # Epic Management Tools
        "create_epic": (
            create_epic_tool,
            CreateEpicParams,
            str,
            "Create a new epic in ServiceNow",
            "str",
        ),
        "update_epic": (
            update_epic_tool,
            UpdateEpicParams,
            str,
            "Update an existing epic in ServiceNow",
            "str",
        ),
        "list_epics": (
            list_epics_tool,
            ListEpicsParams,
            str,  # Expects JSON string
            "List epics from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        # Scrum Task Management Tools
        "create_scrum_task": (
            create_scrum_task_tool,
            CreateScrumTaskParams,
            str,
            "Create a new scrum task in ServiceNow",
            "str",
        ),
        "update_scrum_task": (
            update_scrum_task_tool,
            UpdateScrumTaskParams,
            str,
            "Update an existing scrum task in ServiceNow",
            "str",
        ),
        "list_scrum_tasks": (
            list_scrum_tasks_tool,
            ListScrumTasksParams,
            str,  # Expects JSON string
            "List scrum tasks from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        # Project Management Tools
        "create_project": (
            create_project_tool,
            CreateProjectParams,
            str,
            "Create a new project in ServiceNow",
            "str",
        ),
        "update_project": (
            update_project_tool,
            UpdateProjectParams,
            str,
            "Update an existing project in ServiceNow",
            "str",
        ),
        "list_projects": (
            list_projects_tool,
            ListProjectsParams,
            str,  # Expects JSON string
            "List projects from ServiceNow",
            "json",  # Tool returns list/dict
        ),
        # Business Rule Tools
        "list_business_rules": (
            list_business_rules_tool,
            ListBusinessRulesParams,
            Dict[str, Any],
            "List business rules (sys_script) from ServiceNow",
            "raw_dict",
        ),
        "get_business_rule": (
            get_business_rule_tool,
            GetBusinessRuleParams,
            Dict[str, Any],
            "Get a specific business rule from ServiceNow",
            "raw_dict",
        ),
        "create_business_rule": (
            create_business_rule_tool,
            CreateBusinessRuleParams,
            BusinessRuleResponse,
            "Create a new business rule (sys_script) in ServiceNow",
            "raw_pydantic",
        ),
        "update_business_rule": (
            update_business_rule_tool,
            UpdateBusinessRuleParams,
            BusinessRuleResponse,
            "Update an existing business rule in ServiceNow",
            "raw_pydantic",
        ),
        "delete_business_rule": (
            delete_business_rule_tool,
            DeleteBusinessRuleParams,
            str,
            "Delete a business rule in ServiceNow",
            "json_dict",
        ),
        # System Property Tools
        "list_system_properties": (
            list_system_properties_tool,
            ListSystemPropertysParams,
            Dict[str, Any],
            "List system properties (sys_properties) from ServiceNow",
            "raw_dict",
        ),
        "get_system_property": (
            get_system_property_tool,
            GetSystemPropertyParams,
            Dict[str, Any],
            "Get a specific system property from ServiceNow",
            "raw_dict",
        ),
        "create_system_property": (
            create_system_property_tool,
            CreateSystemPropertyParams,
            SystemPropertyResponse,
            "Create a new system property (sys_properties) in ServiceNow",
            "raw_pydantic",
        ),
        "update_system_property": (
            update_system_property_tool,
            UpdateSystemPropertyParams,
            SystemPropertyResponse,
            "Update an existing system property in ServiceNow",
            "raw_pydantic",
        ),
        "delete_system_property": (
            delete_system_property_tool,
            DeleteSystemPropertyParams,
            str,
            "Delete a system property in ServiceNow",
            "json_dict",
        ),
        # UI Policy Tools
        "list_ui_policies": (
            list_ui_policies_tool,
            ListUiPolicysParams,
            Dict[str, Any],
            "List UI policies (sys_ui_policy) from ServiceNow",
            "raw_dict",
        ),
        "get_ui_policy": (
            get_ui_policy_tool,
            GetUiPolicyParams,
            Dict[str, Any],
            "Get a specific UI policy from ServiceNow",
            "raw_dict",
        ),
        "create_ui_policy": (
            create_ui_policy_tool,
            CreateUiPolicyParams,
            UiPolicyResponse,
            "Create a new UI policy (sys_ui_policy) in ServiceNow",
            "raw_pydantic",
        ),
        "update_ui_policy": (
            update_ui_policy_tool,
            UpdateUiPolicyParams,
            UiPolicyResponse,
            "Update an existing UI policy in ServiceNow",
            "raw_pydantic",
        ),
        "delete_ui_policy": (
            delete_ui_policy_tool,
            DeleteUiPolicyParams,
            str,
            "Delete a UI policy in ServiceNow",
            "json_dict",
        ),
        # UI Policy Action Tools
        "list_ui_policy_actions": (
            list_ui_policy_actions_tool,
            ListUiPolicyActionsParams,
            Dict[str, Any],
            "List UI policy actions (sys_ui_policy_action) from ServiceNow",
            "raw_dict",
        ),
        "get_ui_policy_action": (
            get_ui_policy_action_tool,
            GetUiPolicyActionParams,
            Dict[str, Any],
            "Get a specific UI policy action from ServiceNow",
            "raw_dict",
        ),
        "create_ui_policy_action": (
            create_ui_policy_action_tool,
            CreateUiPolicyActionParams,
            UiPolicyActionResponse,
            "Create a new UI policy action (sys_ui_policy_action) in ServiceNow",
            "raw_pydantic",
        ),
        "update_ui_policy_action": (
            update_ui_policy_action_tool,
            UpdateUiPolicyActionParams,
            UiPolicyActionResponse,
            "Update an existing UI policy action in ServiceNow",
            "raw_pydantic",
        ),
        "delete_ui_policy_action": (
            delete_ui_policy_action_tool,
            DeleteUiPolicyActionParams,
            str,
            "Delete a UI policy action in ServiceNow",
            "json_dict",
        ),
        # UI Action Tools
        "list_ui_actions": (
            list_ui_actions_tool,
            ListUiActionsParams,
            Dict[str, Any],
            "List UI actions (sys_ui_action) from ServiceNow",
            "raw_dict",
        ),
        "get_ui_action": (
            get_ui_action_tool,
            GetUiActionParams,
            Dict[str, Any],
            "Get a specific UI action from ServiceNow",
            "raw_dict",
        ),
        "create_ui_action": (
            create_ui_action_tool,
            CreateUiActionParams,
            UiActionResponse,
            "Create a new UI action (sys_ui_action) in ServiceNow",
            "raw_pydantic",
        ),
        "update_ui_action": (
            update_ui_action_tool,
            UpdateUiActionParams,
            UiActionResponse,
            "Update an existing UI action in ServiceNow",
            "raw_pydantic",
        ),
        "delete_ui_action": (
            delete_ui_action_tool,
            DeleteUiActionParams,
            str,
            "Delete a UI action in ServiceNow",
            "json_dict",
        ),
        # Dictionary Entry Tools
        "list_dictionary_entries": (
            list_dictionary_entries_tool,
            ListDictionaryEntrysParams,
            Dict[str, Any],
            "List dictionary entries (sys_dictionary) from ServiceNow",
            "raw_dict",
        ),
        "get_dictionary_entry": (
            get_dictionary_entry_tool,
            GetDictionaryEntryParams,
            Dict[str, Any],
            "Get a specific dictionary entry from ServiceNow",
            "raw_dict",
        ),
        "create_dictionary_entry": (
            create_dictionary_entry_tool,
            CreateDictionaryEntryParams,
            DictionaryEntryResponse,
            "Create a new dictionary entry (sys_dictionary) in ServiceNow",
            "raw_pydantic",
        ),
        "update_dictionary_entry": (
            update_dictionary_entry_tool,
            UpdateDictionaryEntryParams,
            DictionaryEntryResponse,
            "Update an existing dictionary entry in ServiceNow",
            "raw_pydantic",
        ),
        "delete_dictionary_entry": (
            delete_dictionary_entry_tool,
            DeleteDictionaryEntryParams,
            str,
            "Delete a dictionary entry in ServiceNow",
            "json_dict",
        ),
        # Choice Tools
        "list_choices": (
            list_choices_tool,
            ListChoicesParams,
            Dict[str, Any],
            "List choices (sys_choice) from ServiceNow",
            "raw_dict",
        ),
        "get_choice": (
            get_choice_tool,
            GetChoiceParams,
            Dict[str, Any],
            "Get a specific choice from ServiceNow",
            "raw_dict",
        ),
        "create_choice": (
            create_choice_tool,
            CreateChoiceParams,
            ChoiceResponse,
            "Create a new choice (sys_choice) in ServiceNow",
            "raw_pydantic",
        ),
        "update_choice": (
            update_choice_tool,
            UpdateChoiceParams,
            ChoiceResponse,
            "Update an existing choice in ServiceNow",
            "raw_pydantic",
        ),
        "delete_choice": (
            delete_choice_tool,
            DeleteChoiceParams,
            str,
            "Delete a choice in ServiceNow",
            "json_dict",
        ),
        # Email Notification Tools
        "list_email_notifications": (
            list_email_notifications_tool,
            ListEmailNotificationsParams,
            Dict[str, Any],
            "List email notifications (sysevent_email_action) from ServiceNow",
            "raw_dict",
        ),
        "get_email_notification": (
            get_email_notification_tool,
            GetEmailNotificationParams,
            Dict[str, Any],
            "Get a specific email notification from ServiceNow",
            "raw_dict",
        ),
        "create_email_notification": (
            create_email_notification_tool,
            CreateEmailNotificationParams,
            EmailNotificationResponse,
            "Create a new email notification (sysevent_email_action) in ServiceNow",
            "raw_pydantic",
        ),
        "update_email_notification": (
            update_email_notification_tool,
            UpdateEmailNotificationParams,
            EmailNotificationResponse,
            "Update an existing email notification in ServiceNow",
            "raw_pydantic",
        ),
        "delete_email_notification": (
            delete_email_notification_tool,
            DeleteEmailNotificationParams,
            str,
            "Delete a email notification in ServiceNow",
            "json_dict",
        ),
        # ACL Tools
        "list_acls": (
            list_acls_tool,
            ListAclsParams,
            Dict[str, Any],
            "List ACLs (sys_security_acl) from ServiceNow",
            "raw_dict",
        ),
        "get_acl": (
            get_acl_tool,
            GetAclParams,
            Dict[str, Any],
            "Get a specific ACL from ServiceNow",
            "raw_dict",
        ),
        "create_acl": (
            create_acl_tool,
            CreateAclParams,
            AclResponse,
            "Create a new ACL (sys_security_acl) in ServiceNow",
            "raw_pydantic",
        ),
        "update_acl": (
            update_acl_tool,
            UpdateAclParams,
            AclResponse,
            "Update an existing ACL in ServiceNow",
            "raw_pydantic",
        ),
        "delete_acl": (
            delete_acl_tool,
            DeleteAclParams,
            str,
            "Delete a ACL in ServiceNow",
            "json_dict",
        ),
        # Service Portal Widget Instance Tools
        "list_sp_instances": (
            list_sp_instances_tool,
            ListSpInstancesParams,
            Dict[str, Any],
            "List Service Portal widget instances (sp_instance) from ServiceNow",
            "raw_dict",
        ),
        "get_sp_instance": (
            get_sp_instance_tool,
            GetSpInstanceParams,
            Dict[str, Any],
            "Get a specific Service Portal widget instance from ServiceNow",
            "raw_dict",
        ),
        "create_sp_instance": (
            create_sp_instance_tool,
            CreateSpInstanceParams,
            SpInstanceResponse,
            "Create a new Service Portal widget instance (sp_instance) in ServiceNow",
            "raw_pydantic",
        ),
        "update_sp_instance": (
            update_sp_instance_tool,
            UpdateSpInstanceParams,
            SpInstanceResponse,
            "Update an existing Service Portal widget instance in ServiceNow",
            "raw_pydantic",
        ),
        "delete_sp_instance": (
            delete_sp_instance_tool,
            DeleteSpInstanceParams,
            str,
            "Delete a Service Portal widget instance in ServiceNow",
            "json_dict",
        ),
        # Service Portal Page Tools
        "list_sp_pages": (
            list_sp_pages_tool,
            ListSpPagesParams,
            Dict[str, Any],
            "List Service Portal pages (sp_page) from ServiceNow",
            "raw_dict",
        ),
        "get_sp_page": (
            get_sp_page_tool,
            GetSpPageParams,
            Dict[str, Any],
            "Get a specific Service Portal page from ServiceNow",
            "raw_dict",
        ),
        "create_sp_page": (
            create_sp_page_tool,
            CreateSpPageParams,
            SpPageResponse,
            "Create a new Service Portal page (sp_page) in ServiceNow",
            "raw_pydantic",
        ),
        "update_sp_page": (
            update_sp_page_tool,
            UpdateSpPageParams,
            SpPageResponse,
            "Update an existing Service Portal page in ServiceNow",
            "raw_pydantic",
        ),
        "delete_sp_page": (
            delete_sp_page_tool,
            DeleteSpPageParams,
            str,
            "Delete a Service Portal page in ServiceNow",
            "json_dict",
        ),
        # UI Script Tools
        "list_ui_scripts": (
            list_ui_scripts_tool,
            ListUiScriptsParams,
            Dict[str, Any],
            "List UI scripts (sys_ui_script) from ServiceNow",
            "raw_dict",
        ),
        "get_ui_script": (
            get_ui_script_tool,
            GetUiScriptParams,
            Dict[str, Any],
            "Get a specific UI script from ServiceNow",
            "raw_dict",
        ),
        "create_ui_script": (
            create_ui_script_tool,
            CreateUiScriptParams,
            UiScriptResponse,
            "Create a new UI script (sys_ui_script) in ServiceNow",
            "raw_pydantic",
        ),
        "update_ui_script": (
            update_ui_script_tool,
            UpdateUiScriptParams,
            UiScriptResponse,
            "Update an existing UI script in ServiceNow",
            "raw_pydantic",
        ),
        "delete_ui_script": (
            delete_ui_script_tool,
            DeleteUiScriptParams,
            str,
            "Delete a UI script in ServiceNow",
            "json_dict",
        ),
        # Scheduled Job Tools
        "list_scheduled_jobs": (
            list_scheduled_jobs_tool,
            ListScheduledJobsParams,
            Dict[str, Any],
            "List scheduled jobs (sysauto_script) from ServiceNow",
            "raw_dict",
        ),
        "get_scheduled_job": (
            get_scheduled_job_tool,
            GetScheduledJobParams,
            Dict[str, Any],
            "Get a specific scheduled job from ServiceNow",
            "raw_dict",
        ),
        "create_scheduled_job": (
            create_scheduled_job_tool,
            CreateScheduledJobParams,
            ScheduledJobResponse,
            "Create a new scheduled job (sysauto_script) in ServiceNow",
            "raw_pydantic",
        ),
        "update_scheduled_job": (
            update_scheduled_job_tool,
            UpdateScheduledJobParams,
            ScheduledJobResponse,
            "Update an existing scheduled job in ServiceNow",
            "raw_pydantic",
        ),
        "delete_scheduled_job": (
            delete_scheduled_job_tool,
            DeleteScheduledJobParams,
            str,
            "Delete a scheduled job in ServiceNow",
            "json_dict",
        ),
        # Data Policy Tools
        "list_data_policies": (
            list_data_policies_tool,
            ListDataPolicysParams,
            Dict[str, Any],
            "List data policies (sys_data_policy2) from ServiceNow",
            "raw_dict",
        ),
        "get_data_policy": (
            get_data_policy_tool,
            GetDataPolicyParams,
            Dict[str, Any],
            "Get a specific data policy from ServiceNow",
            "raw_dict",
        ),
        "create_data_policy": (
            create_data_policy_tool,
            CreateDataPolicyParams,
            DataPolicyResponse,
            "Create a new data policy (sys_data_policy2) in ServiceNow",
            "raw_pydantic",
        ),
        "update_data_policy": (
            update_data_policy_tool,
            UpdateDataPolicyParams,
            DataPolicyResponse,
            "Update an existing data policy in ServiceNow",
            "raw_pydantic",
        ),
        "delete_data_policy": (
            delete_data_policy_tool,
            DeleteDataPolicyParams,
            str,
            "Delete a data policy in ServiceNow",
            "json_dict",
        ),
        # Data Policy Rule Tools
        "list_data_policy_rules": (
            list_data_policy_rules_tool,
            ListDataPolicyRulesParams,
            Dict[str, Any],
            "List data policy rules (sys_data_policy_rule) from ServiceNow",
            "raw_dict",
        ),
        "get_data_policy_rule": (
            get_data_policy_rule_tool,
            GetDataPolicyRuleParams,
            Dict[str, Any],
            "Get a specific data policy rule from ServiceNow",
            "raw_dict",
        ),
        "create_data_policy_rule": (
            create_data_policy_rule_tool,
            CreateDataPolicyRuleParams,
            DataPolicyRuleResponse,
            "Create a new data policy rule (sys_data_policy_rule) in ServiceNow",
            "raw_pydantic",
        ),
        "update_data_policy_rule": (
            update_data_policy_rule_tool,
            UpdateDataPolicyRuleParams,
            DataPolicyRuleResponse,
            "Update an existing data policy rule in ServiceNow",
            "raw_pydantic",
        ),
        "delete_data_policy_rule": (
            delete_data_policy_rule_tool,
            DeleteDataPolicyRuleParams,
            str,
            "Delete a data policy rule in ServiceNow",
            "json_dict",
        ),
        # Role Tools
        "list_roles": (
            list_roles_tool,
            ListRolesParams,
            Dict[str, Any],
            "List roles (sys_user_role) from ServiceNow",
            "raw_dict",
        ),
        "get_role": (
            get_role_tool,
            GetRoleParams,
            Dict[str, Any],
            "Get a specific role from ServiceNow",
            "raw_dict",
        ),
        "create_role": (
            create_role_tool,
            CreateRoleParams,
            RoleResponse,
            "Create a new role (sys_user_role) in ServiceNow",
            "raw_pydantic",
        ),
        "update_role": (
            update_role_tool,
            UpdateRoleParams,
            RoleResponse,
            "Update an existing role in ServiceNow",
            "raw_pydantic",
        ),
        "delete_role": (
            delete_role_tool,
            DeleteRoleParams,
            str,
            "Delete a role in ServiceNow",
            "json_dict",
        ),
        # __GEN_TU_DEFS__
    }
    return tool_definitions
