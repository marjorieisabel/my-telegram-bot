import telebot
from telebot import types
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1002445709942  # Ganti dengan ID channel kamu

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# Data storage sederhana (kalau mau lanjut, bisa ganti DB)
pending_users = set()
user_fess_count = {}  # {user_id: [(date, count), ...]}
user_last_messages = {}  # {user_id: [(message_id, datetime), ...]}
total_fess_sent = 0
banned_words = ['anjing', 'bangsat', 'kontol', 'tolol']

# Leaderboard data {user_id: count menfess}
leaderboard = {}

# Anon chat pairing {user_id: partner_id}
anon_chats = {}

# User profiles: {user_id: {lang, notif, username, fess_count}}
user_profiles = {}

# Default language per user
DEFAULT_LANG = "id"

# Text dictionary bilingual
TEXTS = {
    "id": {
        "menu": "Hai! Pilih menu di bawah ini:",
        "about": "Tentang Muncorner:\nBot ini untuk mengirim menfess secara anonim dengan fitur menarik.\n\nPengaduan? Hubungi @admin.",
        "send_fess_start": "Ketik isi menfessmu langsung, harus diawali dengan 💚 ya! Maks 4000 karakter. Contoh: 💚 Aku suka kamu.",
        "send_fess_no_heart": "Pesan harus diawali dengan emoji 💚.",
        "send_fess_too_long": "Pesan terlalu panjang! Maksimal 4000 karakter.",
        "send_fess_bad_word": "Pesan mengandung kata tidak diperbolehkan.",
        "send_fess_limit": "Kamu sudah mengirim 15 menfess hari ini, coba lagi besok ya!",
        "fess_sent": "Fess kamu sudah terkirim!\n[Lihat Fess]({link})",
        "no_pending_send": "Klik /start lalu pilih 'Kirim Menfess' dulu ya.",
        "menu_features": "Fitur-fitur kami:",
        "menu_setting": "Pengaturan kamu:",
        "leaderboard_title": "Leaderboard Menfess (nama lain blur):",
        "leaderboard_entry": "💚 {user}: {count} menfess",
        "leaderboard_no_data": "Belum ada data leaderboard.",
        "anon_start": "Kamu terhubung dengan partner anonim! Ketik /end untuk mengakhiri chat.",
        "anon_wait": "Sedang mencari partner anonim, tunggu sebentar...",
        "anon_end": "Chat anonim selesai.",
        "anon_no_chat": "Kamu belum ada chat anonim aktif.",
        "menu_stat": "Statistik kamu:\nTotal menfess terkirim: {count}",
        "delete_fess_success": "Fess terakhir kamu berhasil dihapus dari channel.",
        "delete_fess_fail": "Gagal hapus Fess. Mungkin sudah lebih dari 60 menit atau tidak ditemukan.",
        "delete_fess_no": "Kamu belum mengirim fess atau sudah dihapus semua.",
        "setting_lang": "Pilih bahasa / Choose language:",
        "setting_notif": "Notifikasi saat fess terkirim:",
        "setting_profile": "Profil kamu:",
        "setting_saved": "Pengaturan berhasil disimpan.",
        "cancel": "Perintah dibatalkan.",
    },
    "en": {
        "menu": "Hi! Please choose a menu below:",
        "about": "About Muncorner:\nThis bot lets you send anonymous menfess with fun features.\n\nReport issues? Contact @admin.",
        "send_fess_start": "Type your menfess message starting with 💚! Max 4000 chars. Example: 💚 I like you.",
        "send_fess_no_heart": "Message must start with 💚 emoji.",
        "send_fess_too_long": "Message too long! Max 4000 characters.",
        "send_fess_bad_word": "Message contains forbidden words.",
        "send_fess_limit": "You have sent 15 menfess today, try again tomorrow!",
        "fess_sent": "Your fess has been sent!\n[See Fess]({link})",
        "no_pending_send": "Please /start and choose 'Send Menfess' first.",
        "menu_features": "Our features:",
        "menu_setting": "Your settings:",
        "leaderboard_title": "Menfess Leaderboard (others blurred):",
        "leaderboard_entry": "💚 {user}: {count} menfess",
        "leaderboard_no_data": "No leaderboard data yet.",
        "anon_start": "You are connected to an anonymous partner! Type /end to finish chat.",
        "anon_wait": "Looking for an anonymous partner, please wait...",
        "anon_end": "Anonymous chat ended.",
        "anon_no_chat": "You have no active anonymous chat.",
        "menu_stat": "Your statistics:\nTotal menfess sent: {count}",
        "delete_fess_success": "Your last fess has been deleted from the channel.",
        "delete_fess_fail": "Failed to delete fess. Maybe more than 60 minutes passed or not found.",
        "delete_fess_no": "You haven't sent or already deleted all fess.",
        "setting_lang": "Choose language / Pilih bahasa:",
        "setting_notif": "Notification on fess sent:",
        "setting_profile": "Your profile:",
        "setting_saved": "Settings saved.",
        "cancel": "Command cancelled.",
    }
}

def get_text(user_id, key):
    lang = user_profiles.get(user_id, {}).get("lang", DEFAULT_LANG)
    return TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key, "")

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
    elif date_list[-1][1] < 15:
        user_fess_count[user_id][-1] = (today, date_list[-1][1] + 1)
        return True
    else:
        return False

def update_leaderboard(user_id):
    leaderboard[user_id] = leaderboard.get(user_id, 0) + 1

def add_fess_message(user_id, message_id):
    now = datetime.now()
    if user_id not in user_last_messages:
        user_last_messages[user_id] = []
    user_last_messages[user_id].append((message_id, now))
    # Keep only messages within 60 minutes
    user_last_messages[user_id] = [(mid, dt) for (mid, dt) in user_last_messages[user_id] if now - dt <= timedelta(minutes=60)]

def find_anon_partner(user_id):
    # Find a waiting user to pair with, exclude self
    waiting = [uid for uid in anon_chats if anon_chats[uid] is None and uid != user_id]
    if waiting:
        partner = waiting[0]
        anon_chats[user_id] = partner
        anon_chats[partner] = user_id
        return partner
    else:
        # Mark user as waiting
        anon_chats[user_id] = None
        return None

def end_anon_chat(user_id):
    partner = anon_chats.get(user_id)
    if partner is not None:
        anon_chats.pop(partner, None)
    anon_chats.pop(user_id, None)

def mask_username(username):
    if not username:
        return "anonymous"
    if len(username) <= 2:
        return username[0] + "*"
    else:
        # Blur all but first and last char
        return username[0] + "*"*(len(username)-2) + username[-1]

# MENU HANDLER
@bot.message_handler(commands=['start'])
def send_main_menu(message):
    user_id = message.from_user.id
    user_profiles.setdefault(user_id, {"lang": DEFAULT_LANG, "notif": True, "username": message.from_user.username or "", "fess_count": 0})
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📖 About", callback_data="about"),
        types.InlineKeyboardButton("💌 Kirim Menfess", callback_data="send_fess"),
        types.InlineKeyboardButton("✨ Fitur", callback_data="features"),
        types.InlineKeyboardButton("⚙️ Setting", callback_data="setting"),
        types.InlineKeyboardButton("📊 Statistik", callback_data="statistic"),
        types.InlineKeyboardButton("🗑️ Hapus Fess", callback_data="delete_fess")
    )
    bot.send_message(user_id, get_text(user_id, "menu"), reply_markup=markup)

# CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    data = call.data
    lang = user_profiles.get(user_id, {}).get("lang", DEFAULT_LANG)

    if data == "about":
        bot.send_message(user_id, get_text(user_id, "about"))

    elif data == "send_fess":
        if not can_send(user_id):
            bot.send_message(user_id, get_text(user_id, "send_fess_limit"))
            bot.answer_callback_query(call.id)
            return
        pending_users.add(user_id)
        bot.send_message(user_id, get_text(user_id, "send_fess_start"))

    elif data == "features":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📈 Leaderboard Menfess", callback_data="feature_leaderboard"),
            types.InlineKeyboardButton("💬 Anon Chat", callback_data="feature_anonchat"),
            types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
        )
        bot.send_message(user_id, get_text(user_id, "menu_features"), reply_markup=markup)

    elif data == "setting":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👤 Profil", callback_data="setting_profile"),
            types.InlineKeyboardButton("🌐 Bahasa / Language", callback_data="setting_language"),
            types.InlineKeyboardButton("🔔 Notifikasi", callback_data="setting_notification"),
            types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
        )
        bot.send_message(user_id, get_text(user_id, "menu_setting"), reply_markup=markup)

    elif data == "statistic":
        fess_count = user_profiles.get(user_id, {}).get("fess_count", 0)
        bot.send_message(user_id, get_text(user_id, "menu_stat").format(count=fess_count))

    elif data == "delete_fess":
        msgs = user_last_messages.get(user_id, [])
        if not msgs:
            bot.send_message(user_id, get_text(user_id, "delete_fess_no"))
        else:
            markup = types.InlineKeyboardMarkup()
            now = datetime.now()
            for i, (msg_id, dt) in enumerate(msgs):
                diff = now - dt
                if diff <= timedelta(minutes=60):
                    btn = types.InlineKeyboardButton(f"Fess {i+1} ({dt.strftime('%H:%M')})", callback_data=f"delete_msg_{msg_id}")
                    markup.add(btn)
            if not markup.keyboard:
                bot.send_message(user_id, get_text(user_id, "delete_fess_fail"))
            else:
                bot.send_message(user_id, "Pilih fess yang ingin dihapus:", reply_markup=markup)

    elif data.startswith("delete_msg_"):
        msg_id = int(data[len("delete_msg_"):])
        try:
            bot.delete_message(CHANNEL_ID, msg_id)
            # Remove from user_last_messages
            user_last_messages[user_id] = [(mid, dt) for (mid, dt) in user_last_messages[user_id] if mid != msg_id]
            bot.send_message(user_id, get_text(user_id, "delete_fess_success"))
        except Exception:
            bot.send_message(user_id, get_text(user_id, "delete_fess_fail"))

    elif data == "feature_leaderboard":
        if not leaderboard:
            bot.send_message(user_id, get_text(user_id, "leaderboard_no_data"))
        else:
            lines = [get_text(user_id, "leaderboard_title")]
            for uid, count in sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]:
                profile = user_profiles.get(uid, {})
                uname = profile.get("username") or f"id:{uid}"
                if uid == user_id:
                    lines.append(get_text(user_id, "leaderboard_entry").format(user=uname, count=count))
                else:
                    lines.append(get_text(user_id, "leaderboard_entry").format(user=mask_username(uname), count=count))
            bot.send_message(user_id, "\n".join(lines))

    elif data == "feature_anonchat":
        partner = find_anon_partner(user_id)
        if partner:
            bot.send_message(user_id, get_text(user_id, "anon_start"))
            bot.send_message(partner, get_text(partner, "anon_start"))
        else:
            bot.send_message(user_id, get_text(user_id, "anon_wait"))

    elif data == "setting_profile":
        profile = user_profiles.get(user_id, {})
        uname = profile.get("username", "unknown")
        fcount = profile.get("fess_count", 0)
        text = f"{get_text(user_id, 'setting_profile')}\nUsername: @{uname}\nTotal menfess: {fcount}"
        bot.send_message(user_id, text)

    elif data == "setting_language":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Indonesia 🇮🇩", callback_data="set_lang_id"),
            types.InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en"),
            types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_setting")
        )
        bot.send_message(user_id, get_text(user_id, "setting_lang"), reply_markup=markup)

    elif data == "set_lang_id":
        user_profiles[user_id]["lang"] = "id"
        bot.send_message(user_id, get_text(user_id, "setting_saved"))

    elif data == "set_lang_en":
        user_profiles[user_id]["lang"] = "en"
        bot.send_message(user_id, get_text(user_id, "setting_saved"))

elif data == "setting_notification":
    profile = user_profiles.get(user_id, {})
    notif = profile.get("notif", True)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("On ✅" if notif else "On",
                                   callback_data="notif_on"),
        types.InlineKeyboardButton("Off ✅" if not notif else "Off",
                                   callback_data="notif_off"),
        types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_setting")
    )
    bot.send_message(user_id, get_text(user_id, "setting_notif"), reply_markup=markup)

elif data == "notif_on":
    user_profiles[user_id]["notif"] = True
    bot.send_message(user_id, get_text(user_id, "setting_saved"))

elif data == "notif_off":
    user_profiles[user_id]["notif"] = False
    bot.send_message(user_id, get_text(user_id, "setting_saved"))

elif data == "back_main":
    # Kirim menu utama lagi
    send_main_menu(call.message)

elif data == "back_setting":
    # Kirim menu setting lagi
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👤 Profil", callback_data="setting_profile"),
        types.InlineKeyboardButton("🌐 Bahasa / Language", callback_data="setting_language"),
        types.InlineKeyboardButton("🔔 Notifikasi", callback_data="setting_notification"),
        types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
    )
    bot.send_message(user_id, get_text(user_id, "menu_setting"), reply_markup=markup)
