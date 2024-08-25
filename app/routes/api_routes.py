from flask import Blueprint, jsonify, request, send_file, url_for, send_from_directory
import os
import json 
from threading import Thread
import time
from app.services.ultrasound_classification_service import classify_image
from app.services.report_generation_service import create_report
from app.services.chatbot_service import get_chatbot_response
from app.services.image_enhancement_service import enhance_image 
from app.services.head_circumference_service import *
from app.services.Smart_reminders_service import text_to_events
# from app.services.story_generation_service import *
from app.services.healthtrack_service import *
from app.services.search_engine_service import *
from app.services.brain_structure_detection_service import detect_image

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
        return jsonify({"error": str(e)}), 500
    

@bp.route('/process_text', methods=['POST'])
def process_text():
    data = request.json
    transcription = data.get('transcription', '')
    
    if not transcription:
        return jsonify({'error': 'No transcription provided'}), 400
    
    result = text_to_events(transcription)
    
    return jsonify(json.loads(result))

@bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    return jsonify({"message": "File uploaded successfully"}), 200

@bp.route('/')
def index():
    return "Flask server is running"


@bp.route('/enhance-image', methods=['POST'])
def enhance_image_route():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file found'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image_bytes = file.read()
        enhanced_image_bytes = enhance_image(image_bytes)
        
        # Convert the image bytes to a base64-encoded string
        enhanced_image_base64 = base64.b64encode(enhanced_image_bytes).decode('utf-8')
        return jsonify({'enhancedImage': enhanced_image_base64})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@bp.route('/calculate-circumference', methods=['POST'])
def calculate_circumference_route():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file part"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        image_bytes = file.read()
        if not image_bytes:
            return jsonify({"error": "No image data provided"}), 400

        # Load model and generate mask
        model = load_model()  # Ensure load_model() is implemented correctly
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
            return jsonify({"error": "Unable to calculate circumference"}), 500

    except Exception as e:
        print(f"Error during processing: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

    
@bp.route('/classify-ultrasound', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    image_file = request.files['image']
    image_bytes = image_file.read()
    
    try:
        response = classify_image(image_bytes)
        return jsonify(response), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/generate-report', methods=['POST'])
def api_generate_report():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

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
        print(f"Error in api_generate_report: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@bp.route('/chatbot', methods=['POST'])
def chatbot():
    message = request.json.get('message')
    
    try:
        response = get_chatbot_response(message)
        return jsonify({"content": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/static/reports/<path:filename>')
def serve_report(filename):
    return send_file(os.path.join('static', 'reports', filename), as_attachment=True)

# @bp.route('/generate-story', methods=['POST'])
# def generate_story_route():
#     data = request.get_json()
#     topic = data.get('topic', 'space adventures')
#     chapters = int(data.get('chapters', 2))
#     language = data.get('language', 'en')

#     try:
#         story, images = Story_Generation(topic, chapters, language)
#         pdf_path = create_pdf(story, images)

#         if pdf_path:
#             pdf_url = f"/pdfs/{os.path.basename(pdf_path)}"
#             return jsonify({"story": story, "images": images, "pdf_url": pdf_url})
#         else:
#             return jsonify({"error": "PDF generation failed"}), 500
#     except Exception as e:
#         print(f"Error during story generation: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# @bp.route('/pdfs/<filename>')
# def get_pdf(filename):
#     pdf_directory = os.path.join(os.path.dirname(__file__), 'pdfs')
#     try:
#         return send_from_directory(pdf_directory, filename)
#     except FileNotFoundError:
#         return jsonify({"error": "File not found"}), 404

@bp.route('/images/<filename>')
def get_image(filename):
    return send_from_directory('images', filename)


search_service = SearchService()

def load_model_in_background():
    print("Starting model loading in background...")
    search_service.load_models()
    print("Model loading complete.")

model_loading_thread = Thread(target=load_model_in_background)
model_loading_thread.start()

@bp.route('/search', methods=['POST'])
def search():
    if not search_service.model_loaded:
        return jsonify({"error": "Models are still loading. Please try again later."}), 503

    query = request.json.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        results = search_service.semantic_search(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/status', methods=['GET'])
def status():
    if search_service.model_loaded:
        return jsonify({"status": "Model loaded and ready for search."}), 200
    else:
        return jsonify({"status": "Model is still loading..."}), 202
    

@bp.route('/detect-image', methods=['POST'])
def detect_image_route():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file found'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image_bytes = file.read()
        detected_image_bytes = detect_image(image_bytes)
        if detected_image_bytes is None:
            raise ValueError('Image detection failed')

        detected_image_base64 = base64.b64encode(detected_image_bytes.getvalue()).decode('utf-8')
        return jsonify({'detectedImage': detected_image_base64})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500