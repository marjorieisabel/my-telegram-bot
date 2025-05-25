from telebot import types
from datetime import datetime, timedelta
from utils import (
    pending_users, user_fess_count, user_last_messages, leaderboard, anon_chats, user_profiles,
    get_text, can_send, contains_bad_words, update_leaderboard, add_fess_message,
    find_anon_partner, end_anon_chat, mask_username, get_leaderboard, get_total_menfess_today, get_user_fess_count,
    user_id_in_anon_chat
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
            bot.send_message(user_id, "💌 **Tentang Muncorner** 💌\n\nMuncorner adalah platform bot Telegram untuk mengirim menfess anonim dan chatting secara rahasia. Kami mendukung privasi dan interaksi yang seru tanpa batasan identitas!\n\nGunakan dengan bijak ya!")
            bot.answer_callback_query(call.id)

        elif data == "send_fess":
            if not can_send(user_id):
                bot.send_message(user_id, get_text(user_id, "send_fess_limit"))
                bot.answer_callback_query(call.id)
                return
            # Pastikan user tidak dalam anon chat dan pending users bersih
            anon_chats.pop(user_id, None)
            pending_users.add(user_id)
            bot.send_message(user_id, "Silakan ketik pesan menfess-mu (wajib ada 💚):")
            bot.answer_callback_query(call.id)

        elif data == "features":
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📈 Leaderboard Menfess", callback_data="feature_leaderboard"),
                types.InlineKeyboardButton("💬 Anon Chat", callback_data="feature_anonchat"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
            )
            bot.send_message(user_id, "✨ Pilih fitur yang ingin kamu lihat:", reply_markup=markup)
            bot.answer_callback_query(call.id)

        elif data == "feature_leaderboard":
            ranking = get_leaderboard()
            text = "📈 **Leaderboard Menfess Mingguan** 📈\n\n"
            for idx, (uid, count) in enumerate(ranking, 1):
                name = user_profiles.get(uid, {}).get("username", "anon")
                name = mask_username(name) if uid != user_id else name
                text += f"{idx}. {name} - {count} fess\n"
            bot.send_message(user_id, text)
            bot.answer_callback_query(call.id)

        elif data == "feature_anonchat":
            # Hapus dari pending users jika ada
            pending_users.discard(user_id)
            partner = find_anon_partner(user_id)
            if partner:
                bot.send_message(user_id, "Partner ditemukan! Mulai ngobrol sekarang.\nKetik /end untuk mengakhiri chat.\nIngat, chat akan otomatis berakhir dalam 60 menit jika tidak aktif.")
                bot.send_message(partner, "Partner ditemukan! Mulai ngobrol sekarang.\nKetik /end untuk mengakhiri chat.\nIngat, chat akan otomatis berakhir dalam 60 menit jika tidak aktif.")
            else:
                bot.send_message(user_id, "Menunggu partner anon... Sabar ya!")
            bot.answer_callback_query(call.id)

        elif data == "setting":
            bot.send_message(user_id, "⚙️ Fitur pengaturan akan segera hadir!")
            bot.answer_callback_query(call.id)

        elif data == "statistic":
            personal = get_user_fess_count(user_id)
            total = get_total_menfess_today()
            bot.send_message(user_id, f"📊 Statistik Menfess:\n\n- Menfess kamu hari ini: {personal}\n- Total menfess Muncorner hari ini: {total}")
            bot.answer_callback_query(call.id)

        elif data == "delete_fess":
            msgs = user_last_messages.get(user_id, [])
            markup = types.InlineKeyboardMarkup()
            now = datetime.now()
            for i, (msg_id, dt) in enumerate(msgs):
                if now - dt <= timedelta(minutes=60):
                    markup.add(types.InlineKeyboardButton(f"Fess {i+1} ({dt.strftime('%H:%M')})", callback_data=f"delete_msg_{msg_id}"))
            if markup.keyboard:
                bot.send_message(user_id, "Pilih fess yang ingin dihapus:", reply_markup=markup)
            else:
                bot.send_message(user_id, "Kamu tidak memiliki fess yang bisa dihapus.")
            bot.answer_callback_query(call.id)

        elif data.startswith("delete_msg_"):
            msg_id = int(data[len("delete_msg_"):])
            try:
                bot.delete_message(CHANNEL_ID, msg_id)
                user_last_messages[user_id] = [(mid, dt) for (mid, dt) in user_last_messages.get(user_id, []) if mid != msg_id]
                bot.send_message(user_id, "Fess berhasil dihapus!")
            except Exception:
                bot.send_message(user_id, "Gagal menghapus fess.")
            bot.answer_callback_query(call.id)

        elif data == "back_main":
            send_main_menu(call.message)
            bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        user_id = message.from_user.id
        text = message.text

        if user_id in pending_users:
            # Proses kirim menfess
            if "💚" not in text:
                bot.send_message(user_id, "Fess kamu harus mengandung 💚. Silakan coba lagi.")
                return
            if contains_bad_words(text):
                bot.send_message(user_id, "Pesan menfess kamu mengandung kata yang tidak diperbolehkan.")
                return
            msg = bot.send_message(CHANNEL_ID, f"💌 Pesan anonim:\n{text}")
            add_fess_message(user_id, msg.message_id)
            update_leaderboard(user_id)
            pending_users.discard(user_id)
            bot.send_message(user_id, "Fess kamu telah dikirim ke Muncorner!")

        elif user_id_in_anon_chat(user_id):
            # Proses pesan anon chat
            partner = anon_chats.get(user_id)
            if partner:
                bot.send_message(partner, f"Anon: {text}")

        else:
            # Pesan biasa yang tidak ter-handle
            bot.send_message(user_id, "Ketik /start untuk mulai.")

    @bot.message_handler(commands=['end'])
    def handle_end(message):
        user_id = message.from_user.id
        partner = anon_chats.get(user_id)
        if partner:
            bot.send_message(partner, "Partner telah mengakhiri percakapan.")
            bot.send_message(user_id, "Kamu telah mengakhiri percakapan.")
            end_anon_chat(user_id)
        else:
            bot.send_message(user_id, "Kamu tidak sedang dalam percakapan anon.")
