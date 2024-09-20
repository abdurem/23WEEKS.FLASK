from marshmallow import Schema, fields, post_load
from datetime import datetime

class PregnancyInfoSchema(Schema):
    pregnancy_start_date = fields.Date(required=True)

    @post_load
    def parse_date(self, data, **kwargs):
        if isinstance(data['pregnancy_start_date'], str):
            data['pregnancy_start_date'] = datetime.strptime(data['pregnancy_start_date'], '%Y-%m-%d').date()
        return data

pregnancy_info_schema = PregnancyInfoSchema()
