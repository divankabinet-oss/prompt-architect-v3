import os
import json
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ---- Проверка доступа ----
ACCESS_PATH = os.path.join(os.path.dirname(__file__), "access", "whitelist.json")
with open(ACCESS_PATH, "r", encoding="utf-8") as f:
    WHITELIST = json.load(f)

def has_access(user_id: int) -> bool:
    return user_id in WHITELIST.get("allowed", []) or user_id in WHITELIST.get("admin", [])

def is_admin(user_id: int) -> bool:
    return user_id in WHITELIST.get("admin", [])

TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"  # Временно для теста


bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# ---------- Load data ----------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(DATA_DIR, "photographers.json"), "r", encoding="utf-8") as f:
    PHOTOGRAPHERS = json.load(f)
with open(os.path.join(DATA_DIR, "lighting.json"), "r", encoding="utf-8") as f:
    LIGHTING = json.load(f)
with open(os.path.join(DATA_DIR, "interiors.json"), "r", encoding="utf-8") as f:
    INTERIORS = json.load(f)
with open(os.path.join(DATA_DIR, "clutter.json"), "r", encoding="utf-8") as f:
    CLUTTER = json.load(f)

# ---------- State ----------
user_state = {}
user_lang = {}

# ---------- DB ----------
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "users.db")

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                prompt TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ---------- Commands ----------
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    if not has_access(msg.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.button(text="Оформить доступ", url="https://t.me/XY_ACADEMY")
        await msg.answer(
            "🚫 Бот доступен только участникам закрытого канала @XY_ACADEMY PRO",
            reply_markup=kb.as_markup()
        )
        return

    user_lang[msg.from_user.id] = "ru"
    kb = InlineKeyboardBuilder()
    kb.button(text="🎨 Создать промпт", callback_data="create")
    kb.button(text="🌐 Language / Язык", callback_data="lang")
    kb.button(text="🗂 История", callback_data="history")
    kb.button(text="📤 Экспорт", callback_data="export")
    kb.adjust(2)
    await msg.answer(
        "👋 Привет! Я *Prompt Architect AI*\n\nСоздаю идеальные промпты для визуализаций\nВыбери действие:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "lang")
async def choose_lang(c: CallbackQuery):
    await c.answer()
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="set_ru")
    kb.button(text="🇬🇧 English", callback_data="set_en")
    kb.adjust(2)
    await c.message.answer("Выбери язык интерфейса / Choose language:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "set_ru")
async def set_ru(c: CallbackQuery):
    await c.answer("Язык изменён")
    user_lang[c.from_user.id] = "ru"
    await c.message.answer("✅ Язык установлен: *Русский*")

@dp.callback_query(F.data == "set_en")
async def set_en(c: CallbackQuery):
    await c.answer("Language changed")
    user_lang[c.from_user.id] = "en"
    await c.message.answer("✅ Language set: *English*")

# ---------- Constructor flow ----------
@dp.callback_query(F.data == "create")
async def start_constructor(c: CallbackQuery):
    await c.answer()
    user_state[c.from_user.id] = {}
    kb = InlineKeyboardBuilder()
    for platform in ["Midjourney", "Seedream", "RealRender", "Nanobanana"]:
        kb.button(text=platform, callback_data=f"platform_{platform}")
    kb.adjust(2)
    await c.message.answer("🔹 Выбери платформу:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("platform_"))
async def choose_platform(c: CallbackQuery):
    await c.answer()
    platform = c.data.split("_", 1)[1]
    user_state[c.from_user.id]["platform"] = platform
    kb = InlineKeyboardBuilder()
    for k in INTERIORS:
        kb.button(text=k, callback_data=f"interior_{k}")
    kb.adjust(2)
    await c.message.answer("🏠 Выбери тип интерьера:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("interior_"))
async def choose_interior(c: CallbackQuery):
    await c.answer()
    inter = c.data.split("_", 1)[1]
    user_state[c.from_user.id]["interior"] = inter
    kb = InlineKeyboardBuilder()
    for k in PHOTOGRAPHERS:
        kb.button(text=k, callback_data=f"photo_{k}")
    kb.adjust(2)
    await c.message.answer("📷 Выбери фотографа / стиль:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("photo_"))
async def choose_photo(c: CallbackQuery):
    await c.answer()
    ph = c.data.split("_", 1)[1]
    user_state[c.from_user.id]["photographer"] = ph
    kb = InlineKeyboardBuilder()
    for k in LIGHTING:
        kb.button(text=k, callback_data=f"light_{k}")
    kb.adjust(2)
    await c.message.answer("💡 Выбери освещение:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("light_"))
async def choose_light(c: CallbackQuery):
    await c.answer()
    lt = c.data.split("_", 1)[1]
    user_state[c.from_user.id]["lighting"] = lt
    kb = InlineKeyboardBuilder()
    for k in ["Slightly imperfect handheld", "Centered cinematic", "Wide architectural", "Close magazine frame"]:
        kb.button(text=k, callback_data=f"angle_{k}")
    kb.adjust(2)
    await c.message.answer("🎥 Выбери ракурс камеры:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("angle_"))
async def choose_angle(c: CallbackQuery):
    await c.answer()
    angle = c.data.split("_", 1)[1]
    user_state[c.from_user.id]["angle"] = angle
    kb = InlineKeyboardBuilder()
    kb.button(text="🚫 Без беспорядка", callback_data="clutter_none")
    kb.button(text="✨ Лёгкий беспорядок", callback_data="clutter_light")
    kb.adjust(2)
    await c.message.answer("✨ Добавить естественный беспорядок?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("clutter_"))
async def choose_clutter(c: CallbackQuery):
    await c.answer()
    uid = c.from_user.id
    choice = c.data.split("_", 1)[1]
    user_state[uid]["clutter"] = choice
    await generate_prompt(c)

# ---------- Generate ----------
async def generate_prompt(c: CallbackQuery):
    data = user_state.get(c.from_user.id, {})
    inter_desc = INTERIORS[data["interior"]]
    ph_data = PHOTOGRAPHERS[data["photographer"]]
    lt_data = LIGHTING[data["lighting"]]
    platform = data["platform"]
    angle = data["angle"]
    clutter_text = CLUTTER["light"] if data.get("clutter") == "light" else ""

    geometry_line = "" if platform == "Nanobanana" else "Geometry of the room, furniture and lighting fixtures remain unchanged."

    prompt = f"""Photo of {inter_desc}.
In the style of {data['photographer']} — {ph_data}.
{lt_data}.
Camera angle {angle}.
{clutter_text}
{geometry_line}
Photorealistic, ultra detailed, architectural magazine style."""

    # Save to DB
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO prompts (user_id, username, prompt) VALUES (?, ?, ?)",
            (c.from_user.id, c.from_user.username, prompt)
        )
        await db.commit()

    # Action buttons
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Перевести", callback_data=f"translate_{c.from_user.id}")
    kb.button(text="🗂 История", callback_data="history")
    kb.button(text="📤 Экспорт", callback_data="export")
    kb.adjust(1)

    # Убираем лишние пробелы
    prompt_clean = "\n".join([line.strip() for line in prompt.split("\n") if line.strip()])
    await c.message.answer(f"✅ *Готовый промпт:*\n```\n{prompt_clean}\n```", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("translate_"))
async def translate_prompt(c: CallbackQuery):
    await c.answer()
    await c.message.answer(
        "🔁 *Краткий перевод / структура:*\n"
        "— Фото интерьера в выбранном стиле фотографа\n"
        "— Тип освещения\n"
        "— Ракурс камеры\n"
        "— (опц.) Лёгкий «обжитый» беспорядок\n"
        "— Фраза о неизменности геометрии/мебели/светильников\n\n"
        "_Скопируй англоязычный блок в генератор (он выше)_"
    )

# ---------- History & Export ----------
@dp.callback_query(F.data == "history")
async def history_menu(c: CallbackQuery):
    await c.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT prompt, created FROM prompts WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (c.from_user.id,)
        ) as cur:
            rows = await cur.fetchall()
    
    if not rows:
        await c.message.answer("📂 История пуста")
        return
    
    text = "\n\n".join([f"🕓 {r[1]}\n```\n{r[0]}\n```" for r in rows])
    await c.message.answer(f"🗂 *Последние 5 промптов:*\n\n{text}")

@dp.callback_query(F.data == "export")
async def export_history(c: CallbackQuery):
    await c.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT created, prompt FROM prompts WHERE user_id=? ORDER BY id DESC",
            (c.from_user.id,)
        ) as cur:
            rows = await cur.fetchall()
    
    if not rows:
        await c.message.answer("Нет данных для экспорта")
        return
    
    lines = [f"=== {created} ===\n{prompt}\n" for created, prompt in rows]
    content = "\n".join(lines)
    
    path = os.path.join(os.path.dirname(DB_PATH), f"prompts_{c.from_user.id}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    await c.message.answer_document(
        FSInputFile(path),
        caption="📤 Экспорт истории промптов"
    )
    os.remove(path)

# ---------- Admin ----------
@dp.message(Command("adduser"))
async def add_user(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        new_id = int(msg.text.split()[1])
        if new_id not in WHITELIST["allowed"]:
            WHITELIST["allowed"].append(new_id)
            with open(ACCESS_PATH, "w", encoding="utf-8") as f:
                json.dump(WHITELIST, f, ensure_ascii=False, indent=2)
            await msg.answer(f"✅ Пользователь `{new_id}` добавлен")
        else:
            await msg.answer(f"ℹ️ Пользователь `{new_id}` уже в whitelist")
    except (IndexError, ValueError):
        await msg.answer("⚠️ Формат: /adduser <user\\_id>")

@dp.message(Command("removeuser"))
async def remove_user(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        rem_id = int(msg.text.split()[1])
        if rem_id in WHITELIST["allowed"]:
            WHITELIST["allowed"].remove(rem_id)
            with open(ACCESS_PATH, "w", encoding="utf-8") as f:
                json.dump(WHITELIST, f, ensure_ascii=False, indent=2)
            await msg.answer(f"❌ Пользователь `{rem_id}` удалён")
        else:
            await msg.answer(f"ℹ️ Пользователя `{rem_id}` нет в whitelist")
    except (IndexError, ValueError):
        await msg.answer("⚠️ Формат: /removeuser <user\\_id>")

@dp.message(Command("users"))
async def list_users(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    admins = WHITELIST.get("admin", [])
    users = WHITELIST.get("allowed", [])
    text = f"👑 *Админы:*\n" + "\n".join([f"`{a}`" for a in admins])
    text += f"\n\n👥 *Пользователи ({len(users)}):*\n" + "\n".join([f"`{u}`" for u in users])
    await msg.answer(text)

@dp.message(Command("broadcast"))
async def broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.answer("⚠️ Формат: /broadcast <текст>")
        return
    
    count = 0
    failed = 0
    for uid in WHITELIST.get("allowed", []) + WHITELIST.get("admin", []):
        try:
            await bot.send_message(uid, f"📢 *Объявление:*\n\n{text}")
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    
    await msg.answer(f"✅ Рассылка завершена\n📤 Отправлено: {count}\n❌ Ошибок: {failed}")

# ---------- Run ----------
async def main():
    await init_db()
    print("✅ Prompt Architect v3 is running")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
