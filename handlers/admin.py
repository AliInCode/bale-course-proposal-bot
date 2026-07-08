import io
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import get_all_professors, delete_professor, delete_all_professors
from excel_export import build_excel
from keyboards import admin_menu_kb, cancel_kb, confirm_clear_kb, back_kb, BACK_LABEL, RESTART_LABEL, REMOVE
from states import States
from utils import to_en_digits
from handlers.start import cmd_restart


async def send_admin_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ خوش آمدید، ادمین!", reply_markup=admin_menu_kb())


async def admin_menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == RESTART_LABEL:
        return await cmd_restart(update, ctx)

    if text == "📋 مشاهده رکوردها":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی یافت نشد.")
            return States.ADMIN_MENU
        msg = "📋 *لیست اساتید ثبت‌شده:*\n\n"
        for i, r in enumerate(rows, 1):
            msg += (
                f"*{i}. {r['full_name']}*  (شناسه: `{r['id']}`)\n"
                f"   کد ملی: {r['national_id']} | تلفن: {r['phone']}\n"
                f"   مدرک/رشته: {r['degree']} | بازنشسته: {r['retired']}\n"
                f"   گروه: {r['department']}\n"
                f"   روزها: {r['days']}\n"
                f"   ساعت‌ها: {r['hours']}\n"
                f"   دروس: {r['courses']}\n\n"
            )
        for chunk in _split(msg):
            await update.message.reply_text(chunk, parse_mode="Markdown")
        return States.ADMIN_MENU

    if text == "📥 خروجی اکسل":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای خروجی اکسل وجود ندارد.")
            return States.ADMIN_MENU
        data = build_excel()
        await update.message.reply_document(
            document=io.BytesIO(data),
            filename="professors.xlsx",
            caption="📊 فایل اکسل اساتید",
        )
        return States.ADMIN_MENU

    if text == "🗑 حذف رکورد":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای حذف وجود ندارد.")
            return States.ADMIN_MENU
        lst = "\n".join(f"• {r['full_name']}  —  شناسه: `{r['id']}`" for r in rows)
        await update.message.reply_text(
            f"*لیست رکوردها:*\n{lst}\n\nشناسه رکورد مورد نظر برای حذف را وارد کنید:",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return States.ADMIN_DEL_RECORD

    if text == "🧹 پاکسازی همه رکوردها":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای پاکسازی وجود ندارد.")
            return States.ADMIN_MENU
        await update.message.reply_text(
            f"⚠️ آیا مطمئنید؟ همه {len(rows)} رکورد برای همیشه حذف خواهند شد و قابل بازگشت نیست!",
            reply_markup=confirm_clear_kb(),
        )
        return States.ADMIN_CLEAR_CONFIRM

    if text == "❌ خروج":
        await update.message.reply_text("خداحافظ!", reply_markup=REMOVE)
        return ConversationHandler.END

    return States.ADMIN_MENU


async def admin_clear_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BACK_LABEL:
        await send_admin_menu(update, ctx)
        return States.ADMIN_MENU
    if text == "✅ بله، همه رکوردها حذف شود":
        count = delete_all_professors()
        await update.message.reply_text(
            f"🧹 {count} رکورد حذف شد.",
            reply_markup=admin_menu_kb(),
        )
    else:
        await update.message.reply_text("انصراف داده شد.", reply_markup=admin_menu_kb())
    return States.ADMIN_MENU


async def admin_del_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_LABEL:
        await send_admin_menu(update, ctx)
        return States.ADMIN_MENU
    rid_str = to_en_digits(update.message.text.strip())
    if not rid_str.isdigit():
        await update.message.reply_text("⚠️ شناسه باید عدد باشد:", reply_markup=back_kb())
        return States.ADMIN_DEL_RECORD
    ok = delete_professor(int(rid_str))
    if ok:
        await update.message.reply_text(
            f"✅ رکورد با شناسه `{rid_str}` حذف شد.",
            parse_mode="Markdown",
            reply_markup=admin_menu_kb(),
        )
    else:
        await update.message.reply_text(
            "⚠️ رکوردی با این شناسه یافت نشد.",
            reply_markup=admin_menu_kb(),
        )
    return States.ADMIN_MENU


def _split(text: str, size=4000):
    parts = []
    while len(text) > size:
        idx = text.rfind("\n", 0, size)
        if idx == -1:
            idx = size
        parts.append(text[:idx])
        text = text[idx:]
    parts.append(text)
    return parts
