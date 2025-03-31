from flask import Flask, request, jsonify
from telegram import Bot, LabeledPrice
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='flask_server.log'
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)


@app.route('/create_invoice', methods=['POST', 'OPTIONS'])
async def create_invoice():
    try:
        # Log incoming request
        logger.info(f"Received request: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")

        # Handle CORS preflight request
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
            return ('', 204, headers)

        # Log request body
        logger.info(f"Request body: {request.data}")

        data = request.json
        logger.info(f"Parsed JSON data: {data}")

        player_id = data.get('playerId')
        item_id = data.get('itemId')
        chat_id = data.get('chatId')

        logger.info(f"Extracted data - player_id: {player_id}, item_id: {item_id}, chat_id: {chat_id}")

        if not all([player_id, item_id, chat_id]):
            error_msg = {'error': 'Missing required parameters'}
            logger.error(f"Validation error: {error_msg}")
            return jsonify(error_msg), 400

        from config import ITEMS
        item = ITEMS.get(item_id)

        if not item:
            error_msg = {'error': 'Invalid item ID'}
            logger.error(f"Invalid item error: {error_msg}")
            return jsonify(error_msg), 400

        # Create a unique payload that includes both item_id and player_id
        unique_payload = f"{item_id}_{player_id}"

        logger.info(f"Sending invoice with payload: {unique_payload}")

        invoice = await bot.send_invoice(
            chat_id=chat_id,
            title=item['name'],
            description=item['description'],
            payload=unique_payload,
            provider_token="",  # Empty for digital goods
            currency="XTR",  # Telegram Stars currency code
            prices=[LabeledPrice(item['name'], int(item['price']))],
            start_parameter="start_parameter"
        )

        response = jsonify({
            'success': True,
            'invoice_message_id': invoice.message_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        logger.info(f"Successfully created invoice: {invoice.message_id}")
        return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'timestamp': datetime.utcnow().isoformat()}), 500


if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)