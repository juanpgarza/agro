# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
import dateutil.parser
import logging
_logger = logging.getLogger(__name__)
import datetime
import dateutil.parser

from odoo.fields import Date as fDate
from datetime import timedelta as td

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

    # Funciona OK, no hace falta
    # @api.model
    # def create(self, vals):
    #     vals['min_date'] = vals['min_date'] + ' 10:00:00'
    #     import pdb; pdb.set_trace()  
    #     return super(StockPicking, self).create(vals)

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

    #
    tracking = fields.Selection(related='product_id.tracking', string='tracking')

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

    barcode = fields.Char(related='product_id.barcode', string='Código barras')
    
    jpg_ids = fields.One2many('stock.report.trace.view', inverse_name='lot_id')

    # dias_vencimiento = fields.Float()

    dias_vencimiento = fields.Integer( string='Días al vencimiento', 
            compute='_compute_age', inverse='_inverse_age', search='_search_age', store=False, compute_sudo=False,)

    @api.depends('removal_date') 
    def _compute_age(self):
        today = fDate.from_string(fDate.today())
        
        for lote in self.filtered('removal_date'):
            fecha_vencimiento = dateutil.parser.parse(lote.removal_date).date()
            # import pdb; pdb.set_trace()
            delta = (fecha_vencimiento - today)
            lote.dias_vencimiento = delta.days

    def _inverse_age(self): 
        today = fDate.from_string(fDate.today())
        for lote in self.filtered('removal_date'): 
            d = td(days=lote.dias_vencimiento) - today 
            book.removal_date = fDate.to_string(d)

    def _search_age(self, operator, value): 
        today = fDate.from_string(fDate.today()) 
        value_days = td(days=value)
        value_date = fDate.to_string(today + value_days) 
        # import pdb; pdb.set_trace()
        return [('removal_date', operator, value_date)]

    @api.model
    def create(self, vals):
        vals['removal_date'] = vals['removal_date'] + ' 10:00:00'
        # import pdb; pdb.set_trace()        
        return super(StockProductionLot, self).create(vals)

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

class StockMove(models.Model):
    _inherit = ['stock.move']
    _order = 'id desc'

    picking_partner = fields.Char('Cliente',related='picking_id.partner_id.name')



class StockReportProductView(models.Model):
        _name = 'stock.report.product.view'
        _description = 'stock.report.product.view'
        _auto = False

        product_id = fields.Many2one('product.product',string='Producto')
        default_code = fields.Char('Referencia Interna',related='product_id.default_code')
        location_id = fields.Many2one('stock.location',string='Ubicación')
        lot_id = fields.Many2one('stock.production.lot',string='Lote')
        qty = fields.Float('Cantidad')
        warehouse_id = fields.Many2one('stock.warehouse',string='Depósito')
        removal_date = fields.Datetime('Fecha venc. lote')

        @api.model_cr
        def init(self):
                tools.drop_view_if_exists(self._cr,'stock_report_product_view')
                self._cr.execute(""" create view stock_report_product_view as (
                            select sw.id as warehouse_id,sq.product_id,sq.location_id, 
                            sq.lot_id,  spl.removal_date, sum(sq.qty) as qty, max(sq.id) as id
                            from stock_warehouse sw
                            /* sw.lot_stock_id: ubicacion elegida para el stock */
                            inner join stock_quant sq on sw.lot_stock_id = sq.location_id
                            inner join stock_production_lot spl on sq.lot_id = spl.id
                            group by 1,2,3,4,5
                        ) """)

class StockReportTraceView(models.Model):
    _name = 'stock.report.trace.view'
    _descripcion = 'stock.report.trace.view'
    _auto = False

    id = fields.Integer('Movimiento')
    product_id = fields.Many2one('product.product',string='Producto')
    qty = fields.Float('Cantidad')
    location_id = fields.Many2one('stock.location',string='Ubicación',Translate=True)
    ubicacion = fields.Char('Cliente')
    lot_id = fields.Many2one('stock.production.lot',string='Lote')
    removal_date = fields.Datetime('Fecha venc. lote')

    @api.model_cr
    def init(self):
            tools.drop_view_if_exists(self._cr,'stock_report_trace_view')
            self._cr.execute(""" create view stock_report_trace_view as (
                                select max(sq.id) as id,
                                --sp.date_done,
                                --pt.name,
                                spl.product_id,
                                sum(sq.qty) as qty,
                                sq.location_id,
                                rp."name" as ubicacion,
                                --spl."name",
                                sq.lot_id,
                                spl.removal_date
                                from stock_move sm
                                inner join stock_quant_move_rel sqm on sm.id = sqm.move_id
                                inner join stock_picking sp on sm.picking_id = sp.id
                                inner join stock_quant sq on sqm.quant_id = sq.id
                                inner join stock_production_lot spl on sq.lot_id = spl.id
                                inner join product_template pt on pt.id = spl.product_id
                                inner join res_partner rp on sm.partner_id = rp.id
                                --where sq.lot_id = 1
                                --sm.id = 5 and 
                                group by 2,4,5,6,7
                                --order by 1
                                union all
                                select max(sq.id),
                                --null,
                                --pt.name as producto,
                                spl.product_id,
                                sum(sq.qty),
                                sq.location_id,
                                '', 
                                --spl."name",
                                sq.lot_id,
                                spl.removal_date
                                from stock_quant sq
                                inner join stock_production_lot spl on sq.lot_id = spl.id
                                inner join product_template pt on pt.id = spl.product_id
                                inner join stock_location sl on sq.location_id = sl.id
                                left join stock_location slp on slp.id = sl.location_id
                                --inner join stock_quant_move_rel sqmr on sqmr.quant_id = sq.id
                                where sl.usage IN ('internal','inventory')
                                --and sq.lot_id = 1
                                group by 2,4,5,6,7
                                order by 5
                                ) """)


class TodoWizard(models.TransientModel):
    _name = 'report.wizard'
    _description = 'Reporte de stock'

    location_id = fields.Many2one('stock.location', string='Ubicaciones') 

    @api.multi
    def do_imprimir(self):
        wizard_id = self.env['report.wizard2'].create({'descripcion': self.location_id.name})
        stock_ids = self.env['stock.report.product.view'].search([('location_id','=',self.location_id.id)])
        # import pdb;pdb.set_trace()
        for stock in stock_ids:            
            vals = {'product_id': stock.product_id.id,'wizard_id': wizard_id.id}
            self.env['report.wizard.line'].create(vals)

        return self.env['report'].get_action(wizard_id, 'agro.report_agro_product_template')

"""        for stock in stock_ids:

             vals = { 'nombre del campo': 'nombre del valor a insertar'} """
             
         

class TodoWizard2(models.TransientModel):
    _name = 'report.wizard2'
    _description = 'Reporte de stock 2'

    descripcion = fields.Char('Descripcion')
    lineas_id = fields.One2many('report.wizard.line', 'wizard_id')
    
class TodoWizardLine(models.TransientModel):
    _name = 'report.wizard.line'
    _description = 'Lineas'

    prueba = fields.Char('Prueba')
    product_id = fields.Many2one('product.product')
    wizard_id = fields.Many2one('report.wizard2')

class AlertaWizard(models.TransientModel):
    _name = 'alerta.wizard'
    _description = 'Reporte de stock'

    # dias = fields.Integer(string='Días') 
    # fecha = fields.Date('Fecha')
    dias_vencimiento = fields.Integer('Días al vencimiento')

    @api.multi
    def do_imprimir(self):         
        wizard_id = self.env['alerta.wizard.encabezado'].create({'descripcion': self.dias_vencimiento})
        #import pdb;pdb.set_trace()
        stock_ids = self.env['stock.production.lot'].search([('dias_vencimiento','<=',self.dias_vencimiento)])
        # import pdb;pdb.set_trace()
        for stock in stock_ids:            
            vals = {'product_id': stock.product_id.id,'wizard_id': wizard_id.id, 'lot_id': stock.id}
            self.env['alerta.wizard.detalle'].create(vals)

        return self.env['report'].get_action(wizard_id, 'agro.report_agro_alerta')

class AlertaWizardEncabezado(models.TransientModel):
    _name = 'alerta.wizard.encabezado'
    _description = 'encabezado'

    descripcion = fields.Char('Descripcion')
    lineas_id = fields.One2many('alerta.wizard.detalle', 'wizard_id')
    
class AlertaWizardDetalle(models.TransientModel):
    _name = 'alerta.wizard.detalle'
    _description = 'detalle'

    prueba = fields.Char('Prueba')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.production.lot')
    wizard_id = fields.Many2one('alerta.wizard.encabezado')

class EnviaMailWizard(models.TransientModel):
    _name = 'enviamail.wizard'
    _description = 'Envio de mails'

    user_target = fields.Many2one('res.users', string='User Target')
    mail_target = fields.Char(string='Email Target')

    @api.multi
    def send_mail(self):
        user_id = self.user_target.id
        body = self.mail_target

        mail_details = {'subject': "Message subject",
            'body': body,
            'partner_ids': [(user_target)]
            } 

        mail = self.env['mail.thread']
        mail.message_post(type="notification", subtype="mt_comment", **mail_details)

class SaleOrder(models.Model):
    _inherit = ['sale.order']
    # _sql_constraints = [ ('agro_numero_pedido_unico',
    #                 "unique (numero_pedido, state != 'cancel')",
    #                  'El número de pedido debe ser único!')]

    _sql_constraints = [ ('agro_numero_pedido_unico',
                    "unique (numero_pedido, active)",
                     'El número de pedido debe ser único!')]

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Realizado'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    numero_pedido = fields.Char('Número de pedido', required=True)

    active = fields.Boolean('Active', default=True)

    @api.multi
    def action_cancel(self):
        self.active = False
        return super(SaleOrder, self).action_cancel()

    # @api.constrains('numero_pedido')
    # def _check_numero_pedido(self): 
    #     for order in self:            
    #         if order.numero_pedido == self.numero_pedido and order.id != self.id:
    #             # raise UserError(_('Nothing to check the availability for.'))
    #             raise UserError('Número pedido duplicado!')
    #         import pdb; pdb.set_trace()