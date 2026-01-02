# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleConditionalDiscountLine(models.TransientModel):
    _name = 'sale.conditional.discount.line'
    _description = 'Línea de Orden de Venta para Cálculo de Descuento'
    
    wizard_id = fields.Many2one(
        'sale.conditional.discount.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=True,
        readonly=True
    )
    
    order_name = fields.Char(
        string='Número Orden',
        related='order_id.name',
        readonly=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='order_id.partner_id',
        readonly=True
    )
    
    date_order = fields.Datetime(
        string='Fecha Orden',
        related='order_id.date_order',
        readonly=True
    )
    
    amount_total = fields.Monetary(
        string='Total Orden',
        related='order_id.amount_total',
        readonly=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id',
        readonly=True
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        readonly=True,
        help='Factura asociada a la orden de venta'
    )
    
    invoice_name = fields.Char(
        string='Número Factura',
        related='invoice_id.name',
        readonly=True
    )
    
    selected = fields.Boolean(
        string='Seleccionar',
        default=True,
        help='Marcar para incluir en el procesamiento'
    )
    
    x_origen = fields.Char(
        string='Origen',
        related='order_id.x_origen',
        readonly=True
    )


class SaleConditionalDiscountWizard(models.TransientModel):
    _name = 'sale.conditional.discount.wizard'
    _description = 'Wizard para Cálculo de Descuentos Condicionados'
    
    # Campo para filtrar por x_origen
    x_origen_filter = fields.Char(
        string='Filtro x_origen',
        required=True,
        help='Valor del campo x_origen para filtrar las órdenes de venta'
    )
    
    # Rango de fechas
    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        default=fields.Date.context_today,
        help='Fecha inicial del rango de búsqueda'
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.context_today,
        help='Fecha final del rango de búsqueda'
    )
    
    # Parámetros para primer descuento
    percentage_increase_1 = fields.Float(
        string='% Aumento Fecha 1',
        required=True,
        default=0.0,
        help='Porcentaje de aumento para el primer cálculo (ejemplo: 19 para 19%)'
    )
    
    percentage_discount_1 = fields.Float(
        string='% Descuento Fecha 1',
        required=True,
        default=0.0,
        help='Porcentaje de descuento para el primer cálculo (ejemplo: 3 para 3%)'
    )
    
    discount_deadline_1 = fields.Date(
        string='Fecha Descuento 1',
        required=True,
        help='Fecha límite para aplicar el primer descuento'
    )
    
    # Parámetros para segundo descuento
    percentage_increase_2 = fields.Float(
        string='% Aumento Fecha 2',
        required=True,
        default=0.0,
        help='Porcentaje de aumento para el segundo cálculo (ejemplo: 19 para 19%)'
    )
    
    percentage_discount_2 = fields.Float(
        string='% Descuento Fecha 2',
        required=True,
        default=0.0,
        help='Porcentaje de descuento para el segundo cálculo (ejemplo: 2 para 2%)'
    )
    
    discount_deadline_2 = fields.Date(
        string='Fecha Descuento 2',
        required=True,
        help='Fecha límite para aplicar el segundo descuento'
    )
    
    # Líneas de órdenes encontradas
    order_line_ids = fields.One2many(
        'sale.conditional.discount.line',
        'wizard_id',
        string='Órdenes de Venta'
    )
    
    # Estado del wizard
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('orders_loaded', 'Órdenes Cargadas'),
        ('processed', 'Procesado')
    ], string='Estado', default='draft', readonly=True)
    
    # Contadores
    orders_found = fields.Integer(
        string='Órdenes Encontradas',
        readonly=True
    )
    
    orders_processed = fields.Integer(
        string='Órdenes Procesadas',
        readonly=True
    )
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Valida que la fecha desde sea menor o igual a la fecha hasta"""
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise ValidationError(_('La fecha desde debe ser menor o igual a la fecha hasta'))
    
    @api.constrains('percentage_increase_1', 'percentage_discount_1', 
                    'percentage_increase_2', 'percentage_discount_2')
    def _check_percentages(self):
        """Valida que los porcentajes sean válidos"""
        for wizard in self:
            if wizard.percentage_increase_1 < 0 or wizard.percentage_discount_1 < 0:
                raise ValidationError(_('Los porcentajes para la fecha 1 deben ser mayores o iguales a 0'))
            if wizard.percentage_increase_2 < 0 or wizard.percentage_discount_2 < 0:
                raise ValidationError(_('Los porcentajes para la fecha 2 deben ser mayores o iguales a 0'))
    
    def action_load_orders(self):
        """Busca y carga las órdenes de venta según los criterios"""
        self.ensure_one()
        
        # Limpiar líneas anteriores
        self.order_line_ids.unlink()
        
        # Construir dominio de búsqueda
        domain = [
            ('x_origen', '=', self.x_origen_filter),
            ('date_order', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('date_order', '<=', fields.Datetime.to_datetime(self.date_to)),
            ('state', 'in', ['sale', 'done'])  # Solo órdenes confirmadas
        ]
        
        # Buscar órdenes
        orders = self.env['sale.order'].search(domain)
        
        if not orders:
            raise UserError(_('No se encontraron órdenes de venta con los criterios especificados.'))
        
        # Crear líneas del wizard
        lines_vals = []
        for order in orders:
            # Buscar factura asociada
            invoice = self.env['account.move'].search([
                ('invoice_origin', '=', order.name),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], limit=1)
            
            lines_vals.append({
                'wizard_id': self.id,
                'order_id': order.id,
                'invoice_id': invoice.id if invoice else False,
                'selected': True
            })
        
        self.order_line_ids = [(0, 0, vals) for vals in lines_vals]
        
        # Actualizar estado y contador
        self.write({
            'state': 'orders_loaded',
            'orders_found': len(orders)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.conditional.discount.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }
    
    def action_select_all(self):
        """Selecciona todas las órdenes"""
        self.ensure_one()
        self.order_line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.conditional.discount.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_deselect_all(self):
        """Deselecciona todas las órdenes"""
        self.ensure_one()
        self.order_line_ids.write({'selected': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.conditional.discount.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _calculate_conditional_discount(self, order, percentage_increase, percentage_discount):
        """
        Calcula el descuento condicionado para una orden según la fórmula:
        Por cada línea: ((((precio_unitario * cantidad) / (porcentaje_aumento + 1)) * porcentaje_aumento) * porcentaje_descuento)
        
        Args:
            order: Registro de sale.order
            percentage_increase: Porcentaje de aumento (ejemplo: 19 para 19%)
            percentage_discount: Porcentaje de descuento (ejemplo: 3 para 3%)
        
        Returns:
            float: Valor total del descuento condicionado
        """
        total_discount = 0.0
        
        # Convertir porcentajes a decimales
        inc_decimal = percentage_increase
        disc_decimal = percentage_discount
        
        for line in order.order_line:
            # Calcular subtotal de la línea
            subtotal = line.price_unit * line.product_uom_qty
            # Aplicar fórmula: ((((subtotal) / (inc + 1)) * inc) * disc)
            base_amount = subtotal / (inc_decimal + 1)
            increase_amount = base_amount * inc_decimal
            discount_amount = increase_amount * disc_decimal
            
            total_discount += discount_amount
        
        return total_discount
    
    def action_calculate_discounts(self):
        """Calcula los descuentos condicionados para las órdenes seleccionadas"""
        self.ensure_one()
        
        # Obtener líneas seleccionadas
        selected_lines = self.order_line_ids.filtered(lambda l: l.selected)
        
        if not selected_lines:
            raise UserError(_('Debe seleccionar al menos una orden para procesar.'))
        
        processed_count = 0
        
        for line in selected_lines:
            order = line.order_id
            
            # Calcular primer descuento condicionado
            discount_1 = self._calculate_conditional_discount(
                order, 
                self.percentage_increase_1, 
                self.percentage_discount_1
            )
            
            # Calcular segundo descuento condicionado
            discount_2 = self._calculate_conditional_discount(
                order, 
                self.percentage_increase_2, 
                self.percentage_discount_2
            )
            
            # Actualizar campos en la orden de venta
            order.write({
                'x_conditional_discount': discount_1,
                'x_conditional_discount_deadline': self.discount_deadline_1,
                'x_conditional_discount_second_date': discount_2,
                'x_conditional_discount_deadline_second_date': self.discount_deadline_2,
            })
            
            # Si tiene factura, actualizar también la factura
            if line.invoice_id:
                line.invoice_id.write({
                    'x_value_discounts': discount_1,
                    'x_discounts_deadline': self.discount_deadline_1,
                    'x_value_discounts_second_date': discount_2,
                    'x_discounts_deadline_second_date': self.discount_deadline_2,
                })
            
            processed_count += 1
        
        # Actualizar estado
        self.write({
            'state': 'processed',
            'orders_processed': processed_count
        })
        
        # Mostrar mensaje de éxito
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Proceso Completado!'),
                'message': _('Se calcularon los descuentos condicionados para %d órdenes.') % processed_count,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }
    
    def action_back(self):
        """Volver al estado inicial"""
        self.ensure_one()
        self.order_line_ids.unlink()
        self.write({
            'state': 'draft',
            'orders_found': 0,
            'orders_processed': 0
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.conditional.discount.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
