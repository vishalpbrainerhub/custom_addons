from odoo import http
from odoo.http import request, Response
import json
from .auth import user_auth


class EcommerceCartLine(http.Controller):

    @http.route('/api/cart_line', auth='user', type='http', methods=['GET'], csrf=False, cors='*')
    def get_cart_line(self):

        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)
        
        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(json.dumps({
                    'status': 'error',
                    'message': user['message']
                }), content_type='application/json', status=401, headers={'Access-Control-Allow-Origin': '*'})

            user_id = user['user_id']
            partners_id = request.env['res.users'].sudo().search([('id', '=', user_id)]).partner_id.id

            cart_line = request.env['sale.order.line'].search_read([
                ('order_id.partner_id', '=', partners_id),
                ('order_id.state', '=', 'draft')  # Filter by draft state
            ], ['product_id', 'price_unit', 'product_uom_qty', 'order_id', 'state'])

            cart_data = []

            for cart in cart_line:
                cart_dict = {}

                if cart['product_uom_qty'] == 0:
                    remover_cartline = request.env['sale.order.line'].search([('id', '=', cart['id'])])
                    remover_cartline.unlink()
                    continue

                product_id = cart['product_id'][0]
                product_info = request.env['product.product'].search_read([('id', '=', product_id)], limit=1)
                # image_url = '/web/image/product.template/' + str(cart['product_id'][0]) + '/image_1920' if cart["image"] else None
                image_url = '/web/image/product.product/' + str(cart['product_id'][0]) + '/image_1920' if product_info[0]['image_1920'] else None

                cart_dict['id'] = cart['id']
                cart_dict['name'] = product_info[0]['name']
                cart_dict['list_price'] = cart['price_unit'] * cart['product_uom_qty']
                cart_dict['active'] = product_info[0]['active']
                cart_dict['barcode'] = product_info[0]['barcode']
                cart_dict['color'] = product_info[0]['color']
                cart_dict['image'] = image_url
                cart_dict['quantity'] = cart['product_uom_qty']
                cart_dict['base_price'] = product_info[0]['list_price']
                cart_dict['discount'] = product_info[0].get('discount', 0.0)
                cart_dict['order_id'] = cart['order_id'][0]
                cart_dict['code'] = product_info[0]['code_']
                
                cart_data.append(cart_dict)

            response_data = {
                'status': 'success',
                'cart': cart_data
            }
            return Response(json.dumps(response_data), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        
        except Exception as e:
            return Response(json.dumps({
                'status': 'error',
                'message': str(e)
            }), content_type='application/json', status=500, headers={'Access-Control-Allow-Origin': '*'})


    

    @http.route('/api/cart_line', auth='user', type='json', methods=['POST'], csrf=False, cors='*')
    def create_cart_line(self):
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(json.dumps({
                    'status': 'error',
                    'message': user['message']
                }), content_type='application/json', status=401, headers={'Access-Control-Allow-Origin': '*'})

            user_id = user['user_id']

            product_id = request.jsonrequest.get('product_id')
            product_uom_qty = request.jsonrequest.get('quantity', False)
            price_unit = request.jsonrequest.get('product_price')
            

            # Check if the product ID is for a product template or a product variant
            product = request.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                # Try checking if it's a product template ID and get the first variant
                template = request.env['product.template'].sudo().browse(product_id)
                if template.exists():
                    # Get the first variant of the template
                    product = template.product_variant_ids[0]
                    if not product:
                        return {
                            'status': 'error',
                            'message': 'The specified product variant does not exist or has been deleted.'
                        }, 400
                else:
                    return {
                        'status': 'error',
                        'message': 'The specified product does not exist or has been deleted.'
                    }, 400

            # Debugging: Print the product details
            # minus the discount price from the product price with quantity
            price_unit = price_unit - (price_unit * product.discount / 100)

            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})

            shipping_address = request.env['social_media.custom_address'].search([('user_id', '=', user_id),("default", "=", True)], limit=1)
            

            sale_order = request.env['sale.order'].search([('partner_id', '=', partner.id), ('state', '=', 'draft')], limit=1)
            if not sale_order:
                sale_order = request.env['sale.order'].create({
                    'partner_id': partner.id,
                    'user_id': user_id,
                    'shipping_address_id': shipping_address.id
                })

            cart_line_check = request.env['sale.order.line'].search([('product_id', '=', product.id), ('order_id', '=', sale_order.id)], limit=1)
            if cart_line_check:
                return {
                    'status': 'error',
                    'message': 'Product already in cart.'
                }

            cart_line = request.env['sale.order.line'].create({
                'product_id': product.id,
                'price_unit': price_unit,
                'product_uom_qty': product_uom_qty,
                'order_id': sale_order.id
            })

            return {
                'cart_line': cart_line.id,
                'status': 'success'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


    #update cart line quantity
    @http.route('/api/cart_line/<int:id>', auth='user', type='json', methods=['PUT'], csrf=False, cors='*')
    def update_cart_line(self, id):
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        # Accessing JSON data correctly
        try:
            product_uom_qty = request.jsonrequest.get('quantity', False)

            # if product_uom_qty == 0:
            #     # 
            
            if not product_uom_qty:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'Quantity is required.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
            
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(json.dumps({
                    'status': 'error',
                    'message': user['message']
                }), content_type='application/json', status=401, headers={'Access-Control-Allow-Origin': '*'})
            
            user_id = user['user_id']

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})

            # Check if there's an existing sale order for this user
            sale_order = request.env['sale.order'].search([('partner_id', '=', partner.id)], limit=1)
            if not sale_order:
                # Create a new sale order if it doesn't exist
                sale_order = request.env['sale.order'].create({
                    'partner_id': partner.id,
                    'user_id': user_id,
                    # Additional necessary fields for sale.order creation
                })

            # Attempt to retrieve the order line safely
            cart_line = request.env['sale.order.line'].browse(id)
            if not cart_line.exists():
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'Cart line does not exist.'
                }), content_type='application/json', status=404, headers={'Access-Control-Allow-Origin': '*'})

            cart_line.write({
                'product_uom_qty': product_uom_qty
            })

            return {'cart_line': cart_line.id, "status": "success"}
        
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

        

    @http.route('/api/cart_line/<int:id>', auth='user', type='http', methods=['DELETE'],csrf=False, cors='*')
    def delete_cart_line(self, id):

        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)
        
        user = user_auth(self)
        if user['status'] == 'error':
            return Response(json.dumps({
                'status': 'error',
                'message': user['message']
            }), content_type='application/json', status=401, headers={'Access-Control-Allow-Origin': '*'})
        
        user_id = user['user_id']

        # Retrieve the partner associated with the user
        partner = request.env['res.users'].browse(user_id).partner_id
        if not partner:
            return Response(json.dumps({
                'status': 'error',
                'message': 'No partner found for the user.'
            }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
        # Check if there's an existing sale order for this user
        sale_order = request.env['sale.order'].search([('partner_id', '=', partner.id)], limit=1)
        if not sale_order:
            # Create a new sale order if it doesn't exist
            sale_order = request.env['sale.order'].create({
                'partner_id': partner.id,
                'user_id': user_id,
                # Additional necessary fields for sale.order creation
            })

        # Creating the order line
        cart_line = request.env['sale.order.line'].browse(id)
        cart_line.unlink()
        
        return Response(json.dumps({
            'status': 'success',
            'message': 'Cart line deleted successfully.'
        }), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    

    