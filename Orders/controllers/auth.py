from odoo import http
from odoo.http import request
import jwt
import os


def user_auth(self):
        token = request.httprequest.headers.get('Authorization', False)
        if not token:
            return {
                "status": "error",
                "message": "Token is required."
            }
        token = token.split(' ')[1]
        secret_key = "secret_key"
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user = request.env['res.users'].sudo().search([('id', '=', payload['user_id'])])
            if user:
                return {
                    "status": "success",
                    "user_id": user.id,
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid token."
                }
        except jwt.ExpiredSignatureError:
            return {
                "status": "error",
                "message": "Token is expired."
            }
        except jwt.InvalidTokenError:
            return {
                "status": "error",
                "message": "Invalid token."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }