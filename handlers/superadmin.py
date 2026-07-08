import io
import re
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import add_admin, remove_admin, list_admins, get_all_professors, delete_professor, delete_all_professors
from excel_export import build_excel
from keyboards import (
    superadmin_menu_kb, cancel_kb, confirm_clear_kb, back_kb, BACK_LABEL, RESTART_LABEL,
    admins_multi_select_kb, REMOVE,
)
from states import States
from utils import to_en_digits
from handlers.start import cmd_restart


async def send_super_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ خوش آمدید، سوپرادمین!", reply_markup=superadmin_menu_kb())


async def super_menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == RESTART_LABEL:
        return await cmd_restart(update, ctx)

    if text == "📋 مشاهده رکوردها":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی وجود ندارد.")
            return States.SUPER_MENU
        msg = "📋 *لیست اساتید:*\n\n"
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
        return States.SUPER_MENU

    if text == "📥 خروجی اکسل":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای خروجی اکسل وجود ندارد.")
            return States.SUPER_MENU
        data = build_excel()
        await update.message.reply_document(
            document=io.BytesIO(data),
            filename="professors.xlsx",
            caption="📊 فایل اکسل اساتید",
        )
        return States.SUPER_MENU

    if text == "🗑 حذف رکورد":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای حذف وجود ندارد.")
            return States.SUPER_MENU
        lst = "\n".join(f"• {r['full_name']}  —  شناسه: `{r['id']}`" for r in rows)
        await update.message.reply_text(
            f"*لیست رکوردها:*\n{lst}\n\nشناسه رکورد مورد نظر برای حذف را وارد کنید:",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return States.SUPER_DEL_RECORD

    if text == "🧹 پاکسازی همه رکوردها":
        rows = get_all_professors()
        if not rows:
            await update.message.reply_text("هیچ رکوردی برای پاکسازی وجود ندارد.")
            return States.SUPER_MENU
        await update.message.reply_text(
            f"⚠️ آیا مطمئنید؟ همه {len(rows)} رکورد برای همیشه حذف خواهند شد و قابل بازگشت نیست!",
            reply_markup=confirm_clear_kb(),
        )
        return States.SUPER_CLEAR_CONFIRM

    if text == "➕ افزودن ادمین":
        await update.message.reply_text(
            "آیدی عددی کاربر موردنظر را وارد کنید:",
            reply_markup=back_kb(),
        )
        return States.SUPER_ADD_ADMIN_ID

    if text == "➖ حذف ادمین":
        admins = list_admins()
        if not admins:
            await update.message.reply_text("هیچ ادمینی ثبت نشده.")
            return States.SUPER_MENU
        ctx.user_data["selected_admin_ids"] = set()
        await update.message.reply_text(
            "ادمین‌هایی که می‌خواهید حذف کنید را انتخاب کنید، سپس «🗑 حذف انتخاب‌شده‌ها» را بزنید:",
            reply_markup=admins_multi_select_kb(admins, set()),
        )
        return States.SUPER_DEL_ADMIN

    if text == "👥 لیست ادمین‌ها":
        admins = list_admins()
        if not admins:
            await update.message.reply_text("هیچ ادمینی ثبت نشده.")
        else:
            lst = "\n".join(f"• {a['label']}  —  آیدی: `{a['user_id']}`" for a in admins)
            await update.message.reply_text(lst, parse_mode="Markdown")
        return States.SUPER_MENU

    if text == "❌ خروج":
        await update.message.reply_text("خداحافظ!", reply_markup=REMOVE)
        return ConversationHandler.END

    return States.SUPER_MENU


async def super_add_admin_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_LABEL:
        ctx.user_data.pop("new_admin_id", None)
        await send_super_menu(update, ctx)
        return States.SUPER_MENU
    uid_str = to_en_digits(update.message.text.strip())
    if not uid_str.lstrip("-").isdigit():
        await update.message.reply_text("⚠️ آیدی باید عدد باشد:", reply_markup=back_kb())
        return States.SUPER_ADD_ADMIN_ID
    ctx.user_data["new_admin_id"] = int(uid_str)
    await update.message.reply_text("یک برچسب (نام) برای این ادمین وارد کنید:", reply_markup=back_kb())
    return States.SUPER_ADD_ADMIN_LB


async def super_add_admin_label(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_LABEL:
        ctx.user_data.pop("new_admin_id", None)
        await send_super_menu(update, ctx)
        return States.SUPER_MENU
    label = update.message.text.strip()
    uid = ctx.user_data.pop("new_admin_id", None)
    if uid:
        add_admin(uid, label)
        await update.message.reply_text(
            f"✅ ادمین «{label}» با آیدی `{uid}` اضافه شد.",
            parse_mode="Markdown",
            reply_markup=superadmin_menu_kb(),
        )
    return States.SUPER_MENU


async def super_del_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    selected: set = ctx.user_data.get("selected_admin_ids", set())

    if text == BACK_LABEL:
        ctx.user_data.pop("selected_admin_ids", None)
        await send_super_menu(update, ctx)
        return States.SUPER_MENU

    admins = list_admins()
    if not admins:
        ctx.user_data.pop("selected_admin_ids", None)
        await update.message.reply_text("هیچ ادمینی ثبت نشده.", reply_markup=superadmin_menu_kb())
        return States.SUPER_MENU

    if text == "🗑 حذف انتخاب‌شده‌ها":
        if not selected:
            await update.message.reply_text(
                "⚠️ هیچ ادمینی انتخاب نکرده‌اید!",
                reply_markup=admins_multi_select_kb(admins, selected),
            )
            return States.SUPER_DEL_ADMIN
        removed_labels = [a["label"] for a in admins if a["user_id"] in selected]
        for uid in selected:
            remove_admin(uid)
        ctx.user_data.pop("selected_admin_ids", None)
        await update.message.reply_text(
            f"✅ {len(removed_labels)} ادمین حذف شد:\n" + "\n".join(f"• {l}" for l in removed_labels),
            reply_markup=superadmin_menu_kb(),
        )
        return States.SUPER_MENU

    # تشخیص آیدی از روی متن دکمه به فرم «✅ label (id)» یا «◻️ label (id)»
    m = re.search(r"\((-?\d+)\)\s*$", text)
    if m:
        uid = int(m.group(1))
        if any(a["user_id"] == uid for a in admins):
            selected.discard(uid) if uid in selected else selected.add(uid)
            ctx.user_data["selected_admin_ids"] = selected

    await update.message.reply_text(
        f"تعداد انتخاب‌شده: {len(selected)}",
        reply_markup=admins_multi_select_kb(admins, selected),
    )
    return States.SUPER_DEL_ADMIN


async def super_del_record(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_LABEL:
        await send_super_menu(update, ctx)
        return States.SUPER_MENU
    rid_str = to_en_digits(update.message.text.strip())
    if not rid_str.isdigit():
        await update.message.reply_text("⚠️ شناسه باید عدد باشد:", reply_markup=back_kb())
        return States.SUPER_DEL_RECORD
    ok = delete_professor(int(rid_str))
    if ok:
        await update.message.reply_text(
            f"✅ رکورد با شناسه `{rid_str}` حذف شد.",
            parse_mode="Markdown",
            reply_markup=superadmin_menu_kb(),
        )
    else:
        await update.message.reply_text(
            "⚠️ رکوردی با این شناسه یافت نشد.",
            reply_markup=superadmin_menu_kb(),
        )
    return States.SUPER_MENU


async def super_clear_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BACK_LABEL:
        await send_super_menu(update, ctx)
        return States.SUPER_MENU
    if text == "✅ بله، همه رکوردها حذف شود":
        count = delete_all_professors()
        await update.message.reply_text(
            f"🧹 {count} رکورد حذف شد.",
            reply_markup=superadmin_menu_kb(),
        )
    else:
        await update.message.reply_text("انصراف داده شد.", reply_markup=superadmin_menu_kb())
    return States.SUPER_MENU


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
