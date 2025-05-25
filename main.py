import os
import telebot
from handlers import register_handlers

TOKEN = os.getenv("7676988779:AAGsGWqRyyGrZt17SNZSAXRvh8KGRCmnYhU")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

register_handlers(bot)

print("Bot is running...")
bot.infinity_polling()
