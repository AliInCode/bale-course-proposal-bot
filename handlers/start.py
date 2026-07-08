from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

from config import SUPER_ADMIN_IDS
from database import is_admin
from keyboards import start_kb, REMOVE
from states import States


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    uid = update.effective_user.id
    name = update.effective_user.first_name or "کاربر"

    if uid in SUPER_ADMIN_IDS:
        from handlers.superadmin import send_super_menu
        await send_super_menu(update, ctx)
        return States.SUPER_MENU

    if is_admin(uid):
        from handlers.admin import send_admin_menu
        await send_admin_menu(update, ctx)
        return States.ADMIN_MENU

    await update.message.reply_text(
    f"سلام {name}! 👋\n\nبه دانشگاه ملی مهارت امام محمد باقر(ع) ساری خوش آمدید.\n\nلطفاً نام و نام‌خانوادگی خود را وارد کنید:",
    reply_markup=start_kb(),
)
    return States.PROF_NAME


async def cmd_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """دکمه ری‌استارت — از هر مرحله‌ای، کاربر را به ابتدای مسیر نقش خودش برمی‌گرداند."""
    await update.message.reply_text("🔄 ری‌استارت شد.")
    return await cmd_start(update, ctx)


async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"آیدی عددی شما:\n`{uid}`", parse_mode="Markdown")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "عملیات لغو شد. برای شروع مجدد /start را بزنید.",
        reply_markup=REMOVE,
    )
    return ConversationHandler.END


async def cancel_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات از طریق دکمه شیشه‌ای «❌ انصراف» در پرسش‌های استاد."""
    query = update.callback_query
    await query.answer()
    ctx.user_data.clear()
    await query.edit_message_text("عملیات لغو شد. برای شروع مجدد /start را بزنید.")
    return ConversationHandler.END
