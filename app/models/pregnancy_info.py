from app import db
from datetime import date

class PregnancyInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    pregnancy_start_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    user = db.relationship('User', back_populates='pregnancy_info')

    def get_current_week(self):
        today = date.today()
        days_pregnant = (today - self.pregnancy_start_date).days
        weeks_pregnant = days_pregnant // 7 + 1
        return min(weeks_pregnant, 40)