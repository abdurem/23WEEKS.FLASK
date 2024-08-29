from flask import Blueprint, jsonify, request, send_file, url_for
import os
import json
from threading import Thread
from app.services.ultrasound_classification_service import classify_image
from app.services.report_generation_service import create_report
from app.services.chatbot_service import get_chatbot_response
from app.services.image_enhancement_service import enhance_image
from app.services.head_circumference_service import *
from app.services.Smart_reminders_service import text_to_events
from app.services.story_generation_service import *
from app.services.healthtrack_service import predict_health_risk
from app.services.anomaly_detection_service import detect_image
from app.utils.error_handler import handle_error, handle_file_error, handle_no_file_selected_error, handle_bad_request
from app.services.name_generation_service import generate_name

bp = Blueprint('api', __name__)

@bp.route('/health-tracking', methods=['POST'])
def predict():
    try:
        data = request.form
        age = float(data.get('age'))
        systolic_bp = float(data.get('systolic_bp'))
        diastolic_bp = float(data.get('diastolic_bp'))
        bs = float(data.get('bs'))
        bt = float(data.get('bt'))
        heart_rate = float(data.get('heart_rate'))

        features = np.array([[age, systolic_bp, diastolic_bp, bs, bt, heart_rate]])
        risk_level = predict_health_risk(features)

        return jsonify({"risk_level": risk_level}), 200
    except Exception as e:
        return handle_error(e)

@bp.route('/process_text', methods=['POST'])
def process_text():
    data = request.json
    transcription = data.get('transcription', '')
    
    if not transcription:
        return handle_bad_request('No transcription provided')
    
    result = text_to_events(transcription)
    
    return jsonify(json.loads(result))

@bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return handle_file_error('file')

    file = request.files['file']
    if file.filename == '':
        return handle_no_file_selected_error('file')

    return jsonify({"message": "File uploaded successfully"}), 200

@bp.route('/enhance-image', methods=['POST'])
def enhance_image_route():
    if 'image' not in request.files:
        return handle_file_error('image')

    file = request.files['image']
    if file.filename == '':
        return handle_no_file_selected_error('image')

    try:
        image_bytes = file.read()
        enhanced_image_bytes = enhance_image(image_bytes)
        enhanced_image_base64 = base64.b64encode(enhanced_image_bytes).decode('utf-8')
        return jsonify({'enhancedImage': enhanced_image_base64})

    except Exception as e:
        return handle_error(e)

@bp.route('/calculate-circumference', methods=['POST'])
def calculate_circumference_route():
    try:
        if 'image' not in request.files:
            return handle_file_error('image')

        file = request.files['image']
        if file.filename == '':
            return handle_no_file_selected_error('image')

        image_bytes = file.read()
        if not image_bytes:
            return handle_bad_request('No image data provided')

        model = load_model()
        mask_image_bytes, circumference, pixel_value = generate_mask_and_circumference(
            model, preprocess_image(image_bytes)
        )

        if circumference is not None:
            mask_base64 = base64.b64encode(mask_image_bytes).decode('utf-8')
            return jsonify({
                "circumference": circumference,
                "pixelValue": pixel_value,
                "maskImage": mask_base64
            })
        else:
            return handle_bad_request("Unable to calculate circumference")

    except Exception as e:
        return handle_error(e)

@bp.route('/classify-ultrasound', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return handle_file_error('image')
    
    image_file = request.files['image']
    image_bytes = image_file.read()
    
    try:
        response = classify_image(image_bytes)
        return jsonify(response), 200
    except Exception as e:
        return handle_error(e)

@bp.route('/generate-report', methods=['POST'])
def api_generate_report():
    if 'image' not in request.files:
        return handle_file_error('image')

    image_file = request.files['image']
    
    try:
        image = Image.open(image_file)
        html_content, pdf_filename = create_report(image)
        pdf_url = url_for('static', filename=f'reports/{pdf_filename}', _external=True)
        return jsonify({
            "report": html_content,
            "pdfLink": pdf_url
        }), 200
    except Exception as e:
        return handle_error(e)

@bp.route('/chatbot', methods=['POST'])
def chatbot():
    message = request.json.get('message')
    
    try:
        response = get_chatbot_response(message)
        return jsonify({"content": response}), 200
    except Exception as e:
        return handle_error(e)

@bp.route('/static/reports/<path:filename>')
def serve_report(filename):
    return send_file(os.path.join('static', 'reports', filename), as_attachment=True)

@bp.route('/generate-story', methods=['POST'])
def generate_story_route():
    data = request.get_json()
    topic = data.get('topic', 'space adventures')
    chapters = int(data.get('chapters', 2))
    language = data.get('language', 'en')

    try:
        story, images = Story_Generation(topic, chapters, language)
        pdf_path = create_pdf(story, images)

        if pdf_path:
            pdf_url = f"/pdfs/{os.path.basename(pdf_path)}"
            return jsonify({"story": story, "images": images, "pdf_url": pdf_url})
        else:
            return handle_bad_request("PDF generation failed")
    except Exception as e:
        return handle_error(e)

@bp.route('/pdfs/<filename>')
def get_pdf(filename):
    pdf_directory = os.path.join(os.path.dirname(__file__), 'pdfs')
    try:
        return send_from_directory(pdf_directory, filename)
    except FileNotFoundError:
        return handle_bad_request("File not found")

@bp.route('/images/<filename>')
def get_image(filename):
    return send_from_directory('images', filename)



@bp.route('/detect-image', methods=['POST'])
def detect_image_route():
    if 'image' not in request.files:
        return handle_file_error('image')

    file = request.files['image']
    if file.filename == '':
        return handle_no_file_selected_error('image')

    try:
        image_bytes = file.read()
        detected_image_bytes = detect_image(image_bytes)
        if detected_image_bytes is None:
            raise ValueError('Image detection failed')

        detected_image_base64 = base64.b64encode(detected_image_bytes.getvalue()).decode('utf-8')
        return jsonify({'detectedImage': detected_image_base64})

    except Exception as e:
        return handle_error(e)

@bp.route('/calculate-fetal-age', methods=['POST'])
def get_fetal_age():
    data = request.json
    circumference_cm = data.get('circumference')
    if circumference_cm is None:
        return jsonify({'error': 'Circumference not provided'}), 400

    try:
        fetal_age = calculate_fetal_age(circumference_cm)
        return jsonify({'fetal_age': fetal_age})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# search_service = SearchService()

# def load_model_in_background():
#     print("Starting model loading in background...")
#     search_service.load_models()
#     print("Model loading complete.")

# model_loading_thread = Thread(target=load_model_in_background)
# model_loading_thread.start()

# @bp.route('/search', methods=['POST'])
# def search():
#     if not search_service.model_loaded:
#         return jsonify({"error": "Models are still loading. Please try again later."}), 503

#     query = request.json.get('query')
#     if not query:
#         return jsonify({"error": "No query provided"}), 400

#     try:
#         results = search_service.semantic_search(query)
#         return jsonify(results), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @bp.route('/status', methods=['GET'])
# def status():
#     if search_service.model_loaded:
#         return jsonify({"status": "Model loaded and ready for search."}), 200
#     else:
#         return jsonify({"status": "Model is still loading..."}), 202
    

@bp.route('/generate_name', methods=['POST'])
def generate_name_route():
    try:
        data = request.json
        gender = data.get('gender', '')
        origin = data.get('origin', '')
        category = data.get('category', '')
        length = data.get('length', '')
        letter = data.get('letter', '')

        names = generate_name(gender, origin, category, length, letter)
        # Log the response for debugging
        print(f"Generated names info: {names}")

        return jsonify({'names': names})
    except Exception as e:
        return jsonify({'error': str(e)}), 500