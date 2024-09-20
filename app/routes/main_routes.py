from flask import Blueprint, jsonify, render_template, request
import os
import requests
import tempfile

bp = Blueprint('main', __name__)

# Groq API details
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions" 
MODEL_NAME = "whisper-large-v3"  

@bp.route('/')
def index():
    return jsonify({
        "message": "🌟 Welcome to 23 Weeks!",
        "status": "✅ Server is running smoothly.",
        "info": "🤖 Explore our AI features for a healthy pregnancy!",
        "api_version": "🔧 v1.0",
        "contact": "📧 Reach us at 23weeks@gmail.com for inquiries."
    })

@bp.route('/whisper')
def whisper():
    return render_template('whisper.html')

@bp.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    try:
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio)
            temp_audio_path = temp_audio.name

        # Send the file as multipart/form-data to the Groq API with model specification
        with open(temp_audio_path, "rb") as audio_data:
            files = {
                'file': (audio_file.filename, audio_data, 'audio/wav')
            }
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
            data = {
                'model': MODEL_NAME  # Add the model parameter here
            }

            response = requests.post(GROQ_API_URL, headers=headers, files=files, data=data)

            # Clean up the temporary file
            os.unlink(temp_audio_path)

            # Check the API response
            if response.status_code == 200:
                transcription = response.json()
                return jsonify({"transcription": transcription.get('text', 'No transcription available')})
            else:
                return jsonify({"error": "Failed to transcribe audio", "details": response.json()}), response.status_code
    except Exception as e:
        if 'temp_audio_path' in locals():
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        return jsonify({"error": str(e)}), 500
