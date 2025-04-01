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
# Add these imports at the top
from urllib.parse import urlencode
GAME_URL = "https://vkss.itch.io/tls"
BOT_USERNAME = os.getenv('theLastStrip_bot')


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


# Add this new function to handle deep links
async def handle_deep_link(update: Update, context: CallbackContext) -> None:
    """Handle deep linking for game purchases."""
    if not update.message or not update.message.text:
        return

    args = context.args
    if not args:
        # No deep link parameter, just start the game
        await start(update, context)
        return

    # Handle deep link parameters
    command = args[0]

    if command.startswith('buy_'):
        # Extract item_id from deep link
        item_id = command.replace('buy_', '')
        if item_id in ITEMS:
            # Process the purchase directly
            item = ITEMS[item_id]
            await context.bot.send_invoice(
                chat_id=update.message.chat_id,
                title=item['name'],
                description=item['description'],
                payload=item_id,
                provider_token="",  # Empty for digital goods
                currency="XTR",  # Telegram Stars currency code
                prices=[LabeledPrice(item['name'], int(item['price']))],
                start_parameter=f"buy_{item_id}"
            )
        else:
            await update.message.reply_text("Invalid item requested.")
    else:
        await start(update, context)


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


# Modify your successful_payment_callback function to handle game returns
async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Handle successful payments with game return URL."""
    payment = update.message.successful_payment
    item_id = payment.invoice_payload
    item = ITEMS[item_id]
    user_id = update.effective_user.id

    # Update statistics
    STATS['purchases'][str(user_id)] += 1

    # Create return URL with purchase data
    game_params = {
        'item_id': item_id,
        'secret': item['secret'],
        'user_id': str(user_id),
        'transaction_id': payment.telegram_payment_charge_id
    }
    return_url = f"{GAME_URL}?{urlencode(game_params)}"

    # Create a button to return to the game
    keyboard = [
        [InlineKeyboardButton(
            "Return to Game",
            web_app=WebAppInfo(url=return_url)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Thank you for your purchase! 🎉\n\n"
        f"Your {item['name']} has been activated.\n\n"
        f"Transaction ID: `{payment.telegram_payment_charge_id}`\n"
        "Click below to return to the game:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")


# Modify your main() function to update the handlers
def main() -> None:
    """Start the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Update the start command to use the deep link handler
        application.add_handler(CommandHandler("start", handle_deep_link))

        # Add your other existing handlers
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("refund", refund_command))
        application.add_handler(CommandHandler("playgame", play_game))
        application.add_handler(CommandHandler("shop", shop))
        application.add_handler(CommandHandler("oneflask", oneflask_purchase))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
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