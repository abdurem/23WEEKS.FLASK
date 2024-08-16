from flask import Blueprint, jsonify, request, send_file, url_for
import os
from app.services.ultrasound_classification_service import classify_image
from app.services.report_generation_service import create_report
from app.services.chatbot_service import get_chatbot_response
from PIL import Image
import traceback
 
bp = Blueprint('api', __name__)

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