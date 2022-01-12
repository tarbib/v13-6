# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_program_free_product = fields.Boolean(readonly=True)
    is_refused_free_product = fields.Boolean(readonly=True)

    def _update_if_refused(self, free_product_values):
        self.ensure_one()
        new_values = free_product_values
        if self.is_refused_free_product:
            new_values["product_uom_qty"] = 0
        return new_values

    def unlink(self):
        for line in self:
            if line.is_program_free_product:
                related_program = self.env["sale.coupon.program"].search(
                    [
                        ("reward_free_product_id", "=", line.product_id.id),
                        ("program_type", "!=", "coupon_program"),
                    ]
                )
                if related_program in line.order_id.no_code_promo_program_ids:
                    line.order_id.no_code_promo_program_ids -= related_program
                elif related_program == line.order_id.code_promo_program_id:
                    line.order_id.code_promo_program_id -= related_program
                else:
                    coupon_to_reactivate = line.order_id.with_context(
                        active_test=False
                    ).applied_coupon_ids.filtered(
                        lambda coupon: coupon.program_id.reward_free_product_id
                        == line.product_id
                    )
                    if (
                        coupon_to_reactivate
                        in line.order_id.applied_coupon_ids
                    ):
                        coupon_to_reactivate.write({'state': 'new'})
                        line.order_id.applied_coupon_ids -= (
                            coupon_to_reactivate
                        )
        return super().unlink()
