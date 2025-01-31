from pyrogram import Client, filters
from pyrogram.types import Message
from decouple import config
from datetime import datetime, timedelta
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
        "chats": [],
        "increase_chance": 0.67,
        "fimosis": None
    }
    users.insert_one(post)


def update_user(user_id, new_len):
    users.update_one(
        {"userId": user_id},
        {"$set": {"lastPlayDate": get_today_date(), "len": new_len}},
    )


def add_chat_to_user(user_id, chat_id):
    if chat_id < 0:
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


def has_active_fimosis(user_data):
    if not user_data.get("fimosis"):
        return False
    start_date = datetime.strptime(user_data["fimosis"]["start"], "%Y-%m-%d")
    return (datetime.now() - start_date).days < user_data["fimosis"]["duration"]


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
        return

    fimosis_active = has_active_fimosis(user)
    
    if fimosis_active:
        max_increase = 5
        decrease_chance = 0.5
    else:
        max_increase = 10
        decrease_chance = 0.33

    current_len = user["len"]
    change = 0 
    
    if current_len > 50:
        if random.random() < decrease_chance:
            change = -random.randint(1, 5)
        else:
            change = random.randint(1, max_increase)
    else: 
        change = random.randint(1, max_increase)

    new_len = current_len + change
    update_user(user_id, new_len)
    
    if not fimosis_active and random.random() < 0.05:
        fimosis_data = {
            "start": get_today_date(),
            "duration": 3
        }
        users.update_one({"userId": user_id}, {"$set": {"fimosis": fimosis_data}})
        await message.reply("⚠️ У вас фимоз! Ограничения действуют 3 дня.")
    
    if change > 0:
        await message.reply(
            f"🍆 Твой кок вырос на <b>{change}</b> см и теперь составляет <b>{new_len}</b> см."
        )
    elif change < 0:
        await message.reply(
            f"🍆 Твой кок уменьшился на <b>{abs(change)}</b> см и теперь составляет <b>{new_len}</b> см."
        )


@bot.on_message(filters.command(["duel", "дуэль"]))
async def duel_handler(client: Client, message: Message):
    if message.chat.id > 0:
        await message.reply("❌ Дуэли доступны только в группах!")
        return
    
    attacker = message.from_user
    defender = None
    
    if message.reply_to_message:
        defender = message.reply_to_message.from_user
    elif len(message.command) > 1:
        target = message.command[1]
        try:
            if target.startswith("@"):
                defender = await client.get_users(target)
            else:
                defender = await client.get_users(int(target))
        except Exception:
            await message.reply("❌ Пользователь не найден")
            return
    
    if not defender:
        await message.reply("❌ Укажите оппонента: ответьте на сообщение, укажите ID или юзернейм")
        return
    
    if attacker.id == defender.id:
        await message.reply("❌ Нельзя вызвать самого себя!")
        return
    
    attacker_data = get_user(attacker.id)
    defender_data = get_user(defender.id)
    today = get_today_date()
    errors = []
    
    for user, data in [(attacker, attacker_data), (defender, defender_data)]:
        if not data:
            errors.append(f"{user.first_name} не зарегистрирован")
        elif data["lastPlayDate"] != today:
            errors.append(f"{user.first_name} не играл сегодня")
        elif has_active_fimosis(data):
            errors.append(f"{user.first_name} имеет фимоз")
    
    if errors:
        await message.reply("❌ Дуэль невозможна:\n" + "\n".join(errors))
        return
    
    winner = random.choice([attacker, defender])
    loser = defender if winner == attacker else attacker
    
    users.update_one({"userId": winner.id}, {"$inc": {"len": 15}})
    users.update_one({"userId": loser.id}, {"$inc": {"len": -10}})
    
    await message.reply(
        f"⚔️ Дуэль завершена!\n"
        f"🏆 Победитель: {winner.first_name} (+15см)\n"
        f"💀 Проигравший: {loser.first_name} (-10см)"
    )


@bot.on_message(filters.command(["profile", "профиль"]))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        await message.reply("❌ Вы не зарегистрированы!")
        return
    
    profile_text = f"📄 Профиль {message.from_user.first_name}:\n"
    profile_text += f"🍆 Длина: {user['len']} см\n"
    profile_text += f"🎰 Шанс увеличения: {round(user['increase_chance']*100)}%\n"
    
    if has_active_fimosis(user):
        days_left = 3 - (datetime.now() - datetime.strptime(user['fimosis']['start'], '%Y-%m-%d')).days
        profile_text += f"⚠️ Фимоз (осталось {days_left} дней)\n"
    
    await message.reply(profile_text)


@bot.on_message(filters.command(["top", "топ"]))
async def top_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id > 0:
        await message.reply("👥 В личных сообщениях нельзя играть в кок.")
        return
    
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
        top_text += f"\n🏅 Твоя позиция: <b>{user_rank}</b>"

    await message.reply(top_text)


@bot.on_message(filters.command(["top_global", "топ_глобальный"]))
async def global_top_handler(client: Client, message: Message):
    top_users = get_global_top_users()
    if not top_users:
        await message.reply("🤷‍♀️ Еще никто не играл.")
        return
    top_text = "🌍 <b>Глобальный топ:</b>\n"

    for i, user in enumerate(top_users):
        top_text += f"<b>{i + 1}.</b> ID: <code>{user['userId']}</code> - <b>{user['len']}</b> см\n"

    user_rank = get_global_user_rank(message.from_user.id)
    if user_rank:
        top_text += f"\n🏅 Твоя позиция: <b>{user_rank}</b>"
    await message.reply(top_text)


@bot.on_message(filters.command(["help", "помощь"]))
async def help_handler(client: Client, message: Message):
    help_text = """
<b>Доступные команды:</b>

🍆 /kok - Изменить длину кока (1 раз в день)
⚔️ /duel [@юзер] - Дуэль с другим игроком
📄 /profile - Показать ваш профиль
🏆 /top - Топ чата
🌍 /top_global - Глобальный топ
🆔 /id - Показать ваш ID
❓ /help - Эта справка

<a href="https://mvory9.github.io/kok-userbot-tg/">Полная документация на GitHub Pages</a>
<a href="https://github.com/Mvory9/kok-userbot-tg/">Репозиторий на GitHub (+ исходный код)</a>
<a href="https://github.com/Mvory9/kok-userbot-tg/issues">Сообщить о баге или предложить идею</a>
"""
    await message.reply(help_text, disable_web_page_preview=True)


bot.run()