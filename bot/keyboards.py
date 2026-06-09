"""Inline keyboards."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def status_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    """Buttons to change a lead's status directly from the chat."""
    buttons = [
        [
            InlineKeyboardButton("🆕 New", callback_data=f"status:{lead_id}:new"),
            InlineKeyboardButton("⏳ In progress", callback_data=f"status:{lead_id}:in_progress"),
            InlineKeyboardButton("✅ Done", callback_data=f"status:{lead_id}:done"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm / cancel buttons for the /new conversation."""
    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm:no"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
