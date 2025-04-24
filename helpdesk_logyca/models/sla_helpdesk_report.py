# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.addons.helpdesk.models.helpdesk_ticket import TICKET_PRIORITY


class SLAHelpdeskReport(models.Model):
    _name = 'sla.helpdesk.report'
    _description = "SLA Status"
    _auto = False
    _order = 'create_date DESC'

    id = fields.Integer('ID')
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', readonly=True)
    sla_status_id = fields.Many2one('helpdesk.sla.status', string='SLA Status', readonly=True)
    create_date = fields.Date("Ticket Create Date", readonly=True)
    priority = fields.Selection(TICKET_PRIORITY, string='Minimum Priority', readonly=True)
    user_id = fields.Many2one('res.users', string="Assigned To", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    vat_partner = fields.Char(related='partner_id.vat')
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket Type", readonly=True)
    ticket_stage_id = fields.Many2one('helpdesk.stage', string="Ticket Stage", readonly=True)
    ticket_deadline = fields.Datetime("Ticket Deadline", readonly=True)
    ticket_failed = fields.Boolean("Ticket Failed", group_operator="bool_or", readonly=True)
    ticket_closed = fields.Boolean("Ticket Closed", readonly=True)
    ticket_close_hours = fields.Integer("Time to close (hours)", group_operator="avg", readonly=True)
    ticket_open_hours = fields.Integer("Open Time (hours)", group_operator="avg", readonly=True)
    ticket_assignation_hours = fields.Integer("Time to first assignation (hours)", group_operator="avg", readonly=True)

    sla_id = fields.Many2one('helpdesk.sla', string="SLA", readonly=True)
    sla_stage_id = fields.Many2one('helpdesk.stage', string="SLA Stage", readonly=True)
    sla_deadline = fields.Datetime("SLA Deadline", group_operator='min', readonly=True)
    sla_reached_datetime = fields.Datetime("SLA Reached Date", group_operator='min', readonly=True)
    sla_status = fields.Selection([('failed', 'Failed'), ('reached', 'Reached'), ('ongoing', 'Ongoing')], string="Status", readonly=True)
    sla_status_failed = fields.Boolean("SLA Status Failed", group_operator='bool_or', readonly=True)
    sla_exceeded_days = fields.Integer("Day to reach SLA", group_operator='avg', readonly=True, help="Day to reach the stage of the SLA, without taking the working calendar into account")

    team_id = fields.Many2one('helpdesk.team', string='Team', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    type_desk = fields.Selection([("pqrs","PQRS (Peticiones, Quejas, Reclamo, Solucitudes y Felicitaciones)"),
                                    ("support","Support"),
                                    ("sale","Sale")], string='Desk Type', default='support')
    platform_id = fields.Many2one('helpdesk.platform', string='Platform')
    service_id = fields.Many2one('helpdesk.service', string='Service')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sla_helpdesk_report')
        self.env.cr.execute("""
            CREATE VIEW sla_helpdesk_report AS (
                SELECT
                    T.id AS id,
                    ST.id as sla_status_id,
                    T.create_date AS create_date,
                    T.id AS ticket_id,
                    T.team_id,
                    T.stage_id AS ticket_stage_id,
                    T.ticket_type_id,
                    T.type_desk AS type_desk,
                    T.platform_id AS platform_id,
                    T.service_id AS service_id,
                    T.user_id,
                    T.partner_id,
                    p.vat AS vat_partner,
                    T.company_id,
                    T.x_type_vinculation as x_type_vinculation,
                    T.priority AS priority,
                    T.sla_reached_late OR T.sla_deadline < NOW() AT TIME ZONE 'UTC' AS ticket_failed,
                    T.sla_deadline AS ticket_deadline,
                    T.close_hours AS ticket_close_hours,
                    EXTRACT(HOUR FROM (COALESCE(T.assign_date, NOW()) - T.create_date)) AS ticket_open_hours,
                    T.assign_hours AS ticket_assignation_hours,
                    ST.sla_id,
                    SLA.stage_id AS sla_stage_id,
                    ST.deadline AS sla_deadline,
                    ST.reached_datetime AS sla_reached_datetime,
                    ST.reached_datetime >= ST.deadline OR (ST.reached_datetime IS NULL AND ST.deadline < NOW() AT TIME ZONE 'UTC') AS sla_status_failed
                FROM helpdesk_ticket T
                    LEFT JOIN helpdesk_stage STA ON (T.stage_id = STA.id)
                    LEFT JOIN helpdesk_sla_status ST ON (T.id = ST.ticket_id)
                    LEFT JOIN helpdesk_sla SLA ON (ST.sla_id = SLA.id)
                    LEFT JOIN res_partner p ON p.id=T.partner_id
                )
            """)
