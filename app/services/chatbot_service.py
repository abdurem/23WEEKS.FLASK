import os
from groq import Groq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Dr. Gyno, a friendly and empathetic prenatal care expert. Your role is to provide helpful and accurate information about pregnancy and prenatal care. Always maintain a warm and supportive tone. 

Important guidelines:
1. Remember details about the user.
2. Don't assume information that hasn't been explicitly stated.
3. If unsure about any information, ask for clarification politely.
4. Always address the user by their name if you know it.

Current conversation context: {history}
User's last message: {input}

Respond to the user's last message, keeping in mind the entire conversation context."""),
    ("human", "{input}"),
])

chain = prompt | StrOutputParser()

message_history = ChatMessageHistory()

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: message_history,
    input_messages_key="input",
    history_messages_key="history",
)

def get_chatbot_response(message):
    try:
        history = message_history.messages

        # Create the prompt to send to Groq
        full_prompt = {
            "messages": [
                {"role": "system", "content": "You are Dr. Gyno, a friendly and empathetic prenatal care expert."},
                {"role": "user", "content": message},
            ],
            "model": "llama3-8b-8192",  # Adjust based on the Groq model you're using
            "max_tokens": 500,
            "temperature": 0.7
        }

        # Call Groq API to get the response
        response = client.chat.completions.create(messages=full_prompt['messages'], model=full_prompt['model'])

        # Extract response text from Groq API result
        ai_response = response.choices[0].message.content

        # Store messages in history
        message_history.add_user_message(message)
        message_history.add_ai_message(ai_response)

        return ai_response.strip()
    
    except Exception as e:
        print(f"Error in getting chatbot response: {str(e)}")
        return "I'm sorry, I'm having trouble responding right now. Please try again later."

def clear_conversation_history():
    global message_history
    message_history = ChatMessageHistory()

