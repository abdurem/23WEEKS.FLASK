from app import db
from sqlalchemy.sql import func
from datetime import timezone

class GynecologistMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    gynecologist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_from_patient = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now(), index=True)
    read = db.Column(db.Boolean, default=False)

    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_messages')
    gynecologist = db.relationship('User', foreign_keys=[gynecologist_id], backref='gynecologist_messages')

    def __repr__(self):
        return f'<GynecologistMessage {self.id}>'
    @property
    def utc_timestamp(self):
        return self.timestamp.replace(tzinfo=timezone.utc)