import os
import pytest
from flask import Flask
from app import create_app, db
from io import BytesIO

# Assuming that the test image is placed in the specified directory
TEST_IMAGE_PATH = 'tests/images/Patient00001_Plane1_1_of_15.png'

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    testing_client = flask_app.test_client()

    # Establish an application context
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # This is where the testing happens!

    ctx.pop()

def test_chatbot(test_client):
    response = test_client.post('/api/chatbot', json={"message": "Hello!"})
    assert response.status_code == 200
    assert "content" in response.json

def test_classify_ultrasound(test_client):
    with open(TEST_IMAGE_PATH, 'rb') as img_file:
        response = test_client.post('/api/classify-ultrasound', data={'image': img_file})
    assert response.status_code == 200
    data = response.json
    assert 'brainClassification' in data
    assert 'mainClassification' in data
    assert 'accuracy' in data['mainClassification']
    assert 'allClasses' in data['mainClassification']

def test_detect_image(test_client):
    with open(TEST_IMAGE_PATH, 'rb') as img_file:
        response = test_client.post('/api/detect-image', data={'image': img_file})
    assert response.status_code == 200
    assert "detectedImage" in response.json

def test_health_tracking(test_client):
    sample_data = {
        "age": 45,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "bs": 5.5,
        "bt": 37.0,
        "heart_rate": 72
    }
    response = test_client.post('/api/health-tracking', data=sample_data)
    assert response.status_code == 200
    assert "risk_level" in response.json

def test_calculate_circumference(test_client):
    with open(TEST_IMAGE_PATH, 'rb') as img_file:
        response = test_client.post('/api/calculate-circumference', data={'image': img_file})
    assert response.status_code == 200
    assert "circumference" in response.json

def test_generate_report(test_client):
    with open(TEST_IMAGE_PATH, 'rb') as img_file:
        response = test_client.post('/api/generate-report', data={'image': img_file})
    assert response.status_code == 200
    assert "report" in response.json
    assert "pdfLink" in response.json

def test_generate_name(test_client):
    sample_data = {
        "gender": "male",
        "origin": "african",
        "category": "traditional",
        "length": "short",
        "letter": "A"
    }
    response = test_client.post('/api/generate_name', json=sample_data)
    assert response.status_code == 200
    assert "names" in response.json

def test_enhance_image(test_client):
    with open(TEST_IMAGE_PATH, 'rb') as img_file:
        response = test_client.post('/api/enhance-image', data={'image': img_file})
    assert response.status_code == 200
    assert "enhancedImage" in response.json

def test_generate_story(test_client):
    sample_data = {
        "topic": "space adventures",
        "chapters": 3,
        "language": "en"
    }
    response = test_client.post('/api/generate-story', json=sample_data)
    assert response.status_code == 200
    assert "story" in response.json
    assert "images" in response.json
    assert "pdf_url" in response.json
