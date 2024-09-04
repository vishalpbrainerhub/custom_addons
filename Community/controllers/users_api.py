from odoo import http, tools
from odoo.http import request, Response
from .auth import SocialMediaAuth
import jwt
import datetime
import json
from dotenv import load_dotenv
import os
import random
from .helper import send_registration_credentials, generate_password, forgot_password
import requests
from odoo.exceptions import AccessDenied



class Users(http.Controller):



    # login user
    @http.route('/user/login', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def login(self):
        email = request.jsonrequest.get('email', False)
        password = request.jsonrequest.get('password', False)

        try:
            if not email or not password:
                return {
                    "status": "error",
                    "message": "email and password are required."
                }

            user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
            login = user.login
            db = request.env.cr.dbname

            # Authenticate the user to create a new session
            uid = request.session.authenticate(db, login, password)
        
            if uid:
                # A new session ID has been generated
                new_session_id = request.session.sid
                payload = {
                    'user_id': user.id,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                }
                secret_key = "secret_key"  # You should have a more secure way of handling the secret key
                token = jwt.encode(payload, secret_key, algorithm='HS256')

                user_data = user.read(['name', 'login', 'email', 'phone', 'company_id'])[0]

                return {
                    "status": "success",
                    "user": user_data,
                    "token": token,
                    "session_id": new_session_id
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid login credentials."
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "info": "Invalid login credentials."
            }
        
        

    # create user
    @http.route('/user/create', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def create(self):
        name = request.jsonrequest.get('name', False)
        login = request.jsonrequest.get('login', False)
        email = request.jsonrequest.get('email', False)
        phone = request.jsonrequest.get('phone', False)
        company_id = request.jsonrequest.get('company_id', False)
        password = request.jsonrequest.get('password', False)
        
        if not email and not password and not login: 
            return {
                "status": "error",
                "message": "Some fields are required."
            }
        
        # Check if user already exists
        existing_user = request.env['res.users'].sudo().search([('email', '=', email)])
        if existing_user:
            return {
                "status": "error",
                "message": "User already exists."
            }

        # Create the user with basic information
        user = request.env['res.users'].sudo().create({
            'name': name,
            'login': login,
            'password': password,
            'email': email,
            'phone': phone,
            'company_id': company_id,
        })

        # Assign the user to the 'Internal User' group
        internal_user_group = request.env.ref('base.group_user')
        user.sudo().write({
            'groups_id': [(4, internal_user_group.id)]  # Adds the user to the Internal User group
        })

        return {
            "status": "success",
            "message": "User created successfully",
            "info": "Email sent to user with login credentials."
        }
    

    # delete user
    @http.route('/user/delete', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def delete(self):
        user_id = request.jsonrequest.get('user_id', False)
        if not user_id:
            obj = {
                "status": "error",
                "message": "user_id is required."
            }
            return obj
        user = request.env['res.users'].sudo().search([('id', '=', user_id)])
        if user:
            user.unlink()
            obj = {
                "status": "success",
                "message": "User deleted successfully."
            }
        else:
            obj = {
                "status": "error",
                "message": "User not found."
            }
        return obj


    # forgot password
    @http.route('/user/forgot_password', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def forgot_password(self):
        email = request.jsonrequest.get('email', False)
        if not email:
            obj = {
                "status": "error",
                "message": "Email is required."
            }
            return obj
        user = request.env['res.users'].sudo().search([('email', '=', email)])
        if not user:
            obj = {
                "status": "error",
                "message": "User not found."
            }
            return obj
        
        
        password = generate_password(email)
        done = user.sudo().write({
            'password': password
        })
        print(done)

        # send email
        data = forgot_password(email, password, email)
        if data == False:
            obj = {
                "status": "error",
                "message": "Email sending failed."
            }
            return obj

        obj = {
            "status": "success",
            "message": "Password reset successfully.",
            "info": "Email sent to user with new login credentials."
        }
        return obj



    # logout user
    @http.route('/user/logout', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False)
    def logout(self):

        data = request.session.logout(keep_db=True)
        print(data)


        return {
            "status": "success",
            "message": "Logged out successfully."
        }
    

    # get all the banner form the Banners folder and return the image path of all the banners
    @http.route('/api/banners', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def banners(self):
        # read the images/banners directory
        banners = []
        for root, dirs, files in os.walk("images/banners"):
            for file in files:
                if file.endswith(".jpg") or file.endswith(".png"):
                    banners.append(os.path.join(root, file))
        
        data =  {
            "status": "success",
            "banners": banners
        }

        return request.make_response(json.dumps(data), [('Content-Type', 'application/json')])
    
    
    @http.route('/images/banners/<path:image>', type='http', auth='public', csrf=False)
    def get_image(self, image):
        image_path = os.path.join('images/banners', image)
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
        

    # get all users
    @http.route('/api/test_user', auth='user', methods=['GET', 'OPTIONS'], csrf=False)
    def users(self):
        users = request.env['res.users'].sudo().search([])
        data = {
            "status": "success",
            "users": users.read(['name', 'login', 'email', 'phone', 'company_id'])
        }
        return Response(json.dumps(data), content_type='application/json')