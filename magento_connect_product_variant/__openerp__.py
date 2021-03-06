# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Magento Connector Product Variant",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Generic Modules",
    "description": """
    Magento E-commerce management. This module will be able to create variant of product in Magento (Configurable products).
    """,
    "license" : "AGPL-3",
    "depends" : [
        "magento_connect",
        "product_variant_multi",
    ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "settings/magento_mapping.xml",
        "settings/magento_data.xml",
        "mgn_view.xml",
        "product_view.xml",
        "sale_view.xml",
        "wizard/wizard_product_template.xml",
    ],
    "active": False,
    "installable": True
}
