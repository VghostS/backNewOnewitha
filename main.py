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


# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
STARS_PROVIDER_TOKEN = "645982161:TEST:2477"  # Telegram Stars test provider token

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
    """Direct purchase handler for OneFlask - goes directly to confirmation."""
    item_id = 'flask_one'
    item = ITEMS[item_id]

    # Use the chat ID directly from the update
    chat_id = update.effective_chat.id

    # Get the user ID for logging
    user_id = update.effective_user.id if update.effective_user else 'Unknown'

    try:
        # Create a unique payload with more robust identification
        payload = f"{item_id}_{user_id}_{chat_id}"
        logger.info(f"Creating invoice with payload: {payload}")

        # Send invoice with detailed logging
        invoice = await context.bot.send_invoice(
            chat_id=chat_id,
            title=item['name'],
            description=item['description'],
            payload=payload,
            provider_token=STARS_PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(item['name'], item['price'])],
            start_parameter="oneflask_purchase"
        )

        logger.info(f"Invoice sent to user {user_id} in chat {chat_id}")

    except Exception as e:
        logger.error(f"Error in oneflask_purchase: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        await update.message.reply_text(
            f"Sorry, there was an error processing your purchase:\n{str(e)}"
        )


async def start(update: Update, context: CallbackContext) -> None:
    """Handle deep links for purchases."""
    # Check if there's a deep link parameter
    if context.args and context.args[0].startswith('purchase_flask_'):
        try:
            # Extract player ID from the deep link
            player_id = int(context.args[0].split('_')[-1])

            # Directly send invoice with player ID in payload
            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title='1 Flask',
                description=f'Flask purchase for Player {player_id}',
                payload=f'flask_one_{player_id}',
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice('1 Flask', 1)],
                start_parameter="start_parameter"
            )
        except Exception as e:
            logger.error(f"Error processing deep link purchase: {str(e)}")
            await update.message.reply_text("Sorry, there was an error processing your purchase.")


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
    """Comprehensive pre-checkout query handling with detailed logging."""
    query = update.pre_checkout_query

    try:
        # Log all available information
        logger.debug("Pre-Checkout Query Details:")
        logger.debug(f"Payload: {query.invoice_payload}")
        logger.debug(f"Total Amount: {query.total_amount}")
        logger.debug(f"Currency: {query.currency}")

        # Payload validation with more robust checks
        payload_parts = query.invoice_payload.split('_')

        # Detailed logging of payload parts
        logger.debug(f"Payload Parts: {payload_parts}")
        logger.debug(f"Number of Payload Parts: {len(payload_parts)}")

        # Check if payload has at least 3 parts and first part is a valid item
        if (len(payload_parts) >= 3 and
                payload_parts[0] in ITEMS and
                payload_parts[0] == 'flask_one'):  # Ensure it's specifically the flask item

            # Additional validation for price
            item = ITEMS[payload_parts[0]]
            if query.total_amount == item['price']:
                logger.info("Pre-checkout validation successful")
                await query.answer(ok=True)
                return

        # If validation fails
        logger.warning("Pre-checkout validation failed")
        await query.answer(
            ok=False,
            error_message="Invalid purchase details. Please try again."
        )

    except Exception as e:
        logger.error(f"Pre-checkout error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        await query.answer(
            ok=False,
            error_message=f"System error: {str(e)}"
        )


async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Handle successful payments with player-specific logic."""
    payment = update.message.successful_payment

    # Parse payload to get item and player ID
    payload_parts = payment.invoice_payload.split('_')
    item_id = payload_parts[0]
    player_id = int(payload_parts[1])

    item = ITEMS[item_id]
    user_id = update.effective_user.id

    # Update statistics
    STATS['purchases'][str(user_id)] += 1

    logger.info(
        f"Successful payment from user {user_id} "
        f"for item {item_id} for Player {player_id} "
        f"(charge_id: {payment.telegram_payment_charge_id})"
    )

    await update.message.reply_text(
        f"Thank you for your purchase! 🎉\n"
        f"Player {player_id} has received: {item['name']}\n\n"
        f"To get a refund, use this command:\n"
        f"`/refund {payment.telegram_payment_charge_id}`",
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