import os
import sys
import django
import asyncio
import datetime
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
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")

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
    REGISTER_KNOWUS,
    REGISTER_RELATED_EXPERIENCES,
    EDIT_PROFILE,
    EDIT_FULLNAME,
    EDIT_CONTACT,
    EDIT_MAJOR,
    EDIT_KNOWUS,
    EDIT_RELATED_EXPERIENCES,
) = range(13)

ADMIN_IDS = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = list(map(int, ADMIN_IDS.split(",")))

# ------------------------------------------
#  اعتبارسنجی‌ها
# ------------------------------------------
def validate_name(name):
    """اعتبارسنجی نام و نام خانوادگی"""
    name = name.strip()
    if len(name) < 2:
        return False, "❌ نام باید حداقل ۲ حرف باشد"
    if len(name) > 50:
        return False, "❌ نام نمی‌تواند بیشتر از ۵۰ حرف باشد"
    if any(char.isdigit() for char in name):
        return False, "❌ نام نمی‌تواند شامل عدد باشد"
    if not any(char.isalpha() for char in name):
        return False, "❌ نام باید شامل حروف باشد"
    return True, "✅ نام معتبر است"

def validate_contact(contact):
    """اعتبارسنجی شماره تماس - فقط شماره موبایل"""
    contact = contact.strip()
    
    # حذف فاصله و خط تیره
    cleaned_contact = contact.replace(' ', '').replace('-', '').replace('+', '')
    
    # شماره موبایل ایران (09 شروع میشه)
    if cleaned_contact.startswith('09'):
        if len(cleaned_contact) == 11 and cleaned_contact[2:].isdigit():
            return True, "✅ شماره موبایل معتبر است"
        else:
            return False, "❌ شماره موبایل باید 11 رقمی باشد (مثال: 09123456789)"
    
    # شماره با پیشوند 989
    elif cleaned_contact.startswith('989'):
        if len(cleaned_contact) == 12 and cleaned_contact[3:].isdigit():
            return True, "✅ شماره موبایل معتبر است"
        else:
            return False, "❌ شماره موبایل معتبر نیست"
    
    # شماره با پیشوند 00989
    elif cleaned_contact.startswith('00989'):
        if len(cleaned_contact) == 14 and cleaned_contact[5:].isdigit():
            return True, "✅ شماره موبایل معتبر است"
        else:
            return False, "❌ شماره موبایل معتبر نیست"
    
    return False, "❌ لطفا فقط شماره موبایل وارد کنید (مثال: 09123456789)"

def validate_major(major):
    """اعتبارسنجی رشته تحصیلی"""
    major = major.strip()
    if len(major) < 2:
        return False, "❌ رشته تحصیلی باید حداقل ۲ حرف باشد"
    if len(major) > 50:
        return False, "❌ رشته تحصیلی نمی‌تواند بیشتر از ۵۰ حرف باشد"
    return True, "✅ رشته معتبر است"

def validate_text_field(text, field_name, min_length=2, max_length=200):
    """اعتبارسنجی فیلدهای متنی عمومی"""
    text = text.strip()
    if len(text) < min_length:
        return False, f"❌ {field_name} باید حداقل {min_length} حرف باشد"
    if len(text) > max_length:
        return False, f"❌ {field_name} نمی‌تواند بیشتر از {max_length} حرف باشد"
    return True, f"✅ {field_name} معتبر است"

# ------------------------------------------
#  کیبوردها
# ------------------------------------------
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["🎯 رویدادهای فعال", "📝 ثبت نام در رویداد"],
         ["👤 پروفایل من", "📊 وضعیت ثبت‌نام‌ها"],
         ["ℹ️ راهنما"]],
        resize_keyboard=True
    )

# ------------------------------------------
#  بررسی عضویت
# ------------------------------------------
async def is_user_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"⚠️ خطا در بررسی عضویت: {e}")
        return False

# ------------------------------------------
#  تایپینگ انیمیشن
# ------------------------------------------
async def show_typing(update, context):
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    await asyncio.sleep(0.5)

# ------------------------------------------
#  شروع ربات
# ------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    close_old_connections()
    chat_id = str(update.effective_chat.id)

    # 🔹 بررسی عضویت در کانال
    is_member = await is_user_member(context.bot, update.effective_user.id)
    if not is_member:
        join_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        await update.message.reply_text(
            f"🚫 برای استفاده از ربات باید عضو کانال زیر شوید:\n\n"
            f"{join_link}\n\n"
            f"بعد از عضویت، دستور /start را دوباره بفرست ✅"
        )
        return ConversationHandler.END

    # ✅ اگر عضو بود، ادامه بده
    user, created = await sync_to_async(Participant.objects.get_or_create)(chat_id=chat_id)

    if created or not user.full_name:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(0.5)
        await update.message.reply_text(
            f"سلام {'@' + update.effective_user.username if update.effective_user.username else 'دوست عزیز'} 👋\n"
            "به آکادمی گیتا خوش اومدی 🎓✨\n\n"
            "لطفا برای شروع <b>نام و نام خانوادگی</b> خودت رو بنویس 🙏",
            parse_mode="HTML"
        )
        return REGISTER_NAME

    # 🔹 اگه کاربر قبلاً ثبت‌نام کرده بود:
    await update.message.reply_text("به منوی اصلی خوش آمدید 🌟", reply_markup=main_menu_keyboard())
    return MENU

# ------------------------------------------
#  ثبت‌نام اولیه با اعتبارسنجی
# ------------------------------------------
async def register_name(update, context):
    text = update.message.text.strip()
    
    # اعتبارسنجی نام
    is_valid, message = validate_name(text)
    if not is_valid:
        await update.message.reply_text(
            f"{message}\n\n"
            "لطفا <b>نام و نام خانوادگی </b> خود را وارد کنید:",
            parse_mode="HTML"
        )
        return REGISTER_NAME

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.full_name = text
    await sync_to_async(user.save)()
    
    await update.message.reply_text(
        "✅ نام شما ثبت شد!\n\n"
        "📞 حالا <b>شماره موبایل</b> خود را وارد کنید:\n\n"
        "• فقط شماره موبایل (مثال: 09123456789)\n",
        parse_mode="HTML"
    )
    return REGISTER_CONTACT

async def register_contact(update, context):
    text = update.message.text.strip()
    
    # اعتبارسنجی تماس
    is_valid, message = validate_contact(text)
    if not is_valid:
        await update.message.reply_text(
        f"{message}\n\n"
        "لطفا فقط <b>شماره موبایل ایرانی</b> وارد کنید:\n"
        "• مثال: 09123456789\n",
        parse_mode="HTML"
        )
        return REGISTER_CONTACT

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.contact = text
    await sync_to_async(user.save)()
    
    await update.message.reply_text(
        "✅ اطلاعات تماس ثبت شد!\n\n"
        "🎓 حالا <b>رشته تحصیلی</b> خود را وارد کنید:\n\n"
        "مثال: مهندسی کامپیوتر، پزشکی، حقوق و...",
        parse_mode="HTML"
    )
    return REGISTER_MAJOR

async def register_major(update, context):
    text = update.message.text.strip()
    
    # اعتبارسنجی رشته
    is_valid, message = validate_major(text)
    if not is_valid:
        await update.message.reply_text(
            f"{message}\n\n"
            "لطفا <b>رشته تحصیلی </b> خود را وارد کنید:",
            parse_mode="HTML"
        )
        return REGISTER_MAJOR

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.major = text
    await sync_to_async(user.save)()
    
    await update.message.reply_text(
        "✅ رشته تحصیلی ثبت شد!\n\n"
        "📢 <b>از چه طریقی با ما آشنا شدید؟</b>\n\n"
        "مثال: دوستان، اینستاگرام، تلگرام، دانشگاه و...",
        parse_mode="HTML"
    )
    return REGISTER_KNOWUS

async def register_knowus(update, context):
    text = update.message.text.strip()
    
    # اعتبارسنجی فیلد آشنا شدن
    is_valid, message = validate_text_field(text, "روش آشنایی", min_length=3, max_length=100)
    if not is_valid:
        await update.message.reply_text(
            f"{message}\n\n"
            "لطفا روش آشنایی خود با ما را وارد کنید:",
            parse_mode="HTML"
        )
        return REGISTER_KNOWUS

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.know_us = text
    await sync_to_async(user.save)()
    
    await update.message.reply_text(
        "✅ روش آشنایی ثبت شد!\n\n"
        "📋 <b>تجربیات مرتبط خود را شرح دهید:</b>\n\n"
        "میتوانید بنویسید: تجربه خاصی ندارم\n"
        "یا تجربیات مرتبط خود را شرح دهید",
        parse_mode="HTML"
    )
    return REGISTER_RELATED_EXPERIENCES

async def register_related_experiences(update, context):
    text = update.message.text.strip()
    
    # اعتبارسنجی تجربیات (اختیاری اما اگر وارد کرد معتبر باشد)
    if text and text != "تجربه خاصی ندارم":
        is_valid, message = validate_text_field(text, "تجربیات مرتبط", min_length=5, max_length=500)
        if not is_valid:
            await update.message.reply_text(
                f"{message}\n\n"
                "لطفا تجربیات مرتبط خود را وارد کنید:",
                parse_mode="HTML"
            )
            return REGISTER_RELATED_EXPERIENCES

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    user.related_experiences = text
    await sync_to_async(user.save)()
    
    await update.message.reply_text(
        "🎉 <b>از همراهیتون با ما ممنونیم.</b>\n\n"
        "به ربات آکادمی گیتا خوش آمدید 🌟\n\n"
        "اکنون میتوانید از منوی اصلی استفاده کنید:\n\n"
        " جهت ثبت نام در دوره ها یا نشست ها ، از قسمت (ثبت نام در رویداد) اقدام نمایید.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    return MENU

# ------------------------------------------
#  منوی اصلی
# ------------------------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_typing(update, context)
    close_old_connections()
    text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)

    # مشاهده رویدادها
    if text == "🎯 رویدادهای فعال":
        events = await sync_to_async(list)(Event.objects.filter(active=True).order_by("start_date"))
        if not events:
            await update.message.reply_text("🎭 در حال حاضر رویداد فعالی وجود ندارد.")
            return MENU

        await update.message.reply_text(f"📋 تعداد {len(events)} رویداد فعال پیدا شد:")
        
        for i, ev in enumerate(events, 1):
            await show_typing(update, context)
            start_local = timezone.localtime(ev.start_date) if ev.start_date else None
            end_local = timezone.localtime(ev.end_date) if ev.end_date else None
            caption_lines = [f"📌 {ev.title}"]

            if start_local:
                j_start = jdatetime.datetime.fromgregorian(datetime=start_local.replace(tzinfo=None))
                caption_lines.append(f"📅 شروع: {j_start.strftime('%Y/%m/%d %H:%M')}")
            if end_local:
                j_end = jdatetime.datetime.fromgregorian(datetime=end_local.replace(tzinfo=None))
                caption_lines.append(f"🕓 پایان: {j_end.strftime('%Y/%m/%d %H:%M')}")

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
    elif text == "📝 ثبت نام در رویداد":
        events = await sync_to_async(list)(Event.objects.filter(active=True))
        if not events:
            await update.message.reply_text("هیچ رویدادی برای ثبت‌نام وجود ندارد.")
            return MENU

        keyboard = [[f"{e.title}"] for e in events]
        keyboard.append(["بازگشت"])
        await update.message.reply_text(
            "رویداد مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_EVENT
        
    elif text == "ℹ️ راهنما":
        help_text = """🎯 *دستورات اصلی ربات:*
• *🎯 رویدادهای فعال* : مشاهده رویدادها
• *📝 ثبت نام در رویداد* : ثبت‌نام در رویداد
• *👤 پروفایل من* : مدیریت اطلاعات شخصی
• *📊 وضعیت ثبت‌نام‌ها* : پیگیری ثبت‌نام‌ها

📝 *نکات مهم:*
- می‌توانید اطلاعات خود را ویرایش کنید
- قبل از هر رویداد یادآور دریافت می‌کنید
- امکان انصراف از رویداد وجود دارد"""
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return MENU

    # وضعیت ثبت‌نام
    elif text == "📊 وضعیت ثبت‌نام‌ها":
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
        keyboard = [["✏️ ویرایش پروفایل"], ["🔙 بازگشت به منوی اصلی"]]
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
        keyboard = [["نام", "تماس", "رشته"], 
                   ["آشنا شده از", "تجربیات مرتبط"], 
                   ["🔙 بازگشت به منوی اصلی"]]
        await update.message.reply_text(
            "کدام بخش را می‌خواهید ویرایش کنید؟", 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return EDIT_PROFILE

    else:
        await update.message.reply_text(
            "❌ گزینه انتخابی معتبر نیست.\n"
            "لطفا از دکمه‌های زیر استفاده کنید:",
            reply_markup=main_menu_keyboard()
        )
        return MENU

# ------------------ ویرایش پروفایل ------------------
async def edit_profile(update, context):
    text = update.message.text.strip()
    mapping = {
        "نام": ("full_name", "نام", EDIT_FULLNAME),
        "تماس": ("contact", "تماس", EDIT_CONTACT),
        "رشته": ("major", "رشته", EDIT_MAJOR),
        "آشنا شده از": ("know_us", "روش آشنایی", EDIT_KNOWUS),
        "تجربیات مرتبط": ("related_experiences", "تجربیات مرتبط", EDIT_RELATED_EXPERIENCES)
    }
    
    if text in mapping:
        field_name, label, next_state = mapping[text]
        context.user_data["edit_field"] = (field_name, label)
        await update.message.reply_text(f"{label} جدید را وارد کنید:")
        return next_state
        
    elif text == "🔙 بازگشت به منوی اصلی":
        await update.message.reply_text("بازگشت به منوی اصلی", reply_markup=main_menu_keyboard())
        return MENU
        
    else:
        await update.message.reply_text("گزینه نامعتبر.")
        return EDIT_PROFILE

# ------------------ هندلرهای ویرایش با اعتبارسنجی ------------------
async def edit_field_handler(update, context):
    field_name, label = context.user_data.get("edit_field", (None, None))
    if not field_name:
        return EDIT_PROFILE
    
    text = update.message.text.strip()
    
    # اعتبارسنجی بر اساس فیلد
    if field_name == "full_name":
        is_valid, message = validate_name(text)
    elif field_name == "contact":
        is_valid, message = validate_contact(text)
    elif field_name == "major":
        is_valid, message = validate_major(text)
    elif field_name == "know_us":
        is_valid, message = validate_text_field(text, "روش آشنایی", min_length=3, max_length=100)
    elif field_name == "related_experiences":
        is_valid, message = validate_text_field(text, "تجربیات مرتبط", min_length=5, max_length=500)
    else:
        is_valid, message = True, "✅ اطلاعات ثبت شد"
    
    if not is_valid:
        await update.message.reply_text(
            f"{message}\n\n"
            f"لطفا {label} جدید را وارد کنید:"
        )
        # برگشت به state مربوطه
        state_mapping = {
            "full_name": EDIT_FULLNAME,
            "contact": EDIT_CONTACT,
            "major": EDIT_MAJOR,
            "know_us": EDIT_KNOWUS,
            "related_experiences": EDIT_RELATED_EXPERIENCES
        }
        return state_mapping.get(field_name, EDIT_PROFILE)

    chat_id = str(update.effective_chat.id)
    user = await sync_to_async(Participant.objects.get)(chat_id=chat_id)
    setattr(user, field_name, text)
    await sync_to_async(user.save)()
    
    await update.message.reply_text(f"✅ {label} با موفقیت ویرایش شد.")
    
    keyboard = [["نام", "تماس", "رشته"], 
                ["آشنا شده از", "تجربیات مرتبط"], 
                ["🔙 بازگشت به منوی اصلی"]]
    await update.message.reply_text(
        "کدام بخش دیگر را می‌خواهید ویرایش کنید؟",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
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
        ev = await sync_to_async(Event.objects.get)(title=text)
    except Exception:
        await update.message.reply_text("❌ رویداد مورد نظر یافت نشد.")
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
    if update.effective_user.id not in ADMIN_IDS:
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
    ws.append(["نام", "تماس", "رشته", "آشنا شده از", "تجربیات مرتبط", "وضعیت حضور"])
    for r in regs:
        ws.append([
            r.participant.full_name,
            r.participant.contact,
            r.participant.major,
            r.participant.know_us,
            r.participant.related_experiences,
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
async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    close_old_connections()

    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # پیدا کردن ایونت‌های فردا
    target_date = today + timedelta(days=1)
    
    events = await sync_to_async(list)(
        Event.objects.filter(
            active=True,
            main_date__date=target_date
        )
    )

    total_sent = 0
    total_failed = 0

    for ev in events:
        print(f"🔔 پردازش یادآوری برای رویداد: {ev.title}")
        
        regs = await sync_to_async(list)(
            Registration.objects.filter(
                event=ev,
                last_reminder_date__isnull=True
            ).select_related("participant")
        )

        for r in regs:
            try:
                reminder_text = ev.reminder_message or f"""
📢 یادآوری رویداد

🏷️ عنوان: {ev.title}
⏰ زمان: {timezone.localtime(ev.main_date).strftime('%Y/%m/%d ساعت %H:%M')}

لطفا با دکمه‌های زیر وضعیت حضور خود را مشخص کنید:
                """.strip()

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ قطعا حضور دارم", callback_data=f"attend_yes_{r.id}")],
                    [InlineKeyboardButton("❌ متاسفانه نمی‌توانم بیایم", callback_data=f"attend_no_{r.id}")]
                ])

                success = False
                try:
                    reminder_image = getattr(ev, "reminder_image", None)
                    if reminder_image and hasattr(reminder_image, "path") and os.path.exists(reminder_image.path):
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
                    success = True
                except Exception as send_error:
                    print(f"⚠️ خطا در ارسال به {r.participant.chat_id}: {send_error}")
                    success = False

                if success:
                    r.last_reminder_date = now
                    await sync_to_async(r.save)()
                    total_sent += 1
                    print(f"✅ یادآوری ارسال شد به: {r.participant.full_name}")
                else:
                    total_failed += 1

                await asyncio.sleep(0.3)

            except Exception as e:
                print(f"❌ خطای غیرمنتظره برای {r.participant.chat_id}: {e}")
                total_failed += 1

    print(f"📊 جمع‌بندی یادآوری: {total_sent} ارسال موفق, {total_failed} خطا")

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
            REGISTER_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_major)],
            REGISTER_KNOWUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_knowus)],
            REGISTER_RELATED_EXPERIENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_related_experiences)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            SELECT_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            EDIT_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_profile)],
            EDIT_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_handler)],
            EDIT_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_handler)],
            EDIT_MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_handler)],
            EDIT_KNOWUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_handler)],
            EDIT_RELATED_EXPERIENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_handler)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(attendance_response, pattern="^attend_"))
    app.add_handler(CommandHandler("list", list_events))
    app.add_handler(CallbackQueryHandler(admin_event_selected, pattern="^admin_event_"))

    app.job_queue.run_repeating(reminder_job, interval=3600, first=5)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

