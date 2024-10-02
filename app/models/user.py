from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    avatar = db.Column(db.String(255))
    full_name = db.Column(db.String(100), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    type = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    pregnancy_info = db.relationship('PregnancyInfo', back_populates='user', uselist=False, foreign_keys='PregnancyInfo.user_id')
    patients = db.relationship('PregnancyInfo', back_populates='gynecologist', foreign_keys='PregnancyInfo.gynecologist_id')

    def get_current_pregnancy_week(self):
        if self.pregnancy_info:
            today = date.today()
            days_pregnant = (today - self.pregnancy_info.pregnancy_start_date).days
            weeks_pregnant = days_pregnant // 7 + 1
            return min(weeks_pregnant, 40)
        return None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)