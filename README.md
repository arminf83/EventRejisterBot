# 🎪 Event Management Bot - آکادمی گیتا

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

**سیستم کامل مدیریت رویدادها با تلگرام بات و پنل ادمین دجانگو**

</div>

## ✨ ویژگی‌ها

### 🤖 تلگرام بات
- ✅ ثبت‌نام کاربران با اعتبارسنجی کامل
- ✅ نمایش رویدادهای فعال با عکس و فایل
- ✅ سیستم یادآوری هوشمند رویدادها
- ✅ مدیریت پروفایل کاربران
- ✅ تایید حضور در رویدادها

### 🎯 پنل ادمین دجانگو
- ✅ مدیریت کامل رویدادها، دسته‌بندی‌ها و نوع رویداد
- ✅ آپلود بنر و فایل‌های ضمیمه
- ✅ خروجی اکسل از شرکت‌کنندگان
- ✅ مدیریت حضور و غیاب

### 🗄️ دیتابیس پیشرفته
- ✅ طراحی رابطۀ کامل برای رویدادها
- ✅ مدیریت شرکت‌کنندگان و ثبت‌نام‌ها
- ✅ پیوست‌ها و فایل‌های رویداد

## 🏗️ ساختار پروژه
Gita/
├── events/ # اپلیکیشن مدیریت رویدادها
│ ├── models.py # مدل‌های دیتابیس
│ ├── admin.py # پنل ادمین
│ └── ...
├── Gita/ # تنظیمات اصلی پروژه
│ ├── settings.py # تنظیمات دجانگو
│ └── ...
├── final_bot.py # تلگرام بات اصلی
├── manage.py # مدیریت دجانگو
└── requirements.txt # نیازمندی‌ها

## 🚀 راه‌اندازی سریع

### پیش‌نیازها
- Python 3.8+
- PostgreSQL
- Telegram Bot Token

### نصب و راه‌اندازی
```bash
# نصب نیازمندی‌ها
pip install -r requirements.txt

# کپی فایل محیطی
cp .env.example .env
# ویرایش .env با اطلاعات خودتان

# میگریت دیتابیس
python manage.py migrate

# ایجاد کاربر ادمین
python manage.py createsuperuser

# اجرای سرور دجانگو
python manage.py runserver

# اجرای تلگرام بات (در ترمینال جدا)
python final_bot.py
۲. پیکربندی محیط

فایل .env را با اطلاعات خود ویرایش کنید:
env

# Telegram Bot Configuration
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
CHANNEL_USERNAME=@your_channel_username
ADMIN_IDS=123456789,987654321

# Database Configuration
DB_NAME=eventbot_db
DB_USER=your_db_username
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Django Secret Key
SECRET_KEY=your_django_secret_key_here

۳. راه‌اندازی دیتابیس
bash

# ایجاد میگریشن‌ها
python manage.py makemigrations

۴. اجرای سرویس‌ها
bash

# اجرای سرور دجانگو (ترمینال اول)
python manage.py runserver

# اجرای تلگرام بات (ترمینال دوم)
python final_bot.py

⚙️ پیکربندی پیشرفته
تنظیمات دیتابیس PostgreSQL
python

# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'eventbot_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

تنظیمات زمان‌بندی
python

# زمان‌بندی شمسی (Jalali)
TIME_ZONE = 'Asia/Tehran'
LANGUAGE_CODE = 'fa'

📊 مدل‌های دیتابیس
🎯 Event (رویداد)
python

class Event(models.Model):
    title = models.CharField(max_length=255)           # عنوان رویداد
    description = models.TextField(blank=True)         # توضیحات
    event_type = models.ForeignKey('EventType')        # نوع رویداد
    category = models.ForeignKey('Category')           # دسته‌بندی
    active = models.BooleanField(default=True)         # وضعیت فعال
    start_date = models.DateTimeField()               # تاریخ شروع
    end_date = models.DateTimeField()                 # تاریخ پایان
    banner = models.ImageField()                      # بنر رویداد
    reminder_message = models.TextField()             # پیام یادآوری

👥 Participant (شرکت‌کننده)
python

class Participant(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)  # آیدی تلگرام
    full_name = models.CharField(max_length=200)             # نام کامل
    contact = models.CharField(max_length=200)               # شماره تماس
    major = models.CharField(max_length=200)                 # رشته تحصیلی
    know_us = models.CharField(max_length=200)               # روش آشنایی
    related_experiences = models.TextField()                # تجربیات مرتبط

📝 Registration (ثبت‌نام)
python

class Registration(models.Model):
    event = models.ForeignKey(Event)                    # رویداد
    participant = models.ForeignKey(Participant)       # شرکت‌کننده
    attendance = models.CharField(                     # وضعیت حضور
        choices=[('present', '✅ حاضر'), ('absent', '❌ غایب')]
    )

🎯 امکانات بات تلگرام
منوی اصلی کاربران

    🎯 رویدادهای فعال - مشاهده لیست رویدادها با جزییات کامل

    📝 ثبت‌نام در رویداد - ثبت‌نام در رویدادهای دلخواه

    👤 پروفایل من - مدیریت و ویرایش اطلاعات شخصی

    📊 وضعیت ثبت‌نام‌ها - پیگیری رویدادهای ثبت‌نام شده

سیستم ثبت‌نام
python

# اعتبارسنجی پیشرفته
def validate_contact(contact):
    """اعتبارسنجی شماره موبایل ایرانی"""
    # پشتیبانی از فرمت‌های مختلف: 09123456789, 989123456789, ...

سیستم یادآوری هوشمند

    🔔 ارسال خودکار یادآوری ۲۴ ساعت قبل از رویداد

    📸 پشتیبانی از ارسال عکس و متن در یادآوری

    ✅ قابلیت تایید/رد حضور مستقیم از بات

    ⏰ جلوگیری از اسپم با سیستم کوoldان

🔧 پنل مدیریت ادمین
مدیریت رویدادها

    ایجاد، ویرایش و حذف رویدادها

    آپلود بنر و فایل‌های ضمیمه

    تنظیم پیام یادآوری اختصاصی

    مدیریت تاریخ و زمان رویداد

گزارش‌گیری
bash

# دستورات ادمین
python manage.py list_events    # مشاهده رویدادها
python manage.py export_data    # خروجی اکسل

خروجی اکسل

    📊 دریافت لیست کامل شرکت‌کنندگان هر رویداد

    📋 اطلاعات تماس و وضعیت حضور

    💾 فرمت قابل استفاده در Excel و Google Sheets

🐳 استقرار با Docker (اختیاری)
dockerfile

FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

yaml

# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/eventbot
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=eventbot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

🛠️ عیب‌یابی
مشکلات رایج

    خطای اتصال به دیتابیس
    bash

# بررسی وضعیت PostgreSQL
sudo systemctl status postgresql

خطای تلگرام بات
bash

# بررسی توکن
echo $TELEGRAM_TOKEN

خطای میگریشن
bash

# بازنشانی میگریشن‌ها
python manage.py migrate --fake-initial

لاگ‌گیری
python

# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    }
}

🤝 مشارکت در توسعه

    ریپازیتوری را فورک کنید

    برنچ feature ایجاد کنید (git checkout -b feature/AmazingFeature)

    تغییرات را کامیت کنید (git commit -m 'Add AmazingFeature')

    به برنچ push کنید (git push origin feature/AmazingFeature)

    Pull Request ایجاد کنید

📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است - برای جزییات کامل فایل LICENSE را مطالعه کنید.
👨‍💻 توسعه‌دهنده

آرمین فاضلی - توسعه‌دهنده فول‌استک و متخصص DevOps
پروفایل گیت‌هاب |
لینکدین
<div dir="rtl">
🎪 ربات مدیریت رویدادها - آکادمی گیتا
✨ ویژگی‌های سامانه
سیستم کاربری پیشرفته

    ثبت‌نام امن - با اعتبارسنجی کامل اطلاعات

    پروفایل динамиک - امکان ویرایش تمام اطلاعات

    مدیریت رویدادها - ثبت‌نام و پیگیری وضعیت

مدیریت رویدادها

    ایجاد رویداد - با قابلیت آپلود بنر و فایل

    زمان‌بندی شمسی - پشتیبانی کامل از تاریخ ایرانی

    یادآوری هوشمند - ارسال خودکار اطلاع‌رسانی

پنل مدیریت حرفه‌ای

    دجانگو ادمین - مدیریت کامل از طریق پنل وب

    گزارش‌گیری - خروجی اکسل از اطلاعات

    مدیریت کاربران - مشاهده و مدیریت شرکت‌کنندگان

🚀 راه‌اندازی
نصب و Configuration
bash

# نصب نیازمندی‌ها
pip install -r requirements.txt

# پیکربندی محیط
cp .env.example .env
# ویرایش فایل .env با اطلاعات خود

# راه‌اندازی دیتابیس
python manage.py migrate
python manage.py createsuperuser

# اجرای سرویس‌ها
python manage.py runserver
python final_bot.py

تنظیمات ضروری
env

TELEGRAM_TOKEN=توکن_ربات_تلگرام
CHANNEL_USERNAME=@آیدی_کانال
ADMIN_IDS=آیدی_عددی_ادمین‌ها

📞 پشتیبانی

برای گزارش باگ یا پیشنهاد feature، از طریق Issues گیت‌هاب اقدام کنید.
</div><div align="center">

با ❤️ ساخته شده برای آکادمی گیتا
</div> ```
