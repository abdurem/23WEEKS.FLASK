import torch
import numpy as np
import cv2
import os
import traceback
from torchvision import transforms
from app.models.modelCSM import CSM
from PIL import Image
from flask import url_for
import base64
from io import BytesIO


def generate_mask_and_circumference(model, image_tensor):
    try:
        print("Generating mask and calculating head circumference...")
        with torch.no_grad():
            output = model(image_tensor)
        
        # Assuming the model output is a tensor representing the mask
        mask_image = output[0]  # Adjust based on your model's output format

        # Convert tensor to NumPy array
        mask_image = mask_image.squeeze().cpu().numpy()  # Remove batch and channel dimensions

        # Convert mask to 8-bit format
        mask_image = (mask_image * 255).astype(np.uint8)  # Convert mask to 8-bit image

        # Apply edge detection
        edge_img = mcc_edge(mask_image)

        # Fit an ellipse to the edge-detected image
        xc, yc, theta, a, b = ellip_fit(edge_img)
        
        # Calculate circumference from ellipse parameters
        circumference = 2 * np.pi * np.sqrt((a**2 + b**2) / 2)
        
        # Convert mask to image bytes
        mask_pil = Image.fromarray(mask_image)
        buffer = BytesIO()
        mask_pil.save(buffer, format="PNG")
        mask_image_bytes = buffer.getvalue()

        # Optional: Calculate pixel value or any other relevant value
        pixel_value = np.mean(mask_image)  # Example pixel value calculation

        return mask_image_bytes, circumference, pixel_value

    except Exception as e:
        print(f"Error generating mask and circumference: {str(e)}")
        raise


# Load the model
def load_model():
    try:
        print("Loading model...")
        model_path = 'app/models/HeadCircumferenceModel.pth'
        
        model = CSM()  
        state_dict = torch.load(model_path, map_location=torch.device('cpu'))
        model.load_state_dict(state_dict)
        model.eval()
        
        print("Model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        traceback.print_exc()
        raise

# Preprocess the image
def preprocess_image(image_bytes):
    try:
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError("Image decoding failed")

        desired_size = (256, 256)
        resized_image = cv2.resize(image, desired_size)
        normalized_image = resized_image / 255.0
        processed_image = np.expand_dims(normalized_image, axis=0)  # Add channel dimension
        processed_image = np.expand_dims(processed_image, axis=0)  # Add batch dimension
        processed_image = torch.tensor(processed_image, dtype=torch.float32)

        return processed_image
    except Exception as e:
        print(f"Error during image preprocessing: {str(e)}")
        traceback.print_exc()
        return None


def calculate_circumference_from_mask(mask_image):
    """
    Calculates the head circumference from the given mask image.

    Args:
        mask_image (np.ndarray): The mask image as a numpy array.

    Returns:
        float: The calculated head circumference in pixels.
    """

    try:
        # Ensure mask_image is a numpy array
        if isinstance(mask_image, torch.Tensor):
            mask_image = mask_image.detach().cpu().squeeze().numpy()
        elif not isinstance(mask_image, np.ndarray):
            raise TypeError("Expected mask_image to be a numpy array or PyTorch tensor")

        # Convert mask image to uint8 if not already
        if mask_image.dtype != np.uint8:
            mask_image = (mask_image * 255).astype(np.uint8)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            raise ValueError("No contours found in mask image")

        # Assuming the largest contour is the head
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate circumference from the largest contour
        circumference = cv2.arcLength(largest_contour, closed=True)

        return circumference

    except Exception as e:
        print(f"Error calculating circumference from mask: {e}")
        raise

# Save mask image and return URL
def save_mask(mask_image, file_name):
    try:
        mask_path = os.path.join('static', 'masks', file_name.replace('.jpg', '_mask.png'))
        os.makedirs(os.path.dirname(mask_path), exist_ok=True)
        cv2.imwrite(mask_path, mask_image)
        return url_for('static', filename=f'masks/{file_name.replace(".jpg", "_mask.png")}', _external=True)
    except Exception as e:
        print(f"Error saving mask image: {str(e)}")
        traceback.print_exc()
        return None

# Main function to calculate circumference
def calculate_circumference(image_bytes):
    try:
        processed_image = preprocess_image(image_bytes)
        
        if processed_image is None:
            raise ValueError("Image processing failed")

        model = load_model()
        mask_image, circumference = generate_mask_and_circumference(model, processed_image)

        if mask_image is not None:
            mask_image_np = mask_image.detach().cpu().squeeze().numpy() * 255
            mask_image_np = mask_image_np.astype(np.uint8)
            return circumference, save_mask(mask_image_np, 'temp_image.jpg')
        else:
            return None, None
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        traceback.print_exc()
        return None, None


def mcc_edge(mask_image):
    """
    Applies edge detection using the Canny method.

    Args:
        mask_image (np.ndarray): The mask image as a numpy array.

    Returns:
        np.ndarray: The edge-detected image.
    """
    if not isinstance(mask_image, np.ndarray):
        raise TypeError("Expected mask_image to be a numpy array")

    # Ensure the mask image is in uint8 format
    if mask_image.dtype != np.uint8:
        mask_image = (mask_image * 255).astype(np.uint8)

    # Apply Canny edge detection
    edges = cv2.Canny(mask_image, 100, 200)
    return edges

def ellip_fit(edge_image):
    """
    Fits an ellipse to the edge-detected image.

    Args:
        edge_image (np.ndarray): The edge-detected image.

    Returns:
        tuple: The ellipse parameters (xc, yc, theta, a, b)
    """
    if not isinstance(edge_image, np.ndarray):
        raise TypeError("Expected edge_image to be a numpy array")

    # Find contours
    contours, _ = cv2.findContours(edge_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise ValueError("No contours found in edge image")

    # Assume the largest contour is the object of interest
    largest_contour = max(contours, key=cv2.contourArea)

    # Fit an ellipse to the largest contour
    if len(largest_contour) < 5:
        raise ValueError("Not enough points to fit an ellipse")

    ellipse = cv2.fitEllipse(largest_contour)
    xc, yc = ellipse[0]  # Center of the ellipse
    (a, b) = ellipse[1]  # Axes lengths
    theta = ellipse[2]  # Rotation angle

    return xc, yc, theta, a, b
