import telebot
import os

TG_DM_BOT_TOKEN = os.environ["TG_DM_BOT_TOKEN"]
bot = telebot.TeleBot(TG_DM_BOT_TOKEN)
write_msg = bot.reply_to


@bot.message_handler(commands=['id'])
def send_id(message):
    user_id = message.from_user.id
    write_msg(message, f'Твой айди: {user_id}')


bot.polling(none_stop=True)
