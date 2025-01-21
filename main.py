from pyrogram import Client, filters
from pyrogram.types import Message
from decouple import config
from datetime import datetime
import pytz
import random
import pymongo

bot = Client(
    name=config("LOGIN"),
    api_id=config("API_ID"),
    api_hash=config("API_HASH"),
    phone_number=config("PHONE"),
)

connection_uri = config("MONGO_URL")
client = pymongo.MongoClient(connection_uri)
db = client.kok
users = db.users


def get_today_date():
    moscow_tz = pytz.timezone("Europe/Moscow")
    moscow_time = datetime.now(moscow_tz)
    return moscow_time.strftime("%Y-%m-%d")


def get_user(user_id):
    return users.find_one({"userId": user_id})


def register_user(user_id):
    post = {
        "userId": user_id,
        "lastPlayDate": "1970-01-01",
        "len": 0,
    }
    users.insert_one(post)


def update_user(user_id, new_len):
    users.update_one(
        {"userId": user_id},
        {"$set": {"lastPlayDate": get_today_date(), "len": new_len}},
    )


def add_chat_to_user(user_id, chat_id):
    user = get_user(user_id)
    if "chats" not in user:
        users.update_one({"userId": user_id}, {"$set": {"chats": [chat_id]}})
    elif chat_id not in user["chats"]:
        user["chats"].append(chat_id)
        users.update_one({"userId": user_id}, {"$set": {"chats": user["chats"]}})


def get_top_users(chat_id, limit=50):
    top_users = list(users.find({}).sort("len", pymongo.DESCENDING).limit(limit))
    chat_users = [user for user in top_users if "chats" in user and chat_id in user["chats"]]
    return chat_users


def get_global_top_users(limit=50):
    return list(users.find().sort("len", pymongo.DESCENDING).limit(limit))


def get_user_rank(user_id, chat_id):
    all_users = list(users.find({}).sort("len", pymongo.DESCENDING))
    chat_users = [user for user in all_users if "chats" in user and chat_id in user["chats"]]
    for index, user in enumerate(chat_users):
        if user["userId"] == user_id:
            return index + 1
    return None


def get_global_user_rank(user_id):
    all_users = list(users.find().sort("len", pymongo.DESCENDING))
    for index, user in enumerate(all_users):
        if user["userId"] == user_id:
            return index + 1
    return None


@bot.on_message(filters.command(["id", "айди"]))
async def command_handler(client: Client, message: Message):
    await message.reply(message.from_user.id)


@bot.on_message(filters.command(["kok", "кок"]))
async def command_handler(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user = get_user(user_id)
    
    if user is None:
        register_user(user_id)
        user = get_user(user_id)
    
    add_chat_to_user(user_id, chat_id)
    
    if user["lastPlayDate"] == get_today_date():
        await message.reply(f"⏰ Ты уже играл сегодня. Твой кок: <b>{user['len']}</b> см")
    else:
        add_len = random.randint(1, 10)
        new_len = user["len"] + add_len
        update_user(user_id, new_len)
        await message.reply(
            f"🍆 Твой кок вырос на <b>{add_len}</b> см и теперь составляет <b>{new_len}</b> см."
        )


@bot.on_message(filters.command(["top", "топ"]))
async def top_handler(client: Client, message: Message):
    chat_id = message.chat.id
    top_users = get_top_users(chat_id)

    if not top_users:
        await message.reply("🤷‍♂️ В этом чате еще никто не играл.")
        return

    top_text = "🏆 <b>Топ коков в этом чате:</b>\n"
    for i, user in enumerate(top_users):
        user_obj = await client.get_users(user["userId"])
        top_text += f"<b>{i + 1}.</b> {user_obj.first_name} - <b>{user['len']}</b> см\n"

    user_rank = get_user_rank(message.from_user.id, chat_id)
    if user_rank:
        top_text += f"\n🏅 Твоя позиция в топе: <b>{user_rank}</b>"

    await message.reply(top_text)


@bot.on_message(filters.command(["top_global", "топ_глобальный"]))
async def global_top_handler(client: Client, message: Message):
    top_users = get_global_top_users()
    if not top_users:
        await message.reply("🤷‍♀️ Еще никто не играл.")
        return
    top_text = "🌍 <b>Глобальный топ коков:</b>\n"

    for i, user in enumerate(top_users):
        # Removed getting user info. Just use the user ID
        top_text += f"<b>{i + 1}.</b> ID: <code>{user['userId']}</code> - <b>{user['len']}</b> см\n"

    user_rank = get_global_user_rank(message.from_user.id)
    if user_rank:
        top_text += f"\n🏅 Твоя позиция в глобальном топе: <b>{user_rank}</b>"
    await message.reply(top_text)


@bot.on_message(filters.command(["help", "помощь"]))
async def help_handler(client: Client, message: Message):
    help_text = """
<b>Список доступных команд:</b>

🍆 /kok (или /кок) - Играть в кок. Увеличивает длину вашего кока на случайное число. Можно играть один раз в день.

🏆 /top (или /топ) - Показывает топ коков в текущем чате и вашу позицию.

🌍 /top_global (или /топ_глобальный) - Показывает глобальный топ коков и вашу позицию в нем.

🆔 /id (или /айди) - Получить айди. Показывает Ваш айди в телеграмме.

❓ /help (или /помощь) - Показывает это сообщение со списком команд.
"""
    await message.reply(help_text)


bot.run()