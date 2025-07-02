{
    "name"          :  "CRM Dashboard",
    "version"       :  "17.0.1.0.0",
    'summary'       :  "dashboard, crm dashboard, sales dashboard, odoo crm, crm metrics, deal size tracker, win rate tracker, crm analytics, sales insights, crm reporting, crm kanban view, pipeline dashboard, odoo sales tracker, crm stats, opportunity dashboard, odoo pipeline, sales performance odoo, crm module odoo, quick crm insights, sales overview, crm kpis, odoo crm plugin, crm analytics odoo, deal tracking",
    "description"   :  "This Module Adds A Small Dashboard Above the CRM Kanban View And Displays (Open Opportunities, Average Deal Size, Days To Win, Won Opportunities, Closed, Closing Rate)",
    'author'        :  "SOFT TECH LTD",
    "website"       :  "softatt.com",
    "license"       :  "OPL-1",
    "category"      :  "sales",
    "depends"       :  ["base", "crm", "sales_team"],
    "currency"      :  "USD",
    "data"          :  [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/dashboard_filters.xml",
        
        ],
    "assets": {
        "web.assets_backend": [
            "sa_crm_dashboard_mini/static/src/components/dashboard/**",
            "sa_crm_dashboard_mini/static/src/scss/**",
            "sa_crm_dashboard_mini/static/src/views/crm/*.js",
            "sa_crm_dashboard_mini/static/src/views/crm/*.xml",
            ],
    },
    "images": ['static/description/banner.gif'],

}
