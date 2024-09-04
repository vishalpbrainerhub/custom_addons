from odoo import models, fields

class Comment(models.Model):
    _name = 'social_media.comment'
    _description = 'Comment'

    post_id = fields.Many2one('social_media.post', string='Post')
    timestamp = fields.Datetime("Timestamp", default=lambda self: fields.Datetime.now())
    content = fields.Text("Content")
    user_id = fields.Many2one('res.users', string='User', required=True)
    comment_likes = fields.One2many('social_media.comment_like', 'comment_id', string="Comment Likes")