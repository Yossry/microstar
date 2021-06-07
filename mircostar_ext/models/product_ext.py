# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_brand_id = fields.Many2one("product.brand", string="Brand", help="Select a brand for this product")
