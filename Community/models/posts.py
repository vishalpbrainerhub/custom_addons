from odoo import models, fields, api
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger(__name__)


class Post(models.Model):
    _name = 'social_media.post'
    _description = 'Post'

    # Fields
    image =  fields.Char("Image Path")
    image_view = fields.Html("Image View", compute='_compute_image_html')
    timestamp = fields.Datetime("Timestamp", default=lambda self: fields.Datetime.now())
    description = fields.Text("Description")
    likes = fields.One2many('social_media.like',  'post_id', string='Likes')
    comments = fields.One2many('social_media.comment', 'post_id', string='Comments')
    user_id = fields.Many2one('res.users', string='User', required=True)
    reports = fields.One2many('social_media.report', 'post_id', string='Reports')

    # Computed fields
    report_count = fields.Integer(string="Report Count", compute='_compute_report_count', store=True)
    likes_count = fields.Integer(string="Likes Count", compute='_compute_likes_count', store=True)
    comments_count = fields.Integer(string="Comments Count", compute='_compute_comments_count', store=True)



    @api.depends('reports')
    def _compute_report_count(self):
        for record in self:
            record.report_count = len(record.reports)
        

    @api.depends('image')
    def _compute_image_html(self):
        for record in self:
            if record.image:
                record.image_view = f'<img src="{record.image}" style="max-height:100px;"/>'
            else:
                record.image_view = "No image"

    @api.depends('likes.user_id')
    def _compute_likes_count(self):
        for record in self:
            record.likes_count = len(record.likes.ids)

    @api.depends('comments')
    def _compute_comments_count(self):
        for record in self:
            record.comments_count = len(record.comments)



class Report(models.Model):
    _name = 'social_media.report'
    _description = 'Reported Post'

    post_id = fields.Many2one('social_media.post', string='Post')
    user_id = fields.Many2one('res.users', string='User')


    