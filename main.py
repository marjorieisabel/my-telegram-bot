import telebot
from handlers import register_handlers

API_TOKEN = "7676988779:AAGsGWqRyyGrZt17SNZSAXRvh8KGRCmnYhU"  # ganti dengan token bot kamu

bot = telebot.TeleBot(API_TOKEN)

# Register semua handler callback dan message
register_handlers(bot)

print("Bot started...")
bot.infinity_polling()
