from marshmallow import Schema, fields, validate

class GynecologistMessageSchema(Schema):
    id = fields.Int(dump_only=True)
    patient_id = fields.Int(required=True)
    gynecologist_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1))
    is_from_doctor = fields.Boolean(required=True)
    timestamp = fields.DateTime(dump_only=True)
    read = fields.Boolean()

gynecologist_message_schema = GynecologistMessageSchema()
gynecologist_messages_schema = GynecologistMessageSchema(many=True)