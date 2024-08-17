from flask import Blueprint, jsonify, request, send_file, url_for
import os
from app.services.ultrasound_classification_service import classify_image
from app.services.report_generation_service import create_report
from app.services.chatbot_service import get_chatbot_response
from app.services.image_enhancement_service import enhance_image 
from app.services.head_circumference_service import *
from app.services.Speech_to_text import transcribe_audio 
from app.services.Smart_reminders_service import text_to_events
from PIL import Image
import traceback
import base64
import tempfile
import json
bp = Blueprint('api', __name__)

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

@bp.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio_data']

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
        audio_file.save(temp_audio_file.name)
        temp_audio_file_path = temp_audio_file.name

    try:
        transcribed_text = transcribe_audio(temp_audio_file_path)
        extracted_data = text_to_events(transcribed_text)
        extracted_data_json = json.loads(extracted_data) if extracted_data else {}
        return jsonify({'text': transcribed_text, 'extracted_data': extracted_data_json})
    except Exception as e:
        print(f"Error during transcription: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_audio_file_path)

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
        if enhanced_image_bytes is None:
            raise ValueError('Image enhancement failed')

        enhanced_image_base64 = base64.b64encode(enhanced_image_bytes).decode('utf-8')
        return jsonify({'enhancedImage': enhanced_image_base64})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/calculate-circumference', methods=['POST'])
def calculate_circumference_route():
    try:
        if 'image' not in request.files:
            raise ValueError('No image file part')

        file = request.files['image']
        if file.filename == '':
            raise ValueError('No selected file')

        image_bytes = file.read()
        if not image_bytes:
            raise ValueError('No image data provided.')

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