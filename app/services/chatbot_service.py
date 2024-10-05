import os
import logging
from groq import Groq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from app import db
from app.models.chat_message import ChatMessage
from app.schemas.chat_message_schema import chat_messages_schema
from datetime import timezone

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def get_or_create_message_history(user_id):
    if not user_id:
        logger.warning("No user ID provided, using default")
        user_id = "default"
    
    if user_id not in message_histories:
        logger.debug(f"Creating new message history for user {user_id}")
        message_histories[user_id] = ChatMessageHistory()
    return message_histories[user_id]

def get_chatbot_response(message, user_id):
    try:
        logger.debug(f"Received message from user {user_id}: {message}")
        
        # Get existing chat history
        history = get_conversation_history(user_id)
        
        full_prompt = {
            "messages": [
                {"role": "system", "content": "You are Dr. Gyno, a friendly and empathetic prenatal care expert."},
                *[{"role": "user" if not msg['is_bot'] else "assistant", "content": msg['content']} for msg in history],
                {"role": "user", "content": message},
            ],
            "model": "llama3-8b-8192",
            "max_tokens": 500,
            "temperature": 0.7
        }

        response = client.chat.completions.create(messages=full_prompt['messages'], model=full_prompt['model'])

        ai_response = response.choices[0].message.content

        # Save user message
        user_message = ChatMessage(user_id=user_id, content=message, is_bot=False)
        db.session.add(user_message)
        
        # Save bot response
        bot_message = ChatMessage(user_id=user_id, content=ai_response, is_bot=True)
        db.session.add(bot_message)
        
        db.session.commit()

        logger.debug(f"Added new messages to history for user {user_id}")

        return ai_response.strip()
    
    except Exception as e:
        logger.error(f"Error in getting chatbot response: {str(e)}")
        return "I'm sorry, I'm having trouble responding right now. Please try again later."
    
def clear_conversation_history(user_id):
    logger.debug(f"Clearing conversation history for user {user_id}")
    ChatMessage.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    logger.debug(f"Cleared conversation history for user {user_id}")

def get_conversation_history(user_id):
    logger.debug(f"Fetching conversation history for user {user_id}")
    messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp).all()
    history = [{
        'id': msg.id,
        'content': msg.content,
        'is_bot': msg.is_bot,
        'timestamp': msg.timestamp.replace(tzinfo=timezone.utc).isoformat()
    } for msg in messages]
    logger.debug(f"Returning history: {history}")
    return history