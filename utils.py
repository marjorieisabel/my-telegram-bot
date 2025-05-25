from telebot import types

texts = {
    "id": {
        "main_menu": "Menu Utama:",
        "about": "Ini adalah bot menfess.",
        "send_menfess_prompt": "Kirim menfess mulai dengan 💚",
        "menfess_saved": "Menfess berhasil dikirim!",
        "menfess_fail": "Pesan harus diawali 💚!",
        "feature_menu": "Pilih fitur:",
        "leaderboard": "Ini leaderboard.",
        "anonchat": "Masuk ke anon chat.",
        "setting_menu": "Menu pengaturan:",
        "setting_language": "Pilih bahasa:",
        "setting_notif": "Atur notifikasi:",
        "setting_profile": "Profil kamu:",
        "setting_saved": "Pengaturan disimpan!",
        "delete_menfess": "Pilih menfess terakhir untuk dihapus:",
        "no_menfess_delete": "Tidak ada menfess yang bisa dihapus.",
        "lang_set": "Bahasa diubah.",
    },
    "en": {
        "main_menu": "Main Menu:",
        "about": "This is menfess bot.",
        "send_menfess_prompt": "Send menfess starting with 💚",
        "menfess_saved": "Menfess sent successfully!",
        "menfess_fail": "Message must start with 💚!",
        "feature_menu": "Choose a feature:",
        "leaderboard": "This is the leaderboard.",
        "anonchat": "Enter anon chat.",
        "setting_menu": "Settings menu:",
        "setting_language": "Choose language:",
        "setting_notif": "Set notifications:",
        "setting_profile": "Your profile:",
        "setting_saved": "Settings saved!",
        "delete_menfess": "Choose last menfess to delete:",
        "no_menfess_delete": "No menfess to delete.",
        "lang_set": "Language changed.",
    }
}

def get_text(user_language, key):
    return texts.get(user_language, texts["id"]).get(key, key)

def send_main_menu(bot, user_id, user_language):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("About", callback_data="about"),
        types.InlineKeyboardButton("Kirim Menfess", callback_data="send_menfess"),
        types.InlineKeyboardButton("Fitur", callback_data="feature"),
        types.InlineKeyboardButton("Setting", callback_data="setting"),
        types.InlineKeyboardButton("Hapus Fess", callback_data="delete_menfess")
    )
    bot.send_message(user_id, get_text(user_language, "main_menu"), reply_markup=markup)
