# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_model_id = fields.Many2one("product.model", string="Model", help="Select a model for this product")
    product_brand_id = fields.Many2one("product.brand", string="Brand", help="Select a brand for this product")
    product_origin_id = fields.Many2one("product.origin", string="Origin", help="Select a Origin for this product")
    product_usage_id = fields.Many2one("product.usage", string="Usage", help="Select a Usage for this product")
    product_size = fields.Char('Size')