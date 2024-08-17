import whisper
import warnings

# Suppress specific warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Load Whisper model
model = whisper.load_model("medium")

def transcribe_audio(audio_file_path):
    result = model.transcribe(audio_file_path)
    return result['text']
