import datetime
import os
import logging
import traceback
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    PreCheckoutQueryHandler,
    CallbackContext
)

from config import ITEMS, MESSAGES

from flask import Flask
import asyncio
import json


# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store statistics
STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int),
    'refunds': defaultdict(int)
}

async def oneflask_purchase(update: Update, context: CallbackContext) -> None:
    """Direct purchase handler for OneFlask."""
    item_id = 'flask_one'  # Assuming 'oneflask' is a key in your ITEMS dictionary
    await update.message.reply_text(
        "You are buying one flask for one star!")

    if item_id not in ITEMS:
        await update.message.reply_text("Sorry, this item is currently unavailable.")
        return

    item = ITEMS[item_id]

    # Create a single confirmation button for purchase
    keyboard = [
        [InlineKeyboardButton(
            f"Confirm Purchase: {item['name']} - {item['price']} ⭐",
            callback_data=item_id
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Item: {item['name']}\n"
        f"Description: {item['description']}\n"
        f"Price: {item['price']} ⭐\n\n"
        "Click the button below to purchase:",
        reply_markup=reply_markup
    )


async def start(update: Update, context: CallbackContext) -> None:
     await update.message.reply_text(
        "Click the button below to play The Last Strip!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎮 Launch The Last Strip",
                web_app=WebAppInfo(url="https://vkss.itch.io/tls")
            )]
        ])
    )


async def shop(update: Update, context: CallbackContext) -> None:
    keyboard = []
    for item_id, item in ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - {item['price']} ⭐",
            callback_data=item_id
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        MESSAGES['welcome'],
        reply_markup=reply_markup
    )


async def play_game(update: Update, context: CallbackContext) -> None:
    """Handle /playgame command to open game as a Mini App."""
    await update.message.reply_text(
        "Click the button below to play The Last Strip!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🎮 Launch The Last Strip",
                web_app=WebAppInfo(url="https://vkss.itch.io/tls")
            )]
        ])
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command - show help information."""
    await update.message.reply_text(
        MESSAGES['help'],
        parse_mode='Markdown'
    )


async def refund_command(update: Update, context: CallbackContext) -> None:
    """Handle /refund command - process refund requests."""
    if not context.args:
        await update.message.reply_text(
            MESSAGES['refund_usage']
        )
        return

    try:
        charge_id = context.args[0]
        user_id = update.effective_user.id

        # Call the refund API
        success = await context.bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id
        )

        if success:
            STATS['refunds'][str(user_id)] += 1
            await update.message.reply_text(MESSAGES['refund_success'])
        else:
            await update.message.reply_text(MESSAGES['refund_failed'])

    except Exception as e:
        error_text = f"Error type: {type(e).__name__}\n"
        error_text += f"Error message: {str(e)}\n"
        error_text += f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
        logger.error(error_text)

        await update.message.reply_text(
            f"❌ Sorry, there was an error processing your refund:\n"
            f"Error: {type(e).__name__} - {str(e)}\n\n"
            "Please make sure you provided the correct transaction ID and try again."
        )


async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle button clicks for item selection."""
    query = update.callback_query
    if not query or not query.message:
        return

    try:
        await query.answer()

        item_id = query.data
        item = ITEMS[item_id]

        # Make sure message exists before trying to use it
        if not isinstance(query.message, Message):
            return

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=item['name'],
            description=item['description'],
            payload=item_id,
            provider_token="",  # Empty for digital goods
            currency="XTR",  # Telegram Stars currency code
            prices=[LabeledPrice(item['name'], int(item['price']))],
            start_parameter="start_parameter"
        )

    except Exception as e:
        logger.error(f"Error in button_handler: {str(e)}")
        if query and query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "Sorry, something went wrong while processing your request."
            )


async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """Handle pre-checkout queries."""
    query = update.pre_checkout_query
    if query.invoice_payload in ITEMS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong...")


async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Handle successful payments."""
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    item_id, player_id = payload.split('_')  # Split the payload to get both item_id and player_id
    item = ITEMS[item_id]
    user_id = update.effective_user.id

    # Update statistics
    STATS['purchases'][str(user_id)] += 1

    logger.info(
        f"Successful payment from user {user_id} "
        f"for item {item_id} (charge_id: {payment.telegram_payment_charge_id}, player_id: {player_id})"
    )

    # Store the purchase data in a format accessible to your game
    purchase_data = {
        'player_id': player_id,
        'item_id': item_id,
        'purchase_time': str(datetime.datetime.now()),
        'secret': item['secret']
    }

    # You might want to store this in a database or temporary storage
    # For this example, we'll store it in a file
    with open(f'purchases/{payment.telegram_payment_charge_id}.json', 'w') as f:
        json.dump(purchase_data, f)

    await update.message.reply_text(
        f"Thank you for your purchase! 🎉\n\n"
        f"Here's your secret code for {item['name']}:\n"
        f"`{item['secret']}`\n\n"
        f"To get a refund, use this command:\n"
        f"`/refund {payment.telegram_payment_charge_id}`\n\n"
        "Save this message to request a refund later if needed.",
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """Start the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("refund", refund_command))
        application.add_handler(CommandHandler("playgame", play_game))  # New handler for /playgame
        application.add_handler(CommandHandler("shop", shop))
        application.add_handler(CommandHandler("oneflask", oneflask_purchase))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Bot started")
        application.run_polling()

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")


if __name__ == '__main__':
    main()