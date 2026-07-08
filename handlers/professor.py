import re
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler

from config import DAYS, MIN_COURSE_COUNT, MAX_COURSE_COUNT, DEPARTMENTS, NOTICE_TEXT, RETIRED_YES, RETIRED_NO
from database import save_professor
from keyboards import (
    cancel_kb, RESTART_LABEL, REMOVE,
    yes_no_inline_kb, department_inline_kb, notice_inline_kb, days_inline_kb,
)
from states import States
from utils import to_en_digits
from handlers.start import cmd_restart


async def _safe_edit(query, text, reply_markup=None, **kwargs):
    """ویرایش پیام؛ اگر محتوا با پیام قبلی یکسان باشد و بله/تلگرام خطای
    «message is not modified» بدهد، بی‌سروصدا نادیده گرفته می‌شود."""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, **kwargs)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


async def prof_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.text == RESTART_LABEL:
        return await cmd_restart(update, ctx)
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("⚠️ نام باید حداقل ۳ حرف باشد:")
        return States.PROF_NAME
    ctx.user_data["full_name"] = name
    await update.message.reply_text("کد ملی خود را وارد کنید (۱۰ رقم):")
    return States.PROF_NATIONAL_ID


async def prof_national_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    nid = to_en_digits(update.message.text.strip())
    if not re.fullmatch(r"\d{10}", nid):
        await update.message.reply_text("⚠️ کد ملی باید دقیقاً ۱۰ رقم عددی باشد:")
        return States.PROF_NATIONAL_ID
    ctx.user_data["national_id"] = nid
    await update.message.reply_text("شماره تلفن همراه(شماره پیام رسان ایتا) خود را وارد کنید:")
    return States.PROF_PHONE


async def prof_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # تبدیل ارقام فارسی/عربی به انگلیسی قبل از اعتبارسنجی — رفع خطای عدم پذیرش شماره فارسی
    phone = to_en_digits(update.message.text.strip())
    if not re.fullmatch(r"09\d{9}", phone):
        await update.message.reply_text("⚠️ شماره باید با ۰۹ شروع شود و ۱۱ رقم باشد:")
        return States.PROF_PHONE
    ctx.user_data["phone"] = phone
    await update.message.reply_text("🎓 مدرک و رشته تحصیلی خود را وارد کنید (مثال: کارشناسی مهندسی برق):")
    return States.PROF_DEGREE


async def prof_degree(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    degree = update.message.text.strip()
    if len(degree) < 2:
        await update.message.reply_text("⚠️ مدرک/رشته تحصیلی را کامل‌تر وارد کنید:")
        return States.PROF_DEGREE
    ctx.user_data["degree"] = degree
    await update.message.reply_text(
        "آیا بازنشسته فنی‌حرفه‌ای هستید؟\n"
        "👇 روی یکی از دو گزینه زیر بزنید:",
        reply_markup=yes_no_inline_kb(),
    )
    return States.PROF_RETIRED


# ── بازنشستگی: دکمه شیشه‌ای بله/خیر ─────────────────────────────────────────
async def prof_retired_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]
    ctx.user_data["retired"] = "بله" if value == "yes" else "خیر"
    ctx.user_data["selected_dept"] = ""
    await query.edit_message_text(
        _department_prompt_text(""),
        reply_markup=department_inline_kb(),
    )
    return States.PROF_DEPARTMENT


def _department_prompt_text(selected: str) -> str:
    base = (
        "🏫 گروه آموزشی خود را انتخاب کنید:\n"
        "👇 روی یکی از گروه‌های زیر بزنید (فقط یک گروه قابل انتخاب است)، "
        "سپس «✅ تأیید» را بزنید."
    )
    if selected:
        base += f"\n\n✅ انتخاب‌شده: {selected}"
    return base


# ── گروه آموزشی: دکمه‌های شیشه‌ای، تک‌گزینه‌ای ───────────────────────────────
async def prof_department_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split(":", 1)[1]
    selected = ctx.user_data.get("selected_dept", "")

    if action == "ok":
        if not selected:
            await query.answer("⚠️ یک گروه انتخاب کنید!", show_alert=True)
            return States.PROF_DEPARTMENT
        await query.answer()
        ctx.user_data["department"] = selected
        await query.edit_message_text(
            NOTICE_TEXT + "\n\n👇 پس از مطالعه، روی «✅ خوندم» بزنید:",
            reply_markup=notice_inline_kb(),
        )
        return States.PROF_NOTICE

    idx = int(action)
    new_selected = DEPARTMENTS[idx]
    ctx.user_data["selected_dept"] = new_selected  # انتخاب جدید همیشه جایگزین قبلی می‌شود (تک‌گزینه‌ای)
    await query.answer()
    await _safe_edit(
        query,
        _department_prompt_text(new_selected),
        reply_markup=department_inline_kb(new_selected),
    )
    return States.PROF_DEPARTMENT


# ── تذکرات: دکمه شیشه‌ای «خوندم» ────────────────────────────────────────────
async def prof_notice_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["day_hours"] = {}
    await query.edit_message_text(
        _days_prompt_text({}),
        reply_markup=days_inline_kb(set()),
    )
    return States.PROF_DAYS


def _days_prompt_text(day_hours: dict) -> str:
    if not day_hours:
        return (
            "📅 روزهای تدریس خود را مشخص کنید.\n"
            "👇 روی یک روز بزنید — بلافاصله ساعت همان روز از شما پرسیده می‌شود.\n"
            "برای هر روز دیگر هم همین کار را تکرار کنید.\n"
            "در پایان روی «✅ پایان و تأیید» بزنید.\n"
            "(اگر روی روزی که قبلاً ثبت شده دوباره بزنید، آن روز حذف می‌شود.)"
        )
    lines = "\n".join(f"  • {d}: {day_hours[d]}" for d in DAYS if d in day_hours)
    return (
        "📅 روزها و ساعت‌های ثبت‌شده تا الان:\n" + lines +
        "\n\n👇 روز دیگری را انتخاب کنید یا «✅ پایان و تأیید» را بزنید:"
    )


# ── روزها: دکمه شیشه‌ای؛ با انتخاب هر روز بلافاصله ساعت همان روز پرسیده می‌شود ──
async def prof_days_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split(":", 1)[1]
    day_hours: dict = ctx.user_data.get("day_hours", {})

    if action == "ok":
        if not day_hours:
            await query.answer("⚠️ حداقل یک روز انتخاب کنید!", show_alert=True)
            return States.PROF_DAYS
        await query.answer()
        days_sorted = [d for d in DAYS if d in day_hours]
        ctx.user_data["days"] = days_sorted
        await query.edit_message_text("✅ روزها و ساعت‌های تدریس ثبت شد.")
        await query.message.reply_text(
            f"📚 چند درس پیشنهادی می‌خواهید معرفی کنید؟ عددی بین {MIN_COURSE_COUNT} تا {MAX_COURSE_COUNT} وارد کنید:",
            reply_markup=cancel_kb(),
        )
        return States.PROF_COURSE_COUNT

    idx = int(action)
    day = DAYS[idx]

    if day in day_hours:
        # روی روزی که قبلاً ساعتش ثبت شده دوباره زده شده → حذف آن روز و ساعتش
        del day_hours[day]
        ctx.user_data["day_hours"] = day_hours
        await query.answer("روز و ساعتش حذف شد")
        await _safe_edit(
            query,
            _days_prompt_text(day_hours),
            reply_markup=days_inline_kb(set(day_hours.keys())),
        )
        return States.PROF_DAYS

    # روز جدید انتخاب شد → بلافاصله ساعت همین روز را بپرس
    await query.answer()
    ctx.user_data["pending_day"] = day
    await query.edit_message_text(f"✅ روز «{day}» انتخاب شد.")
    await query.message.reply_text(
        f"⏰ ساعت تدریس برای روز «{day}» را وارد کنید (مثال: ۸:۰۰ - ۹:۳۰):",
        reply_markup=cancel_kb(),
    )
    return States.PROF_HOURS


async def prof_hours(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    hour_text = update.message.text.strip()
    pending_day = ctx.user_data.get("pending_day")

    if len(hour_text) < 3:
        await update.message.reply_text(
            f"⚠️ ساعت معتبر برای روز «{pending_day}» وارد کنید (مثال: ۸:۰۰ - ۹:۳۰):",
            reply_markup=cancel_kb(),
        )
        return States.PROF_HOURS

    day_hours: dict = ctx.user_data.get("day_hours", {})
    day_hours[pending_day] = hour_text
    ctx.user_data["day_hours"] = day_hours
    ctx.user_data.pop("pending_day", None)

    # بازگشت به انتخاب روز بعدی — کاربر می‌تواند روز دیگری انتخاب کند یا تأیید بزند
    await update.message.reply_text(
        _days_prompt_text(day_hours),
        reply_markup=days_inline_kb(set(day_hours.keys())),
    )
    return States.PROF_DAYS


async def prof_course_count(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = to_en_digits(update.message.text.strip())
    if not raw.isdigit() or not (MIN_COURSE_COUNT <= int(raw) <= MAX_COURSE_COUNT):
        await update.message.reply_text(
            f"⚠️ لطفاً عددی صحیح بین {MIN_COURSE_COUNT} تا {MAX_COURSE_COUNT} وارد کنید:",
            reply_markup=cancel_kb(),
        )
        return States.PROF_COURSE_COUNT

    count = int(raw)
    ctx.user_data["course_count"] = count
    ctx.user_data["courses"] = []
    await update.message.reply_text(
        f"📚 نام درس ۱ از {count} را تایپ کنید:",
        reply_markup=cancel_kb(),
    )
    return States.PROF_COURSES


async def prof_courses(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    course_name = update.message.text.strip()
    course_count = ctx.user_data.get("course_count", MAX_COURSE_COUNT)
    if len(course_name) < 2:
        idx = len(ctx.user_data.get("courses", []))
        await update.message.reply_text(f"⚠️ نام درس را کامل‌تر وارد کنید (درس {idx + 1}):")
        return States.PROF_COURSES

    courses: list = ctx.user_data.get("courses", [])
    courses.append(course_name)
    ctx.user_data["courses"] = courses
    next_index = len(courses)

    if next_index < course_count:
        await update.message.reply_text(
            f"✅ درس {next_index} ثبت شد.\n\n📚 نام درس {next_index + 1} از {course_count} را تایپ کنید:",
            reply_markup=cancel_kb(),
        )
        return States.PROF_COURSES

    errors = _validate(ctx.user_data)
    if errors:
        await update.message.reply_text(
            "❌ خطا در اطلاعات:\n" + "\n".join(errors) +
            "\n\nلطفاً از ابتدا وارد کنید.\nنام و نام‌خانوادگی:",
            reply_markup=cancel_kb(),
        )
        ctx.user_data.clear()
        return States.PROF_NAME

    # روزها از قبل به ترتیب هفته مرتب شده‌اند؛ ساعت متناظر هر روز را هم‌ردیف می‌کنیم
    days_sorted = ctx.user_data["days"]
    day_hours = ctx.user_data["day_hours"]
    ctx.user_data["hours"] = [day_hours[d] for d in days_sorted]

    ctx.user_data["user_id"] = update.effective_user.id
    save_professor(ctx.user_data)

    days_hours_lines = "\n".join(f"  • {d}: {day_hours[d]}" for d in days_sorted)

    summary = (
        "🎉 *اطلاعات شما با موفقیت ثبت شد!*\n\n"
        f"👤 نام: {ctx.user_data['full_name']}\n"
        f"🪪 کد ملی: {ctx.user_data['national_id']}\n"
        f"📱 تلفن: {ctx.user_data['phone']}\n"
        f"🎓 مدرک/رشته: {ctx.user_data['degree']}\n"
        f"🧑‍🦳 بازنشسته فنی‌حرفه‌ای: {ctx.user_data['retired']}\n"
        f"🏫 گروه: {ctx.user_data['department']}\n"
        f"📅 روزها و ساعت‌ها:\n{days_hours_lines}\n"
        f"📚 دروس:\n" +
        "\n".join(f"  {i+1}. {c}" for i, c in enumerate(ctx.user_data["courses"]))
    )
    ctx.user_data.clear()
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=REMOVE)
    return ConversationHandler.END


def _validate(data: dict) -> list:
    errors = []
    if not re.fullmatch(r"\d{10}", data.get("national_id", "")):
        errors.append("• کد ملی معتبر نیست")
    if not re.fullmatch(r"09\d{9}", data.get("phone", "")):
        errors.append("• شماره تلفن معتبر نیست")
    if not data.get("degree"):
        errors.append("• مدرک/رشته تحصیلی وارد نشده")
    if not data.get("retired"):
        errors.append("• وضعیت بازنشستگی مشخص نشده")
    if not data.get("department"):
        errors.append("• گروه آموزشی انتخاب نشده")
    if not data.get("days"):
        errors.append("• روز تدریس انتخاب نشده")
    if not data.get("day_hours") or len(data.get("day_hours", {})) < len(data.get("days", [])):
        errors.append("• ساعت تدریس همه روزها وارد نشده")
    course_count = data.get("course_count", MAX_COURSE_COUNT)
    if len(data.get("courses", [])) < course_count:
        errors.append("• تعداد دروس کافی نیست")
    return errors
