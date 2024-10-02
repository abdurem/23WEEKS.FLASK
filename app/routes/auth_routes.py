import os
from flask import Blueprint, request, jsonify
from flask import current_app as app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from app.schemas.user_schema import user_schema, user_update_schema
from app.schemas.pregnancy_info_schema import pregnancy_info_schema
from marshmallow import ValidationError
from werkzeug.utils import secure_filename
from app.models.pregnancy_info import PregnancyInfo
import dateutil.parser
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = user_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    full_name = data['full_name'].lower()
    email = data['email'].lower()

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400

    user = User(full_name=full_name, email=email, type=data['type'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    user_data = user_schema.dump(user)
    return jsonify(access_token=access_token, user=user_data), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data['email'].lower()
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        
        user_data = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "type": user.type,
            "avatar": user.avatar,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
        
        if user.type == 'user':
            pregnancy_info = PregnancyInfo.query.filter_by(user_id=user.id).first()
            print(pregnancy_info)
            if pregnancy_info:
                gynecologist_data = None
                if pregnancy_info.gynecologist:
                    gynecologist_data = {
                        "id": pregnancy_info.gynecologist.id,
                        "full_name": pregnancy_info.gynecologist.full_name,
                        "avatar": pregnancy_info.gynecologist.avatar
                    }
                
                user_data['pregnancy_info'] = {
                    "pregnancy_start_date": pregnancy_info.pregnancy_start_date.isoformat(),
                    "gynecologist": gynecologist_data
                }
                user_data['current_pregnancy_week'] = pregnancy_info.get_current_week()
            else:
                user_data['pregnancy_info'] = None
                user_data['current_pregnancy_week'] = None

        return jsonify(access_token=access_token, **user_data), 200

    return jsonify({"msg": "Bad email or password"}), 401

@bp.route('/register/patient-info', methods=['POST'])
@jwt_required()
def register_patient_info():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.type != 'user':
        return jsonify({"msg": "Invalid user or user type"}), 400

    try:
        data = pregnancy_info_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    pregnancy_info = PregnancyInfo(
        user_id=user.id,
        pregnancy_start_date=data['pregnancy_start_date'],
        gynecologist_id=data.get('gynecologist_id')
    )

    db.session.add(pregnancy_info)
    db.session.commit()

    user_data = user_schema.dump(user)
    user_data['current_pregnancy_week'] = user.get_current_pregnancy_week()

    user_data['created_at'] = user.created_at.isoformat()
    user_data['updated_at'] = user.updated_at.isoformat()

    if pregnancy_info.gynecologist:
        user_data['pregnancy_info'] = {
            "pregnancy_start_date": pregnancy_info.pregnancy_start_date.isoformat(),
            "gynecologist": {
                "id": pregnancy_info.gynecologist.id,
                "full_name": pregnancy_info.gynecologist.full_name,
                "avatar": pregnancy_info.gynecologist.avatar
            }
        }

    return jsonify(user=user_data), 200

@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(user_schema.dump(user)), 200


@bp.route('/update-account', methods=['POST'])
@jwt_required()
def update_account():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    try:
        data = user_update_schema.load(request.form)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'email' in data:
        user.email = data['email'].lower()

    if 'avatar' in request.form and request.form['avatar'] == "":
        user.avatar = None
    elif 'avatar' in request.files:
        avatar_file = request.files['avatar']
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(f"avatar_{user.id}_{avatar_file.filename}")
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(avatar_path)
            user.avatar = filename

    db.session.commit()

    return jsonify(user_schema.dump(user)), 200

@bp.route('/update-pregnancy', methods=['POST'])
@jwt_required()
def update_pregnancy():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.json

    if not user.pregnancy_info:
        pregnancy_info = PregnancyInfo(user_id=user.id)
        db.session.add(pregnancy_info)
    else:
        pregnancy_info = user.pregnancy_info

    if 'pregnancy_start_date' in data and data['pregnancy_start_date']:
        try:
            # Parse the ISO 8601 date string
            parsed_date = dateutil.parser.isoparse(data['pregnancy_start_date'])
            pregnancy_info.pregnancy_start_date = parsed_date.date()
        except ValueError as e:
            return jsonify({"msg": f"Invalid date format: {str(e)}"}), 400

    if 'gynecologist_id' in data:
        pregnancy_info.gynecologist_id = data['gynecologist_id'] if data['gynecologist_id'] else None

    db.session.commit()

    return jsonify(pregnancy_info_schema.dump(pregnancy_info)), 200

@bp.route('/update-password', methods=['POST'])
@jwt_required()
def update_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()

    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not user.check_password(current_password):
        return jsonify({"msg": "Current password is incorrect"}), 401

    if new_password != confirm_password:
        return jsonify({"msg": "New password and confirm password do not match"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}