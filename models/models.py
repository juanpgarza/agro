# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = ['stock.picking']
    _order = 'min_date desc'
    
    # form view: Que la fecha sea obligatoria
    # form/tree view: cambio de Datetime a Date
    min_date = fields.Date('Fecha',required='True' )
    # tree view: para mostrar el nombre del depósito en la 
    # search view: para poder filtrar por nombre de depósito
    warehouse = fields.Char(related='picking_type_id.warehouse', string='Depósito')
    # tree view: para mostrar la descripción del Tipo de Movimiento en la tree view   
    picking_type = fields.Char(related='picking_type_id.name', string='Tipo movimiento')
    # form view: para filtrar Proveedores/Clientes según el movimiento sea de entrada o de salida 
    code = fields.Selection(related='picking_type_id.code', string='Tipo Operación')
    # Pendiente: intento asociar los filtros de movimiento por depósito a la localidad a la que está asociado
    # el usuario
    user_id = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    localidad_usuario = fields.Char(related='user_id.partner_id.city', string='Localidad')
    # poder informar el usuario que autoriza. Esto casi seguro que cambia
    aprobado_por_id = fields.Many2one('res.users', 'Aprobado por:')
    # obtener el atributo del modelo stock.picking.
    requiere_aprobacion = fields.Boolean(related='picking_type_id.requiere_aprobacion', string='Requiere aprobación')
    # form view: solo lectura y default 'todo de una vez'
    move_type = fields.Selection(default='one',readonly=True)

    # form view: carga la lista de partners con clientes o proveedores según el tipo de movimiento de stock
    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):        
        if self.code == 'incoming':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('customer', '=', True)]}}

class StockQuant(models.Model):
    _inherit = ['stock.quant']

    #tree view: para mostrar la fecha de venc.
    removal_date = fields.Datetime(related='lot_id.removal_date', string='Fecha de venc. lote')

class StockScrap(models.Model):
    _name = 'stock.scrap'
    _inherit = ['stock.scrap', 'mail.thread']
    _description = "scrap"

    # agrego estados "esperando" y "rechazado"
    state = fields.Selection([
        ('draft', 'Draft'),
        ('esperando', 'Esperando Aprobación'),
        ('rechazado', 'Rechazado'),
        ('done', 'Done')], string='Status', default="draft")
    # para registrar quien fue el usuario que aprobó/rechazó
    evaluado_por_id = fields.Many2one('res.users','Evaluado por:')    
    # sobreescribo para:
    #   de draft cambie a esperando
    #   solo realice el movimiento de stock cuando se aprueba el movimiento
    @api.multi
    def do_scrap(self):        
        if self.state == 'draft':            
            self.write({'state': 'esperando'})
            return True
        else:
            super(StockScrap, self).do_scrap()

    # hace el movimiento de stock
    # registra el usuario que aprobó  
    @api.multi
    def action_aprobar(self):        
        self.do_scrap()
        self.write({'evaluado_por_id': self.env.uid})        
        return True

    # cambia el estado a rechazado
    # registra el usuario que rechazó
    @api.multi
    def action_rechazar(self):        
        self.write({'state': 'rechazado'})  
        self.write({'evaluado_por_id': self.env.uid})      
        return True

class StockProductionLot(models.Model):
    _inherit = ['stock.production.lot']
    # para registrar la fecha de produccion
    fecha_produccion = fields.Date('Fecha de producción')
    # Cambio el nombre
    removal_date = fields.Datetime('Fecha de vencimiento')

class StockPickingType(models.Model):
    _inherit = ['stock.picking.type']
    _rec_name = 'warehouse_id'

    # form/tree view: permite indicar que movimientos requieren aprobación y cuales no
    requiere_aprobacion = fields.Boolean(string='Requiere aprobación', 
                                    help='si está marcada, se exigirá que se informe el usuario que autorizó el movimiento')
    # tree view: para mostrar el nombre del depósito
    warehouse = fields.Char(related='warehouse_id.name', string='Depósito')