from telebot import types
from datetime import datetime, timedelta
from utils import get_text, send_main_menu

# Data global (bisa diubah jadi db atau file nanti)
user_profiles = {}
user_menfess = {}
user_language = {}

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        if user_id not in user_language:
            user_language[user_id] = 'id'
        if user_id not in user_profiles:
            user_profiles[user_id] = {"notif": True}
        send_main_menu(bot, user_id, user_language[user_id])

    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        user_id = call.from_user.id
        data = call.data
        lang = user_language.get(user_id, 'id')

        if data == "about":
            bot.send_message(user_id, get_text(lang, "about"))
            send_main_menu(bot, user_id, lang)

        elif data == "send_menfess":
            bot.send_message(user_id, get_text(lang, "send_menfess_prompt"))
            bot.register_next_step_handler_by_chat_id(user_id, process_menfess)

        elif data == "feature":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("Leaderboard", callback_data="leaderboard"),
                types.InlineKeyboardButton("Anon Chat", callback_data="anonchat"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
            )
            bot.send_message(user_id, get_text(lang, "feature_menu"), reply_markup=markup)

        elif data == "leaderboard":
            bot.send_message(user_id, get_text(lang, "leaderboard"))
            send_main_menu(bot, user_id, lang)

        elif data == "anonchat":
            bot.send_message(user_id, get_text(lang, "anonchat"))
            send_main_menu(bot, user_id, lang)

        elif data == "setting":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🌐 Bahasa / Language", callback_data="setting_language"),
                types.InlineKeyboardButton("🔔 Notifikasi", callback_data="setting_notification"),
                types.InlineKeyboardButton("👤 Profil", callback_data="setting_profile"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")
            )
            bot.send_message(user_id, get_text(lang, "setting_menu"), reply_markup=markup)

        elif data == "setting_language":
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("Indonesia 🇮🇩" + (" ✅" if lang == "id" else ""),
                                           callback_data="lang_id"),
                types.InlineKeyboardButton("English 🇺🇸" + (" ✅" if lang == "en" else ""),
                                           callback_data="lang_en"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_setting")
            )
            bot.send_message(user_id, get_text(lang, "setting_language"), reply_markup=markup)

        elif data == "lang_id":
            user_language[user_id] = "id"
            bot.send_message(user_id, get_text("id", "lang_set"))
            send_main_menu(bot, user_id, "id")

        elif data == "lang_en":
            user_language[user_id] = "en"
            bot.send_message(user_id, get_text("en", "lang_set"))
            send_main_menu(bot, user_id, "en")

        elif data == "setting_notification":
            profile = user_profiles.get(user_id, {})
            notif = profile.get("notif", True)
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("On ✅" if notif else "On", callback_data="notif_on"),
                types.InlineKeyboardButton("Off ✅" if not notif else "Off", callback_data="notif_off"),
                types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_setting")
            )
            bot.send_message(user_id, get_text(lang, "setting_notif"), reply_markup=markup)

        elif data == "notif_on":
            user_profiles[user_id]["notif"] = True
            bot.send_message(user_id, get_text(lang, "setting_saved"))
            send_main_menu(bot, user_id, lang)

        elif data == "notif_off":
            user_profiles[user_id]["notif"] = False
            bot.send_message(user_id, get_text(lang, "setting_saved"))
            send_main_menu(bot, user_id, lang)

        elif data == "setting_profile":
            profile = user_profiles.get(user_id, {})
            notif = profile.get("notif", True)
            lang = user_language.get(user_id, "id")
            text = (f"Profil kamu:\n- Bahasa: {lang}\n- Notifikasi: {'On' if notif else 'Off'}\n"
                    f"- Jumlah Menfess terkirim: {len(user_menfess.get(user_id, []))}")
            bot.send_message(user_id, text)
            send_main_menu(bot, user_id, lang)

        elif data == "delete_menfess":
            menfess_list = user_menfess.get(user_id, [])
            now = datetime.utcnow()
            recent_menfess = [(mid, text) for (mid, text, ts) in menfess_list if now - ts < timedelta(minutes=60)]
            if not recent_menfess:
                bot.send_message(user_id, get_text(lang, "no_menfess_delete"))
                send_main_menu(bot, user_id, lang)
            else:
                markup = types.InlineKeyboardMarkup(row_width=1)
                for mid, text in recent_menfess:
                    display_text = (text[:20] + '...') if len(text) > 20 else text
                    markup.add(types.InlineKeyboardButton(display_text, callback_data=f"delmenfess_{mid}"))
                markup.add(types.InlineKeyboardButton("⬅️ Kembali", callback_data="back_main"))
                bot.send_message(user_id, get_text(lang, "delete_menfess"), reply_markup=markup)

        elif data.startswith("delmenfess_"):
            menfess_id = int(data.split("_")[1])
            menfess_list = user_menfess.get(user_id, [])
            user_menfess[user_id] = [(mid, t, ts) for (mid
