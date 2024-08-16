from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from app.schemas.user_schema import user_schema
from marshmallow import ValidationError

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
    return jsonify(access_token=access_token, user_type=user.type), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data['email'].lower()
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, type=user.type, full_name=user.full_name), 200
    return jsonify({"msg": "Bad email or password"}), 401

@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(user_schema.dump(user)), 200