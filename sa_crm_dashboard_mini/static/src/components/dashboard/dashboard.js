/** @odoo-module **/

import { session } from '@web/session';
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class SaCrmDashboard extends Component {
    setup() {
        this.action = useService('action');
        this.orm = useService('orm');
        this.state = useState({
            dashboardValues: null,
            isCollapsed: false,
            isHidden: true,
        });
        onWillStart(this.onWillStart);
    }
    async onWillStart() {
        await this._checkUserGroup();
        if (!this.state.isHidden) {
            await this._fetchData();
        }
    }
    async _fetchData() {
        this.state.dashboardValues = await this.orm.call(
            'crm.lead',
            'get_sa_dashboard_values',
            [],
            { context: session.user_context },
        );
    }

    toggleFiltersWizard() {
        const action = {
            type: "ir.actions.act_window",
            name: "Filters",
            res_model: "sa.crm.filters.wizard",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
        };
    
        this.action.doAction(action);
    }

    ChangeSearchVals(ev) {
        const filters = ev.currentTarget.getAttribute("filter_name");
        const filters_list = filters.split(",");
        const searchItems = this.env.searchModel.getSearchItems((item) =>
            filters_list.includes(item.name)
        );
        this.env.searchModel.query = [];
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }

    toggleCollapse() {
        this.state.isCollapsed = !this.state.isCollapsed;
    }

    async _checkUserGroup() {
        const groupId = 'sa_crm_dashboard_mini.group_sa_crm_min_dashboard';
        try {
            const hasGroup = await this.orm.call('res.users', 'has_group', [groupId]);
            this.state.isHidden = !hasGroup;
        } catch (error) {
            console.error("Error checking user group:", error);
            this.state.isHidden = true;
        }
    }
}

SaCrmDashboard.template = 'sa_crm_dashboard_mini.SaCrmDashboard';