# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
import dateutil.parser
import logging
_logger = logging.getLogger(__name__)
import datetime

class StockPicking(models.Model):
    _inherit = ['stock.picking']
    # _order = 'min_date desc'
    _order = 'id desc'
    
    # form view: Que la fecha sea obligatoria
    # form/tree view: cambio de Datetime a Date
    # si dejo min_date como required='True', no puedo agregar Ordenes de venta
    # min_date = fields.Date('Fecha',required='True' )
    
    # tree view: para mostrar el nombre del depósito en la 
    # search view: para poder filtrar por nombre de depósito
    warehouse = fields.Char(related='picking_type_id.warehouse', string='Depósito')
    # tree view: para mostrar la descripción del Tipo de Movimiento en la tree view   
    picking_type = fields.Char(related='picking_type_id.name', string='Tipo movimiento')
    # form view: para filtrar Proveedores/Clientes según el movimiento sea de entrada o de salida 
    code = fields.Selection(related='picking_type_id.code', string='Tipo Operación')
    # poder informar el usuario que autoriza. Esto casi seguro que cambia
    # aprobado_por_id = fields.Many2one('res.users', 'Aprobado por:')
    # obtener el atributo del modelo stock.picking.
    requiere_aprobacion = fields.Boolean(related='picking_type_id.requiere_aprobacion', string='Requiere aprobación')
    # form view: solo lectura y default 'todo de una vez'
    move_type = fields.Selection(default='one',readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),        
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('esperando', 'Esperando Aprobación'),
        ('rechazado', 'Rechazado'),
        ('assigned', 'Available'),
        ('done', 'Done')])

    # para registrar quien fue el usuario que aprobó/rechazó
    evaluado_por_id = fields.Many2one('res.users','Evaluado por:', readonly=True) 

    @api.multi
    def action_confirm(self):
        # import pdb; pdb.set_trace()
        if self.state == 'draft' and self.requiere_aprobacion:            
            self.write({'state': 'esperando'})
            return True
        else:
            super(StockPicking, self).action_confirm()

    # hace el movimiento de stock
    # registra el usuario que aprobó  
    @api.multi
    def action_aprobar(self):        
        self.action_confirm()
        self.write({'evaluado_por_id': self.env.uid})
        # import pdb; pdb.set_trace()        
        _logger.debug("Pasa por: action_aprobar")      
        return True

    # cambia el estado a rechazado
    # registra el usuario que rechazó
    @api.multi
    def action_rechazar(self):        
        self.write({'state': 'rechazado'})  
        self.write({'evaluado_por_id': self.env.uid})      
        return True

    # form view: carga la lista de partners con clientes o proveedores según el tipo de movimiento de stock
    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):        
        if self.code == 'incoming':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('customer', '=', True)]}}

    warehouse_id = fields.Integer(
        string='Depósito del movimiento',
        compute='_compute_warehouse_id',
        search='_search_warehouse_id',
        # inverse='_write_warehouse_id',
        store=False,  # the default
    )

    @api.depends('picking_type_id.warehouse_id')
    def _compute_warehouse_id(self):
        for picking in self:
            # todo.stage_fold = todo.stage_id.fold
            picking.warehouse_id = picking.picking_type_id.warehouse_id.id

    def _search_warehouse_id(self, operator, value):
        user = self.env['res.users'].browse(self.env.uid)
        # import pdb; pdb.set_trace() 
        return [('picking_type_id.warehouse_id.id', operator, user.warehouse_id_usuario.id)]

class StockQuant(models.Model):
    _inherit = ['stock.quant']

    #tree view: para mostrar la fecha de venc.
    removal_date = fields.Datetime(related='lot_id.removal_date', string='Fecha de venc. lote')

    grupo_usuario = fields.Char('Grupo del usuario', compute='_compute_grupo_usuario')

    @api.multi
    def _compute_grupo_usuario(self):
        # import pdb; pdb.set_trace()
        # _logger.debug("Pasa por acá")
        for quant in self:
            if self.env.user.has_group('base.sin_implementar'):
                quant.grupo_usuario = 'implementador'
            elif self.env.user.has_group('stock.group_stock_manager'):
                quant.grupo_usuario = 'administrador'
            else:
                quant.grupo_usuario = 'usuario'

class StockScrap(models.Model):
    _name = 'stock.scrap'
    _inherit = ['stock.scrap', 'mail.thread']
    # este lo usa para la funcion de trackeo de cambios de estado de mail
    _description = "Rotura"

    # agrego estados "esperando" y "rechazado"
    state = fields.Selection([
        ('draft', 'Draft'),
        ('esperando', 'Esperando Aprobación'),
        ('rechazado', 'Rechazado'),
        ('done', 'Done')], string='Status', default="draft", track_visibility=True)
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
        # import pdb; pdb.set_trace()        
        _logger.debug("Pasa por: action_aprobar")      
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
    fecha_produccion = fields.Date('Fecha de Producción')

class StockPickingType(models.Model):
    _inherit = ['stock.picking.type']
    _rec_name = 'warehouse_id'

    # form/tree view: permite indicar que movimientos requieren aprobación y cuales no
    requiere_aprobacion = fields.Boolean(string='Requiere aprobación', 
                                    help='si está marcada, se exigirá que se informe el usuario que autorizó el movimiento')
    # tree view: para mostrar el nombre del depósito
    warehouse = fields.Char(related='warehouse_id.name', string='Depósito')

    warehouse_id_id = fields.Integer(
        string='Depósito del tipo de movimiento',
        compute='_compute_warehouse_id_id',
        search='_search_warehouse_id_id',
        # inverse='_write_warehouse_id',
        store=False,  # the default
    )

    @api.depends('warehouse_id_id')
    def _compute_warehouse_id_id(self):
        for pickingType in self:
            pickingType.warehouse_id_id = pickingType.warehouse_id.id

    def _search_warehouse_id_id(self, operator, value):
        user = self.env['res.users'].browse(self.env.uid)
        # import pdb; pdb.set_trace() 
        return [('warehouse_id.id', operator, user.warehouse_id_usuario.id)]

    
class ResUsers(models.Model):
    _inherit = ['res.users']

    warehouse_id_usuario = fields.Many2one('stock.warehouse',string='Depósito del usuario')

class StockReportProductView(models.Model):
        _name = 'stock.report.product.view'
        _description = 'stock.report.product.view'
        _auto = False

        product_id = fields.Many2one('product.product',string='Variante de Producto')
        default_code = fields.Char('Referencia Interna',related='product_id.default_code')
        location_id = fields.Many2one('stock.location',string='Ubicación')
        qty = fields.Float('Cantidad')

        @api.model_cr
        def init(self):
                tools.drop_view_if_exists(self._cr,'stock_report_product_view')
                self._cr.execute(""" create view stock_report_product_view as (
                        select max(a.id) as id,a.product_id,a.location_id,
                        sum(a.qty) as qty from stock_quant a inner join stock_location b 
                        on b.id = a.location_id where a.reservation_id is null and b.usage = 'internal' group by 2,3
                        ) """)

class SaleOrder(models.Model):
    _inherit = ['sale.order']

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Realizado'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    numero_pedido = fields.Char('Número de pedido', required=False)