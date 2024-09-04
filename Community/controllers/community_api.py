from odoo import http
from odoo.http import request, Response
from .auth import SocialMediaAuth
import os
import json
import random
from odoo.exceptions import AccessDenied



class SocialMedia(http.Controller):

    def _handle_options(self):
        headers = SocialMediaAuth.get_cors_headers()
        return request.make_response('', headers=headers)

    @http.route('/social_media/create_post', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def create_post(self, **post):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        headers = SocialMediaAuth.get_cors_headers()
        
        if user_auth['status'] == 'error':
            return request.make_response(json.dumps({'status': 'error', 'message': user_auth['message']}), headers=headers)

        if 'image' in request.httprequest.files:
            image_file = request.httprequest.files['image']
            description = post.get('description', '')

            try:
                # Ensure the directory exists
                save_directory = 'images/community'
                if not os.path.exists(save_directory):
                    os.makedirs(save_directory)

                # Use os.path.join to ensure the file path is correct
                file_path = os.path.join(save_directory, f'post_images_{random.randint(100000, 999999)}.png')

                # Save the image properly
                with open(file_path, 'wb') as f:
                    f.write(image_file.read())

                # Create the post in the database, storing the image path instead of the base64-encoded image
                post = request.env['social_media.post'].create({
                    'image': file_path,
                    'description': description,
                    'user_id': user_auth['user_id']
                })

                return request.make_response(json.dumps({'status': 'success', 'post_id': post.id, 'image_path': file_path}), headers=headers)

            except Exception as e:
                return request.make_response(json.dumps({'status': 'error', 'message': str(e)}), headers=headers)
        else:
            return request.make_response(json.dumps({'status': 'error', 'message': 'No image found', 'status_code': '500'}), headers=headers)
        

    @http.route('/social_media/get_posts', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False,cors='*')
    def get_posts(self):
        
        # Handle OPTIONS request for CORS preflight
        if request.httprequest.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Max-Age': '86400',  # 24 hours
            }
            return Response(status=204, headers=headers)

        # Handle GET request
        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401, headers={'Access-Control-Allow-Origin': '*'})

        try:
            posts = request.env['social_media.post'].search([])
            # Filter out post data based on the blacklisted users of user_auth['user_id']
            user_data = request.env['res.users'].sudo().search([('id', '=', user_auth['user_id'])])
            user_data = user_data.read(['blocked_users'])
            blocked_users = user_data[0]['blocked_users']

            posts_data = posts.read(['id', 'image', 'description', 'timestamp', 'user_id'])

            posts_data = [post for post in posts_data if post['user_id'][0] not in blocked_users]

            # get the user profile image from image/profilepics


            overall_data = []
            for post in posts_data:

                # Get the user's profile image
                user_info = request.env['res.users'].sudo().search([('id', '=', post['user_id'][0])])

                # check if user has profile image in image/profilepics
                image_dir = f'images/profilepics/{user_info.id}'
                if os.path.exists(image_dir):
                    image = os.listdir(image_dir)[0]
                
                
                post['profile_image'] = f'{image_dir}/{image}' if os.path.exists(image_dir) else None
                post['user_name'] = f'{user_info.name} {user_info.x_last_name}'



                image_url = post['image'] if post['image'] else None
                post['image'] = image_url

                # Convert datetime to ISO 8601 string format
                if post['timestamp']:
                    post['timestamp'] = post['timestamp'].isoformat()

                is_liked = request.env['social_media.like'].search(
                    [('user_id', '=', user_auth['user_id']), ('post_id', '=', post['id'])])
                post['is_liked'] = True if is_liked else False

                # Get the number of likes for the post
                likes = request.env['social_media.like'].search_count([('post_id', '=', post['id'])])
                post['likes'] = likes

                # Get the number of comments for the post
                comments = request.env['social_media.comment'].search_count([('post_id', '=', post['id'])])
                post['comments_count'] = comments

                # Check if the user is the owner of the post
                post['owner'] = post['user_id'][0] == user_auth['user_id']


                overall_data.append(post)

            # Reverse the list to get the latest post first
            overall_data.reverse()
            return Response(json.dumps({
                'result': {'status': 'success', 'posts': overall_data, "total_posts": len(overall_data)}
            }), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 'error',  # Internal Server Error
                'status_code': '500'
            }), content_type='application/json', status=500, headers={'Access-Control-Allow-Origin': '*'})
        

    @http.route('/images/community/<path:image>', type='http', auth='public', csrf=False,cors='*')
    def get_image(self, image):
        image_path = os.path.join('images/community', image)
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


    @http.route('/social_media/delete_post/<int:post_id>', type='http', auth='public', methods=['DELETE', 'OPTIONS'],csrf=False,cors='*')
    def delete_post(self, post_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            if not post_id:
                return Response(json.dumps({
                    'error': {'message': 'post_id is required'},
                    'status': 'error',
                    'status_code': '400'  # Bad Request
                }), content_type='application/json', status=400)

            post = request.env['social_media.post'].search([('id', '=', post_id)])
            if not post:
                return Response(json.dumps({
                    'error': {'message': 'Post does not exist'},
                    'status': 'error',
                    'status_code': '404'  # Not Found
                }), content_type='application/json', status=404)
            
            default_userId = user_auth['user_id']
            if post.user_id.id != default_userId:
                return Response(json.dumps({
                    'error': {'message': 'You are not authorized to delete this post'},
                    'status': 'error',
                    'status_code': '403'  # Forbidden
                }), content_type='application/json', status=403)
            

            post.unlink()
            return Response(json.dumps({
                'result': {'status': 'success', 'message': 'Post deleted successfully'}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 'error',
                'status_code': '500'  # Internal Server Error
            }), content_type='application/json', status=500)

        

    @http.route('/social_media/like', type='json', auth='public', methods=['POST', 'OPTIONS'],csrf=False,cors='*')
    def like_dislike_post(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'error': user_auth,
                'status': 401  # Unauthorized
            }

        post_id = request.jsonrequest.get('post_id')
        if not post_id:
            return {'status': 'error', 'message': 'post_id is required'}
        
        # if is liked then make it dislike and if not liked then make it like
        try:
            default_userId = user_auth['user_id']
            already_like = request.env['social_media.like'].search(
                [('user_id', '=', default_userId), ('post_id', '=', post_id)])
            if already_like:
                already_like.unlink()
                return {'status': 'success', 'message': 'Post disliked successfully'}
            else:
                like = request.env['social_media.like'].create({
                    'user_id': default_userId,
                    'post_id': post_id
                })
                return {'status': 'success', 'message': 'Post liked successfully', 'like_id': like.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': '500'}


    @http.route('/social_media/get_likes/<int:post_id>', type='http', auth='public', methods=['GET', 'OPTIONS'],csrf=False,cors='*')
    def get_likes(self, post_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            likes = request.env['social_media.like'].search([('post_id', '=', post_id)])
            likes_data = likes.read(['user_id', 'timestamp'])

        
            # Convert timestamp to ISO 8601 format if present
            for like in likes_data:
                user_info = request.env['res.users'].sudo().search([('id', '=', like['user_id'][0])])

                # check if user has profile image in image/profilepics
                image_dir = f'images/profilepics/{user_info.id}'
                if os.path.exists(image_dir):
                    image = os.listdir(image_dir)[0]
                
                
                like['profile_image'] = f'{image_dir}/{image}' if os.path.exists(image_dir) else None
                like['user_name'] = f'{user_info.name} {user_info.x_last_name}'

                if 'timestamp' in like and like['timestamp']:
                    like['timestamp'] = like['timestamp'].isoformat()

            return Response(json.dumps({
                'result': {'status': 'success', 'likes': likes_data}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 'error',
                'status_code': '500'  # Internal Server Error
            }), content_type='application.json', status=500)


    @http.route('/social_media/add_comment', type='json', auth='public',methods=['POST', 'OPTIONS'])
    def create_comment(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'error': user_auth,
                'status': 401  # Unauthorized
            }
        
        post_id = request.jsonrequest.get('post_id')
        content = request.jsonrequest.get('content')

        if not post_id or not content:
            return {'status': 'error', 'message': 'Both post_id and content are required'}

        try:
            default_userId = user_auth['user_id']

            comment = request.env['social_media.comment'].create({
                'user_id': default_userId,
                'post_id': int(post_id),  # Ensure post_id is converted to integer
                'content': content
            })
            return {'status': 'success', 'comment_id': comment.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code':'500'}


    @http.route('/social_media/get_comments/<int:post_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False,cors='*')
    def get_comments(self, post_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            if not post_id:
                return Response(json.dumps({
                    'status': 'error',
                    'message': 'post_id is required'
                }), content_type='application/json', status=400)

            comments = request.env['social_media.comment'].search([('post_id', '=', post_id)])
            comments_data = comments.read(['user_id', 'content', 'timestamp'])

            # Convert timestamp to ISO 8601 format if present
            for comment in comments_data:
                user_info = request.env['res.users'].sudo().search([('id', '=', comment['user_id'][0])])
                image_dir = f'images/profilepics/{user_info.id}'

                # Initialize profile_image to None
                comment['profile_image'] = None

                # Check if the user has a profile image in image/profilepics
                if os.path.exists(image_dir):
                    images = os.listdir(image_dir)
                    if images:
                        image = images[0]
                        comment['profile_image'] = f'{image_dir}/{image}'

                comment['user_name'] = f'{user_info.name} {user_info.x_last_name}'

                if 'timestamp' in comment and comment['timestamp']:
                    comment['timestamp'] = comment['timestamp'].isoformat()

                is_liked = request.env['social_media.comment_like'].search(
                    [('user_id', '=', user_auth['user_id']), ('comment_id', '=', comment['id'])])
                comment['is_liked'] = True if is_liked else False

                # Get the number of likes for the comment
                likes = request.env['social_media.comment_like'].search_count([('comment_id', '=', comment['id'])])
                comment['likes_count'] = likes
            #In every comment send the total likes for that comment and is_liked by the auth user
            # for comment in comments_data:
                

            return Response(json.dumps({
                'result': {'status': 'success', 'comments': comments_data}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'status': 'error',
                'message': str(e),
                'status_code': '500'  # Internal Server Error
            }), content_type='application/json', status=500)


    @http.route('/social_media/delete_comment/<int:comment_id>', type='http', auth='public', methods=['DELETE', 'OPTIONS'], csrf=False,cors='*')
    def delete_comments(self, comment_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            if not comment_id:
                return Response(json.dumps({
                    'error': {'message': 'comment_id is required'},
                    'status': 400  # Bad Request
                }), content_type='application/json', status=400)

            comment = request.env['social_media.comment'].search([('id', '=', comment_id)])
            if not comment:
                return Response(json.dumps({
                    'error': {'message': 'Comment does not exist'},
                    'status': 404  # Not Found
                }), content_type='application/json', status=404)

            default_userId = user_auth['user_id']
            if comment.user_id.id != default_userId:
                return Response(json.dumps({
                    'error': {'message': 'You are not authorized to delete this comment'},
                    'status': 403  # Forbidden
                }), content_type='application/json', status=403)
            
            # Delete the comment
            comment.unlink()


            return Response(json.dumps({
                'result': {'status': 'success', 'message': 'Comment deleted successfully'}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 500  # Internal Server Error
            }), content_type='application/json', status=500)
        

    @http.route('/social_media/like_comment', type='json', auth='public', methods=['POST', 'OPTIONS'],csrf=False,cors='*')
    def like_comment(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        comment_id = request.jsonrequest.get('comment_id', False)

        if not comment_id:
            return {'status': 'error', 'message': 'comment_id is required'}
        
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        if not comment_id:
            return {
                'error': {'message': 'comment_id is required'},
                'status': 400  # Bad Request
            }

        default_userId = user_auth['user_id']


        try:
            # if user has liked the comment then make it dislike and if not liked then make it like
            already_like = request.env['social_media.comment_like'].search(
                [('user_id', '=', default_userId), ('comment_id', '=', comment_id)])
            if already_like:
                already_like.unlink()
                return{
                    'result': {'status': 'success', 'message': 'Comment disliked successfully'}
                }
            
            like = request.env['social_media.comment_like'].create({
                'user_id': default_userId,
                'comment_id': comment_id
            })
            return {
                'result': {'status': 'success', 'message': 'Comment liked successfully', 'like_id': like.id}
            }
        
        except Exception as e:
            return {
                'error': {'message': str(e)},
                'status': 500  # Internal Server Error
            }
        



    @http.route('/social_media/get_comment_likes/<int:comment_id>', type='http', auth='public', methods=['GET', 'OPTIONS'],csrf=False,cors='*')
    def get_comment_likes(self, comment_id):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return Response(json.dumps({
                'error': user_auth,
                'status': 401  # Unauthorized
            }), content_type='application/json', status=401)

        try:
            if not comment_id:
                return Response(json.dumps({
                    'error': {'message': 'comment_id is required'},
                    'status': 400  # Bad Request
                }), content_type='application/json', status=400)

            likes = request.env['social_media.comment_like'].search([('comment_id', '=', comment_id)])
            likes_data = likes.read(['user_id', 'timestamp'])

            # Convert timestamp to ISO 8601 format if present
            for like in likes_data:
                if 'timestamp' in like and like['timestamp']:
                    like['timestamp'] = like['timestamp'].isoformat()

            return Response(json.dumps({
                'result': {'status': 'success', 'likes': likes_data}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 500  # Internal Server Error
            }), content_type='application/json', status=500)
        

    # Block or unblock a user
    @http.route('/social_media/block_user', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def block_user(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        # Authenticate user
        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        blocked_user_id = request.jsonrequest.get('blocked_user_id', False)
        if not blocked_user_id:
            return {'status': 'error', 'message': 'blocked_user_id is required'}

        default_user_id = user_auth['user_id']
        if int(blocked_user_id) == default_user_id:
            return {'status': 'error', 'message': 'You cannot block or unblock yourself'}

        try:
            # Fetch the user to block
            blocked_user = request.env['res.users'].sudo().search([('id', '=', blocked_user_id)], limit=1)
            if not blocked_user:
                return {'status': 'error', 'message': 'User to block does not exist'}

            # Fetch the current user's record
            current_user = request.env['res.users'].sudo().search([('id', '=', default_user_id)], limit=1)

            # Check if the user is already blocked
            if blocked_user in current_user.blocked_users:
                current_user.write({'blocked_users': [(3, blocked_user.id)]})
                return {'status': 'success', 'message': 'User unblocked successfully'}
            else:
                current_user.write({'blocked_users': [(4, blocked_user.id)]})
                return {'status': 'success', 'message': 'User blocked successfully'}

        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': 500}
        

    @http.route('/social_media/report_post', type='json', auth='public', methods=['POST', 'OPTIONS'],csrf=False,cors='*')
    def report_post(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        user_auth = SocialMediaAuth.user_auth(self)
        if user_auth['status'] == 'error':
            return {
                'status': 'error',
                'message': user_auth['message'],
                'status_code': 401  # Unauthorized
            }

        post_id = request.jsonrequest.get('post_id', False)
        if not post_id:
            return {'status': 'error', 'message': 'post_id is required'}

        default_user_id = user_auth['user_id']
        report = request.env['social_media.report'].search([('post_id', '=', post_id), ('user_id', '=', default_user_id)])
        if report:
            return {'status': 'error', 'message': 'You have already reported this post'}
        try:
            report = request.env['social_media.report'].create({
                'post_id': post_id,
                'user_id': default_user_id
            })
            return {'status': 'success', 'message': 'Post reported successfully', 'report_id': report.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e), 'status_code': 500}
        

    
    @http.route('/social_media/get_reported_posts', type='http', auth='public', methods=['GET', 'OPTIONS'],csrf=False,cors='*')
    def get_reported_posts(self):
        if request.httprequest.method == 'OPTIONS':
            return self._handle_options()

        
        try:
            reported_posts = request.env['social_media.report'].search([])
            reported_posts_data = reported_posts.read(['post_id', 'user_id'])

            return Response(json.dumps({
                'result': {'status': 'success', 'reported_posts': reported_posts_data}
            }), content_type='application/json')

        except Exception as e:
            return Response(json.dumps({
                'error': {'message': str(e)},
                'status': 500  # Internal Server Error
            }), content_type='application/json', status=500)

    

    @http.route('/social_media/vpvp', type='json', auth='user')
    def debug_likes(self):
        posts = request.env['social_media.post'].sudo().search([])
        post_data = []
        for post in posts:
            post._compute_likes_count()  # Force recompute to debug
            post_data.append({
                'id': post.id,
                'description': post.description,
                'likes_count': post.likes_count
            })
        return {'posts': post_data}