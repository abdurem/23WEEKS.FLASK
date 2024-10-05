from app import db
from app.models.gynecologist_message import GynecologistMessage
from app.models.pregnancy_info import PregnancyInfo
from app.schemas.gynecologist_message_schema import gynecologist_messages_schema
from sqlalchemy import func
import logging
from sqlalchemy.orm import aliased
from datetime import datetime, timezone
from flask import url_for

logger = logging.getLogger(__name__)

def save_message(patient_id, gynecologist_id, content, is_from_patient):
    try:
        server_time = datetime.now()
        utc_time = server_time.astimezone(timezone.utc)
        
        print(f"Server time: {server_time}")
        print(f"UTC time: {utc_time}")
        
        message = GynecologistMessage(
            patient_id=patient_id,
            gynecologist_id=gynecologist_id,
            content=content,
            is_from_patient=is_from_patient,
            timestamp=utc_time
        )
        db.session.add(message)
        db.session.commit()
        
        print(f"Saved message timestamp: {message.timestamp}")
        return message
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        db.session.rollback()
        raise

def get_chat_history(patient_id, gynecologist_id):
    try:
        messages = GynecologistMessage.query.filter_by(
            patient_id=patient_id,
            gynecologist_id=gynecologist_id
        ).order_by(GynecologistMessage.timestamp.asc()).all()
        
        return {
            "messages": [
                {
                    "id": message.id,
                    "content": message.content,
                    "timestamp": message.utc_timestamp.isoformat(),
                    "is_from_patient": message.is_from_patient,
                    "read": message.read
                }
                for message in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise
    
def get_gynecologist_conversations(gynecologist_id, page=1, per_page=20):
    try:
        subquery = db.session.query(
            GynecologistMessage.patient_id,
            func.max(GynecologistMessage.timestamp).label('last_message_time')
        ).filter_by(gynecologist_id=gynecologist_id).group_by(GynecologistMessage.patient_id).subquery()
        
        LastMessage = aliased(GynecologistMessage)
        
        query = db.session.query(LastMessage).join(
            subquery,
            db.and_(
                LastMessage.patient_id == subquery.c.patient_id,
                LastMessage.timestamp == subquery.c.last_message_time
            )
        ).filter(LastMessage.gynecologist_id == gynecologist_id).order_by(subquery.c.last_message_time.desc())

        paginated_messages = query.paginate(page=page, per_page=per_page, error_out=False)

        result = []
        for message in paginated_messages.items:
            pregnancy_info = PregnancyInfo.query.filter_by(user_id=message.patient_id).first()
            patient = message.patient
            result.append({
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "avatar": url_for('static', filename=f'uploads/{patient.avatar}', _external=True) if patient.avatar else None,
                "last_message": {
                    "content": message.content,
                    "is_from_patient": message.is_from_patient,
                    "timestamp": message.timestamp.isoformat()
                },
                "pregnancy_week": pregnancy_info.get_current_week() if pregnancy_info else None,
                "last_message_time": message.timestamp.isoformat()
            })

        return {
            "conversations": result,
            "total": paginated_messages.total,
            "pages": paginated_messages.pages,
            "current_page": page
        }
    except Exception as e:
        logger.error(f"Error fetching gynecologist conversations: {str(e)}")
        raise