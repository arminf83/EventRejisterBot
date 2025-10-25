import os
import sys
import django
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# تنظیمات Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "Gita"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Gita.settings")
load_dotenv(os.path.join(BASE_DIR, ".env"))
django.setup()

from events.models import Event, Registration

# مراحل گفتگو
MENU, SELECT_EVENT, FULLNAME, CONTACT, MAJOR, YEAR, CONFIRM = range(7)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [["مشاهده رویدادها", "ثبت‌نام در رویداد"], ["وضعیت ثبت‌نام", "لغو"]]
    await update.message.reply_text(
        f"سلام {user.first_name or ''}! خوش اومدی 😊",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MENU


# هندلر منو
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "مشاهده رویدادها":
        events = await sync_to_async(list)(
            Event.objects.filter(active=True).select_related("event_type", "category").order_by("start_date")[:20]
        )

        if not events:
            await update.message.reply_text("رویدادی یافت نشد.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        for ev in events:
            msg = (
                f"🎯 {ev.title}\n"
                f"📅 تاریخ: {ev.start_date.strftime('%Y-%m-%d %H:%M') if ev.start_date else '-'}\n"
                f"🏷 نوع: {ev.event_type.name if ev.event_type else '-'}\n"
                f"📚 دسته‌بندی: {ev.category.name if ev.category else '-'}\n"
            )
            if ev.image and ev.image.path:
                try:
                    with open(ev.image.path, "rb") as img:
                        await update.message.reply_photo(photo=img, caption=msg)
                except Exception:
                    await update.message.reply_text(msg)
            else:
                await update.message.reply_text(msg)

        return ConversationHandler.END

    elif text == "ثبت‌نام در رویداد":
        events = await sync_to_async(list)(
            Event.objects.filter(active=True).order_by("start_date")[:50]
        )

        if not events:
            await update.message.reply_text("رویدادی فعال وجود ندارد.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        keyboard = [[f"{ev.id} - {ev.title}"] for ev in events]
        await update.message.reply_text(
            "کد رویداد مورد نظر را انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_EVENT

    elif text == "وضعیت ثبت‌نام":
        await update.message.reply_text("برای مشاهده وضعیت، نام کامل خود را بفرست:", reply_markup=ReplyKeyboardRemove())
        return FULLNAME

    else:
        await update.message.reply_text("متوجه نشدم.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


# انتخاب رویداد
async def select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    try:
        ev_id = int(raw.split()[0])
        ev = await sync_to_async(Event.objects.get)(id=ev_id)
    except Exception:
        await update.message.reply_text("شناسه رویداد نامعتبره. دوباره /start بزن.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data["event_id"] = ev.id
    await update.message.reply_text(f"ثبت‌نام برای: {ev.title}\nاسم کاملت رو بفرست:", reply_markup=ReplyKeyboardRemove())
    return FULLNAME


# دریافت نام کامل
async def fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("شماره تماس یا ایمیلت رو بفرست (اختیاری):")
    return CONTACT


# دریافت تماس
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text("رشته یا تخصصت چیه؟ (اختیاری):")
    return MAJOR


# دریافت رشته
async def major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["major"] = update.message.text.strip()
    await update.message.reply_text("سال تحصیلی یا وضعیتت چیه؟ (مثلاً سال ۲ یا فارغ‌التحصیل):")
    return YEAR


# دریافت سال تحصیلی و تایید
async def year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["year"] = update.message.text.strip()
    ev = await sync_to_async(Event.objects.get)(id=context.user_data["event_id"])

    summary = (
        f"✅ ثبت‌نام در: {ev.title}\n\n"
        f"👤 نام: {context.user_data['full_name']}\n"
        f"📞 تماس: {context.user_data.get('contact','') or '-'}\n"
        f"🎓 رشته: {context.user_data.get('major','') or '-'}\n"
        f"📆 سال: {context.user_data.get('year','') or '-'}\n\n"
        f"تایید می‌کنی؟ (بلی / خیر)"
    )

    await update.message.reply_text(summary)
    return CONFIRM


# تایید ثبت‌نام
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt in ["بلی", "بله", "yes", "y"]:
        ev = await sync_to_async(Event.objects.get)(id=context.user_data["event_id"])
        await sync_to_async(Registration.objects.create)(
            event=ev,
            full_name=context.user_data["full_name"],
            contact=context.user_data.get("contact", ""),
            major=context.user_data.get("major", ""),
            year=context.user_data.get("year", ""),
        )
        await update.message.reply_text("ثبت‌نام با موفقیت انجام شد ✅")
    else:
        await update.message.reply_text("ثبت‌نام لغو شد.")
    return ConversationHandler.END


# لغو گفتگو
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# اجرای ربات
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ فایل .env یا TELEGRAM_TOKEN تنظیم نشده است.")
        return

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            SELECT_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fullname)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, major)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
