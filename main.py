import json
from pyrogram import Client, filters
from pyrogram.types import Message
from decouple import config
from datetime import datetime, timedelta
import pytz
import random
import pymongo
import asyncio

bot = Client(
    name=config("LOGIN"),
    api_id=config("API_ID"),
    api_hash=config("API_HASH"),
    phone_number=config("PHONE"),
)

connection_uri = config("MONGO_URL")
client = pymongo.MongoClient(connection_uri)
db = client.kokbot
users = db.users

DUEL_REQUESTS = {}
DUEL_TIMEOUT = 300  # 5 минут (в секундах)

PREMIUM_EMOJI = {
    "eggplant": "<emoji id=5267172356501039375>🍆</emoji>"
}


def get_today_date():
    moscow_tz = pytz.timezone("Europe/Moscow")
    moscow_time = datetime.now(moscow_tz)
    return moscow_time.strftime("%Y-%m-%d")


def get_user(user_id):
    return users.find_one({"userId": user_id})


def register_user(user_id):
    find_user_len_in_oldBase = find_user_by_id(user_id)

    post = {}

    if find_user_len_in_oldBase:
        post = {
            "userId": user_id,
            "lastPlayDate": "1970-01-01",
            "len": find_user_len_in_oldBase,
            "chats": [],
            "fimos_end": "1970-01-01",
            "lastDuelDate": "1970-01-01",
        }

    else:
        post = {
            "userId": user_id,
            "lastPlayDate": "1970-01-01",
            "len": 0,
            "chats": [],
            "fimos_end": "1970-01-01",
            "lastDuelDate": "1970-01-01",
        }

    users.insert_one(post)


def update_user(user_id, new_len, fimos_end=None, last_duel_date=None):
    update_data = {"$set": {"lastPlayDate": get_today_date(), "len": new_len}}
    if fimos_end:
        update_data["$set"]["fimos_end"] = fimos_end
    if last_duel_date:
        update_data["$set"]["lastDuelDate"] = last_duel_date
    users.update_one({"userId": user_id}, update_data)


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


def is_fimos(user):
    if user is None:
        return False
    return user["fimos_end"] > get_today_date()


def get_fimos_end_date():
    moscow_tz = pytz.timezone("Europe/Moscow")
    moscow_time = datetime.now(moscow_tz)
    fimos_end = moscow_time + timedelta(days=3)
    return fimos_end.strftime("%Y-%m-%d")


async def cleanup_duel_requests():
    now = datetime.now()
    expired_requests = [req_id for req_id, req_data in DUEL_REQUESTS.items() if (now - req_data["timestamp"]).total_seconds() > DUEL_TIMEOUT]
    for req_id in expired_requests:
        req_data = DUEL_REQUESTS.pop(req_id)
        try:
            duel_user_obj = await bot.get_users(req_data["duel_user_id"])
            user_obj = await bot.get_users(req_data["user_id"])
            await bot.send_message(req_data["chat_id"], f"❌ Время ожидания дуэли от <a href='tg://user?id={req_data['user_id']}'>{user_obj.first_name}</a> к <a href='tg://user?id={req_data['duel_user_id']}'>{duel_user_obj.first_name}</a> истекло.", disable_notification=True)
        except Exception:
            pass


def get_users_duel_today(chat_id):
    all_users = list(users.find({}))
    chat_users = [user for user in all_users if "chats" in user and chat_id in user["chats"] and user["lastDuelDate"] == get_today_date()]
    return chat_users


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
        current_len = user["len"]
        change = 0
        fimos = is_fimos(user)
        fimos_message = ""

        if fimos:
            if random.random() < 0.5:  # 50% шанс уменьшения при фимозе
                change = -random.randint(1, 5)
            else:
                change = random.randint(1, 5)

            if change > 0:
                fimos_message = f"\n⚠️ Из-за фимоза твой кок вырос всего на <b>{change}</b> см."
            elif change < 0:
                fimos_message = f"\n⚠️ Из-за фимоза твой кок уменьшился на <b>{abs(change)}</b> см."

        elif current_len > 50:
            if random.random() < 0.33:  # 33% шанс уменьшения
                change = -random.randint(1, 5)
            else:  # 67% шанс увеличения
                change = random.randint(1, 10)
        else:
            change = random.randint(1, 10)

        if change == 0:
            change = random.choice([-random.randint(1, 3), random.randint(1, 3)])

        new_len = current_len + change
        fimos_end = None

        if current_len > 50 and random.random() < 0.03 and not fimos:
            fimos_end = get_fimos_end_date()
            fimos_message = f"\n😱 У тебя фимоз! Он продлится до: <b>{fimos_end}</b>."

        update_user(user_id, new_len, fimos_end)

        if change > 0 and not fimos:
            await message.reply(f"{PREMIUM_EMOJI['eggplant']} Твой кок вырос на <b>{change}</b> см и теперь составляет <b>{new_len}</b> см.{fimos_message}")
        elif change < 0 and not fimos:
            await message.reply(f"{PREMIUM_EMOJI['eggplant']} Твой кок уменьшился на <b>{abs(change)}</b> см и теперь составляет <b>{new_len}</b> см.{fimos_message}")
        elif fimos:
            await message.reply(f"{PREMIUM_EMOJI['eggplant']} Твой кок теперь составляет <b>{new_len}</b> см.{fimos_message}")


@bot.on_message(filters.command(["top", "топ"]))
async def top_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id > 0:
        await message.reply(f"👥 В личных сообщениях нельзя играть в кок. Используйте эту команду в групповом чате.")
        return

    top_users = get_top_users(chat_id)

    if not top_users:
        await message.reply("🤷‍♂️ В этом чате еще никто не играл.")
        return

    duel_users_today = get_users_duel_today(chat_id)

    top_text = "🏆 <b>Топ коков в этом чате:</b>\n"
    for i, user in enumerate(top_users):
        user_obj = await client.get_users(user["userId"])
        duel_mark = " ⚔️" if user in duel_users_today else ""
        top_text += f"<b>{i + 1}.</b> {user_obj.first_name} - <b>{user['len']}</b> см{duel_mark}\n"

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
        top_text += f"<b>{i + 1}.</b> ID: <code>{user['userId']}</code> - <b>{user['len']}</b> см\n"

    user_rank = get_global_user_rank(message.from_user.id)
    if user_rank:
        top_text += f"\n🏅 Твоя позиция в глобальном топе: <b>{user_rank}</b>"
    await message.reply(top_text)


@bot.on_message(filters.command(["help", "помощь"]))
async def help_handler(client: Client, message: Message):
    help_text = f"""
<b>Список доступных команд:</b>

{PREMIUM_EMOJI['eggplant']} <code>/kok</code> (или <code>/кок</code>) - Играть в кок. Увеличивает длину вашего кока на случайное число. Можно играть один раз в день.

🏆 <code>/top</code> (или <code>/топ</code>) - Показывает топ коков в текущем чате и вашу позицию.

🌍 <code>/top_global</code> (или <code>/топ_глобальный</code>) - Показывает глобальный топ коков и вашу позицию в нем.

🆔 <code>/id</code> (или <code>/айди</code>) - Получить айди. Показывает Ваш айди в телеграмме.

⚔️ <code>/duel @username</code> - Вызвать пользователя на дуэль. Можно драться только один раз в день.

✅ <code>/accept_duel</code> - Принять предложение дуэли.
❌ <code>/decline_duel</code> - Отклонить предложение дуэли.

👤 <code>/profile</code> - Показывает ваш профиль.

❓ <code>/help</code> (или <code>/помощь</code>) - Показывает это сообщение со списком команд.

<a href="https://mvory9.github.io/kok-userbot-tg/">Полная документация на GitHub Pages</a>
<a href="https://github.com/Mvory9/kok-userbot-tg/">Репозиторий на GitHub (+ исходный код)</a>
<a href="https://github.com/Mvory9/kok-userbot-tg/issues">Сообщить о баге или предложить идею</a>
"""
    await message.reply(help_text, disable_web_page_preview=True)


@bot.on_message(filters.command(["duel", "дуэль"]))
async def duel_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if is_fimos(user):
        await message.reply("😔 У тебя фимоз, ты не можешь участвовать в дуэлях.")
        return

    if user["lastDuelDate"] == get_today_date():
        await message.reply("⚔️ Ты уже дрался сегодня, приходи завтра.")
        return

    if user["len"] < 50:
        await message.reply("⚔️ Ты еще слишком мал для дуэлей. Твой кок должен быть больше 50 см.")
        return

    if not message.reply_to_message and not message.command[1:]:
        await message.reply("⚔️ Пожалуйста, ответьте на сообщение пользователя, которого хотите вызвать на дуэль, или укажите его юзернейм/ID")
        return

    duel_user_id = None
    if message.reply_to_message:
        duel_user_id = message.reply_to_message.from_user.id
    else:
        try:
            duel_user_id = int(message.command[1]) if message.command[1].isdigit() else (await client.get_users(message.command[1])).id
        except ValueError:
            await message.reply("❌ Неверный формат юзернейма/ID.")
            return
        except Exception as e:
            await message.reply("❌ Пользователь не найден.")
            return

    if user_id == duel_user_id:
        await message.reply("🤨 Ты не можешь вызвать себя на дуэль.")
        return

    if message.reply_to_message and message.chat.id != message.reply_to_message.chat.id:
        await message.reply("🤨 Дуэли возможны только в одном чате")
        return

    duel_user = get_user(duel_user_id)
    if duel_user is None:
        await message.reply("🙅‍♀️ Этот пользователь еще не играл.")
        return

    if is_fimos(duel_user):
        await message.reply("😔 Этот пользователь не может участвовать в дуэлях, у него фимоз.")
        return

    if duel_user["len"] < 50:
        await message.reply("⚔️ Этот пользователь еще слишком мал для дуэлей. Его кок должен быть больше 50 см.")
        return

    if user["lastPlayDate"] != get_today_date() or duel_user["lastPlayDate"] != get_today_date():
        await message.reply("⏰ Ты или твой соперник не играли сегодня, вы не можете драться.")
        return

    if duel_user["lastDuelDate"] == get_today_date():
        duel_user_obj = await client.get_users(duel_user_id)
        await message.reply(f"⚔️ {duel_user_obj.first_name} уже дрался сегодня, приходи завтра.")
        return

    for req_id, req_data in DUEL_REQUESTS.items():
        if req_data["duel_user_id"] == duel_user_id:
            duel_user_obj = await client.get_users(duel_user_id)
            await message.reply(f"⚔️ {duel_user_obj.first_name} уже вызвали на дуэль. Дождись пока он примет или отклонит её.")
            return

    request_id = f"{user_id}_{duel_user_id}"
    DUEL_REQUESTS[request_id] = {
        "user_id": user_id,
        "duel_user_id": duel_user_id,
        "timestamp": datetime.now(),
        "chat_id": message.chat.id,
    }
    duel_user_obj = await client.get_users(duel_user_id)
    await message.reply(f"⚔️ {duel_user_obj.first_name}, Вас вызвали на дуэль! Используйте <code>/accept_duel</code> или <code>/decline_duel</code> для принятия или отклонения дуэли.")


@bot.on_message(filters.command(["accept_duel"]))
async def accept_duel_handler(client: Client, message: Message):
    user_id = message.from_user.id

    await cleanup_duel_requests()

    request_id = None
    for req_id, req_data in DUEL_REQUESTS.items():
        if req_data["duel_user_id"] == user_id:
            request_id = req_id
            break

    if not request_id:
        await message.reply("❌ Нет активных запросов на дуэль для Вас или запрос устарел.")
        return

    request_data = DUEL_REQUESTS[request_id]
    user_id = request_data["user_id"]
    duel_user_id = request_data["duel_user_id"]

    user = get_user(user_id)
    duel_user = get_user(duel_user_id)

    if is_fimos(user) or is_fimos(duel_user):
        await message.reply("Один из Вас имеет фимоз, дуэль невозможна.")
        del DUEL_REQUESTS[request_id]
        return

    if user["lastDuelDate"] == get_today_date() or duel_user["lastDuelDate"] == get_today_date():
        await message.reply("Один из Вас уже дрался сегодня, дуэль невозможна.")
        del DUEL_REQUESTS[request_id]
        return

    duel_change = 10
    user_change = -5

    if random.random() < 0.5:
        duel_change, user_change = user_change, duel_change

    new_len_user = user["len"] + user_change
    new_len_duel = duel_user["len"] + duel_change

    update_user(user_id, new_len_user, last_duel_date=get_today_date())
    update_user(duel_user_id, new_len_duel, last_duel_date=get_today_date())

    user_obj = await client.get_users(user_id)
    duel_user_obj = await client.get_users(duel_user_id)

    await message.reply(f"⚔️ Дуэль между {user_obj.first_name} и {duel_user_obj.first_name}!\n\n" f"💪 {user_obj.first_name} {'потерял' if user_change < 0 else 'получил'} {abs(user_change)} см. Теперь его кок: {new_len_user} см.\n" f"💪 {duel_user_obj.first_name} {'потерял' if duel_change < 0 else 'получил'} {abs(duel_change)} см. Теперь его кок: {new_len_duel} см.")
    del DUEL_REQUESTS[request_id]


@bot.on_message(filters.command(["decline_duel"]))
async def decline_duel_handler(client: Client, message: Message):
    user_id = message.from_user.id

    await cleanup_duel_requests()

    request_id = None
    for req_id, req_data in DUEL_REQUESTS.items():
        if req_data["duel_user_id"] == user_id:
            request_id = req_id
            break

    if not request_id:
        await message.reply("❌ Нет активных запросов на дуэль для Вас или запрос устарел.")
        return

    request_data = DUEL_REQUESTS[request_id]
    user_obj = await client.get_users(request_data["user_id"])

    await message.reply(f"❌ {user_obj.first_name} отклонил вызов на дуэль.")
    del DUEL_REQUESTS[request_id]


@bot.on_message(filters.command(["profile", "профиль"]))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if user is None:
        await message.reply("🤷‍♀️ Вы еще не играли.")
        return

    fimos = is_fimos(user)
    fimos_message = ""
    if fimos:
        fimos_message = f"\n⚠️ У Вас фимоз до: {user['fimos_end']}"

    duel_date = user['lastDuelDate']
    duel_message = ""
    if duel_date != "1970-01-01":
        duel_message = f"\n⚔️ Дата последней дуэли: <b>{user['lastDuelDate']}</b>"

    await message.reply(f"📊 <b>Ваш профиль:</b>\n\n" f"📏 Длина вашего кока: <b>{user['len']}</b> см\n" f"📅 Дата последней игры: <b>{user['lastPlayDate']}</b>\n" f"{duel_message}{fimos_message}")


def find_user_by_id(target_user_id):
    with open("kok.users.json", 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    for user in data:
        user_id = user['userId']
        if isinstance(user_id, dict) and '$numberLong' in user_id:
            user_id = int(user_id['$numberLong'])
        elif isinstance(user_id, int):
            pass  # Уже число, ничего не делаем
        else:
            continue  # Пропускаем некорректные данные
        
        if user_id == target_user_id:
            return user['len']
    
    return False
    

async def main():
    while True:
        await asyncio.sleep(10)
        await cleanup_duel_requests()


if __name__ == "__main__":
    bot.loop.create_task(main())
    bot.run()