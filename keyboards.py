from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import DAYS

REMOVE = ReplyKeyboardRemove()
BACK_LABEL = "🔙 بازگشت به منوی اصلی"
RESTART_LABEL = "🔄 ری‌استارت"


def _kb(rows, resize=True, one_time=False):
    return ReplyKeyboardMarkup(rows, resize_keyboard=resize,
                               one_time_keyboard=one_time)


def cancel_kb():
    return _kb([["❌ انصراف"]])


def start_kb():
    """کیبورد اولین پیام به استاد — شامل دکمه ری‌استارت در کنار انصراف"""
    return _kb([["❌ انصراف"], [RESTART_LABEL]])


def back_kb():
    """دکمه بازگشت به منوی اصلی — برای مراحل ادمین/سوپرادمین"""
    return _kb([[BACK_LABEL]])


def multi_select_kb(options: list, selected: set, done_label="✅ تأیید"):
    rows = []
    for opt in options:
        tick = "✅ " if opt in selected else "◻️ "
        rows.append([tick + opt])
    rows.append([done_label])
    rows.append(["❌ انصراف"])
    return _kb(rows)


def days_kb(selected: set):
    return multi_select_kb(DAYS, selected, done_label="✅ تأیید")


def admins_multi_select_kb(admins, selected_ids: set):
    """کیبورد انتخاب چندگانه ادمین‌ها برای حذف. admins: لیست رکوردهای دیتابیس."""
    rows = []
    for a in admins:
        tick = "✅ " if a["user_id"] in selected_ids else "◻️ "
        rows.append([f"{tick}{a['label']} ({a['user_id']})"])
    rows.append(["🗑 حذف انتخاب‌شده‌ها"])
    rows.append([BACK_LABEL])
    return _kb(rows)


# ── منوی ادمین / سوپرادمین ──────────────────────────────────────────────────
def admin_menu_kb():
    return _kb([["📋 مشاهده رکوردها", "📥 خروجی اکسل"], ["🗑 حذف رکورد", "🧹 پاکسازی همه رکوردها"], [RESTART_LABEL], ["❌ خروج"]])


def superadmin_menu_kb():
    return _kb([
        ["📋 مشاهده رکوردها", "📥 خروجی اکسل"],
        ["🗑 حذف رکورد", "🧹 پاکسازی همه رکوردها"],
        ["➕ افزودن ادمین", "➖ حذف ادمین", "👥 لیست ادمین‌ها"],
        [RESTART_LABEL],
        ["❌ خروج"],
    ])


def confirm_clear_kb():
    return _kb([["✅ بله، همه رکوردها حذف شود", "❌ انصراف"], [BACK_LABEL]])


def department_kb(selected: str = ""):
    """Single select — فقط یکی انتخاب می‌شه"""
    from config import DEPARTMENTS
    rows = []
    for dept in DEPARTMENTS:
        tick = "✅ " if dept == selected else "◻️ "
        rows.append([tick + dept])
    if selected:
        rows.append(["✅ تأیید"])
    rows.append(["❌ انصراف"])
    return _kb(rows)


def notice_kb():
    return _kb([["✅ خوندم"], ["❌ انصراف"]])


def yes_no_kb():
    from config import RETIRED_YES, RETIRED_NO
    return _kb([[RETIRED_YES, RETIRED_NO], ["❌ انصراف"]])


# ── دکمه‌های شیشه‌ای (Inline) برای سوالات استاد ─────────────────────────────
# این‌ها به‌جای کیبورد معمولی، دکمه‌های زیر پیام (inline keyboard) نمایش می‌دهند
# و با callback_data کار می‌کنند (نیاز به CallbackQueryHandler دارند).

def _chunk(buttons, per_row=2):
    """دکمه‌ها را per_row تایی در هر ردیف می‌چیند."""
    return [buttons[i:i + per_row] for i in range(0, len(buttons), per_row)]


def yes_no_inline_kb():
    from config import RETIRED_YES, RETIRED_NO
    rows = [
        [
            InlineKeyboardButton(RETIRED_YES, callback_data="retired:yes"),
            InlineKeyboardButton(RETIRED_NO, callback_data="retired:no"),
        ],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(rows)


def department_inline_kb(selected: str = ""):
    """دکمه‌های شیشه‌ای گروه آموزشی — انتخاب تک‌گزینه‌ای."""
    from config import DEPARTMENTS
    buttons = []
    for i, dept in enumerate(DEPARTMENTS):
        tick = "✅ " if dept == selected else ""
        buttons.append(InlineKeyboardButton(tick + dept, callback_data=f"dept:{i}"))
    rows = _chunk(buttons, per_row=2)
    if selected:
        rows.append([InlineKeyboardButton("✅ تأیید", callback_data="dept:ok")])
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def notice_inline_kb():
    rows = [
        [InlineKeyboardButton("✅ خوندم", callback_data="notice:ack")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(rows)


def days_inline_kb(done_days: set):
    """دکمه‌های شیشه‌ای روزهای هفته. روزهایی که ساعتشان قبلاً ثبت شده تیک می‌خورند."""
    buttons = []
    for i, day in enumerate(DAYS):
        tick = "✅ " if day in done_days else "◻️ "
        buttons.append(InlineKeyboardButton(tick + day, callback_data=f"day:{i}"))
    rows = _chunk(buttons, per_row=2)
    if done_days:
        rows.append([InlineKeyboardButton("✅ پایان و تأیید", callback_data="day:ok")])
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)
