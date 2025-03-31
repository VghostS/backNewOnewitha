from flask import Flask, request, jsonify
from telegram import Bot, LabeledPrice
import os
from dotenv import load_dotenv
import logging
import asyncio
from quart import Quart  # We'll use Quart instead of Flask for better async support

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='server.log'
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)

app = Quart(__name__)  # Using Quart instead of Flask


@app.route('/create_invoice', methods=['POST', 'OPTIONS'])
async def create_invoice():
    try:
        logger.info("Received request to create_invoice")

        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
            return ('', 204, headers)

        # Get JSON data
        data = await request.get_json()
        logger.info(f"Received data: {data}")

        player_id = data.get('playerId')
        item_id = data.get('itemId')
        chat_id = data.get('chatId')

        logger.info(f"Processing request for player_id: {player_id}, item_id: {item_id}, chat_id: {chat_id}")

        if not all([player_id, item_id, chat_id]):
            return jsonify({'error': 'Missing required parameters'}), 400

        from config import ITEMS
        item = ITEMS.get(item_id)

        if not item:
            return jsonify({'error': 'Invalid item ID'}), 400

        unique_payload = f"{item_id}_{player_id}"

        try:
            invoice = await bot.send_invoice(
                chat_id=int(chat_id),  # Ensure chat_id is an integer
                title=item['name'],
                description=item['description'],
                payload=unique_payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(item['name'], int(item['price']))],
                start_parameter="start_parameter"
            )

            response = jsonify({
                'success': True,
                'invoice_message_id': invoice.message_id
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        except Exception as e:
            logger.error(f"Telegram API error: {str(e)}")
            return jsonify({'error': f'Telegram API error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True)