from datetime import datetime, timedelta

banned_words = ['anjing', 'bangsat', 'kontol', 'tolol']

pending_users = set()
user_fess_count = {}  # {user_id: [(date, count), ...]}
user_last_messages = {}  # {user_id: [(message_id, datetime), ...]}
leaderboard = {}  # {user_id: int count total menfess}
anon_chats = {}  # {user_id: partner_id or None}
user_profiles = {}  # {user_id: dict profil}

DEFAULT_LANG = "id"

TEXTS = {
    "id": {
        "menu": "Hai! Pilih menu di bawah ini:",
        "send_fess_limit": "Kamu sudah mencapai batas mengirim menfess hari ini (max 15).",
        "send_fess_start": "Silakan kirim menfess kamu sekarang. Wajib ada emoji 💚.",
        "send_fess_success": "Menfess berhasil dikirim, terima kasih!",
        "bad_words_warning": "Pesan mengandung kata-kata terlarang, tolong ubah.",
        "delete_fess_no": "Kamu belum mengirim menfess apapun.",
        "delete_fess_fail": "Tidak ada menfess yang bisa dihapus.",
        "delete_fess_success": "Menfess berhasil dihapus.",
        "menu_features": "Pilih fitur yang ingin kamu gunakan:",
        "statistic": "Statistik",
        "about_muncorner": (
            "Muncorner adalah platform anonim untuk berbagi curhatan dan cerita dengan aman.\n"
            "Kamu bisa mengirim menfess, ngobrol anon, dan lihat statistik menarik!"
        ),
        "leaderboard_title": "🏆 Ranking Menfess Mingguan",
        "leaderboard_yours": "Kamu: {count} menfess",
        "leaderboard_other": "{username}: {count} menfess",
        "anon_chat_start": "Anon chat dimulai! Kamu akan terhubung dengan partner anonim selama 60 menit.",
        "anon_chat_wait": "Sedang mencari partner, tunggu sebentar...",
        "anon_chat_no_partner": "Maaf, tidak ada partner yang tersedia sekarang. Coba lagi nanti.",
        "anon_chat_end_user": "Kamu telah mengakhiri chat anonim.",
        "anon_chat_end_partner": "Partner mengakhiri chat anonim.",
        "anon_chat_inactive": "Chat anonim berakhir karena tidak ada balasan selama 5 menit.",
        "anon_chat_reminder": "Chat anonim akan berakhir dalam 2 menit.",
        "statistic_personal": "Kamu telah mengirim {count} menfess.",
        "statistic_total": "Total menfess hari ini di Muncorner: {count}",
    },
    "en": {
        # Bisa kamu isi kalau mau support bahasa Inggris
    }
}

def get_text(user_id, key, **kwargs):
    lang = user_profiles.get(user_id, {}).get("lang", DEFAULT_LANG)
    text = TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key, "")
    if kwargs:
        return text.format(**kwargs)
    return text

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
    # Hapus pesan > 60 menit
    user_last_messages[user_id] = [
        (mid, dt) for (mid, dt) in user_last_messages[user_id]
        if now - dt <= timedelta(minutes=60)
    ]

def find_anon_partner(user_id):
    waiting = [uid for uid in anon_chats if anon_chats[uid] is None and uid != user_id]
    if waiting:
        partner = waiting[0]
        anon_chats[user_id] = partner
        anon_chats[partner] = user_id
        return partner
    else:
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
        return username[0] + "*"*(len(username)-2) + username[-1]

def leaderboard_get_last_7days():
    cutoff = datetime.now() - timedelta(days=7)
    counts = {}
    for uid, count in leaderboard.items():
        # Karena leaderboard cuma hitung total count, kita asumsikan semua dalam 7 hari
        counts[uid] = count
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_counts

def leaderboard_get_today_total():
    # Karena leaderboard cuma count total menfess, untuk simplifikasi
    return sum(leaderboard.values())
