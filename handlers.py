from telebot import types
from datetime import datetime, timedelta
from utils import (
    pending_users, user_fess_count, user_last_messages, leaderboard, anon_chats, user_profiles,
    get_text, can_send, contains_bad_words, update_leaderboard, add_fess_message,
    find_anon_partner, end_anon_chat, mask_username, leaderboard_get_last_7days, leaderboard_get_today_total
)

CHANNEL_ID = -1002445709942

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_main_menu(message):
        user_id = message.from_user.id
        user_profiles.setdefault(user_id, {"lang": "id", "notif": True, "username": message.from_user.username or "", "fess_count": 0})
        send_menu(bot, user_id)

    def send_menu(bot, user_id):
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

    @bot.message_handler(func=lambda message: message.from_user.id in pending_users)
    def handle_fess_message(message):
        user_id = message.from_user.id
        text = message.text
        if not text:
            bot.send_message(user_id, "Pesan tidak boleh kosong!")
            return
        if "💚" not in text:
            bot.send_message(user_id, "Menfess wajib mengandung emoji 💚.")
            return
        if contains_bad_words(text):
            bot.send_message(user_id, get_text(user_id, "bad_words_warning"))
            return
        msg = bot.send_message(CHANNEL_ID, text)
        update_leaderboard(user_id)
        add_fess_message(user_id, msg.message_id)
        pending_users.discard(user_id)
        bot.send_message(user_id, get_text(user_id, "send_fess_success"))

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        user_id = call.from_user.id
        data = call.data

        if data == "about":
            bot.send_message(user_id, get_text(user_id, "about_muncorner"))
        elif data == "send_fess":
            if not can_send(user_id):
                bot.send_message(user_id, get_text(user_id, "send_fess_limit"))
                return
            pending_users.add(user_id)
            bot.send_message(user_id, get_text(user_id, "send_fess_start"))
        elif data == "features":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🏆 Leaderboard Menfess", callback_data="feature_leaderboard"),
                types.InlineKeyboardButton("💬 Anon Chat", callback_data="feature_anonchat"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
            )
            bot.send_message(user_id, get_text(user_id, "menu_features"), reply_markup=markup)
        elif data == "back_main":
            send_menu(bot, user_id)
        elif data == "feature_leaderboard":
            ranking = leaderboard_get_last_7days()
            text = get_text(user_id, "leaderboard_title") + "\n\n"
            for uid, count in ranking:
                if uid == user_id:
                    text += f"👑 Kamu: {count} menfess\n"
                else:
                    uname = mask_username(user_profiles.get(uid, {}).get("username", "anonymous"))
                    text += f"{uname}: {count} menfess\n"
            bot.send_message(user_id, text)
        elif data == "statistic":
            personal_count = leaderboard.get(user_id, 0)
            total_count = leaderboard_get_today_total()
            text = get_text(user_id, "statistic_personal", count=personal_count) + "\n" + \
                   get_text(user_id, "statistic_total", count=total_count)
            bot.send_message(user_id, text)
        elif data == "setting":
            bot.send_message(user_id, "Menu setting akan segera tersedia.")
        elif data == "delete_fess":
            msgs = user_last_messages.get(user_id, [])
            if not msgs:
                bot.send_message(user_id, get_text(user_id, "delete_fess_no"))
            else:
                markup = types.InlineKeyboardMarkup()
                now = datetime.now()
                for i, (msg_id, dt) in enumerate(msgs):
                    if now - dt <= timedelta(minutes=60):
                        markup.add(types.InlineKeyboardButton(f"Fess {i+1} ({dt.strftime('%H:%M')})", callback_data=f"delete_msg_{msg_id}"))
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
            except:
                bot.send_message(user_id, get_text(user_id, "delete_fess_fail"))
        elif data == "feature_anonchat":
            partner = find_anon_partner(user_id)
            if partner:
                bot.send_message(user_id, get_text(user_id, "anon_chat_start"))
                bot.send_message(partner, get_text(partner, "anon_chat_start"))
            else:
                bot.send_message(user_id, get_text(user_id, "anon_chat_wait"))

    @bot.message_handler(func=lambda message: anon_chats.get(message.from_user.id))
    def handle_anon_message(message):
        user_id = message.from_user.id
        partner_id = anon_chats.get(user_id)
        if partner_id:
            bot.send_message(partner_id, f"Partner: {message.text}")
