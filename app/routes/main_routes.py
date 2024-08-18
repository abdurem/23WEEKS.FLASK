from flask import Blueprint, jsonify, render_template, request
from openai import OpenAI
import os
import tempfile

bp = Blueprint('main', __name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@bp.route('/')
def index():
    return jsonify({"message": "Welcome to the Flask Backend!"})

@bp.route('/whisper')
def whisper():
    return render_template('whisper.html')

@bp.route('/transcribe', methods=['POST'])
def transcribe():
    print (os.environ.get("OPENAI_API_KEY"))
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio)
            temp_audio_path = temp_audio.name

        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        os.unlink(temp_audio_path)
        
        return jsonify({"transcription": transcription.text})
    except Exception as e:
        if 'temp_audio_path' in locals():
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        return jsonify({"error": str(e)}), 500