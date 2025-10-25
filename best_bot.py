import os
import sys
import django
import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from django.utils import timezone
from django.db import close_old_connections
from asgiref.sync import sync_to_async
from openpyxl import Workbook
import jdatetime

from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# ------------------------------------------
#  Django setup
# ------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "Gita"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Gita.settings")
django.setup()

from events.models import Event, Participant, Registration, Attachment

# ------------------------------------------
#  مراحل گفتگو
# ------------------------------------------
(
    MENU,
    SELECT_EVENT,
    REGISTER_NAME,
    REGISTER_CONTACT,
    REGISTER_MAJOR,
    REGISTER_YEAR,
    REGISTER_KNOWUS,
    REGISTER_RELATED_EXPERIENCES,
    EDIT_PROFILE,
    EDIT_FULLNAME,
    EDIT_CONTACT,
    EDIT_MAJOR,
    EDIT_YEAR,
    error_handler,
) = range(14)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# ------------------------------------------
#  کیبوردها
# ------------------------------------------
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["🎯 مشاهده رویدادها", "📝 ثبت‌نام در رویداد"],
         ["📋 وضعیت ثبت‌نام", "👤 پروفایل من"]],
        resize_keyboard=True
    )

# ------------------------------------------
#  شروع ربات
# ------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    close_old_connections()
    chat_id = str(update.effective_chat.id)
    user, created = await sync_to_async(Participant.objects.get_or_create)(chat_id=chat_id)

    if created or not user.full_name:
        await update.message.reply_text(
            """سلام
خوش اومدی! 😍

ما در آکادمی گیتا جمعی از علاقه‌مندان به هوش مصنوعی، کامپیوتر و دنیای بازی رو دور هم آوردیم تا جایی بسازیم برای یادگیری، خلاقیت و لحظات خوب.
خوشحالیم که شما را در کنارمون داریم. 🙏نام و نام خانوادگی کامل را وارد کنید:
"""
        )
        return REGISTER_NAME

    await update.message.reply_text("به منوی اصلی خوش آمدید 🌟", reply_markup=main_menu_keyboard())
    return MENU

# ------------------------------------------
#  ثبت‌نام اولیه
# ------------------------------------------
async def register_name(update, context):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.full_name = text
    await sync_to_async(user.save)()
    await update.message.reply_text("📞 شماره تماس خود را وارد کنید:")
    return REGISTER_CONTACT

async def register_contact(update, context):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.contact = text
    await sync_to_async(user.save)()
    await update.message.reply_text("🎓 رشته‌ی تحصیلی خود را وارد کنید:")
    return REGISTER_MAJOR

async def register_major(update, context):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.major = text
    await sync_to_async(user.save)()
    await update.message.reply_text("📢 از چه طریقی با ما آشنا شدید؟")
    return REGISTER_KNOWUS

async def register_knowus(update, context):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.knowـus = text
    await sync_to_async(user.save)()
    await update.message.reply_text("📋 تجربیات مرتبط خود را شرح دهید:")
    return REGISTER_RELATED_EXPERIENCES

async def register_related_experiences(update, context):
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.Relatedـexperiences = text
    await sync_to_async(user.save)()
    await update.message.reply_text(
        "✅ ثبت‌نام شما با موفقیت انجام شد!\nبه منوی اصلی خوش آمدید 🌟",
        reply_markup=main_menu_keyboard()
    )
    return MENU

# ------------------------------------------
#  منوی اصلی
# ------------------------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    close_old_connections()
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)

    # مشاهده رویدادها
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
                j_start = jdatetime.datetime.fromgregorian(datetime=start_local.replace(tzinfo=None))
                caption_lines.append(f"📅 شروع: {j_start.strftime('%Y/%m/%d')}")
            if end_local:
                j_end = jdatetime.datetime.fromgregorian(datetime=end_local.replace(tzinfo=None))
                caption_lines.append(f"🕓 پایان: {j_end.strftime('%Y/%m/%d')}")

            if ev.description:
                caption_lines.append("")
                caption_lines.append(ev.description)
            caption = "\n".join(caption_lines)

            chat_id_int = update.effective_chat.id
            if ev.banner:
                try:
                    with open(ev.banner.path, "rb") as img:
                        await context.bot.send_photo(chat_id=chat_id_int, photo=img, caption=caption)
                except Exception as e:
                    print("Photo send error:", e)
                    await context.bot.send_message(chat_id=chat_id_int, text=caption)
            else:
                await context.bot.send_message(chat_id=chat_id_int, text=caption)

            attachments = await sync_to_async(list)(Attachment.objects.filter(event=ev))
            for att in attachments:
                try:
                    with open(att.file.path, "rb") as f:
                        await context.bot.send_document(chat_id=chat_id_int, document=f, caption=att.description or "")
                except Exception as e:
                    print("File send error:", e)

            await asyncio.sleep(0.5)

        return MENU

    # ثبت‌نام در رویداد
    elif text == "📝 ثبت‌نام در رویداد":
        events = await sync_to_async(list)(Event.objects.filter(active=True))
        if not events:
            await update.message.reply_text("هیچ رویدادی برای ثبت‌نام وجود ندارد.")
            return MENU

        keyboard = [[f"{e.id} - {e.title}"] for e in events]
        keyboard.append(["بازگشت"])
        await update.message.reply_text(
            "رویداد مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_EVENT

    # وضعیت ثبت‌نام
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

    # پروفایل من
    elif text == "👤 پروفایل من":
        user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
        msg = (
            f"👤 <b>پروفایل شما</b>\n\n"
            f"👨‍💼 نام: <b>{user.full_name or '—'}</b>\n"
            f"📞 تماس: <b>{user.contact or '—'}</b>\n"
            f"🎓 رشته: <b>{user.major or '—'}</b>\n"
            f"📢 آشنا شده از: <b>{user.know_us or '—'}</b>\n"
            f"📋 تجربیات مرتبط: <b>{user.related_experiences or '—'}</b>\n"
        )
        keyboard = [["✏️ ویرایش پروفایل"], ["بازگشت"]]
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return MENU

    elif "بازگشت" in text:
        await update.message.reply_text("بازگشت به منوی اصلی", reply_markup=main_menu_keyboard())
        return MENU
    elif text == "✏️ ویرایش پروفایل":
        keyboard = [["نام", "تماس","رشته"],["آشنا شده از", "تجربیات مرتبط"], ["بازگشت"]]
        await update.message.reply_text("کدام بخش را می‌خواهید ویرایش کنید؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return EDIT_PROFILE

    else:
        await update.message.reply_text("گزینه نامعتبر است.")
        return MENU

# ------------------ ویرایش پروفایل ------------------
async def edit_profile(update, context):
    text = update.message.text.strip()
    mapping = {
        "نام": ("full_name", "نام"),
        "تماس": ("contact", "تماس"),
        "رشته": ("major", "رشته"),
        "سال": ("year", "سال"),
        "آشنا شده از": ("knowـus", "آشنا شده از"),
        "تجربیات مرتبط": ("Relatedـexperiences", "تجربیات مرتبط")
    }
    if text in mapping:
        field_name, label = mapping[text]
        await update.message.reply_text(f"{label} جدید را وارد کنید:")
        context.user_data["edit_field"] = (field_name, label)
        return EDIT_FULLNAME  # از همان handler مشترک استفاده می‌کنیم
    elif text == "بازگشت":
        return MENU
    else:
        await update.message.reply_text("گزینه نامعتبر.")
        return EDIT_PROFILE

async def edit_field(update, context):
    field_name, label = context.user_data.get("edit_field", (None, None))
    if not field_name:
        return EDIT_PROFILE
    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    setattr(user, field_name, update.message.text.strip())
    await sync_to_async(user.save)()
    await update.message.reply_text(f"✅ {label} با موفقیت ویرایش شد.")
    keyboard = [["نام", "تماس"], ["رشته", "سال"], ["آشنا شده از", "تجربیات مرتبط"], ["بازگشت"]]
    await update.message.reply_text("کدام بخش را می‌خواهید ویرایش کنید؟",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return EDIT_PROFILE

# ------------------------------------------
#  انتخاب رویداد
# ------------------------------------------
async def select_event(update, context):
    close_old_connections()
    text = update.message.text.strip()
    if text == "بازگشت":
        await update.message.reply_text("بازگشت به منوی اصلی", reply_markup=main_menu_keyboard())
        return MENU

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
    await update.message.reply_text(f"✅ ثبت‌نام شما در «{ev.title}» با موفقیت انجام شد.")
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

    now_j = jdatetime.datetime.now()
    filename = f"participants_{ev.title.replace(' ', '_')}_{now_j.strftime('%Y%m%d_%H%M%S')}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Participants"
    ws.append(["نام", "تماس", "رشته", "سال", "آشنا شده از", "تجربیات مرتبط", "وضعیت حضور"])
    for r in regs:
        ws.append([
            r.participant.full_name,
            r.participant.contact,
            r.participant.major,
            r.participant.year,
            r.participant.knowـus,
            r.participant.Relatedـexperiences,
            r.attendance or "⏳"
        ])

    filepath = os.path.join(BASE_DIR, filename)
    wb.save(filepath)
    with open(filepath, "rb") as f:
        await query.message.reply_document(document=f, caption=f"📊 لیست شرکت‌کنندگان {ev.title}")
    os.remove(filepath)
    await query.edit_message_text(f"📁 فایل اکسل رویداد «{ev.title}» ارسال شد.")

# ------------------------------------------
#  یادآوری رویدادها
# ------------------------------------------
async def reminder_job(app):
    while True:
        try:
            close_old_connections()
            now = timezone.localtime(timezone.now())
            events = await sync_to_async(list)(
                Event.objects.prefetch_related("registrations__participant").filter(
                    start_date__gte=now,
                    start_date__lte=now + timedelta(hours=24),
                    active=True
                )
            )

            for ev in events:
                regs = [r for r in ev.registrations.all() if not r.reminder_sent]
                if not regs:
                    continue

                reminder_text = ev.reminder_message or f"📢 یادآوری: رویداد «{ev.title}» فردا برگزار می‌شود."
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

                        r.reminder_sent = True
                        await sync_to_async(r.save)()
                        await asyncio.sleep(0.05)

                    except Exception as e:
                        print(f"❌ خطا در ارسال یادآوری به {r.participant.chat_id}: {e}")

        except Exception as e:
            print(f"⚠️ خطا در reminder_job: {e}")

        await asyncio.sleep(3600)  # بررسی هر ۱ ساعت

# ------------------------------------------
#  پاسخ حضور / عدم حضور
# ------------------------------------------
async def attendance_response(update, context):
    query = update.callback_query
    await query.answer()

    _, state, reg_id = query.data.split("_")
    reg = await sync_to_async(Registration.objects.get)(id=reg_id)
    reg.attendance = "present" if state == "yes" else "absent"
    await sync_to_async(reg.save)()

    status_text = "✅ حضور شما ثبت شد." if state == "yes" else "❌ غیبت شما ثبت شد."
    if query.message.photo:
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n{status_text}", reply_markup=None)
    else:
        await query.edit_message_text(text=f"{query.message.text}\n\n{status_text}", reply_markup=None)

# ------------------------------------------
#  اجرای ربات
# ------------------------------------------
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ توکن تلگرام تنظیم نشده است.")
        return

    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)

    app = ApplicationBuilder().token(token).request(request).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_contact)],
            REGISTER_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_major)],REGISTER_KNOWUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_knowus)],
            REGISTER_RELATED_EXPERIENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_related_experiences)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            SELECT_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            EDIT_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_profile)],
            EDIT_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            EDIT_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            EDIT_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            EDIT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(attendance_response, pattern="^attend_"))
    app.add_handler(CommandHandler("list", list_events))
    app.add_handler(CallbackQueryHandler(admin_event_selected, pattern="^admin_event_"))

    # اجرای تسک یادآوری به صورت پس‌زمینه
    asyncio.get_event_loop().create_task(reminder_job(app))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()