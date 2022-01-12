# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    reward_free_product_id = fields.Many2one(
        comodel_name="product.product", string="Free Product"
    )
    reward_free_product_quantity = fields.Integer(
        default=1,
        readonly=True,
        string="Quantity",
        help="Reward product quantity",
    )
    reward_free_product_uom_id = fields.Many2one(
        related="reward_free_product_id.product_tmpl_id.uom_id",
        string="Unit of Measure",
    )

    @api.onchange('reward_type')
    def _onchange_reward_type(self):
        if self.reward_type != "free_product_as_normal":
            self.reward_free_product_id = False
