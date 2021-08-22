# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from itertools import groupby

class StockMove(models.Model):
	_inherit = "stock.move"

	image_128 = fields.Binary(string="Image")

	@api.onchange('product_id')
	def onchange_product_image(self):
		for product in self:
			product.image_128 = product.product_id.image_128

	def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
		self.ensure_one()
		# apply putaway
		location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
		vals = {
			'move_id': self.id,
			'product_id': self.product_id.id,
			'product_uom_id': self.product_uom.id,
			'location_id': self.location_id.id,
			'location_dest_id': location_dest_id,
			'picking_id': self.picking_id.id,
		}
		if quantity:
			uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
			uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
			rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
				vals = dict(vals, product_uom_qty=uom_quantity)
			else:
				vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
		if reserved_quant:
			vals = dict(
				vals,
				location_id=reserved_quant.location_id.id,
				lot_id=reserved_quant.lot_id.id or False,
				package_id=reserved_quant.package_id.id or False,
				owner_id =reserved_quant.owner_id.id or False,
			)
		for move in self:
			self.write({
						'image_128' : move.product_id.image_128,
					})
		return vals

	def _assign_picking(self):
		Picking = self.env['stock.picking']
		grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])
		for group, moves in grouped_moves:
			moves = self.env['stock.move'].concat(*list(moves))
			new_picking = False
			picking = moves[0]._search_picking_for_assignation()
			if picking:
				if any(picking.partner_id.id != m.partner_id.id or
						picking.origin != m.origin for m in moves):
					picking.write({
						'partner_id': False,
						'origin': False,
					})
			else:
				new_picking = True
				picking = Picking.create(moves._get_new_picking_values())
			for product in self:
				product.image_128 = product.product_id.image_128
				
			for move in picking.move_lines:
				move.image_128 =  self.product_id.image_128 
		
			moves.write({'picking_id': picking.id})
			moves._assign_picking_post_process(new=new_picking)
		return True

