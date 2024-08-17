import os
import urllib.request
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO

# Define model path and file location
model_path = 'https://raw.githubusercontent.com/Shujaat123/MUSI_Enhancement_TCMR_CNN/main/32_channel_3x3_MaxPool/32_channel_3x3_trial_0.h5'
model_file = 'model_weights.h5'  # Save the model to a local file

# Download and load the model
def load_enhancement_model():
    if os.path.exists(model_file):
        os.remove(model_file)

    # Download the model using urllib
    urllib.request.urlretrieve(model_path, model_file)
    model = load_model(model_file)
    return model

# Image enhancement function
def enhance_image(image_bytes):
    try:
        model = load_enhancement_model()
        print("Model loaded successfully.")

        # Load and preprocess the image
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        image = image.resize((224, 224))  # Resize to match model input size
        grayscale_image = ImageOps.grayscale(image)

        # Convert images to arrays
        original_image_array = img_to_array(image)
        grayscale_image_array = img_to_array(grayscale_image)
        grayscale_image_array = np.expand_dims(grayscale_image_array, axis=0)  # Add batch dimension
        grayscale_image_array = np.expand_dims(grayscale_image_array, axis=-1)  # Add channel dimension for grayscale
        grayscale_image_array = grayscale_image_array / 255.0  # Normalize the image

        # Make predictions
        predictions = model.predict(grayscale_image_array)
        predicted_image_array = predictions[0]  # Get the first image in the batch
        predicted_image_array = np.clip(predicted_image_array * 255.0, 0, 255).astype(np.uint8)  # Denormalize the image

        # Return the enhanced image as bytes
        enhanced_image = Image.fromarray(predicted_image_array.squeeze())
        enhanced_image_bytes = BytesIO()
        enhanced_image.save(enhanced_image_bytes, format='PNG')
        enhanced_image_bytes.seek(0)
        
        return enhanced_image_bytes

    except Exception as e:
        print(f"Error in enhance_image: {str(e)}")
        return None
