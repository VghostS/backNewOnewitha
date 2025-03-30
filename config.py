from typing import Dict, Any

ITEMS: Dict[str, Dict[str, Any]] = {
    'flask_one': {
        'name': '1 Flask',
        'price': 1,
        'description': 'One Flask for 1 Star',
        'secret': 'FLASKONE'
    },
    'flask_5': {
        'name': '5 Flasks',
        'price': 2,
        'description': '5 Flasks for 2 Stars',
        'secret': 'FLASKFIVE'
    },
    'flask_10': {
        'name': '10 Flasks',
        'price': 5,
        'description': '10 Flasks for 5 Stars',
        'secret': 'FLASKTEN'
    },
    'flask_50': {
            'name': '50 Flasks',
            'price': 20,
            'description': '50 Flasks for 20 Stars',
            'secret': 'FLASKFIFTY'
        }
}

MESSAGES = {
    'welcome': (
        "Welcome to the Last Strip Store\n"
        "Select an item to purchase with Telegram Stars and Play the Evolve Game and Upgrade your Avatar"
    ),
    'help': (
        "🛍 *Digital Store Bot Help*\n\n"
        "Commands:\n"
        "/start - View available items\n"
        "/help - Show this help message\n"
        "/refund - Request a refund (requires transaction ID)\n\n"
        "How to use:\n"
        "1. Use /start to see available items\n"
        "2. Click on an item to purchase\n"
        "3. Pay with Stars\n"
        "4. Receive your secret code\n"
        "5. Use /refund to get a refund if needed"
    ),
    'refund_success': (
        "✅ Refund processed successfully!\n"
        "The Stars have been returned to your balance."
    ),
    'refund_failed': (
        "❌ Refund could not be processed.\n"
        "Please try again later or contact support."
    ),
    'refund_usage': (
        "Please provide the transaction ID after the /refund command.\n"
        "Example: `/refund YOUR_TRANSACTION_ID`"
    )
}