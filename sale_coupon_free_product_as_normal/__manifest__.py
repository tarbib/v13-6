# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale coupon automatic free product as normal",
    "description": "Camptocamp features for automatic free product program",
    "version": "13.0.1.0.0",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "category": "Others",
    "depends": [
        # odoo
        "sale_coupon",
    ],
    "website": "http://www.camptocamp.com",
    "data": [
        # Views
        "views/sale_coupon_program.xml",
    ],
    "installable": True,
}
