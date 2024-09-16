from flask import Flask, request, jsonify
from groq import Groq
import os


client = Groq(api_key=os.environ.get("GROQ_API_KEY")) 

MODEL = 'llama3-groq-70b-8192-tool-use-preview'

def generate_name(criteria):
    """Generate baby names based on the given criteria."""
   
    # Extract criteria from the dictionary
    gender = criteria.get("gender", "")
    origin = criteria.get("origin", "")
    meaning = criteria.get("meaning", "")
    name_length = criteria.get("name_length", "")
    start_letter = criteria.get("start_letter", "")
    count = criteria.get("count", 5) 
   
    print(gender)
    print(origin)
    print(meaning)
    print(name_length)
    print(start_letter)

    # Build the user prompt for the Groq model based on criteria
    user_prompt = (
        f"Generate {count} {origin} baby names that are {gender}, "
        f"start with the letter '{start_letter}', have a meaning related to '{meaning}', "
        f"and have a name length of {name_length}."
    )
   
    # Prepare the messages to send to the Groq API
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that generates baby names based on the user's criteria such as gender, origin, starting letter, meaning, and name length."
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]
   
    # Call the Groq API to generate names
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=150  # Adjust based on expected response size
    )
   
    # Log the API response
    print("API Response:", response)
   
    # Extract the content from the response
    content = response.choices[0].message.content.strip()

    # Process the content to extract names and meanings
    lines = content.split('\n')
    names = []
    for line in lines:
        if line.strip():  # Check if the line is not empty
            parts = line.split(' - ')
            if len(parts) == 2:
                name = parts[0].strip()
                meaning = parts[1].strip()
                names.append({"Name": name, "Meaning": meaning})
   
    return {"baby_names": names}