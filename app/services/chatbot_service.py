import requests
import os

def get_chatbot_response(message):
    url = "https://chatgpt-42.p.rapidapi.com/conversationgpt4-2"
    payload = {
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "system_prompt": "You are a prenatal care expert named Dr. Gyno. Provide helpful and accurate information about pregnancy and prenatal care.",
        "temperature": 0.9,
        "top_k": 5,
        "top_p": 0.9,
        "max_tokens": 256,
        "web_access": False
    }
    headers = {
        "x-rapidapi-key": os.environ.get('RAPID_API_KEY'),
        "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        chatbot_response = response.json()
        return chatbot_response['result']
    except requests.exceptions.RequestException as e:
        raise e
