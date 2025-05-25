import telebot
from telebot import types
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1002445709942  # Ganti dengan ID channel kamu

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

pending_users = set()
user_fess_count = {}
user_messages = {}  # Simpan list pesan tiap user: {message_id, timestamp, text}
total_fess_sent = 0

banned_words = ['anjing', 'bangsat', 'kontol', 'tolol']

def contains_bad_words(text):
    return any(word in text.lower() for word in banned_words)

def can_send(user_id):
    today = datetime.now().date()
    if user_id not in user_fess_count:
        user_fess_count[user_id] = [(today, 1)]
        return True
    date_list = user_fess_count[user_id]
    if date_list[-1][0] != today:
        user_fess_count[user_id] = [(today, 1)]
        return True
    elif date_list[-1][1] < 25:
        user_fess_count[user_id][-1] = (today, date_list[-1][1] + 1)
        return True
    else:
        return False

def save_user_message(user_id, message_id, text):
    now = datetime.now()
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append({"message_id": message_id, "timestamp": now, "text": text})
    # Hapus pesan yang lebih dari 60 menit
    user_messages[user_id] = [m for m in user_messages[user_id] if now - m['timestamp'] < timedelta(minutes=60)]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_about = types.InlineKeyboardButton("📖 About", callback_data="about")
    btn_send = types.InlineKeyboardButton("💌 Kirim Menfess", callback_data="send_fess")
    btn_setting = types.InlineKeyboardButton("⚙️ Setting", callback_data="setting")
    btn_language = types.InlineKeyboardButton("🌐 Language", callback_data="language")
    btn_feature = types.InlineKeyboardButton("✨ Fitur", callback_data="fitur")
    btn_stat = types.InlineKeyboardButton("📊 Statistik", callback_data="show_stats")
    btn_unsend = types.InlineKeyboardButton("🗑️ Hapus Fess", callback_data="unsend_fess")

    markup.add(btn_about, btn_send, btn_setting, btn_language, btn_feature)
    markup.add(btn_stat, btn_unsend)
    bot.send_message(message.chat.id, "Hai! Pilih menu di bawah ini:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_menu(call):
    user_id = call.from_user.id

    if call.data == "about":
        text = ("📖 *Tentang Muncorner*\n\n"
                "Muncorner adalah bot menfess anonim untuk komunitas kita. "
                "Kirim pesan rahasia dengan mudah dan aman.\n\n"
                "Gunakan menu untuk mengakses fitur.")
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif call.data == "send_fess":
        if not can_send(user_id):
            bot.send_message(user_id, "Hey cornerpeeps! Kamu sudah mencapai batas 5 menfess hari ini. Coba lagi besok ya!")
            bot.answer_callback_query(call.id)
            return
        pending_users.add(user_id)
        bot.send_message(user_id, "Cornerpeeps! Kamu bisa langsung ketik isi menfess yang mau kamu kirim sekarang tanpa trigger apapun (bisa teks aja atau gambar dengan teks) lalu kirim.")

    elif call.data == "setting":
        bot.send_message(user_id, "⚙️ Menu Setting masih dalam pengembangan...")

    elif call.data == "language":
        bot.send_message(user_id, "🌐 Pilih bahasa yang kamu inginkan:\n(Coming soon)")

    elif call.data == "fitur":
        bot.send_message(user_id, "✨ Fitur Muncorner:\n- Kirim menfess anonim\n- Statistik pengiriman\n- Hapus fess dalam 60 menit\n- Leaderboard pribadi\n(Developing...)")

    elif call.data == "show_stats":
        bot.send_message(user_id, f"📊 Total menfess terkirim: {total_fess_sent}")

    elif call.data == "unsend_fess":
        now = datetime.now()
        recent_msgs = [m for m in user_messages.get(user_id, []) if now - m['timestamp'] < timedelta(minutes=60)]

        if not recent_msgs:
            bot.send_message(user_id, "Kamu tidak punya fess dalam 60 menit terakhir yang bisa dihapus.")
            bot.answer_callback_query(call.id)
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for m in recent_msgs:
            preview = m['text'][:30] + ("..." if len(m['text']) > 30 else "")
            btn = types.InlineKeyboardButton(f"{preview}", callback_data=f"delete_fess_{m['message_id']}")
            markup.add(btn)
        bot.send_message(user_id, "Pilih fess yang ingin kamu hapus:", reply_markup=markup)

    elif call.data.startswith("delete_fess_"):
        msg_id = int(call.data.split("_")[-1])
        try:
            bot.delete_message(CHANNEL_ID, msg_id)
            # Hapus dari list user_messages
            user_messages[user_id] = [m for m in user_messages.get(user_id, []) if m['message_id'] != msg_id]
            bot.send_message(user_id, "Fess berhasil dihapus.")
        except Exception:
            bot.send_message(user_id, "Gagal menghapus fess. Mungkin sudah lebih dari 48 jam atau sudah dihapus sebelumnya.")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_fess(message):
    global total_fess_sent
    user_id = message.from_user.id

    if user_id not in pending_users:
        bot.reply_to(message, "Klik /start dan tekan 'Kirim Menfess' dulu untuk mulai.")
        return

    try:
        msg_sent = None
        username = message.from_user.username or f"id:{user_id}"

        if message.content_type == 'text':
            text = message.text.strip()
            if len(text) > 4000:
                bot.reply_to(message, "Pesan terlalu panjang! Maksimal 4000 karakter.")
                return
            if contains_bad_words(text):
                bot.reply_to(message, "Pesan kamu mengandung kata yang tidak diperbolehkan.")
                return
            msg_sent = bot.send_message(CHANNEL_ID, "💚 " + text)

        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption.strip() if message.caption else ""
            if len(caption) > 1024:
                bot.reply_to(message, "Caption terlalu panjang! Maksimal 1024 karakter.")
                return
            if contains_bad_words(caption):
                bot.reply_to(message, "Caption kamu mengandung kata yang tidak diperbolehkan.")
                return
            msg_sent = bot.send_photo(CHANNEL_ID, file_id, caption="💚 " + caption)

        if msg_sent:
            total_fess_sent += 1
            log_text = text if message.content_type == 'text' else caption
            save_user_message(user_id, msg_sent.message_id, log_text)

            link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{msg_sent.message_id}"
            bot.send_message(user_id, f"Fess kamu sudah terkirim!\n\n[Lihat Fess]({link})", parse_mode="Markdown")

            with open("log.txt", "a") as f:
                f.write(f"{username} ({user_id}): {log_text}\n")

    except Exception as e:
        bot.reply_to(message, f"Gagal kirim fess. Error: {e}")

    pending_users.remove(user_id)

bot.infinity_polling()
