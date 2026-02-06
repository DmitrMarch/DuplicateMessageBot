from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import vk_api
import telebot
import os
import requests
import json
import time

# Токены от ботов
VK_DM_BOT_TOKEN = os.environ["VK_DM_BOT_TOKEN"]
TG_DM_BOT_TOKEN = os.environ["TG_DM_BOT_TOKEN"]

# Кортежи с айдишниками чатов и админов
VK_CHAT_IDS = tuple(int(cid) for cid in os.environ["VK_CHAT_IDS"].split(":"))
VK_ADMIN_IDS = tuple(int(uid) for uid in os.environ["VK_ADMIN_IDS"].split(":"))
TG_CHAT_IDS = tuple(int(cid) for cid in os.environ["TG_CHAT_IDS"].split(":"))

# Файл со списком отслеживаемых пользователей
VK_USERS_FILE = "vk_users.json"


# Вспомогательные функции для работы с файлом
def load_users() -> set:
    if not os.path.exists(VK_USERS_FILE):
        return set()
    with open(VK_USERS_FILE, "r") as f:
        return set(json.load(f).get("users", []))

def save_users(users: set) -> None:
    with open(VK_USERS_FILE, "w") as f:
        json.dump({"users": list(users)}, f, indent=2)


# Список айдишников отслеживаемых пользователей
vk_user_ids = load_users()


# Переменные с сессиями ботов
VK_BOT = vk_api.VkApi(token=VK_DM_BOT_TOKEN)
VK_LONG_POLL = VkLongPoll(VK_BOT, preload_messages=True)
VK_API = VK_BOT.get_api()
TG_BOT = telebot.TeleBot(TG_DM_BOT_TOKEN)


# Вспомогательные функции для бота в ВК
def get_entity_fullname(entity_info: dict) -> str:
    if entity_info.get("name", ""):
        return entity_info["name"]
    else:
        return f"{entity_info['first_name']} {entity_info['last_name']}"

def if_empty2attachment(message_text: str) -> str:
    return message_text if message_text else "[<b>Вложения не поддерживаются</b>]"

def is_negative(entity_id: str) -> bool:
    return entity_id.startswith("-") and entity_id[1:].isdigit()

def resolve_entity(entity_id: int | str) -> dict:
    entity_id = str(entity_id)
    if is_negative(entity_id):
        resp = VK_API.groups.get_by_id(group_id=abs(int(entity_id)))
    else:
        resp = VK_API.users.get(user_ids=entity_id)
    if resp:
        return resp[0]
    else:
        return {}

def get_numeric_entity_id(entity_id: str) -> int:
    entity_id = entity_id.lstrip()
    if "|" in entity_id:
        entity_id = entity_id[1:entity_id.index("|")]
    if entity_id.startswith("id"):
        entity_id = entity_id.replace("id", "")
    if entity_id.isdigit() or is_negative(entity_id):
        return int(entity_id)
    entity_info = resolve_entity(entity_id)
    return entity_info["id"] if entity_info else 0


# Функции команд для бота в ВК
def cmd_add(chat_id: int, argument: str) -> None:
    if argument:
        uid = get_numeric_entity_id(argument)
        if uid < 1:
            msg = "Такого пользователя не существует :("
        elif uid in vk_user_ids:
            msg = "Пользователь уже есть в списке :("
        else:
            vk_user_ids.add(uid)
            save_users(vk_user_ids)
            msg = f"Пользователь @id{uid} добавлен"
    else:
        msg = "Пользователь не указан :("

    VK_API.messages.send(peer_id=chat_id, message=msg, random_id=get_random_id())

def cmd_del(chat_id: int, argument: str) -> None:
    if argument:
        uid = get_numeric_entity_id(argument)
        if uid < 1:
            msg = "Такого пользователя не существует :("
        elif uid not in vk_user_ids:
            msg = "Такого пользователя нет в списке :("
        else:
            vk_user_ids.remove(uid)
            save_users(vk_user_ids)
            msg = f"Пользователь @id{uid} удалён"
    else:
        msg = "Пользователь не указан :("

    VK_API.messages.send(peer_id=chat_id, message=msg, random_id=get_random_id())

def cmd_list(chat_id: int, _) -> None:
    if not vk_user_ids:
        msg = "Список отслеживаемых пользователей пуст :("
    else:
        msg = (
            "Список отслеживаемых пользователей:\n"
            + "\n".join(f"@id{uid}" for uid in vk_user_ids)
        )
    VK_API.messages.send(peer_id=chat_id, message=msg, random_id=get_random_id())


# Словарь команд
COMMANDS = {
    "/del": cmd_del,
    "/add": cmd_add,
    "/list": cmd_list,
}

# Цикл бота в ВК
while 1:
    try:
        for event in VK_LONG_POLL.listen():
            if event.type != VkEventType.MESSAGE_NEW:
                continue
            if not event.from_chat or hasattr(event, "source_act"):
                continue

            peer_id = event.peer_id
            user_id = event.user_id
            text = event.text

            # Команды для админов
            if user_id in VK_ADMIN_IDS and text.startswith("/"):
                parts = text.split(maxsplit=1)
                cmd = parts[0]
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in COMMANDS:
                    COMMANDS[cmd](peer_id, arg)
                    continue

            # Отслеживание сообщений ВК и отправка в ТГ
            if peer_id in VK_CHAT_IDS and user_id in vk_user_ids:
                user = resolve_entity(user_id)
                fullname = get_entity_fullname(user)

                tg_msg = (
                    f"Сообщение от пользователя <b>{fullname}</b>:\n"
                    f"<blockquote>{if_empty2attachment(text)}</blockquote>"
                )

                if hasattr(event, "message_data"):
                    message_data = event.message_data
                else:
                    message_data = {}
                vk_fwd_msgs = message_data.get("fwd_messages", [])
                vk_rpl_msg = message_data.get("reply_message", {})

                if vk_fwd_msgs:
                    tg_msg += "\n\nВложенные сообщения:\n<blockquote>"
                    for vk_fwd_msg in vk_fwd_msgs:
                        vk_fwd_entity_id = vk_fwd_msg["from_id"]
                        entity = resolve_entity(vk_fwd_entity_id)
                        fullname = get_entity_fullname(entity)
                        tg_msg += (
                            "<tg-emoji emoji-id='5453969572354878595'>⭐</tg-emoji>  "
                            f"<b>{fullname}</b>: {if_empty2attachment(vk_fwd_msg['text'])}\n\n"
                        )
                    tg_msg += "</blockquote>"

                if vk_rpl_msg:
                    vk_rpl_entity_id = vk_rpl_msg["from_id"]
                    entity = resolve_entity(vk_rpl_entity_id)
                    fullname = get_entity_fullname(entity)
                    tg_msg += (
                        f"\n\nВ ответ на сообщение <b>{fullname}</b>:\n"
                        f"<blockquote>"
                        f"{if_empty2attachment(vk_rpl_msg['text'])}"
                        "</blockquote>"
                    )

                for tg_chat_id in TG_CHAT_IDS:
                    TG_BOT.send_message(
                        tg_chat_id,
                        tg_msg,
                        parse_mode="HTML"
                    )

    except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError
    ):
        print("Временно потеряно соединение с сервером ВК")
        time.sleep(5)
    except vk_api.exceptions.ApiError:
        print("Произошла ошибка при обращении к VK API")
        time.sleep(1)
    except telebot.apihelper.ApiTelegramException:
        print("Произошла ошибка при обращении к Telegram Bot API")
        time.sleep(1)
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {repr(e)}")
        time.sleep(1)
