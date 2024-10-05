from marshmallow import Schema, fields

class ChatMessageSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    content = fields.Str(required=True)
    is_bot = fields.Boolean()
    timestamp = fields.DateTime(format='iso')

chat_message_schema = ChatMessageSchema()
chat_messages_schema = ChatMessageSchema(many=True)