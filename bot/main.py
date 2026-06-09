"""Bot entrypoint. Run with: python -m bot.main"""
import asyncio
import logging
import warnings

from telegram.warnings import PTBUserWarning
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from . import database as db
from . import handlers
from .config import get_settings


async def _post_init(application: Application) -> None:
    """Initialise the database once the bot is starting up."""
    await db.init_db()


def build_application() -> Application:
    settings = get_settings()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    # Quiet down the very chatty HTTP client logger.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # The /new conversation intentionally mixes text steps with a callback
    # confirm button; silence the (harmless) per_message advisory.
    warnings.filterwarnings("ignore", message="If 'per_message=False'", category=PTBUserWarning)

    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Copy .env.example to .env and add your token from @BotFather."
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .build()
    )

    # /new — step-by-step conversation
    conversation = ConversationHandler(
        entry_points=[CommandHandler("new", handlers.new_start)],
        states={
            handlers.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_name)],
            handlers.CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_contact)],
            handlers.MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.new_message)],
            handlers.CONFIRM: [CallbackQueryHandler(handlers.new_confirm, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(conversation)
    application.add_handler(CommandHandler("leads", handlers.leads_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    application.add_handler(CallbackQueryHandler(handlers.status_callback, pattern=r"^status:"))
    application.add_error_handler(handlers.error_handler)

    return application


def main() -> None:
    # Python 3.14 no longer auto-creates an event loop in the main thread,
    # while python-telegram-bot's run_polling() expects one to exist.
    # Create and register a fresh loop explicitly (safe on Python 3.11–3.14).
    asyncio.set_event_loop(asyncio.new_event_loop())

    application = build_application()
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
