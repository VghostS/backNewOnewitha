from flask import Flask, request, jsonify
import os
import telebot

app = Flask(__name__)
bot_token = os.getenv('BOT_TOKEN')

if bot_token is None:
    raise ValueError("No BOT_TOKEN found in environment variables")

bot = telebot.TeleBot(bot_token)

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
    app.run(port=5000, host='0.0.0.0')