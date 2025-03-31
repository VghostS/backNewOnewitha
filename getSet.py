from flask import Flask, request, jsonify
import os

app = Flask(__name__)
bot = os.getenv('BOT_TOKEN')

# Endpoint to get a default message
@app.route('/get', methods=['GET'])
def get_message():
    return jsonify({'message': 'Hello !'})

# Endpoint to set a custom message with the user's name
@app.route('/set', methods=['POST'])
def set_message():
    data = request.json
    name = data.get('name', 'there')
    return jsonify({'message': f'Hello {name}'})

# Telegram bot handler for /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the bot!")

if __name__ == '__main__':
    app.run(port=5000)