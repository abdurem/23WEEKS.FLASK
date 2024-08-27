import os
from flask import Blueprint, request, jsonify
from flask import current_app as app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from app.schemas.user_schema import user_schema, user_update_schema
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}