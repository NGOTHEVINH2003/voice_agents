import os
import json
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
from typing import Optional, Dict, Any

load_dotenv()

SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN=os.getenv("SLACK_APP_TOKEN")
API_BASE_URL=os.getenv("API_BASE_URL")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Backend API configuration
# API_BASE_URL = config.get('API_BASE_URL', 'http://localhost:8000')
API_TIMEOUT = 300

class RAGQueryHandler:
    """Handles RAG queries to the backend API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.query_endpoint = f"{base_url}/api/chat/query"
        self.metrics_endpoint = f"{base_url}/metrics"
    
    def query(self, question: str, user_id: str, channel_id: str, answer_id: str ) -> Dict[str, Any]:
        """Send query to RAG backend"""
        try:
            payload = {
                "question": question,
                "user_id": user_id,
                "type": "Slack".lower(),
                "channel_id": channel_id,
                "answer_id": answer_id
            }
            
            response = requests.post(
                self.query_endpoint,
                json=payload,
                timeout=API_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"API timeout for query: {question[:50]}...")
            return {"error": "Request timeout. Please try again."}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {"error": f"Failed to process query: {str(e)}"}
    
# Initialize query handler
query_handler = RAGQueryHandler(API_BASE_URL)

def format_sources(sources: list) -> str:
    """Format source citations for Slack message"""
    if not sources:
        return ""
    
    formatted = "\n\n*Sources:*\n"
    for idx, source in enumerate(sources[:5], 1):  # Limit to top 5 sources
        doc_name = source.get('document', 'Unknown')
        score = source.get('score', 0)
        page = source.get('page', 'N/A')
        formatted += f"{idx}. `{doc_name}` (page {page}, relevance: {score:.2f})\n"
    
    return formatted

def format_answer_message(result: Dict[str, Any]) -> Dict[str, Any]:
    """Format the RAG response into a Slack message block"""
    if "error" in result:
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error:* {result['error']}"
                    }
                }
            ]
        }
    
    answer = result.get('answer', 'No answer found.')
    sources = result.get('sources', [])
    confidence = result.get('confidence', 0)
    latency = result.get('latency_ms', 0)
    
    # Build message blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Answer:*\n{answer}"
            }
        }
    ]
    
    # Add sources if available
    if sources:
        source_text = format_sources(sources)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": source_text
            }
        })
    
    # Add metadata
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Confidence: {confidence:.1%} | Response time: {latency}ms"
            }
        ]
    })
    
    # Add feedback buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Helpful"
                },
                "value": "helpful",
                "action_id": "feedback_helpful"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Not Helpful"
                },
                "value": "not_helpful",
                "action_id": "feedback_not_helpful"
            }
        ]
    })
    
    return {"blocks": blocks}

@app.command("/ask")
def handle_ask_command(ack, command, say, client):
    """Handle /ask slash command"""
    ack()  # Acknowledge command immediately
    
    question = command['text'].strip()
    user_id = command['user_id']
    channel_id = command['channel_id']
    
    if not question:
        say("Please provide a question. Usage: `/ask <your question>`")
        return
    
    # Show loading message
    loading_msg = client.chat_postMessage(
        channel=channel_id,
        text=f"Searching for: _{question}_..."
    )
    
    try:
        # Query the RAG backend
        logger.info(f"Processing query from user {user_id}: {question[:100]}...")
        result = query_handler.query(question, user_id, channel_id, loading_msg['ts'])
        
        print(loading_msg)
        # Format and send response
        message = format_answer_message(result)
        
        # Update the loading message with the result
        client.chat_update(
            channel=channel_id,
            ts=loading_msg['ts'],
            text=result.get('answer', 'No answer found.'),
            **message
        )
        
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        client.chat_update(
            channel=channel_id,
            ts=loading_msg['ts'],
            text=f"❌ An error occurred while processing your question: {str(e)}"
        )

@app.action("feedback_helpful")
def handle_helpful_feedback(ack, body, client):
    """Handle positive feedback"""
    ack()
    
    try:
        user_id = body['user']['id']
        message_ts = body['message']['ts']
        
        # Log feedback
        requests.post(
            f"{API_BASE_URL}/feedback",
            json={
                "answer_id": message_ts,
                "user_id": user_id,
                "type": "thumbs_up",
                "platform": "SLACK",
                "comment": ""
            },
            timeout=5
        )
        
        # Update message to show feedback received
        client.reactions_add(
            channel=body['channel']['id'],
            timestamp=message_ts,
            name="+1"
        )
        
    except Exception as e:
        logger.error(f"Error handling helpful feedback: {str(e)}")

@app.action("feedback_not_helpful")
def handle_not_helpful_feedback(ack, body, client):
    """Handle negative feedback"""
    ack()
    
    try:
        user_id = body['user']['id']
        message_ts = body['message']['ts']

        print("message_ts "  + message_ts)
        
        # Log feedback
        requests.post(
            f"{API_BASE_URL}/feedback",
            json={
                "answer_id": message_ts,
                "user_id": user_id,
                "type": "thumbs_down",
                "platform": "SLACK",
                "comment": "",
            },
            timeout=5
        )
        
        # Update message to show feedback received
        client.reactions_add(
            channel=body['channel']['id'],
            timestamp=message_ts,
            name="-1"
        )
        
    except Exception as e:
        logger.error(f"Error handling not helpful feedback: {str(e)}")

@app.event("app_mention")
def handle_mention(event, say, client):
    """Handle when bot is mentioned"""
    text = event['text']
    user_id = event['user']
    
    # Remove bot mention from text
    question = text.split('>', 1)[-1].strip()
    
    if not question:
        say("Hi! Ask me a question about the company documents. For example: `@bot How often is the company policy reviewed and updated?`")
        return
    
    # Process as a query
    result = query_handler.query(question, user_id)
    message = format_answer_message(result)
    
    say(thread_ts=event['ts'], **message)

@app.command("/help")
def handle_help_command(ack, say):
    """Show help message"""
    ack()
    
    help_text = """
*RAG Knowledge Bot - Help*

*Commands:*
• `/ask <question>` - Ask a question about company documents
• `/help` - Show this help message

*Examples:*
• `/ask How often is the company policy reviewed and updated?`

*Features:*
• Natural language queries
• Source citations
• Confidence scores
• Feedback buttons

*Tips:*
• Be specific in your questions
• Use complete sentences for best results
• Check the sources for more details
"""
    
    say(help_text)

@app.event("message")
def handle_message_events(body, logger):
    """Log message events (for monitoring)"""
    logger.debug(f"Message event: {body}")

if __name__ == "__main__":
    # Start the bot using Socket Mode
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    
    logger.info("RAG Slackbot is running!")
    handler.start()