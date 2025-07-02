/** @odoo-module **/

import { registry } from "@web/core/registry";
import { crmKanbanView } from '@crm/views/crm_kanban/crm_kanban_view';  // Import the original CRM Kanban view
import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
import { SaCrmDashboard } from '@sa_crm_dashboard_mini/components/dashboard/dashboard';

// Create an extended renderer to include SaCrmDashboard
export class SaCrmDashboardKanbanRenderer extends KanbanRenderer {}

// Assign the custom template and add SaCrmDashboard as a component
SaCrmDashboardKanbanRenderer.template = 'sa_crm_dashboard_mini.SaCrmMiniDashboardKanbanView';
SaCrmDashboardKanbanRenderer.components = {
    ...KanbanRenderer.components,
    SaCrmDashboard,
};

// Extend crmKanbanView by replacing its renderer with the new one
export const SaCrmDashboardKanbanView = {
    ...crmKanbanView,
    Renderer: SaCrmDashboardKanbanRenderer,
};

// Update the registry with the extended view without adding a new entry
registry.category("views").add("crm_kanban", SaCrmDashboardKanbanView, { force: true });
