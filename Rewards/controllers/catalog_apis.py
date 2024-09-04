from odoo import http
from odoo.http import request, Response
import json
from .auth import user_auth



class CatalogApis(http.Controller):

    @http.route('/api/catalog', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def get_catalog(self):
        # Check if user is authenticated
        user = user_auth(self)
        if user['status'] == 'error':
            return Response(
                json.dumps({'status': 'error', 'message': user['message']}),
                content_type='application/json',
                status=401,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        try:
            catalogs = request.env['rewards.catalog'].sudo().search([])
            catalog_data = []
            for catalog in catalogs:
                image_url = '/web/image/rewards.catalog/' + str(catalog.id) + '/image' if catalog.image else None
                catalog_data.append({
                    'id': catalog.id,
                    'title': catalog.title,
                    'description': catalog.description,
                    'points': catalog.points,
                    'image': image_url
                })

            response_dict = {
                'status': 'success',
                'data': catalog_data
            }
            return Response(
                json.dumps(response_dict),
                content_type='application/json',
                status=200,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        except Exception as e:
            return Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json',
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )