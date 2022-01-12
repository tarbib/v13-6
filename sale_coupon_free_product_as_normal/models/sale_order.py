# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _apply_filter_programs_not_automatic_free_product(self, programs):
        return programs.filtered(
            lambda p: p.reward_type != "free_product_as_normal"
        )

    def _get_applied_programs(self):
        programs = super()._get_applied_programs()
        # By default free product programs are not applied
        programs = self._apply_filter_programs_not_automatic_free_product(
            programs
        )
        return programs

    def _get_applicable_no_code_promo_program(self):
        programs = super()._get_applicable_no_code_promo_program()
        # By default free product programs are not applicable
        programs = self._apply_filter_programs_not_automatic_free_product(
            programs
        )
        return programs

    def _get_applied_programs_with_rewards_on_current_order(self):
        programs = (
            super()._get_applied_programs_with_rewards_on_current_order()
        )
        # By default free product programs are not applied
        programs = self._apply_filter_programs_not_automatic_free_product(
            programs
        )
        return programs

    def _create_reward_line(self, program):
        if program.reward_type == "free_product_as_normal" and (
            program.promo_code_usage == "code_needed"
            or program.program_type == "coupon_program"
        ):
            self._create_or_update_free_product_as_normal_line(program)
        else:
            return super()._create_reward_line(program)

    def remove_inapplicable_free_product_program(self, applicable_programs):
        # Remove free product lines with program not applicable anymore
        applied_programs = (
            self.no_code_promo_program_ids
            | self.code_promo_program_id
            | self.applied_coupon_ids.mapped("program_id")
        )
        for program in applied_programs:
            if (
                program.reward_type == "free_product_as_normal"
                and program not in applicable_programs
            ):
                sale_order_line = self.order_line.filtered(
                    lambda l: l.is_program_free_product
                    and l.product_id == program.reward_free_product_id
                )
                if sale_order_line:
                    sale_order_line.unlink()
                self.no_code_promo_program_ids -= program
                self.code_promo_program_id -= program
        # Remove free product lines without any program
        applied_programs = (
            self.no_code_promo_program_ids
            | self.code_promo_program_id
            | self.applied_coupon_ids.mapped("program_id")
        )
        for line in self.order_line:
            if line.is_program_free_product:
                program = applied_programs.filtered(
                    lambda p: p.reward_type == "free_product_as_normal"
                    and p.reward_free_product_id == line.product_id
                )
                if not program:
                    line.unlink()

    def _get_free_product_values(self, program):
        free_product = program.reward_free_product_id
        taxes = free_product.taxes_id
        if self.fiscal_position_id:
            taxes = self.fiscal_position_id.map_tax(taxes)
        return {
            "product_id": free_product.id,
            "price_unit": 0,
            "product_uom_qty": program.reward_free_product_quantity,
            "is_program_free_product": True,
            "name": _("Free Product") + " - " + free_product.name,
            "product_uom": free_product.uom_id.id,
            "tax_id": [(4, tax.id, False) for tax in taxes],
        }

    def _create_or_update_free_product_as_normal_line(self, program):
        free_product_values = self._get_free_product_values(program)
        sale_order_line = self.order_line.filtered(
            lambda l: l.is_program_free_product
            and l.product_id == program.reward_free_product_id
        )
        if sale_order_line:
            free_product_values = sale_order_line._update_if_refused(
                free_product_values
            )
            sale_order_line.write(free_product_values)
        else:
            self.write({"order_line": [(0, 0, free_product_values)]})

    def apply_automatic_free_product_program(self, applicable_programs):
        for program in applicable_programs:
            if (
                program.reward_type == "free_product_as_normal"
                and program.promo_code_usage == "no_code_needed"
            ):
                self._create_or_update_free_product_as_normal_line(program)
                self.write({"no_code_promo_program_ids": [(4, program.id)]})
        return True

    def update_free_product_program_with_code(
        self, applicable_programs, program
    ):
        if (
            program.reward_type == "free_product_as_normal"
            and (
                program.promo_code_usage == "code_needed"
                or program.program_type == "coupon_program"
            )
            and program in applicable_programs
        ):
            self._create_or_update_free_product_as_normal_line(program)
        return True

    def update_free_product_program_with_promo_code(self, applicable_programs):
        # From code needed program
        if self.code_promo_program_id:
            self.update_free_product_program_with_code(
                applicable_programs, self.code_promo_program_id
            )
        # From standard coupons
        for coupon in self.applied_coupon_ids:
            self.update_free_product_program_with_code(
                applicable_programs, coupon.program_id
            )
        return True

    def recompute_coupon_lines(self):
        for sale in self:
            # Call only one time _get_applicable_programs to win in performance
            applicable_programs = sale._get_applicable_programs()
            # Remove free product program which are now inapplicable
            sale.remove_inapplicable_free_product_program(applicable_programs)
            # Apply automatic free product program if needed
            sale.apply_automatic_free_product_program(applicable_programs)
            # Update free product program with promo code if needed
            sale.update_free_product_program_with_promo_code(
                applicable_programs
            )
            super(SaleOrder, sale).recompute_coupon_lines()
        return True
