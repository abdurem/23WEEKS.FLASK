from marshmallow import Schema, fields, validate
from flask import url_for

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    type = fields.Str(required=True, validate=validate.OneOf(['user', 'doctor']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    avatar = fields.Method("get_avatar_url", dump_only=True)
    pregnancy_info = fields.Nested('PregnancyInfoSchema', dump_only=True)
    current_pregnancy_week = fields.Int(dump_only=True)

    def get_avatar_url(self, obj):
        if obj.avatar:
            return url_for('static', filename=f'uploads/{obj.avatar}', _external=True)
        return None

class UserUpdateSchema(Schema):
    avatar = fields.Str(validate=validate.Length(min=0, max=100))
    full_name = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email()

user_schema = UserSchema()
user_update_schema = UserUpdateSchema()
