from flask import Flask, request, jsonify
from telegram import Bot, LabeledPrice
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)


@app.route('/create_invoice', methods=['POST'])
async def create_invoice():
    try:
        data = request.json
        player_id = data.get('playerId')
        item_id = data.get('itemId')
        chat_id = data.get('chatId')

        if not all([player_id, item_id, chat_id]):
            return jsonify({'error': 'Missing required parameters'}), 400

        from config import ITEMS
        item = ITEMS.get(item_id)

        if not item:
            return jsonify({'error': 'Invalid item ID'}), 400

        # Create a unique payload that includes both item_id and player_id
        unique_payload = f"{item_id}_{player_id}"

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

        return jsonify({'success': True, 'invoice_message_id': invoice.message_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)