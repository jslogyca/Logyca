from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError


class deliveringColaboraMassively(models.TransientModel):
    _name = "deliver.colabora.massively"
    _description = "Wizard to deliver colabora massively"

    def deliverColabora(self):
        context = dict(self._context or {})
        postulations = self.env['benefit.application'].browse(context.get('active_ids'))
        colabora_postulations = postulations.filtered(lambda p: p.benefit_name == 'colabora')
        if not colabora_postulations:
            raise UserError(_('¡Error! Entre las postulaciones seleccionadas, ninguna es el beneficio LOGYCA/COLABORA.'))
        self.deliver(colabora_postulations)
        return {'type': 'ir.actions.act_window_close'}


    def deliver(self, postulations_ids):
        for benefit_application in postulations_ids:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if benefit_application.partner_id.contact_email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_welcome_kit_colabora_rvc')
                template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)

                if not benefit_application.gln:
                    # si no tiene GLN, asignamos uno.
                    if benefit_application._validate_gln() == False and benefit_application.glns_codes_quantity == 0:
                        benefit_application.assignate_gln_code()

                if benefit_application.assign_colabora():
                    benefit_application.assign_credentials_colabora()

                # Actualizar Contacto y Empresa
                benefit_application.update_contact(benefit_application.partner_id)
                if benefit_application.parent_id:
                    benefit_application.update_company(benefit_application)

                benefit_application.write({'state': 'done'})
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))
            
        return {'type': 'ir.actions.act_window_close'}