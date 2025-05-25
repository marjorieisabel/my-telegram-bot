from telebot import types
from datetime import datetime, timedelta
from utils import (
    pending_users, user_fess_count, user_last_messages, leaderboard, anon_chats, user_profiles,
    get_text, can_send, contains_bad_words, update_leaderboard, add_fess_message,
    find_anon_partner, end_anon_chat, mask_username
)

CHANNEL_ID = -1002445709942
ANON_CHAT_DURATION = 60 * 60  # 60 menit dalam detik
ANON_CHAT_TIMEOUT = 5 * 60     # 5 menit timeout
ANON_CHAT_REMINDER = 2 * 60    # 2 menit reminder sebelum selesai


def register_handlers(bot):
    # START & MENU UTAMA
    @bot.message_handler(commands=['start'])
    def send_main_menu(message):
        user_id = message.from_user.id
        user_profiles.setdefault(user_id, {
            "lang": "id",
            "notif": True,
            "username": message.from_user.username or "",
            "fess_count": 0
        })
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


    # CALLBACK QUERY HANDLER (untuk tombol inline)
    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        user_id = call.from_user.id
        data = call.data

        try:
            # ABOUT: Jelasin Muncorner
            if data == "about":
                about_text = (
                    "Muncorner adalah platform anonim untuk berbagi cerita, "
                    "curhat, dan menfess secara bebas dengan komunitas. "
                    "Kami jaga privasi dan kebebasan berekspresi kamu."
                )
                bot.send_message(user_id, about_text)
                bot.answer_callback_query(call.id)

            # KIRIM MENFESS (tombol buka input)
            elif data == "send_fess":
                if not can_send(user_id):
                    bot.send_message(user_id, get_text(user_id, "send_fess_limit"))
                    bot.answer_callback_query(call.id)
                    return
                pending_users.add(user_id)
                bot.send_message(user_id, "Kirim menfess kamu sekarang! **Wajib ada emoji 💚 dalam pesan, jika tidak maka pesan tidak akan dikirim.**")
                bot.answer_callback_query(call.id)

            # FITUR LANJUTAN
            elif data == "features":
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("📈 Leaderboard Menfess", callback_data="feature_leaderboard"),
                    types.InlineKeyboardButton("💬 Anon Chat", callback_data="feature_anonchat"),
                    types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
                )
                bot.send_message(user_id, get_text(user_id, "menu_features"), reply_markup=markup)
                bot.answer_callback_query(call.id)

            # LEADERBOARD MENFESS 1 MINGGU
            elif data == "feature_leaderboard":
                # Ambil data leaderboard (fess terbanyak 7 hari terakhir)
                rankings = leaderboard.get_last_7days()  # Asumsikan fungsi ini ada dan return list [(user_id, count), ...]
                text = "📈 *Leaderboard Menfess Mingguan*\n\n"
                rank = 1
                for uid, count in rankings:
                    if uid == user_id:
                        username = user_profiles.get(uid, {}).get("username") or f"user{uid}"
                    else:
                        username = mask_username(user_profiles.get(uid, {}).get("username") or f"user{uid}")
                    text += f"{rank}. {username}: {count} menfess\n"
                    rank += 1
                    if rank > 10:
                        break
                bot.send_message(user_id, text, parse_mode="Markdown")
                bot.answer_callback_query(call.id)

            # ANON CHAT
            elif data == "feature_anonchat":
                if user_id in anon_chats:
                    bot.send_message(user_id, "Kamu sudah sedang chat anon. Kirim pesan atau /end_anon untuk akhiri.")
                    bot.answer_callback_query(call.id)
                    return
                partner_id = find_anon_partner(user_id)
                if partner_id:
                    anon_chats[user_id] = {
                        "partner": partner_id,
                        "start": datetime.now(),
                        "last_msg": datetime.now()
                    }
                    anon_chats[partner_id] = {
                        "partner": user_id,
                        "start": datetime.now(),
                        "last_msg": datetime.now()
                    }
                    bot.send_message(user_id, "Anon chat dimulai! Kamu bisa ngobrol selama 60 menit.")
                    bot.send_message(partner_id, "Anon chat dimulai! Kamu bisa ngobrol selama 60 menit.")
                else:
                    bot.send_message(user_id, "Belum ada partner anon chat yang tersedia, coba lagi nanti ya.")
                bot.answer_callback_query(call.id)

            # KEMBALI KE MENU UTAMA
            elif data == "back_main":
                send_main_menu(call.message)
                bot.answer_callback_query(call.id)

            # HAPUS MENFESS
            elif data == "delete_fess":
                msgs = user_last_messages.get(user_id, [])
                if not msgs:
                    bot.send_message(user_id, get_text(user_id, "delete_fess_no"))
                    bot.answer_callback_query(call.id)
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
                    bot.answer_callback_query(call.id)

            elif data.startswith("delete_msg_"):
                msg_id = int(data[len("delete_msg_"):])
                try:
                    bot.delete_message(CHANNEL_ID, msg_id)
                    user_last_messages[user_id] = [(mid, dt) for (mid, dt) in user_last_messages.get(user_id, []) if mid != msg_id]
                    bot.send_message(user_id, get_text(user_id, "delete_fess_success"))
                except Exception:
                    bot.send_message(user_id, get_text(user_id, "delete_fess_fail"))
                bot.answer_callback_query(call.id)

            # STATISTIK
            elif data == "statistic":
                user_count = user_fess_count.get(user_id, 0)
                total_daily = leaderboard.get_today_total()  # Asumsikan fungsi ini ada
                text = (
                    f"📊 Statistik Kamu:\n"
                    f"- Jumlah menfess kamu: {user_count}\n\n"
                    f"📊 Statistik Muncorner hari ini:\n"
                    f"- Total menfess semua user: {total_daily}"
                )
                bot.send_message(user_id, text)
                bot.answer_callback_query(call.id)

            else:
                bot.answer_callback_query(call.id, text="Fitur belum tersedia atau tidak dikenal.")

        except Exception as e:
            print(f"Error di callback handler: {e}")
            bot.answer_callback_query(call.id, text="Terjadi kesalahan, coba lagi nanti.")


    # HANDLE PESAN PENDING MENFESS
    @bot.message_handler(func=lambda m: m.from_user.id in pending_users)
    def handle_pending_fess(message):
        user_id = message.from_user.id
        text = message.text or ""

        # Wajib ada emoji 💚
        if "💚" not in text:
            bot.send_message(user_id, "Pesan menfess harus mengandung emoji 💚, coba lagi ya!")
            return

        if contains_bad_words(text):
            bot.send_message(user_id, get_text(user_id, "bad_words_warning"))
            return

        # Kirim ke channel
        msg = bot.send_message(CHANNEL_ID, text)
        now = datetime.now()
        user_last_messages.setdefault(user_id, []).append((msg.message_id, now))
        user_fess_count[user_id] = user_fess_count.get(user_id, 0) + 1
        update_leaderboard(user_id)

        bot.send_message(user_id, get_text(user_id, "send_fess_success"))
        pending_users.remove(user_id)


    # HANDLE ANON CHAT MESSAGE
    @bot.message_handler(func=lambda m: m.from_user.id in anon_chats)
    def handle_anon_chat_message(message):
        user_id = message.from_user.id
        chat = anon_chats.get(user_id)
        if not chat:
            return
        partner_id = chat["partner"]
        now = datetime.now()

        # Update last message timestamp
        chat["last_msg"] = now
        anon_chats[partner_id]["last_msg"] = now

        # Kirim pesan ke partner
        text = f"Anon Chat: {message.text}"
        bot.send_message(partner_id, text)

        # Cek durasi chat (60 menit)
        if (now - chat["start"]).total_seconds() > ANON_CHAT_DURATION:
            bot.send_message(user_id, "Anon chat sudah selesai 60 menit.")
            bot.send_message(partner_id, "Anon chat sudah selesai 60 menit.")
            end_anon_chat(user_id)
            return

        # Reminder 2 menit sebelum selesai
        remaining = ANON_CHAT_DURATION - (now - chat["start"]).total_seconds()
        if remaining <= ANON_CHAT_REMINDER:
            bot.send_message(user_id, f"Anon chat akan selesai dalam {int(remaining // 60)} menit.")
            bot.send_message(partner_id, f"Anon chat akan selesai dalam {int(remaining // 60)} menit.")


    # COMMAND /end_anon untuk mengakhiri chat anon sendiri
    @bot.message_handler(commands=['end_anon'])
    def end_anon_command(message):
        user_id = message.from_user.id
        if user_id not in anon_chats:
            bot.send_message(user_id, "Kamu sedang tidak dalam anon chat.")
            return
        partner_id = anon_chats[user_id]["partner"]
        bot.send_message(user_id, "Kamu mengakhiri anon chat.")
        bot.send_message(partner_id, "Partner mengakhiri anon chat.")
        end_anon_chat(user_id)


    # CEK DAN END ANON CHAT JIKA TIDAK BALAS 5 MENIT
    # Fungsi ini harus dijalankan secara periodik (misal pakai scheduler eksternal)
    def check_anon_timeouts():
        now = datetime.now()
        to_end = []
        for uid, chat in anon_chats.items():
            last_msg = chat.get("last_msg")
            if last_msg and (now - last_msg).total_seconds() > ANON_CHAT_TIMEOUT:
                to_end.append(uid)
        for uid in to_end:
            partner_id = anon_chats[uid]["partner"]
            bot.send_message(uid, "Anon chat berakhir karena tidak ada balasan selama 5 menit.")
            bot.send_message(partner_id, "Anon chat berakhir karena partner tidak membalas selama 5 menit.")
            end_anon_chat(uid)
