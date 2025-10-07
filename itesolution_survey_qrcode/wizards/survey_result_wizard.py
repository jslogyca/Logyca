from odoo import fields, models, api


class SurveyResultWizard(models.TransientModel):
    _name = 'survey.result.wizard'
    _description = 'Survey Result Viewing Wizard'

    type = fields.Selection([('all', 'All'), ('manual', 'Manual')], 'Type', default='all', required=True)
    date_begin = fields.Date('Start Date')
    date_end = fields.Date('End Date')

    def button_done(self):
        self.ensure_one()
        if self.type == 'manual':
            url = '/survey/results/%s?date_begin=%s&date_end=%s' % (self.env.context.get('active_id'),
                                                                    self.date_begin, self.date_end)
        else:
            url = '/survey/results/%s' % self.env.context.get('active_id')
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Survey",
            'target': 'self',
            'url': url
        }
