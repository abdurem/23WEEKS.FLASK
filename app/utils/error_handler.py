# error_handler.py
from flask import jsonify

def handle_error(e):
    """Centralized error handling."""
    # You can log the error or perform other actions here
    return jsonify({"error": str(e)}), 500

def handle_file_error(file_field_name):
    """Handle errors related to file uploads."""
    return jsonify({"error": f"No file part for {file_field_name}"}), 400

def handle_no_file_selected_error(file_field_name):
    """Handle cases where no file was selected."""
    return jsonify({"error": f"No selected file for {file_field_name}"}), 400

def handle_bad_request(message):
    """Handle bad requests with a specific message."""
    return jsonify({"error": message}), 400
