import os
import onnxruntime as ort
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO

model_file = 'app/models/ImageEnhancement.onnx'  # Update with your actual model path

def load_enhancement_model():
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"The model file {model_file} does not exist.")
    
    session = ort.InferenceSession(model_file)
    # Print the shape of the model's input tensor for debugging
    input_shape = session.get_inputs()[0].shape
    print(f"Model input shape: {input_shape}")
    return session

def enhance_image(image_bytes):
    try:
        session = load_enhancement_model()
        print("Model loaded successfully.")

        # Load and preprocess the image
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        original_size = image.size
        
        # Optionally apply denoising
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        image = image.resize((64, 64))  # Resize to match model input size (e.g., 64x64)
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

        # Resize the output image back to the original size
        enhanced_image = Image.fromarray(predicted_image_array.squeeze())
        
        # Optionally apply upscaling
        enhanced_image = enhanced_image.resize(original_size, Image.Resampling.BICUBIC)
        
        # Save the enhanced image to bytes
        enhanced_image_bytes = BytesIO()
        enhanced_image.save(enhanced_image_bytes, format='PNG')
        enhanced_image_bytes.seek(0)
        
        return enhanced_image_bytes.getvalue()  # Return bytes

    except Exception as e:
        print(f"Error in enhance_image: {str(e)}")
        raise e
