"""
ربات بله - با python-telegram-bot (base_url تغییر یافته برای بله)
"""

import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, BALE_BASE_URL
from database import init_db
from states import States

from handlers.start import cmd_start, cmd_myid, cancel, cancel_cb
from handlers.professor import (
    prof_name, prof_national_id, prof_phone, prof_degree,
    prof_retired_cb, prof_department_cb, prof_notice_cb, prof_days_cb,
    prof_hours, prof_course_count, prof_courses,
)
from handlers.admin import admin_menu_handler, admin_del_record, admin_clear_confirm
from handlers.superadmin import (
    super_menu_handler,
    super_add_admin_id, super_add_admin_label, super_del_admin, super_del_record,
    super_clear_confirm,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CANCEL_FILTER = filters.Regex("^❌ انصراف$")


def build_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            States.PROF_NAME:        [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_name)],
            States.PROF_NATIONAL_ID: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_national_id)],
            States.PROF_PHONE:       [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_phone)],
            States.PROF_DEGREE:      [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_degree)],
            # این ۴ مرحله با دکمه‌های شیشه‌ای (inline) کار می‌کنند، نه پیام متنی
            States.PROF_RETIRED:     [CallbackQueryHandler(prof_retired_cb, pattern=r"^retired:")],
            States.PROF_DEPARTMENT:  [CallbackQueryHandler(prof_department_cb, pattern=r"^dept:")],
            States.PROF_NOTICE:      [CallbackQueryHandler(prof_notice_cb, pattern=r"^notice:")],
            States.PROF_DAYS:        [CallbackQueryHandler(prof_days_cb, pattern=r"^day:")],
            States.PROF_HOURS:       [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_hours)],
            States.PROF_COURSE_COUNT: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_course_count)],
            States.PROF_COURSES:     [MessageHandler(filters.TEXT & ~CANCEL_FILTER, prof_courses)],

            States.ADMIN_MENU:        [MessageHandler(filters.TEXT & ~CANCEL_FILTER, admin_menu_handler)],
            States.ADMIN_DEL_RECORD:  [MessageHandler(filters.TEXT & ~CANCEL_FILTER, admin_del_record)],
            States.ADMIN_CLEAR_CONFIRM: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, admin_clear_confirm)],

            States.SUPER_MENU:         [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_menu_handler)],
            States.SUPER_ADD_ADMIN_ID: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_add_admin_id)],
            States.SUPER_ADD_ADMIN_LB: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_add_admin_label)],
            States.SUPER_DEL_ADMIN:    [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_del_admin)],
            States.SUPER_DEL_RECORD:   [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_del_record)],
            States.SUPER_CLEAR_CONFIRM: [MessageHandler(filters.TEXT & ~CANCEL_FILTER, super_clear_confirm)],
        },
        fallbacks=[
            MessageHandler(CANCEL_FILTER, cancel),
            CallbackQueryHandler(cancel_cb, pattern=r"^cancel$"),
            CommandHandler("start", cmd_start),
        ],
        allow_reentry=True,
        persistent=False,
    )


def main():
    init_db()
    logger.info("دیتابیس آماده شد.")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .base_url(BALE_BASE_URL)
        .build()
    )

    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(build_conv())

    logger.info("ربات در حال اجراست...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
