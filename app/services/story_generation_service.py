from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
from fpdf import FPDF
from gtts import gTTS
import requests
import logging
import os
from PIL import Image
from io import BytesIO
from langdetect import detect, LangDetectException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def generate_image(prompt, chapter, theme='3d African kids with no text'):
    api_url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }
    
    full_prompt = f"{theme} theme illustration: {prompt}"
    
    data = {
        "prompt": full_prompt,
        "n": 1,  # Generate one image per chapter
        "size": "1024x1024",  # Image size
        "model": "dall-e-3"  # Specify DALL-E 3 model
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        
        # Ensure the images directory exists
        image_dir = 'images'
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Download the image locally
        image_filename = f"chapter_{chapter}.jpg"
        image_path = os.path.join(image_dir, image_filename)
        img_data = requests.get(image_url).content
        with open(image_path, 'wb') as handler:
            handler.write(img_data)

        # Print the image URL to the console
        print(f"Image URL for Chapter {chapter}: {image_url}")
        
        # Return the DALL-E generated image URL
        return image_url
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to generate image for Chapter {chapter}: {e}")
        return None
    
def Story_Generation(topic, chapters=5, language='en'):
    story = []
    images = []

    for chapter in range(1, chapters + 1):
        prompt = f"""
        You only generates stories in {language} language.
        You are a native story generator in {language} Write an original story in {language} language for kids in africa. 
        Create a story in the {language} language with no english translation.
        All the chapters should be fully written in {language} language.
        This story have {chapter} chapters about {topic} and should be fully wrirten in {language} language.
        Don't mention any religion in the story.
        The story are for the kids under 5 years old.
        Don't mention the word kids in Africa.
        """
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=500,
            temperature=0.7,
            user=language
        )

        chapter_content = response.choices[0].message.content
        story.append(f"{chapter_content}\n\n")

        # Generate image for each chapter using DALL-E 3 with an African theme
        image_prompt = f"Illustration for Chapter {chapter}: {chapter_content}"
        image_path = generate_image(image_prompt, chapter, theme='African kids with no text in it')
        images.append(image_path if image_path else None)

    return story, images  # Ensure only two values are returned

def download_image(image_url, save_directory, chapter_number):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Create image path
        image_filename = f"chapter_{chapter_number}.jpg"
        image_path = os.path.join(save_directory, image_filename)

        # Open the image directly from the response
        image = Image.open(BytesIO(response.content))
        
        # Convert and save the image as a JPEG
        image = image.convert('RGB')
        image.save(image_path, 'JPEG')
        print(f"Image for Chapter {chapter_number} downloaded and saved at: {image_path}")
        
        return image_path
    except Exception as e:
        print(f"Failed to download image for Chapter {chapter_number}: {e}")
        return None

def create_pdf(story, images):
    # Define the directory to save the PDF and images
    base_directory = os.path.dirname(__file__)
    pdf_directory = os.path.join(base_directory, 'pdfs')
    image_directory = os.path.join(base_directory, 'images')
    
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)

    # Define the PDF filename and path
    pdf_filename = "generated_story.pdf"
    pdf_path = os.path.join(pdf_directory, pdf_filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Process each chapter and image
    for i, (chapter_text, image_url) in enumerate(zip(story, images)):
        pdf.add_page()

        # Add the chapter text
        try:
            pdf.multi_cell(0, 10, chapter_text.encode('latin-1', 'replace').decode('latin-1'))
        except UnicodeEncodeError as e:
            print(f"Encoding error in chapter {i+1}: {e}")
            continue

        pdf.ln(10)  # Add some space after the text

        # Download and add the image to the PDF
        if image_url:
            print(f"Found image for Chapter {i+1} at: {image_url}")
            image_path = download_image(image_url, image_directory, i+1)

            if image_path and os.path.exists(image_path):
                try:
                    # Add the image to the PDF
                    pdf.image(image_path, x=10, w=180)  # Adjust width as needed
                    pdf.ln(10)
                    print(f"Image added to PDF for Chapter {i+1}")
                except Exception as e:
                    print(f"Failed to add image to PDF for Chapter {i+1}: {e}")
            else:
                print(f"Image path does not exist or download failed for Chapter {i+1}")
        else:
            print(f"No image URL provided for Chapter {i+1}")

    # Save the PDF
    try:
        pdf.output(pdf_path)
        print(f"PDF generated successfully and saved at {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Failed to generate PDF: {str(e)}")
        return None

def generate_voice_with_eleven_labs(text):
    # Correct API endpoint for text-to-speech generation
    api_url = "https://api.elevenlabs.io/v1/text-to-speech/cgSgspJ2msm6clMCkdW9"  # Adjust this if the endpoint is different

    headers = {
        'xi-api-key': os.getenv("ELEVEN_LABS_API_KEY"),  # Use the correct header for API key
        'Content-Type': 'application/json'
    }

    # Payload structure based on Eleven Labs API requirements
    data = {
        "text": text,
        "voice_settings": {
            "voice_id": "cgSgspJ2msm6clMCkdW9",  # Confirm this is a valid voice ID
            "model_id": "eleven_multilingual_v2",  # Ensure this is the correct model ID
            "stability": 0.75,  # Required parameter for voice settings
            "similarity_boost": 0.75  # Required parameter for voice settings
        }
    }

    try:
        print(f"Sending request to Eleven Labs with data: {data}")
        response = requests.post(api_url, headers=headers, json=data)

        print(f"Response Status Code: {response.status_code}")

        response.raise_for_status()  # This will raise an error for HTTP statuses 4xx/5xx

        # Return the audio content directly as a BytesIO object
        print("Voice generated successfully.")
        return BytesIO(response.content)

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if response is not None and response.content:
            try:
                error_detail = response.json()
                print(f"API Error Response (HTTP): {error_detail}")
            except ValueError:
                print("Error parsing JSON response. Raw response content:")
                print(response.text)
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred: {req_err}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None
    
def detect_language_and_speak(text, manual_language=None):
    try:
        detected_language = detect(text) if not manual_language else manual_language
    except LangDetectException:
        print("Language detection failed. Using manual language if provided.")
        detected_language = manual_language if manual_language else 'en'

    if detected_language == 'en':
        # Use Eleven Labs for English
        return generate_voice_with_eleven_labs(text)
    else:
        # Use gTTS for other languages
        african_languages = {
            'am': 'am', 'sw': 'sw', 'yo': 'yo', 'ig': 'ig', 'ha': 'ha', 'af': 'af', 'en': 'en'
        }

        if detected_language in african_languages:
            tts_language = african_languages[detected_language]
            tts = gTTS(text=text, lang=tts_language)
            audio_content = BytesIO()
            tts.write_to_fp(audio_content)
            audio_content.seek(0)  # Move to the start of the BytesIO object
            return audio_content
        else:
            print(f"Language {detected_language} is not supported or detected incorrectly.")
            return None


