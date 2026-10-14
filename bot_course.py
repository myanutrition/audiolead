import logging
import sqlite3
import os
from datetime import datetime, timedelta
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import RetryAfter
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@myanutrition"
SEND_HOUR = 7
SEND_MINUTE = 0
ADMIN_CHAT_ID = 7917196527
ADMIN_IDS = {7917196527, 950626021}  # Даяна, Юля
MAX_DAY = 3

# ==================== FILE IDs ====================
AUDIOS = {
    0: "CQACAgIAAxkBAAIkIGrNPQgYjp0C4Qk7iLQXuc73ntq_AAK-sAACQKBoSnVzdqZq9QSpPQQ",  # Вступление, 39 сек
    1: "CQACAgIAAxkBAAIkIWrNPQjpbF990c7kyLoH0HQbusFuAALDsAACQKBoSluWvlLmWTkwPQQ",  # День 1, 618 сек
    2: "CQACAgIAAxkBAAIkImrNPQhqSZ9P8MT3mp78ei3n96qnAALKsAACQKBoSufAHNjrp2CbPQQ",  # День 2, 593 сек
    3: "CQACAgIAAxkBAAIkI2rNPQg4l57k4FDRAuZxBcvJftMYAALOsAACQKBoSnFBLBOfroSCPQQ",  # День 3, 632 сек
}

# ==================== ТЕКСТЫ ====================

TEXT_NOT_SUBSCRIBED = "Чтобы получить доступ к мини-курсу, подпишись на канал автора 🎙️"

TEXT_START = (
    "Привет! 👋 Я Юля Минченко, нутрициолог с высшим образованием и сертифицированный коуч по питанию 🌿\n\n"
    "Это мини-курс «Как забыть про диеты навсегда» 🎧\n\n"
    "Вас ждёт 3 коротких подкаста о том, почему мы годами мучаемся и пытаемся наладить питание. "
    "При том, что хорошо знаем, как «правильно питаться», и всё равно периодически переедаем, "
    "бросаем, начинаем заново и ищем следующую диету.\n\n"
    "Как выйти из этого круга?\n\n"
    "Будет три шага:\n"
    "День 1. Вернуться к базовым настройкам\n"
    "День 2. Всё связано\n"
    "День 3. Мы все разные\n\n"
    "Начинаем."
)

TEXT_AFTER_INTRO = "Каждый день я буду присылать одно аудио и небольшое задание для наблюдения за собой 📝"

TEXT_SEE_YOU_TOMORROW = "Следующее аудио придёт завтра в 10:00 по Москве 🎧"

TEXT_MIGRATE = (
    "Привет! Я обновила материалы — теперь здесь новый бесплатный мини-курс «Как забыть про диеты навсегда» 🌿\n\n"
    "Три коротких аудио о том, почему мы годами пытаемся наладить питание — и как из этого выйти.\n\n"
    "Хотите пройти?"
)

TEXTS_BEFORE = {
    1: (
        "🧭 <b>День 1. Вернуться к базовым настройкам</b>\n\n"
        "Из-за большого количества правил в питании и диетной культуры мы совсем разучились слушать свой организм. "
        "А именно он лучше знает, в какой момент и сколько нам нужно есть.\n\n"
        "В детстве мы могли целый день носиться по улице, а потом прийти домой настолько голодными, "
        "что были готовы съесть всё. А могли услышать: «Доедай». И совершенно искренне ответить: «Я больше не хочу».\n\n"
        "Но потом между нами и телом появляется огромное количество правил.\n\n"
        "«После шести нельзя».\n"
        "«Сладкое только по выходным».\n"
        "«Если худеешь — терпи».\n"
        "«Это плохой продукт».\n"
        "«Сегодня всё испортила».\n\n"
        "И вместо вопроса «что мне нужно?» мы спрашиваем только «А как правильно?». "
        "Сегодня попробуем вернуть свои правильные настройки."
    ),
    2: (
        "🔗 <b>День 2. Всё связано</b>\n\n"
        "Представьте. Вы плохо спали. Утром опаздывали. Днём пропустили нормальный обед. "
        "Начальник сделал неприятное замечание.\n\n"
        "После работы вы всё-таки заставили себя пойти на тренировку. "
        "А вечером открыли пачку чего-нибудь вкусного — и оказалось невозможно остановиться.\n\n"
        "Мы сразу думаем: я слабохарактерная 😔\n\n"
        "Но где именно в этой истории началась проблема? С самого печенья? Или значительно раньше?\n\n"
        "Сегодня поговорим о том, почему сон, стресс, нагрузка, режим дня и питание "
        "нельзя рассматривать отдельно друг от друга 💡"
    ),
    3: (
        "🌿 <b>День 3. Мы все разные</b>\n\n"
        "Представьте. Ваша знакомая похудела и рассказывает: «Я просто нашла свой способ питания — "
        "мне идеально подошло». Это может быть интервальное голодание, кето-диета, подсчёт калорий "
        "и что угодно ещё.\n\n"
        "Вы пробуете сделать так же… Но почему-то у вас не получается.\n\n"
        "Ей стало легче контролировать питание, а вы постоянно думаете о еде. "
        "Ей удобно есть по определённому режиму — а у вас этот режим рушится через несколько дней.\n\n"
        "Вы вините себя: «Почему у неё получилось, а у меня нет?» 😔\n\n"
        "Сегодня поговорим о том, почему один и тот же способ может прекрасно работать для одного человека "
        "и совершенно не подходить другому. И почему дело не в вашей силе воли или дисциплине 💡"
    ),
}

TEXTS_AFTER = {
    1: (
        "Сегодня ничего не исправляем. Только наблюдаем 👀 В течение дня пару раз спросите себя:\n\n"
        "<b>Почему я сейчас хочу есть?</b>\n\n"
        "Это может быть:\n"
        "— физический голод\n"
        "— привычное время\n"
        "— еда оказалась рядом\n"
        "— компания\n"
        "— скука\n"
        "— усталость\n"
        "— эмоции\n"
        "— просто удовольствие\n\n"
        "А когда заканчиваете есть:\n"
        "<b>Почему я решила остановиться именно сейчас?</b>\n\n"
        "Не оценивайте себя 🤍 Наша задача — впервые посмотреть на своё питание просто как на информацию о себе. "
        "Завтра поговорим о том, почему проблема с питанием начинается вообще не с еды."
    ),
    2: (
        "Сегодня попробуйте посмотреть не только на еду, а на день целиком 🔍\n\n"
        "Если вечером у вас сильный голод, тяга к сладкому или переедание, мысленно отмотайте на несколько часов назад:\n\n"
        "Как я спала?\n"
        "Когда я ела?\n"
        "Насколько устала?\n"
        "Что сегодня происходило эмоционально?\n"
        "Была ли тренировка или необычная нагрузка?\n"
        "Не пыталась ли я компенсировать вчерашнюю еду?\n\n"
        "Обычно то, что кажется «проблемой с ужином», было запущено ещё утром 💡\n\n"
        "Завтра нас ждёт самая интересная, последняя часть. "
        "Почему чужая идеальная система питания может совершенно не подходить вам."
    ),
    3: (
        "За эти три дня мы прошли путь от:\n"
        "«Со мной что-то не так, почему я не могу просто нормально питаться?»\n"
        "к совершенно другим выводам 🌿\n\n"
        "Мы поняли, что на ваше питание влияет:\n"
        "— ваш график, окружение\n"
        "— сон, стресс и движение\n"
        "— предыдущий опыт диет\n"
        "— доступность еды\n"
        "— привычки\n"
        "— и то, как устроена именно ваша жизнь\n\n"
        "Поэтому универсальный план или диета будет работать неделю — и рассыпаться при первом изменении "
        "обстоятельств, стрессе или усталости.\n\n"
        "Вам не нужен ещё один план или марафон, который придётся соблюдать. "
        "Вам нужна ваша Система питания, которой вы сможете пользоваться 💡\n\n"
        "Именно такую систему вы выстроите вместе со мной в программе «Система питания». "
        "Вы постепенно научитесь самостоятельно принимать решения о питании: что есть, когда, "
        "в каком количестве, почему происходят срывы и как худеть без диет.\n\n"
        "Вы будете знать, что делать не только в идеальный день, но и когда нет времени, вы устали, "
        "оказались в ресторане, переели или привычный режим сбился 🤍\n\n"
        "Система питания должна подстраиваться под жизнь, а не жизнь под систему.\n\n"
        "Если чувствуете, что именно этого вам всё время не хватало 👇\n\n"
        "🎁 Промокод на скидку для слушателей мини-курса: <b>КУРС</b>"
    ),
}

# ==================== КНОПКИ ====================

def kb_subscribe():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/myanutrition")],
        [InlineKeyboardButton("✅ Я подписался(ась)", callback_data="check_sub")],
    ])

def kb_start_course():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Начать мини-курс →", callback_data="btn_start_course")],
    ])

def kb_day3():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Перейти в «Систему питания» →", callback_data="btn_mysystem")],
    ])

def kb_migrate():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, хочу! →", callback_data="btn_migrate")],
    ])

def kb_broadcast_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить", callback_data="bcast_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="bcast_cancel")],
    ])

# ==================== БАЗА ДАННЫХ ====================

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            start_date TEXT,
            last_day INTEGER DEFAULT 0,
            blocked INTEGER DEFAULT 0,
            subscribed INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT,
            user_id INTEGER,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS button_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            button TEXT,
            user_id INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, start_date, last_day, subscribed) VALUES (?, ?, ?, ?)",
        (user_id, None, 0, 1)
    )
    c.execute(
        "INSERT INTO stats (event, user_id, created_at) VALUES (?, ?, ?)",
        ("new_user", user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def set_course_started(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    today = datetime.now().date().isoformat()
    c.execute(
        "UPDATE users SET start_date = ?, last_day = 1 WHERE user_id = ?",
        (today, user_id)
    )
    conn.commit()
    conn.close()

def log_event(event, user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO stats (event, user_id, created_at) VALUES (?, ?, ?)",
        (event, user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def log_button_click(button, user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO button_clicks (button, user_id, created_at) VALUES (?, ?, ?)",
        (button, user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def mark_blocked(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET blocked = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_old_users():
    """Пользователи из старого курса — у кого last_day >= 1"""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE blocked = 0 AND last_day >= 1")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def reset_user_progress(user_id):
    """Сбрасывает прогресс пользователя для нового курса"""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET start_date = NULL, last_day = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id, start_date, last_day FROM users WHERE blocked = 0 AND start_date IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    return rows

def get_users_by_day(day=None, done=False):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if done:
        c.execute("SELECT user_id FROM users WHERE blocked = 0 AND last_day >= ?", (MAX_DAY,))
    elif day is None:
        c.execute("SELECT user_id FROM users WHERE blocked = 0 AND start_date IS NOT NULL")
    else:
        c.execute("SELECT user_id FROM users WHERE blocked = 0 AND last_day >= ?", (day,))
    users = c.fetchall()
    conn.close()
    return [u[0] for u in users]

def update_last_day(user_id, day):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_day = ? WHERE user_id = ?", (day, user_id))
    conn.commit()
    conn.close()

def user_exists(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_stats():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE blocked = 1")
    blocked = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM stats WHERE event = 'not_subscribed'")
    not_subscribed = c.fetchone()[0]

    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("SELECT COUNT(*) FROM stats WHERE event = 'new_user' AND created_at >= ?", (week_ago,))
    new_week = c.fetchone()[0]

    days_stats = {}
    for day in range(1, MAX_DAY + 1):
        c.execute("SELECT COUNT(*) FROM users WHERE last_day = ? AND blocked = 0", (day,))
        days_stats[day] = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE last_day >= ? AND blocked = 0", (MAX_DAY,))
    completed = c.fetchone()[0]

    c.execute("SELECT button, COUNT(*) FROM button_clicks GROUP BY button")
    clicks = dict(c.fetchall())

    conn.close()
    return {
        "total": total,
        "blocked": blocked,
        "not_subscribed": not_subscribed,
        "new_week": new_week,
        "days": days_stats,
        "completed": completed,
        "clicks": clicks,
    }

# ==================== ПРОВЕРКА ПОДПИСКИ ====================

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# ==================== УВЕДОМЛЕНИЯ АДМИНУ ====================

async def notify_admin(bot, text):
    try:
        await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logging.error(f"Ошибка уведомления админа: {e}")

# ==================== ОТПРАВКА КОНТЕНТА ====================

async def safe_send(bot, user_id, func, *args, **kwargs):
    for attempt in range(3):
        try:
            return await func(user_id, *args, **kwargs)
        except Exception as e:
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                mark_blocked(user_id)
                return None
            if attempt < 2:
                logging.warning(f"Попытка {attempt+1} не удалась для {user_id}: {e}. Повтор через 5 сек...")
                await asyncio.sleep(5)
            else:
                logging.error(f"Все 3 попытки не удались для {user_id}: {e}")
    return None

async def send_welcome(bot, user_id):
    # Приветственное сообщение
    await safe_send(bot, user_id, bot.send_message, TEXT_START)
    await asyncio.sleep(1)

    # Аудио вступление
    await safe_send(bot, user_id, bot.send_audio, AUDIOS[0])
    await asyncio.sleep(1)

    # Текст + кнопка начать курс
    await safe_send(bot, user_id, bot.send_message, TEXT_AFTER_INTRO, reply_markup=kb_start_course())


async def send_day1(bot, user_id):
    await safe_send(bot, user_id, bot.send_message, TEXTS_BEFORE[1], parse_mode="HTML")
    await asyncio.sleep(1)
    await safe_send(bot, user_id, bot.send_audio, AUDIOS[1])
    await asyncio.sleep(1)
    await safe_send(bot, user_id, bot.send_message, TEXTS_AFTER[1], parse_mode="HTML")
    await asyncio.sleep(1)
    await safe_send(bot, user_id, bot.send_message, TEXT_SEE_YOU_TOMORROW)


async def send_day(bot, user_id, day):
    if day > MAX_DAY:
        return

    await safe_send(bot, user_id, bot.send_message, TEXTS_BEFORE[day], parse_mode="HTML")
    await asyncio.sleep(1)

    await safe_send(bot, user_id, bot.send_audio, AUDIOS[day])
    await asyncio.sleep(1)

    keyboard = None
    if day == MAX_DAY:
        keyboard = kb_day3()

    await safe_send(bot, user_id, bot.send_message, TEXTS_AFTER[day], parse_mode="HTML", reply_markup=keyboard)

    if day < MAX_DAY:
        await asyncio.sleep(1)
        await safe_send(bot, user_id, bot.send_message, TEXT_SEE_YOU_TOMORROW)

    update_last_day(user_id, day)

# ==================== ЕЖЕДНЕВНАЯ ЗАДАЧА ====================

async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    today = datetime.now().date()

    for user_id, start_date_str, last_day in users:
        if not start_date_str:
            continue
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            days_passed = (today - start_date).days
            next_day = last_day + 1

            if next_day <= MAX_DAY and days_passed == (next_day - 1):
                await send_day(context.bot, user_id, next_day)
                await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Ошибка в daily_job для пользователя {user_id}: {e}")

# ==================== ХЭНДЛЕРЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_exists(user_id):
        await update.message.reply_text("Вы уже зарегистрированы! Ожидайте следующее аудио 🎧")
        return

    subscribed = await is_subscribed(context.bot, user_id)
    if not subscribed:
        log_event("not_subscribed", user_id)
        await update.message.reply_text(TEXT_NOT_SUBSCRIBED, reply_markup=kb_subscribe())
        return

    add_user(user_id)
    username = update.effective_user.username or update.effective_user.first_name
    await notify_admin(context.bot, f"🆕 Новый пользователь: @{username} (ID: {user_id})")
    await send_welcome(context.bot, user_id)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Проверка подписки
    if data == "check_sub":
        subscribed = await is_subscribed(context.bot, user_id)
        if not subscribed:
            await query.message.reply_text(
                "Похоже, вы ещё не подписались 🙈 Подпишитесь на канал и нажмите кнопку снова!",
                reply_markup=kb_subscribe()
            )
            return
        if user_exists(user_id):
            await query.message.reply_text("Вы уже зарегистрированы! Ожидайте следующее аудио 🎧")
            return
        add_user(user_id)
        username = query.from_user.username or query.from_user.first_name
        await notify_admin(context.bot, f"🆕 Новый пользователь: @{username} (ID: {user_id})")
        await query.message.reply_text("Отлично, подписка подтверждена! 🎉 Начинаем!")
        await send_welcome(context.bot, user_id)
        return

    # Кнопка "Да, хочу!" — миграция старых пользователей
    if data == "btn_migrate":
        log_button_click("btn_migrate", user_id)
        await send_welcome(context.bot, user_id)
        return

    # Кнопка "Начать мини-курс"
    if data == "btn_start_course":
        log_button_click("btn_start_course", user_id)
        set_course_started(user_id)
        await send_day1(context.bot, user_id)
        return

    # Кнопка "Перейти в «Систему питания»"
    if data == "btn_mysystem":
        log_button_click("btn_mysystem", user_id)
        await query.message.reply_text(
            "Переходи по ссылке 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Перейти в «Систему питания» →", url="https://myanutrition.ru/mysystem")
            ]])
        )
        return

    # --- Подтверждение рассылки (только админ) ---
    if data in ("bcast_confirm", "bcast_cancel"):
        if user_id != ADMIN_CHAT_ID:
            return
        await handle_broadcast_callback(update, context, data)
        return


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    s = get_stats()

    days_text = ""
    for day, count in s["days"].items():
        days_text += f"  День {day}: {count} чел.\n"

    clicks_text = ""
    for btn, count in s["clicks"].items():
        clicks_text += f"  {btn}: {count}\n"
    if not clicks_text:
        clicks_text = "  Пока нет кликов\n"

    text = (
        f"📊 Статистика бота\n\n"
        f"👥 Всего пользователей: {s['total']}\n"
        f"🆕 Новых за неделю: {s['new_week']}\n"
        f"🚫 Заблокировали бота: {s['blocked']}\n"
        f"❌ Не подписались и ушли: {s['not_subscribed']}\n"
        f"✅ Завершили курс (День 3): {s['completed']}\n\n"
        f"📅 По дням:\n{days_text}\n"
        f"🔘 Клики по кнопкам:\n{clicks_text}"
    )

    await update.message.reply_text(text)


async def fixdb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    today = datetime.now().date().isoformat()
    c.execute("SELECT user_id, start_date FROM users")
    rows = c.fetchall()
    fixed = 0
    for user_id, start_date in rows:
        if start_date and (len(str(start_date)) != 10 or not str(start_date).startswith('20')):
            c.execute("UPDATE users SET start_date = ? WHERE user_id = ?", (today, user_id))
            fixed += 1
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Исправлено записей: {fixed}\nУстановлена дата: {today}")


# ==================== РАССЫЛКА ====================

PENDING_BROADCAST = {}


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Рассылка с полным сохранением форматирования.

    Как пользоваться:
      1. Напишите пост в чат с ботом — с любым форматированием,
         ссылками, абзацами, можно с фото.
      2. Ответьте на это сообщение командой:
           /broadcast all     — всем, кто начал курс
           /broadcast done    — прошедшим курс полностью (день 3)
           /broadcast day 2   — тем, кто на дне 2+
      3. Подтвердите отправку кнопкой.
    """
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    args = context.args
    usage = (
        "📣 <b>Рассылка</b>\n\n"
        "1. Напишите пост в этот чат — с форматированием, ссылками, абзацами.\n"
        "2. Ответьте на него командой:\n\n"
        "<code>/broadcast all</code> — всем, кто начал курс\n"
        "<code>/broadcast done</code> — прошедшим курс полностью (день 3)\n"
        "<code>/broadcast day 2</code> — тем, кто на дне 2+\n\n"
        "3. Подтвердите отправку кнопкой.\n\n"
        "Люди получат точную копию вашего сообщения — ничего не слетит."
    )

    if not args:
        await update.message.reply_text(usage, parse_mode="HTML")
        return

    replied = update.message.reply_to_message
    if not replied:
        await update.message.reply_text(
            "❗️ Команду нужно отправить <b>ответом</b> на сообщение, которое хотите разослать.\n\n" + usage,
            parse_mode="HTML"
        )
        return

    target = args[0].lower()
    day = None
    done = False

    if target == "done":
        done = True
        label = f"прошедшим курс полностью (день {MAX_DAY})"
    elif target == "day":
        if len(args) < 2 or not args[1].isdigit():
            await update.message.reply_text("Укажите день числом: /broadcast day 2")
            return
        day = int(args[1])
        label = f"тем, кто на дне {day}+"
    elif target == "all":
        label = "всем, кто начал курс"
    else:
        await update.message.reply_text("Первый аргумент: all, done или day N.")
        return

    users = get_users_by_day(day=day, done=done)

    if not users:
        await update.message.reply_text("В этой группе пока никого нет — рассылать некому.")
        return

    PENDING_BROADCAST[ADMIN_CHAT_ID] = {
        "from_chat_id": replied.chat_id,
        "message_id": replied.message_id,
        "users": users,
        "label": label,
    }

    await update.message.reply_text(
        f"📣 Рассылка готова.\n\n"
        f"Получатели: {label}\n"
        f"Количество: {len(users)} чел.\n\n"
        f"Отправляем?",
        reply_markup=kb_broadcast_confirm()
    )


async def handle_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    query = update.callback_query
    pending = PENDING_BROADCAST.pop(ADMIN_CHAT_ID, None)

    if data == "bcast_cancel":
        await query.message.reply_text("❌ Рассылка отменена.")
        return

    if not pending:
        await query.message.reply_text(
            "Черновик рассылки не найден — возможно, бот перезапускался. Отправьте команду заново."
        )
        return

    users = pending["users"]
    from_chat_id = pending["from_chat_id"]
    message_id = pending["message_id"]

    await query.message.reply_text(f"🚀 Начинаю рассылку: {len(users)} чел...")

    sent, failed, blocked_count = 0, 0, 0

    for i, user_id in enumerate(users, start=1):
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            sent += 1
        except RetryAfter as e:
            logging.warning(f"Flood control: ждём {e.retry_after} сек")
            await asyncio.sleep(e.retry_after + 1)
            try:
                await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id
                )
                sent += 1
            except Exception as e2:
                failed += 1
                logging.error(f"Ошибка рассылки для {user_id} после паузы: {e2}")
        except Exception as e:
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                mark_blocked(user_id)
                blocked_count += 1
            else:
                failed += 1
                logging.error(f"Ошибка рассылки для {user_id}: {e}")

        await asyncio.sleep(0.5)

        if i % 50 == 0:
            try:
                await context.bot.send_message(
                    ADMIN_CHAT_ID, f"⏳ Отправлено {i} из {len(users)}..."
                )
            except Exception:
                pass

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"✅ Рассылка завершена!\n\n"
        f"Отправлено: {sent}\n"
        f"Заблокировали бота: {blocked_count}\n"
        f"Прочих ошибок: {failed}"
    )


async def migrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылает старым пользователям приглашение в новый курс"""
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    users = get_old_users()
    if not users:
        await update.message.reply_text("Нет старых пользователей для миграции.")
        return

    await update.message.reply_text(f"🔄 Начинаю миграцию: {len(users)} чел...")

    sent, failed, blocked_count = 0, 0, 0

    for i, user_id in enumerate(users, start=1):
        try:
            reset_user_progress(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text=TEXT_MIGRATE,
                reply_markup=kb_migrate()
            )
            sent += 1
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=TEXT_MIGRATE,
                    reply_markup=kb_migrate()
                )
                sent += 1
            except Exception as e2:
                failed += 1
                logging.error(f"Ошибка миграции для {user_id} после паузы: {e2}")
        except Exception as e:
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                mark_blocked(user_id)
                blocked_count += 1
            else:
                failed += 1
                logging.error(f"Ошибка миграции для {user_id}: {e}")

        await asyncio.sleep(0.5)

        if i % 50 == 0:
            try:
                await context.bot.send_message(
                    ADMIN_CHAT_ID, f"⏳ Обработано {i} из {len(users)}..."
                )
            except Exception:
                pass

    await update.message.reply_text(
        f"✅ Миграция завершена!\n\n"
        f"Отправлено: {sent}\n"
        f"Заблокировали бота: {blocked_count}\n"
        f"Прочих ошибок: {failed}"
    )


async def runnow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("🚀 Запускаю рассылку прямо сейчас...")
    await daily_job(context)
    await update.message.reply_text("✅ Рассылка завершена!")


async def test_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    user_id = update.effective_user.id
    await update.message.reply_text("🧪 Запускаю тестовый режим...")

    await send_welcome(context.bot, user_id)
    await asyncio.sleep(2)
    await send_day1(context.bot, user_id)

    for day in range(2, MAX_DAY + 1):
        await asyncio.sleep(2)
        await send_day(context.bot, user_id, day)

    await update.message.reply_text("✅ Тест завершён!")


# ==================== ЗАПУСК ====================

def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_mode))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("runnow", runnow_command))
    app.add_handler(CommandHandler("migrate", migrate_command))
    app.add_handler(CommandHandler("fixdb", fixdb_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    job_queue = app.job_queue
    now = datetime.now()
    target_time = now.replace(hour=SEND_HOUR, minute=SEND_MINUTE, second=0, microsecond=0)
    if now >= target_time:
        target_time += timedelta(days=1)
    delay = (target_time - now).total_seconds()
    job_queue.run_repeating(daily_job, interval=86400, first=delay)

    print("Бот запущен! ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
