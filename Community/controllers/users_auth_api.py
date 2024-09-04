from odoo import http, tools
from odoo.http import request, Response
from .auth import SocialMediaAuth
import os
import json
import random
from odoo.exceptions import AccessDenied
from odoo import api, SUPERUSER_ID
import base64
import random


class UsersAuthApi(http.Controller):

    def _handle_options(self):
        headers = SocialMediaAuth.get_cors_headers()
        return request.make_response('', headers=headers)
    
    @http.route('/user/reset_password', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def reset_password(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        old_password = request.jsonrequest.get('old_password', False)
        new_password = request.jsonrequest.get('new_password', False)

        print(f"Old Password: {old_password}----------------------------------------")
        print(f"New Password: {new_password}----------------------------------------")

        if not old_password or not new_password:
            return {'status': 'error', 'message': 'Both old_password and new_password are required'}

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        try:
            # Fetch the user based on the authenticated user ID
            user = request.env['res.users'].sudo().browse(user_auth['user_id'])
            if not user:
                return {'status': 'error', 'message': 'User not found'}

            # Create the user_agent_env dictionary
            user_agent_env = {'interactive': True}

            # Verify the old password with user_agent_env using the extended _check_credentials
            try:
                user._check_credentials(old_password, user_agent_env=user_agent_env)
                user.sudo().write({'password': new_password})
                return {'status': 'success', 'message': 'Password is correct and reset successfully'}
            except AccessDenied as e:
                return {'status': 'error', 'message': str(e), 'status_code': 401}

        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': 500}
        


    # update the user's address
    @http.route('/user/add_address', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def add_address(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        

        address = request.jsonrequest.get('address', False)
        continued_address = request.jsonrequest.get('continued_address', False)
        city = request.jsonrequest.get('city', False)
        postal_code = request.jsonrequest.get('postal_code', False)
        village = request.jsonrequest.get('village', False)
        country_id = request.jsonrequest.get('country_id', False)
        state_id = request.jsonrequest.get('state_id', False)
        
        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        try:
            # Fetch the user based on the authenticated user ID
            user_id = user_auth['user_id']
            
            user_address = request.env['social_media.custom_address'].search([('user_id', '=', user_id)])
            print(f"User Address: {user_address}")
            if len(user_address) == 0:
                user_address = request.env['social_media.custom_address'].create({
                    'user_id': user_id,
                    'address': address,
                    'continued_address': continued_address,
                    'city': city,
                    'postal_code': postal_code,
                    'village': village,
                    'country_id': country_id,
                    'state_id': state_id,
                    'default': True
                })

                # get user
                user = request.env['res.users'].sudo().browse(user_id)
                if not user:
                    return {'status': 'error', 'message': 'User not found'}
                
                user.sudo().write({
                    'street': address,
                    'street2': continued_address + ' ' + village,
                    'city': city,
                    'zip': postal_code,
                    'country_id': country_id,
                    'state_id': state_id
                })

            
            else:
                # create a new address
                user_address = request.env['social_media.custom_address'].create({
                    'user_id': user_id,
                    'address': address,
                    'continued_address': continued_address,
                    'city': city,
                    'postal_code': postal_code,
                    'village': village,
                    'country_id': country_id,
                    'state_id': state_id,
                    'default': False
                })

            
            return {'status': 'success', 'message': 'Address added successfully'}

        except Exception as e:
            print(f"Error: {str(e)}")
            return {'status': 'error', 'message': str(e), 'status_code': 500}
        

    @http.route('/user/get_address', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False,cors='*')
    def get_address(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            user_id = user_auth['user_id']
            user_address = request.env['social_media.custom_address'].search([('user_id', '=', user_id)])
            if not user_address:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'No address found for this user'
                }), content_type='application/json', status=404)

            user_address_data = user_address.read(['address', 'continued_address', 'city', 'postal_code', 'village', 'default', 'state_id', 'country_id'])
            return Response(json.dumps({
                'result': {'status': 'success', 'address': user_address_data}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 500  # Internal Server Error
            }), content_type='application/json', status=500)
        

    @http.route('/user/change_default_address', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def change_default_address(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        user_id = user_auth['user_id']
        address_id = request.jsonrequest.get('address_id', False)
        if not address_id:
            return {'status': 'error', 'message': 'address_id is required'}

        try:
            user_address = request.env['social_media.custom_address'].search([('user_id', '=', user_id)])
            if not user_address:
                return {'status': 'error', 'message': 'No address found for this user'}

            # Update the default address
            for address in user_address:
                if address.id == address_id:
                    address.write({'default': True})
                else:
                    address.write({'default': False})

            # update the fields in the user model
            # get user
            user = request.env['res.users'].sudo().browse(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            user.sudo().write({
                'street': address.address,
                'street2': address.continued_address + ' ' + address.village,
                'city': address.city,
                'zip': address.postal_code,
                'country_id': address.country_id.id,
                'state_id': address.state_id.id
            })

            return {'status': 'success', 'message': 'Default address changed successfully',}

        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': 500}
    



    # update user profile like change the name, display_name
    @http.route('/user/update_details', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def update_details(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        user_id = user_auth['user_id']
        name = request.jsonrequest.get('name', False)
        last_name = request.jsonrequest.get('last_name', False)

        try:
            user = request.env['res.users'].sudo().browse(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}

            user.sudo().write({
                'name': name,
                'x_last_name': last_name,
            })

            return {'status': 'success', 'message': 'Profile updated successfully'}

        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': 500}
        

    @http.route('/user/profile_image', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def profile_image(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return request.make_response(json.dumps({'status': 'error', 'message': user_auth['message']}))

        user_id = user_auth['user_id']
        image_file = request.httprequest.files.get('image')

        if not image_file:
            return Response(json.dumps({
                'status': 'error',
                'message': 'Image file is required'
            }), content_type='application/json', status=400)
        
        try:
            # Read the image file and encode it to base64
            image_content = image_file.read()
            image_base64 = base64.b64encode(image_content).decode('utf-8')

            user = request.env['res.users'].sudo().browse(user_id)
            if not user:
                return request.make_response(json.dumps({'status': 'error', 'message': 'User not found'}))

            # Update the user's profile image
            user.sudo().write({
                'image_1920': image_base64
            })
            
            return Response(json.dumps({
                'status': 'success',
                'message': 'Profile image updated successfully'
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'status': 'error',
                'message': str(e)
            }), content_type='application/json', status=500)
        

    # read and delete the address all
    @http.route('/user/del', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def del25(self):
        
        data = request.env['social_media.custom_address'].search([])
        data.unlink()

        return Response(json.dumps({
            'status': 'success',
            'message': 'All addresses deleted successfully'
        }), content_type='application/json')




    @http.route('/user/details', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False, cors='*')
    def user_details(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if 'status' in user_auth and user_auth['status'] == 'error':
            return Response(json.dumps({
                'status': 'error',
                'message': user_auth['message']
            }), content_type='application/json', status=401)

        # Check if 'user_id' is present in the response
        if 'user_id' not in user_auth:
            return request.make_response(json.dumps({'status': 'error', 'message': 'Authentication failed'}))

        user_id = user_auth['user_id']
        user = request.env['res.users'].sudo().browse(user_id)
        if not user:
            return Response(json.dumps({
                'status': 'error',
                'message': 'User not found'
            }), content_type='application/json', status=404)
        
        user_data = user.read(['name', 'login', 'email', 'phone', 'company_id', 'blocked_users', 'x_last_name', 'image_1920'])[0]
        image = user_data.pop('image_1920', None)  # Remove image data from user_data

        # Store this image in community folder and return the path
        save_directory = 'images/profilepics'
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # in save directory create folder with user_id
        save_directory = os.path.join(save_directory, str(user_id))
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        else:
            # remove the previous image
            files = os.listdir(save_directory)
            for file in files:
                os.remove(os.path.join(save_directory, file))
        

        image_path = os.path.join(save_directory, f'profile{random.randint(1,5000)}_{user_id}.png')

        if image:  # Ensure there is image data
            with open(image_path, 'wb') as f:
                f.write(base64.b64decode(image))
            user_data['image_path'] = f'/{image_path}'
        else:
            # Handle cases where there is no image data, perhaps log this or set a default
            user_data['image_path'] = 'Path to default image or no image'

        return Response(json.dumps({
            'status': 'success',
            'user': user_data
        }), content_type='application/json')

    @http.route('/images/profilepics/<path:image>', type='http', auth='public', csrf=False,cors='*')
    def get_image(self, image):
        image_path = os.path.join('images/profilepics', image)
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return Response(image_data, content_type='image/png')
        else:
            return Response(json.dumps({
                'error': {'message': 'Image not found'},
                'status': 'error',
                'status_code': '404'  # Not Found
            }), content_type='application/json', status=404)
        

    # get country list with ids and names along with states
    @http.route('/countries_list', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False,cors='*')
    def countries(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        countries = request.env['res.country'].search_read([], ['id', 'name'])

        return Response(json.dumps({
            'status': 'success',
            'countries': countries
        }), content_type='application/json')
    

    @http.route('/states_list/<int:country_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False,cors='*')
    def states(self, country_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()
        
        states = request.env['res.country.state'].search_read([('country_id', '=', country_id)], ['id', 'name'])

        return Response(json.dumps({
            'status': 'success',
            'states': states
        }), content_type='application/json')