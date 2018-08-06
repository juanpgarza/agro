# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = ['stock.picking']
    _order = 'min_date desc'
    
    min_date = fields.Date('Fecha', required='True' )

    warehouse = fields.Char(related='picking_type_id.warehouse', string='Depósito')
    picking_type = fields.Char(related='picking_type_id.name', string='Tipo movimiento')
    code = fields.Selection(related='picking_type_id.code', string='Tipo Operación')

    user_id = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    localidad_usuario = fields.Char(related='user_id.partner_id.city', string='Localidad')

    aprobado_por_id = fields.Many2one('res.users', 'Aprobado por:')

    requiere_aprobacion = fields.Boolean(related='picking_type_id.requiere_aprobacion', string='Requiere aprobación')

    move_type = fields.Selection([
        ('direct', 'Partial'), ('one', 'All at once')], 'Delivery Type',
        default='one', required=True,
        readonly=True)

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):        
        if self.code == 'incoming':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('customer', '=', True)]}}


class StockPickingType(models.Model):
    _inherit = ['stock.picking.type']
    _rec_name = 'warehouse_id'

    requiere_aprobacion = fields.Boolean(string='Requiere aprobación', help='si está marcada, se exigirá que se informe el usuario que autorizó el movimiento')
    warehouse = fields.Char(related='warehouse_id.name', string='Depósito')


class StockProductionLot(models.Model):
    _inherit = ['stock.production.lot']

    descripcion = fields.Char('Descripción')
    fecha_produccion = fields.Datetime('Fecha de producción')
    removal_date = fields.Datetime('Fecha de vencimiento')

class StockQuant(models.Model):
    _inherit = ['stock.quant']

    removal_date = fields.Datetime(related='lot_id.removal_date', string='Fecha de venc. lote')

class StockScrap(models.Model):

    _name = 'stock.scrap'
    _inherit = ['stock.scrap', 'mail.thread']
    _description = "scrap"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('esperando', 'Esperando Aprobación'),
        ('rechazado', 'Rechazado'),
        ('done', 'Done')], string='Status', default="draft")

    evaluado_por_id = fields.Many2one('res.users','Evaluado por:')

    @api.multi
    def do_scrap(self):        
        if self.state == 'draft':            
            self.write({'state': 'esperando'})
            return True
        else:
            super(StockScrap, self).do_scrap()

    @api.multi
    def action_aprobar(self):        
        self.do_scrap()
        self.write({'evaluado_por_id': self.env.uid})        
        return True

    @api.multi
    def action_rechazar(self):        
        self.write({'state': 'rechazado'})  
        self.write({'evaluado_por_id': self.env.uid})      
        return True

