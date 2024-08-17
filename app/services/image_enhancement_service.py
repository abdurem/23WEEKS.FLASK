import os
import onnxruntime as ort
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO

# Define the path to the local ONNX model file
model_file = 'app/models/ImageEnhancementModel.onnx'

# Load the ONNX model
def load_enhancement_model():
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"The model file {model_file} does not exist.")
    
    session = ort.InferenceSession(model_file)
    return session

# Image enhancement function
def enhance_image(image_bytes):
    try:
        session = load_enhancement_model()
        print("Model loaded successfully.")

        # Load and preprocess the image
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        image = image.resize((224, 224))  # Resize to match model input size
        grayscale_image = ImageOps.grayscale(image)

        # Convert images to arrays
        grayscale_image_array = np.array(grayscale_image).astype(np.float32)
        grayscale_image_array = np.expand_dims(grayscale_image_array, axis=0)  # Add batch dimension
        grayscale_image_array = np.expand_dims(grayscale_image_array, axis=-1)  # Add channel dimension for grayscale
        grayscale_image_array = grayscale_image_array / 255.0  # Normalize the image

        # Prepare input for ONNX model
        inputs = {session.get_inputs()[0].name: grayscale_image_array}
        
        # Make predictions
        predictions = session.run(None, inputs)
        predicted_image_array = predictions[0][0]  # Get the first image in the batch
        
        # Check the shape of the predicted image array
        if predicted_image_array.ndim == 3:
            predicted_image_array = np.expand_dims(predicted_image_array, axis=0)
        
        predicted_image_array = np.clip(predicted_image_array.squeeze() * 255.0, 0, 255).astype(np.uint8)  # Denormalize the image

        # Return the enhanced image as bytes
        enhanced_image = Image.fromarray(predicted_image_array.squeeze())
        enhanced_image_bytes = BytesIO()
        enhanced_image.save(enhanced_image_bytes, format='PNG')
        enhanced_image_bytes.seek(0)
        
        return enhanced_image_bytes.getvalue()  # Return bytes

    except Exception as e:
        print(f"Error in enhance_image: {str(e)}")
        return None
