from telebot import types
from datetime import datetime, timedelta
from utils import (
    pending_users, user_fess_count, user_last_messages, leaderboard, anon_chats, user_profiles,
    get_text, can_send, contains_bad_words, update_leaderboard, add_fess_message,
    find_anon_partner, end_anon_chat, mask_username
)

CHANNEL_ID = -1002445709942

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_main_menu(message):
        user_id = message.from_user.id
        user_profiles.setdefault(user_id, {"lang": "id", "notif": True, "username": message.from_user.username or "", "fess_count": 0})
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

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        user_id = call.from_user.id
        data = call.data

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

        # Tambahkan semua callback lainnya mirip dengan contoh di atas
        # ...

        # Contoh untuk delete_fess
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
                user_last_messages[user_id] = [(mid, dt) for (mid, dt) in user_last_messages[user_id] if mid != msg_id]
                bot.send_message(user_id, get_text(user_id, "delete_fess_success"))
            except Exception:
                bot.send_message(user_id, get_text(user_id, "delete_fess_fail"))

        # Tambahkan handler lain sesuai kode awal
