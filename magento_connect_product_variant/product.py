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

from osv import osv, fields
from tools.translate import _

from magento import *

import netsvc
import unicodedata
import re

LOGGER = netsvc.Logger()

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class product_template(osv.osv):
    _inherit = "product.template"

    def onchange_name(self, cr, uid, ids, name, slug):
        value = {}
        if not slug:
            slug = slugify(unicode(name,'UTF-8'))
            value = {'magento_tpl_url_key': slug}
        return {'value':value}

    _columns = {
        'magento_tpl_sku':fields.char('Magento SKU', size=64),
        'magento_tpl_exportable':fields.boolean('Exported to Magento?', change_default=True, help='If check this value, this product is publishing in Magento Store. For disable this product in your Magento Store, change visibility option to Nowhere.'),
        'magento_tpl_sale_shop': fields.many2many('sale.shop', 'magento_configurable_sale_shop_rel', 'product_template_id', 'sale_shop_id', 'Websites', help='Select yours Sale Shops available this product (configurable product)'),
        'magento_tpl_status':fields.boolean('Status'),
        'magento_tpl_visibility': fields.selection([('0','Select Option'),('1','Nowhere'),('2','Catalog'),('3','Search'),('4','Catalog,Search')], 'Visibility'),
        'magento_tpl_url_key': fields.char('Url Key', size=256, translate=True),
        'magento_tpl_shortdescription': fields.text('Short Description', translate=True),
        'magento_tpl_metadescription': fields.text('Description', translate=True),
        'magento_tpl_metakeyword': fields.text('Keyword', translate=True),
        'magento_tpl_metatitle': fields.char('Title', size=256, translate=True),
        'magento_tpl_attribute_group_id': fields.many2one('product.attributes.group', 'Attribute'),
    }

    _defaults = {
        'magento_tpl_status':lambda * a:True,
        'magento_tpl_visibility': '4',
    }

    def product_product_variants_vals(self, cr, uid, product_temp, variant, context):
        """Return Dicc to Product Product Values
        :product_temp Object
        :return vals"""
        
        vals = super(product_template, self).product_product_variants_vals(cr, uid, product_temp, variant, context)

        if  product_temp.magento_tpl_exportable:
            variant = self.pool.get('product.variant.dimension.value').browse(cr, uid, variant[0])
            code = variant.option_id.code and variant.option_id.code or variant.option_id.name
            
            vals['magento_exportable'] = True
            vals['magento_product_type'] = 'simple'
            vals['magento_sku'] =  "%s-%s" % (product_temp.magento_tpl_sku, code)
            vals['magento_shortdescription'] = product_temp.magento_tpl_shortdescription
            vals['magento_metadescription'] = product_temp.magento_tpl_metadescription
            vals['magento_metakeyword'] = product_temp.magento_tpl_metakeyword
            vals['magento_metatitle'] = product_temp.magento_tpl_metatitle
            vals['attribute_group_id'] = product_temp.magento_tpl_attribute_group_id.id
            vals['magento_sale_shop'] = [(6,0, [x.id for x in product_temp.magento_tpl_sale_shop])]

        vals['magento_url_key'] = product_temp.magento_tpl_url_key
        vals['magento_status'] = True
        vals['magento_visibility'] = '1' #Nowhere

        return vals

product_template()

class product_product(osv.osv):
    _inherit = "product.product"

    def magento_create_product_configurable(self, cr, uid, magento_app, product, store_view, context = None):
        """Create Product Variant (configurable) from Magento Values
        :magento_app object
        :product dicc
        :store_view ID
        :return product_product_oerp_id
        """
        product_template_oerp_id = None
        product_template_id = self.pool.get('magento.external.referential').check_mgn2oerp(cr, uid, magento_app, 'product.template', product['product_id'])
        if not product_template_id:
            values = self.magento_product_values(cr, uid, magento_app, product, context)
            values['is_multi_variants'] = True
            product_template_name = values['name']
            product_template_magento_id = product['product_id']
            product_template_oerp_id = self.pool.get('product.template').create(cr, uid, values, context)
            self.pool.get('magento.external.referential').create_external_referential(cr, uid, magento_app, 'product.template', product_template_oerp_id, product_template_magento_id)
            LOGGER.notifyChannel('Magento Sync API', netsvc.LOG_INFO, "Create Product Template: magento app %s, openerp id %s, magento product id %s." % (magento_app.name, product_template_oerp_id, product['product_id']))

            #~ Update product.template dicc
            with ProductConfigurable(magento_app.uri, magento_app.username, magento_app.password) as productconfigurable_api:
                product_info = productconfigurable_api.info(product['product_id'])
                product_attributes = productconfigurable_api.getSuperAttributes(product['product_id'])

            #create product simples
            context = {
                'generate_from_template' : True,
                'product_tmpl_id' : product_template_oerp_id,
            }
            with Product(magento_app.uri, magento_app.username, magento_app.password) as product_api:
                product_template_info = product_api.info(product_template_magento_id)
                for prod in product_info:
                    product = product_api.info(prod['stock_item']['product_id'])
                    self.magento_create_product(cr, uid, magento_app, product, store_view, context)

            product_template_obj = self.pool.get('product.template').browse(cr, uid, product_template_oerp_id, context)

            # Base External Mapping
            context['magento_app'] = magento_app
            context['product_info'] = product_template_info
            vals = self.pool.get('base.external.mapping').get_external_to_oerp(cr, uid, 'magento.product.configurable', product_template_obj.id, product_template_info, context)

            # Vals add
            vals['magento_exportable'] = True

            dimesion_types = []
            if product_attributes:
                for product_attribute in product_attributes:
                    # Dimension type
                    type_name = product_attribute['attribute_code']
                    magento_id = product_attribute['attribute_id']
                    dimesion_type = self.pool.get('product.variant.dimension.type').magento_dimension_type(cr, uid, magento_app, type_name, magento_id)
                    dimesion_types.append(dimesion_type)
                    
                    # Dimension Option
                    dimension_options = []
                    for prod_values in product_attribute['values']:
                        dimension_options.append({'value': prod_values['product_super_attribute_id'], 'label': prod_values['label']})
                    if len(dimension_options)>0:
                        dimension_option = self.pool.get('product.variant.dimension.option').magento_dimension_option(cr, uid, magento_app, dimesion_type, dimension_options)

            if len(dimesion_types)>0:
                vals['dimension_type_ids'] = [(6,0,dimesion_types)]

            self.pool.get('product.template').write(cr, uid, [product_template_oerp_id], vals)
            LOGGER.notifyChannel('Magento Sync API', netsvc.LOG_INFO, "Write Product Template: magento %s, openerp id %s, magento product id %s." % (magento_app.name, product_template_oerp_id, product['product_id']))

            # Add all options dimension value
            if len(dimesion_types)>0:
                self.pool.get('product.template').add_all_option(cr, uid, [product_template_oerp_id], context)

            cr.commit()
        else:
            LOGGER.notifyChannel('Magento Sync API', netsvc.LOG_INFO, "Skip! Product Template exists: magento %s, magento product id %s. Not create" % (magento_app.name, product['product_id']))

        return product_template_oerp_id

product_product()
