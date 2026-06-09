"""Telegram command, conversation and callback handlers."""
import html
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from . import database as db
from .keyboards import confirm_keyboard, status_keyboard

logger = logging.getLogger(__name__)

# Conversation states for /new
NAME, CONTACT, MESSAGE, CONFIRM = range(4)

STATUS_LABELS = {
    "new": "🆕 New",
    "in_progress": "⏳ In progress",
    "done": "✅ Done",
}


def _esc(value: str) -> str:
    return html.escape(str(value))


def _format_lead(lead: dict) -> str:
    status = STATUS_LABELS.get(lead["status"], lead["status"])
    return (
        f"<b>#{lead['id']}</b> — {status}\n"
        f"👤 {_esc(lead['name'])}\n"
        f"📞 {_esc(lead['contact'])}\n"
        f"💬 {_esc(lead['message'])}\n"
        f"🌐 {_esc(lead['source'])}"
    )


# --------------------------------------------------------------------------- #
# Basic commands
# --------------------------------------------------------------------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 <b>Mimi Leads Bot</b>\n\n"
        "I help manage incoming client leads.\n\n"
        "• /new — add a lead step by step\n"
        "• /leads — show recent leads\n"
        "• /stats — counts by status\n"
        "• /help — full command list",
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Available commands</b>\n"
        "/new — add a new lead (guided dialog)\n"
        "/leads — show the latest leads with status buttons\n"
        "/stats — summary counts by status\n"
        "/help — show this message\n"
        "/cancel — abort the current dialog",
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------- #
# /new — ConversationHandler: name -> contact -> message -> confirm
# --------------------------------------------------------------------------- #
async def new_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Let's add a new lead.\n\n"
        "<b>Step 1/3</b> — what is the client's name?\n"
        "Send /cancel at any time to abort.",
        parse_mode=ParseMode.HTML,
    )
    return NAME


async def new_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "<b>Step 2/3</b> — contact? (email or phone)",
        parse_mode=ParseMode.HTML,
    )
    return CONTACT


async def new_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text(
        "<b>Step 3/3</b> — describe the request / message.",
        parse_mode=ParseMode.HTML,
    )
    return MESSAGE


async def new_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["message"] = update.message.text.strip()
    data = context.user_data
    summary = (
        "<b>Please confirm the new lead:</b>\n\n"
        f"👤 {_esc(data['name'])}\n"
        f"📞 {_esc(data['contact'])}\n"
        f"💬 {_esc(data['message'])}"
    )
    await update.message.reply_text(
        summary, parse_mode=ParseMode.HTML, reply_markup=confirm_keyboard()
    )
    return CONFIRM


async def new_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":", 1)[1]

    if choice == "no":
        context.user_data.clear()
        await query.edit_message_text("❌ Cancelled. No lead was saved.")
        return ConversationHandler.END

    data = context.user_data
    lead_id = await db.add_lead(data["name"], data["contact"], data["message"])
    context.user_data.clear()
    await query.edit_message_text(f"✅ Lead #{lead_id} saved.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


# --------------------------------------------------------------------------- #
# /leads and status changes
# --------------------------------------------------------------------------- #
async def leads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    leads = await db.list_leads(limit=10)
    if not leads:
        await update.message.reply_text("No leads yet. Add one with /new.")
        return
    for lead in leads:
        await update.message.reply_text(
            _format_lead(lead),
            parse_mode=ParseMode.HTML,
            reply_markup=status_keyboard(lead["id"]),
        )


async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try:
        _, lead_id_str, new_status = query.data.split(":")
        lead_id = int(lead_id_str)
        await db.update_status(lead_id, new_status)
    except (ValueError, KeyError) as exc:
        logger.warning("Bad status callback %r: %s", query.data, exc)
        await query.answer("Could not update status.")
        return

    await query.answer(f"Status → {new_status}")
    lead = await db.get_lead(lead_id)
    if lead:
        await query.edit_message_text(
            _format_lead(lead),
            parse_mode=ParseMode.HTML,
            reply_markup=status_keyboard(lead_id),
        )


# --------------------------------------------------------------------------- #
# /stats
# --------------------------------------------------------------------------- #
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    counts = await db.stats()
    total = sum(counts.values())
    await update.message.reply_text(
        "<b>Leads summary</b>\n\n"
        f"🆕 New: {counts['new']}\n"
        f"⏳ In progress: {counts['in_progress']}\n"
        f"✅ Done: {counts['done']}\n"
        "— — —\n"
        f"Σ Total: {total}",
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------- #
# Error handler
# --------------------------------------------------------------------------- #
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
