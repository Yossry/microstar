# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_model_id = fields.Many2one("product.model", string="Model", tracking=True, help="Select a model for this product")
    product_brand_id = fields.Many2one("product.brand", string="Brand", tracking=True, help="Select a brand for this product")
    product_origin_id = fields.Many2one("product.origin", string="Origin", tracking=True, help="Select a Origin for this product")
    product_usage_id = fields.Many2one("product.usage", string="Usage", tracking=True, help="Select a Usage for this product")
    product_size = fields.Char('Size', tracking=True)
    supplier_notes = fields.Html('Supplier Notes')
    other_notes = fields.Html('Other Notes')
    item_code = fields.Char('Item Code', tracking=True)
    min_qty = fields.Float('Minimum Qty', tracking=True)
    max_qty = fields.Float('Maximum Qty', tracking=True)
    product_description = fields.Html('Description')
