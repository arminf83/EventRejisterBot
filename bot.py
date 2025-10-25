import os
import sys
import django
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from openpyxl import Workbook
import jdatetime
from django.utils import timezone

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "Gita"))

load_dotenv(os.path.join(BASE_DIR, ".env"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Gita.settings")
django.setup()

from events.models import Event, Participant, Registration, Attachment

# ------------------ مراحل گفتگو ------------------
MENU, SELECT_EVENT, EDIT_PROFILE, EDIT_FULLNAME, EDIT_CONTACT, EDIT_MAJOR, EDIT_YEAR = range(7, 14)
REGISTER_NAME, REGISTER_CONTACT, REGISTER_MAJOR, REGISTER_YEAR = range(100, 104)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# ------------------ منوی اصلی ------------------
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎯 مشاهده رویدادها", "📝 ثبت‌نام در رویداد"],
        ["📋 وضعیت ثبت‌نام", "👤 پروفایل من"]
    ]
    await update.message.reply_text(
        "منوی اصلی:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return MENU

# ------------------ شروع ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user, created = await sync_to_async(Participant.objects.get_or_create)(chat_id=chat_id)

    if created or not user.full_name:
        await update.message.reply_text(
            "به ربات خوش اومدی! 🌱\nبرای استفاده، لطفاً ابتدا ثبت‌نام کن.\n\nنام کامل خود را وارد کنید:"
        )
        return REGISTER_NAME

    return await show_menu(update, context)

# ------------------ ثبت‌نام اولیه ------------------
async def register_name(update, context):
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.full_name = update.message.text.strip()
    await sync_to_async(user.save)()
    await update.message.reply_text("📞 شماره تماس خود را وارد کنید:")
    return REGISTER_CONTACT

async def register_contact(update, context):
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.contact = update.message.text.strip()
    await sync_to_async(user.save)()
    await update.message.reply_text("🎓 رشته‌ی تحصیلی خود را وارد کنید:")
    return REGISTER_MAJOR

async def register_major(update, context):
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.major = update.message.text.strip()
    await sync_to_async(user.save)()
    await update.message.reply_text("📆 سال تحصیلی خود را وارد کنید:")
    return REGISTER_YEAR

async def register_year(update, context):
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.year = update.message.text.strip()
    await sync_to_async(user.save)()
    await update.message.reply_text("✅ ثبت‌نام شما با موفقیت انجام شد!\nبه منوی اصلی خوش آمدید 🌟")
    return await show_menu(update, context)

# ------------------ منو ------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)

    if text == "🎯 مشاهده رویدادها":
        events = await sync_to_async(list)(Event.objects.filter(active=True).order_by("start_date"))
        if not events:
            await update.message.reply_text("رویدادی فعال نیست.")
            return MENU

        for ev in events:
            start_local = timezone.localtime(ev.start_date) if ev.start_date else None
            end_local = timezone.localtime(ev.end_date) if ev.end_date else None
            caption_lines = [f"📌 {ev.title}"]

            if start_local:
                j_start = jdatetime.datetime.fromgregorian(datetime=start_local)
                caption_lines.append(f"📅 شروع: {j_start.strftime('%Y/%m/%d')}")
            if end_local:
                j_end = jdatetime.datetime.fromgregorian(datetime=end_local)
                caption_lines.append(f"🕓 پایان: {j_end.strftime('%Y/%m/%d')}")

            if ev.description:
                caption_lines.append("")
                caption_lines.append(ev.description)
            caption = "\n".join(caption_lines)

            if ev.banner:
                try:
                    with open(ev.banner.path, "rb") as img:
                        await update.message.reply_photo(photo=img, caption=caption)
                except Exception:
                    await update.message.reply_text(caption)
            else:
                await update.message.reply_text(caption)

            attachments = await sync_to_async(list)(Attachment.objects.filter(event=ev))
            for att in attachments:
                try:
                    with open(att.file.path, "rb") as f:
                        await update.message.reply_document(document=f, caption=att.description or "")
                except Exception:
                    pass

        return MENU

    elif text == "📝 ثبت‌نام در رویداد":
        events = await sync_to_async(list)(Event.objects.filter(active=True))
        if not events:
            await update.message.reply_text("رویدادی برای ثبت‌نام وجود ندارد.")
            return MENU

        keyboard = [[f"{e.id} - {e.title}"] for e in events]
        keyboard.append(["بازگشت"])
        await update.message.reply_text(
            "رویداد مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_EVENT

    elif text == "📋 وضعیت ثبت‌نام":
        regs = await sync_to_async(list)(
            Registration.objects.filter(participant__chat_id=chat_id).select_related("event")
        )
        if not regs:
            await update.message.reply_text("شما هنوز در هیچ رویدادی ثبت‌نام نکردید.")
            return MENU
        msg = "📋 لیست ثبت‌نام‌های شما:\n\n"
        for r in regs:
            msg += f"✅ {r.event.title}\n"
        await update.message.reply_text(msg)
        return MENU

    elif text == "👤 پروفایل من":
        user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
        msg = (
            f"👤 نام: {user.full_name or '-'}\n"
            f"📞 تماس: {user.contact or '-'}\n"
            f"🎓 رشته: {user.major or '-'}\n"
            f"📆 سال: {user.year or '-'}"
        )
        keyboard = [["✏️ ویرایش پروفایل"], ["بازگشت"]]
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return MENU

    elif text == "✏️ ویرایش پروفایل":
        keyboard = [["نام", "تماس"], ["رشته", "سال"], ["بازگشت"]]
        await update.message.reply_text("کدام بخش را می‌خواهید ویرایش کنید؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return EDIT_PROFILE

    elif text == "بازگشت":
        return await show_menu(update, context)

    else:
        await update.message.reply_text("گزینه نامعتبر.")
        return MENU

# ------------------ ویرایش پروفایل ------------------
async def edit_profile(update, context):
    text = update.message.text.strip()
    if text == "نام":
        await update.message.reply_text("نام جدید را وارد کنید:")
        return EDIT_FULLNAME
    elif text == "تماس":
        await update.message.reply_text("تماس جدید را وارد کنید:")
        return EDIT_CONTACT
    elif text == "رشته":
        await update.message.reply_text("رشته جدید را وارد کنید:")
        return EDIT_MAJOR
    elif text == "سال":
        await update.message.reply_text("سال جدید را وارد کنید:")
        return EDIT_YEAR
    elif text == "بازگشت":
        return MENU
    else:
        await update.message.reply_text("گزینه نامعتبر.")
        return EDIT_PROFILE

async def edit_field(update, context, field_name, label):
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    setattr(user, field_name, update.message.text.strip())
    await sync_to_async(user.save)()
    await update.message.reply_text(f"✅ {label} با موفقیت ویرایش شد.")
    keyboard = [["نام", "تماس"], ["رشته", "سال"], ["بازگشت"]]
    await update.message.reply_text("کدام بخش را می‌خواهید ویرایش کنید؟",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return EDIT_PROFILE

async def edit_fullname(update, context): return await edit_field(update, context, "full_name", "نام")
async def edit_contact(update, context): return await edit_field(update, context, "contact", "تماس")
async def edit_major(update, context): return await edit_field(update, context, "major", "رشته")
async def edit_year(update, context): return await edit_field(update, context, "year", "سال")

# ------------------ انتخاب رویداد ------------------
async def select_event(update, context):
    text = update.message.text.strip()
    if text == "بازگشت":
        return await show_menu(update, context)

    try:
        ev_id = int(text.split(" - ")[0])
        ev = await sync_to_async(Event.objects.get)(id=ev_id)
    except Exception:
        await update.message.reply_text("کد رویداد نامعتبر است.")
        return MENU

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    reg_exists = await sync_to_async(Registration.objects.filter(event=ev, participant=user).exists)()
    if reg_exists:
        await update.message.reply_text("شما قبلاً در این رویداد ثبت‌نام کرده‌اید ✅")
        return MENU

    await sync_to_async(Registration.objects.create)(event=ev, participant=user)
    await update.message.reply_text(f"✅ شما با موفقیت در {ev.title} ثبت‌نام شدید")
    return MENU

# ------------------ ادمین ------------------
async def list_events(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("دسترسی غیرمجاز 🚫")
    events = await sync_to_async(list)(Event.objects.filter(active=True))
    if not events:
        return await update.message.reply_text("هیچ رویداد فعالی وجود ندارد.")
    buttons = [[InlineKeyboardButton(e.title, callback_data=f"admin_event_{e.id}")] for e in events]
    await update.message.reply_text("رویداد مورد نظر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_event_selected(update, context):
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[-1])
    ev = await sync_to_async(Event.objects.get)(id=event_id)
    regs = await sync_to_async(list)(Registration.objects.filter(event=ev).select_related("participant"))
    if not regs:
        return await query.edit_message_text("هیچ شرکت‌کننده‌ای ثبت‌نام نکرده.")

    filename = f"participants_{ev.title.replace(' ', '_')}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Participants"
    ws.append(["نام", "تماس", "رشته", "سال", "وضعیت حضور"])
    for r in regs:
        ws.append([
            r.participant.full_name,
            r.participant.contact,
            r.participant.major,
            r.participant.year,
            r.attendance or "⏳"
        ])

    filepath = os.path.join(BASE_DIR, filename)
    wb.save(filepath)
    with open(filepath, "rb") as f:
        await query.message.reply_document(document=f, caption=f"📊 لیست شرکت‌کنندگان {ev.title}")
    os.remove(filepath)
    await query.edit_message_text(f"📁 فایل اکسل رویداد «{ev.title}» ارسال شد.")

# ------------------ یادآوری ------------------
async def reminder_job(app):
    while True:
        now = timezone.localtime(timezone.now())

        # ایونت‌هایی که در 24 ساعت آینده برگزار میشن
        upcoming_events = await sync_to_async(list)(
            Event.objects.filter(
                start_date__range=(now + timedelta(hours=23), now + timedelta(hours=25)),
                active=True
            )
        )

        for ev in upcoming_events:
            # فقط ثبت‌نام‌هایی که هنوز یادآوری نگرفتن
            regs = await sync_to_async(list)(
                Registration.objects.filter(event=ev, reminder_sent=False).select_related("participant")
            )

            if not regs:
                continue

            reminder_text = ev.reminder_message or f"یادآوری: جلسه‌ی {ev.title} فردا برگزار می‌شود."
            reminder_image = getattr(ev, "reminder_image", None)

            for r in regs:
                try:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ حضور دارم", callback_data=f"attend_yes_{r.id}")],
                        [InlineKeyboardButton("❌ نمیام", callback_data=f"attend_no_{r.id}")]
                    ])

                    if reminder_image:
                        with open(reminder_image.path, "rb") as img:
                            await app.bot.send_photo(
                                chat_id=r.participant.chat_id,
                                photo=img,
                                caption=reminder_text,
                                reply_markup=keyboard
                            )
                    else:
                        await app.bot.send_message(
                            chat_id=r.participant.chat_id,
                            text=reminder_text,
                            reply_markup=keyboard
                        )

                    # علامت‌گذاری این کاربر که یادآوری براش ارسال شده
                    r.reminder_sent = True
                    await sync_to_async(r.save)()

                except Exception as e:
                    print(f"❌ Error sending reminder to {r.participant.chat_id}: {e}")

        # چک هر ۱ ساعت
        await asyncio.sleep(60)



async def attendance_response(update, context):
    query = update.callback_query
    await query.answer()

    _, state, reg_id = query.data.split("_")
    reg = await sync_to_async(Registration.objects.get)(id=reg_id)
    reg.attendance = "present" if state == "yes" else "absent"
    await sync_to_async(reg.save)()

    # متن وضعیت
    status_text = "✅ حضور شما ثبت شد." if state == "yes" else "❌ غیبت شما ثبت شد."

    # بررسی نوع پیام
    if query.message.photo:
        # اگر پیام عکس‌دار بوده (send_photo)
        caption = query.message.caption or ""
        await query.edit_message_caption(
            caption=f"{caption}\n\n{status_text}",
            reply_markup=None
        )
    else:
        # اگر پیام متنی ساده بوده (send_message)
        text = query.message.text or ""
        await query.edit_message_text(
            text=f"{text}\n\n{status_text}",
            reply_markup=None
        )

# ------------------ اجرای ربات ------------------
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ TELEGRAM_TOKEN تنظیم نشده.")
        return

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # ثبت‌نام اولیه
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contact)],
            REGISTER_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_major)],
            REGISTER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_year)],

            # منوی اصلی
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            SELECT_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            EDIT_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_profile)],
            EDIT_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_fullname)],
            EDIT_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_contact)],
            EDIT_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_major)],
            EDIT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_year)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("list", list_events))
    app.add_handler(CallbackQueryHandler(admin_event_selected, pattern="^admin_event_"))
    app.add_handler(CallbackQueryHandler(attendance_response, pattern="^attend_"))

    # اجرای دائمی تسک یادآوری
    asyncio.get_event_loop().create_task(reminder_job(app))

    app.run_polling()

if __name__ == "__main__":
    main()
