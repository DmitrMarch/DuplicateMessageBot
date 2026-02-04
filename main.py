from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api
import telebot
import os
import requests

VK_DM_BOT_TOKEN = os.environ["VK_DM_BOT_TOKEN"]
TG_DM_BOT_TOKEN = os.environ["TG_DM_BOT_TOKEN"]

VK_CHAT_IDS = [int(cid) for cid in os.environ["VK_CHAT_IDS"].split(":")]
VK_USER_IDS = [int(uid) for uid in os.environ["VK_USER_IDS"].split(":")]
TG_CHAT_IDS = [int(cid) for cid in os.environ["TG_CHAT_IDS"].split(":")]

VK_BOT = vk_api.VkApi(token=VK_DM_BOT_TOKEN)
TG_BOT = telebot.TeleBot(TG_DM_BOT_TOKEN)

while 1:
    try:
        for event in VkLongPoll(VK_BOT, preload_messages=True).listen():
            if event.type == VkEventType.MESSAGE_NEW and event.from_chat:
                peer_id = event.peer_id
                user_id = event.user_id
                if peer_id in VK_CHAT_IDS and user_id in VK_USER_IDS:
                    vk_msg = "Сообщение из ВК:\n<blockquote>" + event.text + "</blockquote>"
                    vk_fwd_msgs = event.message_data["fwd_messages"]
                    tg_msg = vk_msg
                    if vk_fwd_msgs:
                        tg_msg += "\n\nВложенные в него сообщения:\n<blockquote>"
                        for vk_fwd_msg in vk_fwd_msgs:
                            tg_msg += ("<tg-emoji emoji-id='5453969572354878595'>"
                                       "⭐</tg-emoji>  " + vk_fwd_msg["text"] + "\n\n")
                        tg_msg += "</blockquote>"

                    for tg_chat_id in TG_CHAT_IDS:
                        TG_BOT.send_message(tg_chat_id, tg_msg, parse_mode="HTML")

    except requests.exceptions.ReadTimeout or requests.exceptions.ConnectionError:
        print("Временно потеряно соедиение с сервером ВК")
