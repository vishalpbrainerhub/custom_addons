from odoo import http
from odoo.http import request, Response
import json
from datetime import datetime
from .auth import user_auth

class Ecommerce_orders(http.Controller):

    @http.route('/api/orders/<int:order_id>', auth='public', type='http', methods=['GET'])
    def get_orders_test(self, order_id):
        try:
            if not order_id:
                return Response(
                    json.dumps({'status': 'error', 'message': 'No order ID provided'}),
                    content_type='application/json',
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            orders = request.env['sale.order'].sudo().search([
                ('id', '=', order_id)
            ])


            if not orders:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Order not found'}),
                    content_type='application/json',
                    status=404,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            order_reward_points = request.env['rewards.points'].sudo().search([('order_id', '=', order_id)]).points
            response_data = []

            
            for order in orders:
                # Convert the datetime to a string

                user_address = request.env['social_media.custom_address'].sudo().search([
                    ('id', '=', order.shipping_address_id)
                ])

                shipping_address =  f'{user_address.address}, {user_address.continued_address}, {user_address.city}, {user_address.postal_code}, {user_address.village}, {user_address.state_id.name}, {user_address.country_id.name}' if user_address else None

                order_data = {
                    'id': order.id,
                    'name': order.name,
                    'state': order.state,
                    'taxable_amount': order.amount_total,
                    'date_order': order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else None,
                    'partner_id': order.partner_id.id,
                    'partner_name': order.partner_id.name,
                    'partner_email': order.partner_id.email,
                    'partner_phone': order.partner_id.phone,
                    'partner_address': shipping_address,
                    'vat_1_percentage': 22,
                    'vat_2_percentage': 10,
                    'shipping_charge': 450,
                    "vat_1_value": order.amount_total * 0.22,
                    "vat_2_value": order.amount_total * 0.1,
                    "total_amount": order.amount_total + 450 + (order.amount_total * 0.22) + (order.amount_total * 0.1),
                    "reward_points": order_reward_points,
                    "all_products": []
                }

                
                for line in order.order_line:
                    image_url = '/web/image/product.product/' + str(line.product_id.id) + '/image_1920' if line.product_id.image_1920 else None
                    discount_percentage = request.env['product.template'].sudo().search([('id', '=', line.product_id.id)]).discount

                    product_data = {
                        'id': line.product_id.id,
                        'name': line.product_id.name,
                        'list_price': line.price_unit * line.product_uom_qty,
                        'active': line.product_id.active,
                        'barcode': line.product_id.barcode,
                        'color': line.product_id.color,
                        'image': image_url,
                        'quantity': line.product_uom_qty,
                        'base_price': line.product_id.list_price,
                        'discount': discount_percentage,
                        'order_id': line.order_id.id,
                        'code': line.product_id.code_,
                    }

                    order_data['all_products'].append(product_data)

            
                response_data.append(order_data)
            
            return Response(
                json.dumps(response_data),
                content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )


    @http.route('/api/orders', auth='user', type='http', methods=['GET'], csrf=False, cors='*')
    def get_orders(self):
        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(
                    json.dumps({'status': 'error', 'message': user['message']}),
                    content_type='application/json',
                    status=401,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            user_id = user['user_id']

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
            # Search for the orders who are in sent, sale or done state
            orders = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sent', 'sale', 'done'])
            ])

            response_data = []
            for order in orders:
                # Convert the datetime to a string
                user_address = request.env['social_media.custom_address'].sudo().search([
                    ('id', '=', order.shipping_address_id)
                ])

                shipping_address =  f'{user_address.address}, {user_address.continued_address}, {user_address.city}, {user_address.postal_code}, {user_address.village}, {user_address.state_id.name}, {user_address.country_id.name}' if user_address else None

                order_data = {
                    'id': order.id,
                    'name': order.name,
                    'state': order.state,
                    'taxable_amount': order.amount_total,
                    'date_order': order.date_order.strftime('%Y-%m-%d %H:%M:%S') if order.date_order else None,
                    'partner_id': order.partner_id.id,
                    'partner_name': order.partner_id.name,
                    'partner_email': order.partner_id.email,
                    'partner_phone': order.partner_id.phone,
                    'partner_address': shipping_address,
                    'vat_1_percentage': 10,
                    'vat_2_percentage': 20,
                    'shipping_charge': 450,
                    "vat_1_value": order.amount_total * 0.1,
                    "vat_2_value": order.amount_total * 0.2,
                    "total_amount": order.amount_total + 450 + (order.amount_total * 0.1) + (order.amount_total * 0.2)
                }

            
                response_data.append(order_data)

            final_response = {
                'status': 'success',
                'orders': response_data
            }
            
            return Response(
                json.dumps(final_response),
                content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )


    @http.route('/api/confirm_order', auth='user', type='json', methods=['POST'])
    def confirm_order(self, **post):
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
                return {
                    'status': 'error',  
                    'message': user['message']
                }
            
            user_id = user['user_id']
            order_id = request.jsonrequest.get('order_id')

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
            
            # Search for the order
            order = request.env['sale.order'].sudo().search([
                    ('id', '=', order_id),
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'draft')
                ], limit=1)

            if not order:
                return {
                    'status': 'error',
                    'message': 'Order not found or already confirmed'
                }, 404
            
            order_line = request.env['sale.order.line'].sudo().search([
                ('order_id', '=', order.id)
            ])

            if not order_line:
                return {
                    'status': 'error',
                    'message': 'Order has no products'
                }, 400

            # Confirm the order
            order.action_confirm()

            user_address = request.env['social_media.custom_address'].sudo().search([
                    ('id', '=', order.shipping_address_id)
                ])
            

            shipping_address =  f'{user_address.address}, {user_address.continued_address}, {user_address.city}, {user_address.postal_code}, {user_address.village}, {user_address.state_id.name}, {user_address.country_id.name}' if user_address else None
            
            

            # Return success message with order details
            return {
                'status': 'success',
                'message': 'Order confirmed successfully and cart cleared',
                'order_id': order.id,
                'order_state': order.state,
                'order_amount_total': order.amount_total,
                'order_date_order': order.date_order,
                'partner_address': shipping_address

            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500
        

    
    @http.route('/api/reorder', auth='user', type='json', methods=['POST'])
    def reorder(self):
        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return {
                    'status': 'error',
                    'message': user['message']
                }
            
            user_id = user['user_id']
            order_id = request.jsonrequest.get('order_id')

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            print(partner)
            if not partner:
                return {
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }
            
            # Search for the order
            order = request.env['sale.order'].sudo().search([
                    ('id', '=', order_id),
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['sent', 'sale', 'done'])
                ], limit=1)

            if not order:
                return {
                    'status': 'error',
                    'message': 'Order not found or cannot be reordered'
                }, 404
            
            
            new_order = order.copy()
            new_order.action_confirm()

            # check if the order has reward points
            order_reward_points = request.env['rewards.points'].sudo().search([('order_id', '=', order_id)]).points
            if order_reward_points:
                request.env['rewards.points'].sudo().create({
                    'points': order_reward_points,
                    'user_id': user_id,
                    'order_id': new_order.id,
                    'status': 'gain'
                })

                # Update the total points
                total_points_obj = request.env['rewards.totalpoints'].sudo().search([('user_id', '=', user_id)])
                if total_points_obj:
                    total_points = total_points_obj.total_points + order_reward_points
                    total_points_obj.write({'total_points': total_points})

            user_address = request.env['social_media.custom_address'].sudo().search([
                    ('id', '=', new_order.shipping_address_id)
                ])
            
            shipping_address =  f'{user_address.address}, {user_address.continued_address}, {user_address.city}, {user_address.postal_code}, {user_address.village}, {user_address.state_id.name}, {user_address.country_id.name}' if user_address else None

            return {
                'status': 'success',
                'message': 'Order reordered successfully',
                'order_id': new_order.id,
                'order_state': new_order.state,
                'order_amount_total': new_order.amount_total,
                'order_date_order': new_order.date_order,
                'order_reward_points': order_reward_points,
                'partner_address': shipping_address
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500
        

    
    @http.route('/api/cancel_order', auth='user', type='json', methods=['POST'], csrf=False)
    def cancel_order(self, **post):
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
                return {
                    'status': 'error',
                    'message': user['message']
                }
            
            user_id = user['user_id']
            order_id = request.jsonrequest.get('order_id')

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
            
            order = request.env['sale.order'].sudo().search([
                    ('id', '=', order_id),
                    ('partner_id', '=', partner.id),
                    ('state', '!=', 'draft')
                ], limit=1)

            if not order:
                return {
                    'status': 'error',
                    'message': 'Order not found or already confirmed'
                }, 404
            
            order_line = request.env['sale.order.line'].search([
                ('order_id', '=', order.id)
            ])

            if not order_line:
                return {
                    'status': 'error',
                    'message': 'Order has no products'
                }, 400

            # Cancel the order
            order.action_cancel()

            # Return success message with order details
            return {
                'status': 'success',
                'message': 'Order cancelled successfully',
                'order_id': order.id,
                'order_state': order.state,
                'order_amount_total': order.amount_total,
                'order_date_order': order.date_order,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500
        
    
    # delete order
    @http.route('/api/delete_order/<int:order_id>', auth='user', type='http', methods=['DELETE'], csrf=False)
    def delete_order(self, order_id):
        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(
                    json.dumps({'status': 'error', 'message': user['message']}),
                    content_type='application/json',
                    status=401,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            user_id = user['user_id']

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
            
            order = request.env['sale.order'].sudo().search([
                    ('id', '=', order_id),
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['draft', 'cancel'])
                ], limit=1)

            if not order:
                return Response(
                    json.dumps({'status': 'error', 'message': 'Order not found or cannot be deleted'}),
                    content_type='application/json',
                    status=404,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            order.unlink()

            return Response(
                json.dumps({'status': 'success', 'message': 'Order deleted successfully'}),
                content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )
        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
    
    # create Invoice and send email
    @http.route('/api/create_invoice', auth='user', type='json', methods=['POST'])
    def create_invoice(self, **post):
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
                return {
                    'status': 'error',
                    'message': user['message']
                }
            
            user_id = user['user_id']
            order_id = request.jsonrequest.get('order_id')

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
            
            order = request.env['sale.order'].sudo().search([
                    ('id', '=', order_id),
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'sale')
                ], limit=1)

            if not order:
                return {
                    'status': 'error',
                    'message': 'Order not found or not confirmed'
                }, 404
            
            invoice = order._create_invoices()

            # Send the invoice email
            mail_values = {
                'subject': 'Invoice for Order %s' % order.name,
                'email_to': partner.email,
                'body_html': 'Please find attached the invoice for your order.',
                'email_from': request.env.user.email or 'admin@gmail.com'
            }

            mail = request.env['mail.mail'].create(mail_values)
            mail.send()

            return {
                'status': 'success',
                'message': 'Invoice created and sent successfully',
                'invoice_id': invoice.id,
                'invoice_state': invoice.state,
                'invoice_amount_total': invoice.amount_total,
                'invoice_date_invoice': invoice.date_invoice,
            }
        
        except Exception as e:

            return {
                'status': 'error',
                'message': str(e)
            }, 500
        

    # get all orders loop over it and cancel all orders and then delete them all

    @http.route('/api/cancel_all_orders', auth='user', type='http', methods=['GET'])
    def cancel_all_orders(self):
        try:
            user = user_auth(self)
            if user['status'] == 'error':
                return Response(
                    json.dumps({'status': 'error', 'message': user['message']}),
                    content_type='application/json',
                    status=401,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            user_id = user['user_id']

            # Retrieve the partner associated with the user
            partner = request.env['res.users'].browse(user_id).partner_id
            if not partner:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No partner found for the user.'
                }), content_type='application/json', status=400, headers={'Access-Control-Allow-Origin': '*'})
        
            
            orders = request.env['sale.order'].sudo().search([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ['sent', 'sale', 'done'])
                ])

            for order in orders:
                order.action_cancel()
                order.unlink()

            return Response(
                json.dumps({'status': 'success', 'message': 'All orders cancelled and deleted successfully'}),
                content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )
        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        



        