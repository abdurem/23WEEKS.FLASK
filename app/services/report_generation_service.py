import io
import base64
import os
import uuid
from datetime import datetime
import google.generativeai as genai
import markdown
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch

api_key = os.environ.get('GOOGLE_AI_API_KEY')
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    generation_config=generation_config
)

def describe_image(image):
    prompt = """
    You are an expert in medical image analysis with a focus on ultrasound images. 
    Your task is to examine the uploaded ultrasound image for any anomalies, conditions, or findings. 
    Please provide a detailed analysis and report based on the following guidelines: 
    1. **Detailed Analysis**: Thoroughly examine the ultrasound image for any abnormalities or issues. 
    Describe the findings in detail, including any notable observations. 
    2. **Analysis Report**: Summarize the findings in a structured format. Include any potential diagnoses, observations, and the significance of the findings. 
    3. **Recommendations**: Based on your analysis, suggest any further tests, treatments, or follow-up actions that might be necessary. 
    4. **Treatments**: If applicable, outline potential treatments or remedies that could be considered based on the analysis. 
    Important Notes: 
    - Ensure that the analysis is relevant to human health issues. 
    - If the image is unclear or of low quality, mention that certain aspects cannot be determined. 
    - Include a disclaimer: "Consult with a Doctor before making any decisions."
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        max_size = (1024, 1024)
        image.thumbnail(max_size)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        response = model.generate_content([
            {"mime_type": "image/png", "data": img_base64},
            prompt
        ])
        
        html = markdown.markdown(response.text)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        style = soup.new_tag('style')
        style.string = """
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            h1, h2, h3 { color: #2c3e50; }
            strong { color: #e74c3c; }
            ul { padding-left: 20px; }
            .disclaimer { background-color: #f8f9fa; border-left: 5px solid #ccc; padding: 10px; margin-top: 20px; }
        """
        soup.insert(0, style)
        
        disclaimer = soup.find(string=lambda text: "Disclaimer:" in text if text else False)
        if disclaimer:
            disclaimer_tag = disclaimer.find_parent()
            new_div = soup.new_tag('div', attrs={'class': 'disclaimer'})
            disclaimer_tag.wrap(new_div)
        
        return str(soup)
    except Exception as e:
        return f"<p>An unexpected error occurred: {str(e)}</p>"

def generate_pdf(html_content):
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
    
    os.makedirs('static/reports', exist_ok=True)
    
    filepath = os.path.join('static/reports', filename)
    
    # Create a PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Create a list to hold the flowables
    Story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Process each element in the HTML
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul']):
        if element.name in ['h1', 'h2', 'h3']:
            Story.append(Paragraph(element.text, styles['Heading' + element.name[-1]]))
        elif element.name == 'p':
            Story.append(Paragraph(element.text, styles['Normal']))
        elif element.name == 'ul':
            for li in element.find_all('li'):
                Story.append(Paragraph('• ' + li.text, styles['Normal']))
        Story.append(Spacer(1, 0.2 * inch))
    
    # Build the PDF
    doc.build(Story)
    
    return filename

def create_report(image):
    html_content = describe_image(image)
    pdf_filename = generate_pdf(html_content)
    return html_content, pdf_filename