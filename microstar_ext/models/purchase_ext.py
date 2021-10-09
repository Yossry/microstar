# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_image = fields.Binary(related='product_id.image_1920', store=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    salesman_id = fields.Many2one('hr.employee', 'Salesman')
