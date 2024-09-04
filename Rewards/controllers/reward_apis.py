from odoo import http
from odoo.http import request, Response
import json
from .auth import user_auth


class RewardAPIs(http.Controller):

    @http.route('/api/rewards', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def get_rewards(self):
        # Check if user is authenticated
        user = user_auth(self)
        if user['status'] == 'error':
            return Response(
                json.dumps({'status': 'error', 'message': user['message']}),
                content_type='application/json',
                status=401,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        user_id = user['user_id']
        
        rewards = request.env['rewards.points'].sudo().search([('user_id', '=', user_id)])
        total_points = request.env['rewards.totalpoints'].sudo().search([('user_id', '=', user_id)])
        rewards_data = []
        for reward in rewards:
            
            rewards_data.append({
                'id': reward.id,
                'user_id': reward.user_id.id,
                'order_id': reward.order_id.id,
                'points': reward.points,
                'date': reward.date.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
                'status': reward.status,
                'catalog_id': reward.catalog_id.id,
            })
            
            # if status is redeem, add catalog title and if status is gain, add order total amount
            if reward.status == 'redeem':
                rewards_data[-1]['catalog_title'] = reward.catalog_id.title
            elif reward.status == 'gain':
                rewards_data[-1]['order_total'] = reward.order_id.amount_total

        # make rewards_data in descending order
        rewards_data = sorted(rewards_data, key=lambda x: x['date'], reverse=True)

        response_dict = {
            'status': 'success',
            'data': rewards_data,
            'total_points': total_points.total_points,
        }
        return Response(
            json.dumps(response_dict),
            content_type='application/json',
            status=200,
            headers={'Access-Control-Allow-Origin': '*'}
        )
    

    @http.route('/api/rewards', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def create_reward(self, **post):
        # Check if user is authenticated
        user = user_auth(self)
        if user['status'] == 'error':
            return {'status': 'error', 'message': user['message']}
        
        try:
            user_id = user['user_id']
            order_id = request.jsonrequest.get('order_id')

            
            # Check if order_id is provided
            if not order_id:
                return {'status': 'error', 'message': 'Order ID is required'}
            
            # Check if order exists
            order = request.env['sale.order'].sudo().search([('id', '=', order_id)])
            if not order:
                return {'status': 'error', 'message': 'Order not found'}
            
            points = 0

            for line in order.order_line:
                print(line.product_id.rewards_score)
                points += line.product_id.rewards_score * line.product_uom_qty
            
            if points == 0:
                return {'status': 'error', 'message': 'No points to gain'}
            
            total_points_obj = request.env['rewards.totalpoints'].sudo().search([('user_id', '=', user_id)])

            if total_points_obj:
                total_points = total_points_obj.total_points + points
                total_points_obj.write({'total_points': total_points})

            else:
                total_points = points
                request.env['rewards.totalpoints'].sudo().create({
                    'total_points': total_points,
                    'user_id': user_id
                })

            create_reward = request.env['rewards.points'].sudo().create({
                'user_id': user_id,
                'order_id': order_id,
                'points': points,
                'status': 'gain'
            })

            return {'status': 'success', 'message': 'Reward created successfully', 'data': create_reward.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        

    @http.route('/api/claim_catalog', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def claim_catalog(self):
        # Check if user is authenticated
        user = user_auth(self)
        if user['status'] == 'error':
            return {'status': 'error', 'message': user['message']}
        
        try:
            user_id = user['user_id']
            catalog_id = request.jsonrequest.get('catalog_id')
            
            # Check if catalog_id is provided
            if not catalog_id:
                return {'status': 'error', 'message': 'Catalog ID is required'}
            
            # Check if catalog exists
            catalog = request.env['rewards.catalog'].sudo().search([('id', '=', catalog_id)])
            if not catalog:
                return {'status': 'error', 'message': 'Catalog not found'}
            
            total_points_obj = request.env['rewards.totalpoints'].sudo().search([('user_id', '=', user_id)])
            total_points = total_points_obj.total_points


            if total_points < catalog.points:
                return {'status': 'error', 'message': 'Not enough points to claim this catalog'}
            
            total_points_obj.write({'total_points': total_points - catalog.points})

            create_reward = request.env['rewards.points'].sudo().create({
                'user_id': user_id,
                'catalog_id': catalog_id,
                'points': catalog.points,
                'status': 'redeem'
            })

            return {'status': 'success', 'message': 'Catalog claimed successfully', 'data': create_reward.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
