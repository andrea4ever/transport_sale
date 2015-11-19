# -*- coding: utf-8 -*-
# © 2004-2010 Alien Group (<http://www.alien-group.com>).
# © 2015 Apulia Software 
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _


class SaleOrderFleetVehicle(models.Model):

    _name = 'sale.order.fleet_vehicle'

    _description = 'All sales order and associated vehicles'

    sale_order_id = fields.Many2one('sale.order', ondelete='cascade')
    sales_date = fields.Date()
    partner_departure_id = fields.Many2one('res.partner', string='From')
    partner_destination_id = fields.Many2one('res.partner', string='To')
    delivery_date = fields.Date(help='The date that will start to transport')
    return_date = fields.Date(
        help='The expected date to finish all the transport')
    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', required=True, ondelete='restrict')
    license_plate = fields.Char(size=64)
    internal_number = fields.Integer()
    employee_driver_id = fields.Many2one(
        'hr.employee', required=True, ondelete='restrict')
    employee_helper_id = fields.Many2one('hr.employee', ondelete='restrict')
    fleet_trailer_id = fields.Many2one(
        'fleet.vehicle', ondelete='restrict', required=True)
    trailer_license_plate = fields.Char(size=64)
    cargo_ids = fields.One2many(
        'sale.order.cargo', 'sale_order_fleet_id',
        help='All sale order transported cargo')

    def fleet_trailer_id_change(self, cr, uid, ids,fleet_trailer_id):
        result={}
        
        if not fleet_trailer_id:
            return {'value':result}
        
        trailer = self.pool.get('fleet.vehicle').browse(cr,uid,fleet_trailer_id)
        
        if trailer:
            result['trailer_license_plate'] = trailer.license_plate
            
        return {'value':result}
    
    def fleet_vehicle_id_change(self, cr, uid, ids,fleet_vehicle_id,context):
        result={}
        
        if not fleet_vehicle_id:
            return {'value':result}
                            
        vehicle = self.pool.get('fleet.vehicle').browse(cr,uid,fleet_vehicle_id)                           
        sale_order = self.pool.get('sale.order').browse(cr,uid,context.get('sale_order_id')) 
                           
        if vehicle:
            result['license_plate'] =  vehicle.license_plate
            result['employee_driver_id'] = vehicle.emp_driver_id.id            
            result['internal_number']=vehicle.internal_number
        
        print sale_order
        
        if sale_order:
            #print "sale_date=" + sale_order.date_order
            result['sales_date'] =  sale_order.date_order
            #print "sale departure id=" + sale_order.partner_departure_id.id
            result['partner_departure_id'] =  sale_order.partner_departure_id.id
            #print "sale shipping id=" + sale_order.partner_shipping_id.id
            result['partner_destination_id'] =  sale_order.partner_shipping_id.id
            #print "deli date=" + sale_order.delivery_date 
            result['delivery_date'] =  sale_order.delivery_date
            #print "deli date=" + sale_order.return_dae
            result['return_date'] =  sale_order.return_date    

        return {'value':result}
    
    def copy(self, cr, uid, _id, default=None, context=None):
        
        if not default:
            default = {}
#         default.update({            
#             'state': 'draft',            
#         })
        return super(sale_order_fleet_vehicle, self).copy(cr, uid, _id, default, context=context)
        
        
#     _sql_constraints = [('vehicle_uniq', 'unique(fleet_vehicle_id,sale_order_id)',
#                          'Vehicle must be unique per sale order! Remove the duplicate vehicle'),
#                         ('employee_unique','unique(employee_driver_id,sale_order_id)',
#                          'A driver must be unique per sale order! Remove the duplicate driver'),]  
         
class SaleOrderCargo(models.Model):

    _name = 'sale.order.cargo'

    _description = 'Transport cargo from a sale order transport service'

    sale_order_fleet_id = fields.Many2one(
        'sale.order.fleet_vehicle',  ondelete='cascade', required=True)
    transport_date = fields.Date(
        required=True, help='The day when the product was transported.')
    cargo_product_id = fields.Many2one(
        'product.product',
        help='Associated port document of '
             'the transported product if applicable.')
    cargo_docport = fields.Char(
        help='Associated port document of '
             'the transported product if applicable.')
    brand = fields.Char(help='Brand of the transported product if applicable.')
    model = fields.Char(help='Model of the transported product if applicable.')
    cargo_ident = fields.Char(
        help='Identification of the cargo.Ex:Id,License Plate,Chassi')
    sale_order_id = fields.Many2one('sale.order', required=True)
    transport_from_id = fields.Many2one('res.partner', string='From')
    transport_to_id = fields.Many2one('res.partner', string='To')

    def cargo_id_change(self,cr,uid,ids,cargo_product_id,context):
        
        result={}      
        if not cargo_product_id:
            return {'value':result}
                        
        sale_order = self.pool.get('sale.order').browse(cr,uid,context.get('sale_order_id')) 
        
        if sale_order:
            result['sale_order_id'] = context.get('sale_order_id')
            
#             if [ product sale_order_fleet_idfor product in sale_order.order_line if cargo_product_id == product.product_id]:            
    
        return {'value':result}
    
    def copy(self, cr, uid, _id, default=None, context=None): 
        
        if not default:
            default = {}
#         default.update({
#         })
        
        res_id = super(sale_order_cargo, self).copy(cr, uid, _id, default, context)
        return res_id 


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    fleet_vehicles_ids = fields.One2many(
        'sale.order.fleet_vehicle', 'sale_order_id', required=True)
    partner_departure_id = fields.Many2one('res.partner', required=True)
    delivery_date = fields.Date('Transport Start', required=True,
                                help='Expected Transport start date.')
    return_date = fields.Date('Transport Finish', required=True,
                              help='Expected Transport finish date.')
    cargo_ids = fields.One2many('sale.order.cargo', 'sale_order_id',
                                string='Cargo Manifest',
                                help='All transported cargo manifest.')

    def _validate_data(self, cr, uid, ids):
        for dates in self.browse(cr,uid,ids):
            if dates.return_date < dates.delivery_date:
                return False            
            else:
                return True
    #TODO : check condition and return boolean accordingly
    
    def _validate_cargo_products(self,cr,uid,ids):
        
        result = True
        cargo_products_ids = []
        
        sale_order = self.browse(cr,uid,ids[0])
        
        if sale_order:            
            cargo_products_ids = [cargo.cargo_product_id.id for cargo in sale_order.cargo_ids]
            
            if not cargo_products_ids:
                result = True
            else:                
                line_products_ids = [line.product_id.id for line in sale_order.order_line]
                result = set(cargo_products_ids) == set(line_products_ids)
                            
        return result
    
    def _validate_cargo_products_qty(self,cr,uid,ids):
        
        result = True
        msg_format=""
        line_product_ids = []
        line_product_qts = []
        
        sale_order = self.browse(cr,uid,ids[0])
        
        if sale_order:            
            cargo_product_ids = [cargo.cargo_product_id.id for cargo in sale_order.cargo_ids]
            
            #give all products for order line
            line_product_ids = [line.product_id.id for line in sale_order.order_line]
            line_product_qts = [line.product_uom_qty for line in sale_order.order_line]
            
            line_product_ids_qts = {}
            line_product_dif_ids = {}
            
            for idx,prod_id in enumerate(line_product_ids):                
                if prod_id in line_product_ids_qts.keys():
                    line_product_ids_qts[prod_id]+= line_product_qts[idx]
                else:
                    line_product_ids_qts[prod_id] = line_product_qts[idx]                            
                        
            if not cargo_product_ids:
                result = True
            else:
                for cargo_product_id in set(cargo_product_ids):                                    
                    line_product_ids_dict = { prod_id:qtd  for prod_id,qtd in line_product_ids_qts.iteritems() 
                                         if prod_id == cargo_product_id 
                                         and int(line_product_ids_qts[prod_id]) != cargo_product_ids.count(cargo_product_id)}  
                    
                    line_product_dif_ids.update(line_product_ids_dict)
                                                   
                if len(line_product_dif_ids) > 0:
                    
                    line_product_names = self.pool.get('product.product').name_get(cr,uid,line_product_dif_ids.keys(),context=None)
                    cargo_product_qts = [ cargo_product_ids.count(cargo_product_id) for cargo_product_id in line_product_dif_ids.keys()]
                    for product_name in line_product_names:
                        index= line_product_names.index(product_name)
                        
                        msg_format =  _("""Product:%s\n\tOrder=%s vs Cargo=%s\n""") % (product_name[1],
                                                                                       int(line_product_dif_ids[product_name[0]]),
                                                                                       cargo_product_qts[index])
                                                             
                    message = _("""The following products quantities in cargo don't match\n quantities in sales order line:\n%s
                                    """) % (msg_format)
                        
                    raise osv.except_osv(_('Error'), message)
                    result = False
                else:
                    result = True
        return result
    
    _constraints = [(_validate_data,'Error: Invalid return date', ['delivery_date','return_date']),
                    (_validate_cargo_products,"Error: There is a cargo product that doesn't belongs to the sale order line!",['cargo_ids','order_line']),
                    (_validate_cargo_products_qty,"Error: In products quantities",['cargo_ids','order_line'])]


class FleetVehicle(models.Model):

    _inherit = 'fleet.vehicle'

    sales_order_ids = fields.One2many(
        'sale.order.fleet_vehicle', 'fleet_vehicle_id', string='Vehicle Sales')
    internal_number = fields.Integer()
    is_trailer = fields.Boolean()


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    sales_order_ids = fields.One2many(
        'sale.order.fleet_vehicle', 'employee_driver_id',
        string='Driver Sales')
    is_driver = fields.Boolean()
