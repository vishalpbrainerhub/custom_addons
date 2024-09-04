from odoo import http
from odoo.http import request, Response
import json
from .auth import user_auth



class MobileEcommerceApiController(http.Controller):


    @http.route('/api/products', auth='none', type='http', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def get_products(self):
        # Handle OPTIONS request for CORS preflight
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        try:

            user_info = user_auth(self)
            if user_info['status'] == 'error':
                return Response(
                    json.dumps({'status': 'error', 'message': user_info['message']}),
                    content_type='application/json',
                    status=401,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            user_id = user_info['user_id']
            users_dict = request.env['res.users'].sudo().search([('id', '=', user_id)])
            partner_id = users_dict.partner_id.id
            
            products_data = request.env['product.template'].search_read([], ['id', 'name', 'list_price', 'active', 'barcode', 'color', 'image_1920', 'discount','is_published','rewards_score','default_code','code_'])
            product_list = []

            order_lines = request.env['sale.order.line'].sudo().search([('order_partner_id', '=', partner_id)])
            product_ids = []
            for line in order_lines:
                product_ids.append(line.product_id.id)

            for product in products_data:
                # Handle the image (convert to URL if needed)
                image_url = '/web/image/product.template/' + str(product['id']) + '/image_1920' if product['image_1920'] else None
                product_data = {
                    'name': product['name'],
                    'list_price': product['list_price'],
                    'active': product['active'],
                    'barcode': product['barcode'],
                    'color': product['color'],
                    'image': image_url,
                    'id': product['id'],
                    'quantity': 0,
                    'discount': product["discount"],
                    'is_published': product["is_published"],
                    'rewards_score': product["rewards_score"],
                    'default_code': product["default_code"],
                    'code': product["code_"],
                    'discounted_price': product['list_price'] - (product['list_price'] * product["discount"] / 100) ,
                }
                if product['id'] in product_ids:
                    # update the quantity of the product in the cart
                    for line in order_lines:
                        if line.product_id.id == product['id']:
                            product_data['quantity'] = line.product_uom_qty
                            product_data['discounted_price'] = product_data['discounted_price'] * line.product_uom_qty
                            break
                product_list.append(product_data)
            

            response_data = {
                'status': 'success',
                'products': product_list,
                'total_products': len(product_list)
            }
            return Response(json.dumps(response_data), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})

        except Exception as e:
            print(e)
            return Response(json.dumps({
                'status': 'error',
                'message': str(e)
            }), content_type='application/json', status=500, headers={'Access-Control-Allow-Origin': '*'})



    @http.route('/api/products/<int:product_code>', auth='none', type='http', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_product(self, product_code):
        # Handle OPTIONS request for CORS preflight
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        try:
            user_info = user_auth(self)
            if user_info['status'] == 'error':
                return Response(
                    json.dumps({'status': 'error', 'message': user_info['message']}),
                    content_type='application/json',
                    status=401,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            user_id = user_info['user_id']
            users_dict = request.env['res.users'].sudo().search([('id', '=', user_id)])
            partner_id = users_dict.partner_id.id

            product_data = request.env['product.template'].search_read([('code_', '=', product_code)], ['id', 'name', 'list_price', 'active', 'barcode', 'color', 'image_1920', 'discount','is_published','rewards_score','default_code','code_'])
            product_list = []

            order_lines = request.env['sale.order.line'].sudo().search([('order_partner_id', '=', partner_id)])
            product_ids = []
            for line in order_lines:
                product_ids.append(line.product_id.id)

            for product in product_data:
                # Handle the image (convert to URL if needed)
                image_url = '/web/image/product.template/' + str(product['id']) + '/image_1920' if product['image_1920'] else None
                product_data = {
                    'name': product['name'],
                    'list_price': product['list_price'],
                    'active': product['active'],
                    'barcode': product['barcode'],
                    'color': product['color'],
                    'image': image_url,
                    'id': product['id'],
                    'quantity': 0,
                    'discount': product["discount"],
                    'is_published': product["is_published"],
                    'rewards_score': product["rewards_score"],
                    'default_code': product["default_code"],
                    'code': product["code_"],
                    'discounted_price': product['list_price'] - ( product['list_price'] * product["discount"] / 100),
                }
                if product['id'] in product_ids:
                    # update the quantity of the product in the cart
                    for line in order_lines:
                        if line.product_id.id == product['id']:
                            product_data['quantity'] = line.product_uom_qty
                            product_data['discounted_price'] = product_data['discounted_price'] * line.product_uom_qty
                            break
                product_list.append(product_data)

            response_data = {
                'status': 'success',
                'products': product_list,
                'total_products': len(product_list)
            }
            return Response(json.dumps(response_data), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        
        except Exception as e:

            return Response(json.dumps({
                'status': 'error',
                'message': str(e)
            }), content_type='application/json', status=500, headers={'Access-Control-Allow-Origin': '*'})
        

    # update product's quantity in the cart
    @http.route('/api/products/<int:product_id>', auth='none', type='json', methods=['PUT', 'OPTIONS'], csrf=False, cors='*')
    def update_product_quantity(self, product_id):
        # Handle OPTIONS request for CORS preflight
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'PUT, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        try:
            user_info = user_auth(self)
            if user_info['status'] == 'error':
                return {
                    'status': 'error',
                    'message': user_info['message']
                }
            user_id = user_info['user_id']
            users_dict = request.env['res.users'].sudo().search([('id', '=', user_id)])
            partner_id = users_dict.partner_id.id

            product = request.env['product.template'].sudo().search([('id', '=', product_id)])
            if not product:
                return {
                    'status': 'error',
                    'message': 'Product not found'
                }, 404

            quantity = request.jsonrequest.get('quantity', 1)
            if quantity < 0:
                return {
                    'status': 'error',
                    'message': 'Quantity must be a positive number'
                }, 400

            order_lines = request.env['sale.order.line'].sudo().search([('order_partner_id', '=', partner_id), ('product_id', '=', product_id)])
            if order_lines:
                order_lines.write({'product_uom_qty': quantity})
            else:
                request.env['sale.order.line'].sudo().create({
                    'order_partner_id': partner_id,
                    'product_id': product_id,
                    'product_uom_qty': quantity,
                    'price_unit': product.list_price,
                })

            return {
                'status': 'success',
                'message': 'Product quantity updated successfully'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500
        
