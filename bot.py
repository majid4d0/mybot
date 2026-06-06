import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 10000))

relay = {}        # شماره پیام سمت ادمین -> کد کاربر
seen = set()      # کاربرانی که قبلاً پیام داده‌اند

def header(u):
    name = u.full_name or "بدون نام"
    uname = f"@{u.username}" if u.username else "—"
    prem = "بله" if getattr(u, "is_premium", False) else "خیر"
    return (
        "📩 پیام جدید\n"
        f"👤 نام: {name}\n"
        f"🔗 یوزرنیم: {uname}\n"
        f"🆔 کد کاربر: {u.id}\n"
        f"🌐 زبان: {u.language_code or '—'}\n"
        f"⭐ پرمیوم: {prem}\n"
        f"#id{u.id}"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg is None:
        return

    # حالت ۱: ادمین در حال پاسخ دادن است
    if msg.chat.id == ADMIN_ID:
        if msg.reply_to_message:
            uid = relay.get(msg.reply_to_message.message_id)
            if uid is None:
                txt = msg.reply_to_message.text or msg.reply_to_message.caption or ""
                if "#id" in txt:
                    try:
                        uid = int(txt.split("#id")[1].split()[0])
                    except Exception:
                        uid = None
            if uid:
                await context.bot.copy_message(chat_id=uid,
                    from_chat_id=ADMIN_ID, message_id=msg.message_id)
            else:
                await msg.reply_text("روی پیامِ همان کاربر ریپلای کن تا جواب برسد.")
        else:
            await msg.reply_text("برای پاسخ، روی پیام کاربر «ریپلای» کن.")
        return

    # حالت ۲: کاربر عادی پیام داده
    u = msg.from_user
    if u.id not in seen:
        seen.add(u.id)
        try:
            photos = await context.bot.get_user_profile_photos(u.id, limit=1)
            if photos.total_count > 0:
                await context.bot.send_photo(ADMIN_ID,
                    photos.photos[0][-1].file_id, caption=header(u))
            else:
                await context.bot.send_message(ADMIN_ID, header(u))
        except Exception:
            await context.bot.send_message(ADMIN_ID, header(u))
    sent = await context.bot.send_message(ADMIN_ID, f"💬 پیام از {u.full_name}\n#id{u.id}")
    relay[sent.message_id] = u.id
    fwd = await context.bot.copy_message(chat_id=ADMIN_ID,
        from_chat_id=msg.chat.id, message_id=msg.message_id)
    relay[fwd.message_id] = u.id
    await msg.reply_text("پیام شما دریافت شد ✅ به‌زودی پاسخ داده می‌شود.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_webhook(listen="0.0.0.0", port=PORT,
        url_path=BOT_TOKEN, webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    main()
