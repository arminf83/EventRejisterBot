# 🤖 Gita Academy Telegram Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Django](https://img.shields.io/badge/Django-Backend-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot_API-0088cc)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

**An advanced Telegram bot for managing event registrations, reminders, and admin reports — powered by Django.**

[Report Bug](https://github.com/arminf83/gita-academy-bot/issues) | [Request Feature](https://github.com/arminf83/gita-academy-bot/pulls)

</div>

---

## ✨ Features

* ✅ **User Registration System** – Collects name, phone, and ID safely
* ✅ **Event Management** – Users can register or remove themselves easily
* ✅ **Automatic Reminders** – Sends event reminders via Telegram
* ✅ **Admin Dashboard** – Manage users and export Excel reports
* ✅ **Error Handling & Logging** – Full logging with structured messages
* ✅ **PostgreSQL Integration** – Secure and scalable database
* ✅ **Multilingual Design** – Fully supports Persian (Farsi) messages

---

## 🚀 Quick Start

### Prerequisites

* Python 3.10+
* PostgreSQL
* Telegram Bot Token (via [BotFather](https://t.me/BotFather))
* Django Installed

### Installation

```bash
git clone https://github.com/arminf83/gita-academy-bot.git
cd gita-academy-bot
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

| Variable            | Description                  | Example                                      |
| ------------------- | ---------------------------- | -------------------------------------------- |
| `TELEGRAM_TOKEN`    | Telegram Bot Token           | `123456:ABCDEF...`                           |
| `DJANGO_SECRET_KEY` | Django secret key            | `django-insecure-xyz`                        |
| `DATABASE_URL`      | PostgreSQL connection string | `postgres://user:pass@localhost:5432/dbname` |
| `ADMINS`            | Telegram ID(s) of admins     | `123456789,987654321`                        |

### Run the bot

```bash
python manage.py runserver
python manage.py run_bot
```

---

## 🧩 Folder Structure

```
├── gita_academy_bot/
│   ├── bot/               # Telegram bot logic
│   ├── core/              # Django settings and config
│   ├── templates/         # HTML templates (if any)
│   └── static/            # Static files
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧠 Example Commands

| Command     | Description                            |
| ----------- | -------------------------------------- |
| `/start`    | Start conversation with the bot        |
| `/register` | Register for an event                  |
| `/cancel`   | Remove registration                    |
| `/list`     | List all registered users (admin only) |
| `/export`   | Export Excel file (admin only)         |

---

## 🧾 License

This project is licensed under the **MIT License** – see the [LICENSE](./LICENSE) file for details.

---

<details>
<summary>🇮🇷 نسخه فارسی</summary>

# 🤖 ربات تلگرام آکادمی گیتا

ربات تلگرامی پیشرفته برای مدیریت ثبت‌نام رویدادها، یادآوری خودکار و گزارش‌های مدیریتی — ساخته‌شده با جنگو (Django).

---

## ✨ ویژگی‌ها

* ✅ **ثبت‌نام کاربران** با نام، شماره و شناسه
* ✅ **مدیریت رویدادها** (افزودن، حذف، مشاهده لیست)
* ✅ **یادآوری خودکار در تلگرام** برای رویدادها
* ✅ **پنل ادمین** برای مدیریت کاربران و خروجی اکسل
* ✅ **اتصال کامل به PostgreSQL**
* ✅ **پشتیبانی از چندزبان (فارسی و انگلیسی)**
* ✅ **امنیت و لاگ کامل در تمامی عملیات‌ها**

---

## ⚙️ نصب و راه‌اندازی

```bash
git clone https://github.com/arminf83/gita-academy-bot.git
cd gita-academy-bot
pip install -r requirements.txt
```

فایل `.env` را در ریشه پروژه بسازید و اطلاعات لازم را مطابق جدول بالا وارد کنید.
سپس با دستور زیر اجرا کنید:

```bash
python manage.py runserver
python manage.py run_bot
```

---

## 👨‍💻 توسعه‌دهنده

**Armin F.**
📬 Telegram: [@armin_dev](https://t.me/armin_dev)
🌐 GitHub: [arminf83](https://github.com/arminf83)

</details>

---

<div align="center">

💙 Developed with passion by **Armin F.**
🎓 Gita Academy – 2025

</div>
