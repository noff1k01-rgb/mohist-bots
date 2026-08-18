#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import discord
from discord.ext import commands, tasks
from discord import ui, ButtonStyle, app_commands
import json
import asyncio
import time
from datetime import datetime

# =====================================================
#  🔐  ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# =====================================================

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Токен не найден!")

WEBDAV_URL = os.getenv("WEBDAV_URL", "https://tentacis.netcraze.pro:8083/webdav/")
WEBDAV_LOGIN = os.getenv("WEBDAV_LOGIN")
WEBDAV_PASSWORD = os.getenv("WEBDAV_PASSWORD")
WEBDAV_BASE = "/licnoe/Divace/server/"

# =====================================================
#  📦  ИМПОРТ WEBDAV
# =====================================================

try:
    from webdav3.client import Client
    WEBDAV_AVAILABLE = True
except ImportError:
    WEBDAV_AVAILABLE = False
    print("⚠️ webdavclient3 не установлен!")

# =====================================================
#  ☁️  РАБОТА С WEBDAV
# =====================================================

def get_webdav_client():
    """Создаёт клиент для WebDAV"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return None
    
    options = {
        'webdav_hostname': WEBDAV_URL,
        'webdav_login': WEBDAV_LOGIN,
        'webdav_password': WEBDAV_PASSWORD,
        'disable_ssl_certificate_validation': True,
        'webdav_timeout': 30,
    }
    return Client(options)

def get_full_path(filename):
    """Возвращает полный путь к файлу"""
    return f"{WEBDAV_BASE}{filename}"

def upload_to_webdav(filename, data):
    """Загружает данные на WebDAV"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return False
    
    try:
        client = get_webdav_client()
        if not client:
            return False
        
        full_path = get_full_path(filename)
        content = json.dumps(data, indent=4, ensure_ascii=False)
        
        try:
            client.mkdir(WEBDAV_BASE)
        except:
            pass
        
        try:
            client.download(full_path)
            client.upload(full_path, content.encode('utf-8'))
        except:
            client.upload(full_path, content.encode('utf-8'))
        
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки {filename}: {e}")
        return False

def download_from_webdav(filename):
    """Скачивает данные с WebDAV"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return None
    
    try:
        client = get_webdav_client()
        if not client:
            return None
        
        full_path = get_full_path(filename)
        content = client.download(full_path)
        return json.loads(content.decode('utf-8'))
    except:
        return None

def list_webdav_files():
    """Получает список файлов на WebDAV"""
    try:
        client = get_webdav_client()
        if not client:
            return []
        try:
            files = client.list(WEBDAV_BASE)
            return [f for f in files if not f.endswith('/')]
        except:
            return []
    except:
        return []

def test_webdav_write():
    """Тестовая запись на WebDAV"""
    try:
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Тестовая запись от бота Mohist_Level"
        }
        result = upload_to_webdav("test_write.json", test_data)
        if result:
            files = list_webdav_files()
            if "test_write.json" in files:
                return True, "✅ Тестовая запись успешна!"
            else:
                return False, "⚠️ Файл не появился в списке"
        else:
            return False, "❌ Не удалось записать файл"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"

# =====================================================
#  🔄  KEEP-ALIVE
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "✅ Mohist_Level работает!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=10000, debug=False)

threading.Thread(target=run, daemon=True).start()
print("✅ Keep-Alive запущен!")

# =====================================================
#  📁  РАБОТА С ДАННЫМИ
# =====================================================

LEVEL_FILE = "level_data.json"
CONFIG_FILE = "level_config.json"
VOICE_TIME_FILE = "voice_time.json"
PROFILE_FILE = "user_profiles.json"

_data_cache = {
    "level": None,
    "voice": None,
    "profiles": None,
    "config": None
}

def load_level_data(force_reload=False):
    if not force_reload and _data_cache["level"] is not None:
        return _data_cache["level"]
    data = download_from_webdav("level_data.json")
    if data is not None:
        _data_cache["level"] = data
        return data
    try:
        with open(LEVEL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _data_cache["level"] = data
            return data
    except:
        data = {}
        _data_cache["level"] = data
        return data

def save_level_data(data):
    _data_cache["level"] = data
    try:
        with open(LEVEL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("level_data.json", data)

def load_voice_time(force_reload=False):
    if not force_reload and _data_cache["voice"] is not None:
        return _data_cache["voice"]
    data = download_from_webdav("voice_time.json")
    if data is not None:
        _data_cache["voice"] = data
        return data
    try:
        with open(VOICE_TIME_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _data_cache["voice"] = data
            return data
    except:
        data = {}
        _data_cache["voice"] = data
        return data

def save_voice_time(data):
    _data_cache["voice"] = data
    try:
        with open(VOICE_TIME_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("voice_time.json", data)

def load_profiles(force_reload=False):
    if not force_reload and _data_cache["profiles"] is not None:
        return _data_cache["profiles"]
    data = download_from_webdav("user_profiles.json")
    if data is not None:
        _data_cache["profiles"] = data
        return data
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _data_cache["profiles"] = data
            return data
    except:
        data = {}
        _data_cache["profiles"] = data
        return data

def save_profiles(data):
    _data_cache["profiles"] = data
    try:
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("user_profiles.json", data)

def load_config(force_reload=False):
    if not force_reload and _data_cache["config"] is not None:
        return _data_cache["config"]
    data = download_from_webdav("level_config.json")
    if data is not None:
        _data_cache["config"] = data
        return data
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _data_cache["config"] = data
            return data
    except:
        default = {
            "message_xp": 1,
            "voice_xp": 2,
            "voice_interval": 60,
            "level_up_message": True,
            "level_up_channel": None,
            "message_cooldown": 60
        }
        save_config(default)
        return default

def save_config(data):
    _data_cache["config"] = data
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("level_config.json", data)

# =====================================================
#  💾  АВТОСОХРАНЕНИЕ И АВТООБНОВЛЕНИЕ
# =====================================================

@tasks.loop(minutes=5.0)
async def auto_reload_data():
    """Автоматически перезагружает данные с WebDAV каждые 5 минут"""
    try:
        load_level_data(force_reload=True)
        load_voice_time(force_reload=True)
        load_profiles(force_reload=True)
        load_config(force_reload=True)
    except Exception as e:
        print(f"❌ Ошибка автообновления: {e}")

@tasks.loop(minutes=1.0)
async def auto_save():
    """Автоматически сохраняет данные каждую минуту"""
    try:
        save_config(load_config())
        save_level_data(load_level_data())
        save_voice_time(load_voice_time())
        save_profiles(load_profiles())
    except Exception as e:
        print(f"❌ Автосохранение: {e}")

# =====================================================
#  📊  ФУНКЦИИ ДЛЯ XP
# =====================================================

def get_xp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

def get_level_from_xp(xp):
    level = 0
    while True:
        required = get_xp_for_level(level)
        if xp < required:
            break
        xp -= required
        level += 1
    return level

def get_progress(user_data):
    xp = user_data.get("xp", 0)
    level = user_data.get("level", 0)
    current_level_xp = get_xp_for_level(level - 1) if level > 0 else 0
    next_level_xp = get_xp_for_level(level)
    if next_level_xp == current_level_xp:
        return 100
    progress = (xp - current_level_xp) / (next_level_xp - current_level_xp) * 100
    return min(max(progress, 0), 100)

def get_rank(user_id, guild_id):
    data = load_level_data()
    guild_data = data.get(str(guild_id), {})
    sorted_users = sorted(
        guild_data.items(),
        key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
        reverse=True
    )
    for i, (uid, _) in enumerate(sorted_users, 1):
        if uid == str(user_id):
            return i
    return None

def get_voice_time(user_id, guild_id):
    data = load_voice_time()
    guild_data = data.get(str(guild_id), {})
    return guild_data.get(str(user_id), 0)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"

def create_progress_bar(progress, length=15):
    filled = int(progress / 100 * length)
    empty = length - filled
    return f"`{'█' * filled}{'░' * empty}`"

def get_user_profile(user_id, guild_id):
    profiles = load_profiles()
    guild_profiles = profiles.get(str(guild_id), {})
    return guild_profiles.get(str(user_id), {})

def update_user_profile(user_id, guild_id, data):
    profiles = load_profiles()
    if str(guild_id) not in profiles:
        profiles[str(guild_id)] = {}
    profiles[str(guild_id)][str(user_id)] = data
    save_profiles(profiles)

# =====================================================
#  🎨  ЦВЕТА И ЭМОДЗИ ДЛЯ ПРОФИЛЯ
# =====================================================

def get_level_color(level):
    """Цвет в зависимости от уровня"""
    if level >= 100:
        return discord.Color.gold()
    elif level >= 75:
        return discord.Color.purple()
    elif level >= 50:
        return discord.Color.blue()
    elif level >= 25:
        return discord.Color.green()
    elif level >= 10:
        return discord.Color.orange()
    elif level >= 5:
        return discord.Color.teal()
    else:
        return discord.Color.grey()

def get_level_rank_emoji(level):
    """Эмодзи для ранга"""
    if level >= 100:
        return "👑"
    elif level >= 75:
        return "💎"
    elif level >= 50:
        return "🌟"
    elif level >= 30:
        return "⭐"
    elif level >= 20:
        return "✨"
    elif level >= 10:
        return "💫"
    else:
        return "🌱"

def get_xp_emoji(progress):
    """Эмодзи для прогресса"""
    if progress >= 90:
        return "🔥"
    elif progress >= 70:
        return "⚡"
    elif progress >= 50:
        return "💪"
    elif progress >= 30:
        return "📈"
    else:
        return "🌱"

def get_medal(rank):
    """Медаль для места в топе"""
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    else:
        return f"#{rank}"

# =====================================================
#  🎮  БОТ
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

voice_tracker = {}
message_tracker = {}

# =====================================================
#  ✏️  РЕДАКТИРОВАНИЕ ПРОФИЛЯ
# =====================================================

class ProfileEditModal(ui.Modal, title="✏️ Изменение профиля"):
    def __init__(self, user_id, guild_id):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        
        profile = get_user_profile(user_id, guild_id)
        
        self.name = ui.TextInput(
            label="📇 Имя",
            placeholder="Введите ваше имя...",
            default=profile.get("name", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=50
        )
        self.add_item(self.name)
        
        self.age = ui.TextInput(
            label="🎂 Возраст",
            placeholder="Введите ваш возраст...",
            default=profile.get("age", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=3
        )
        self.add_item(self.age)
        
        self.gender = ui.TextInput(
            label="⚧ Пол",
            placeholder="Муж / Жен / Другой...",
            default=profile.get("gender", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=20
        )
        self.add_item(self.gender)
        
        self.bio = ui.TextInput(
            label="📝 Биография",
            placeholder="Расскажите о себе...",
            default=profile.get("bio", ""),
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.bio)
    
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваш профиль!", ephemeral=True)
            return
        
        data = {
            "name": self.name.value,
            "age": self.age.value,
            "gender": self.gender.value,
            "bio": self.bio.value,
            "updated_at": datetime.now().isoformat()
        }
        
        update_user_profile(self.user_id, self.guild_id, data)
        
        embed = discord.Embed(
            title="✅ Профиль обновлён!",
            description="Ваши данные успешно сохранены.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ProfileView(ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
    
    @ui.button(label="✏️ Редактировать профиль", style=ButtonStyle.primary, row=0)
    async def edit_profile(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваш профиль!", ephemeral=True)
            return
        
        modal = ProfileEditModal(self.user_id, self.guild_id)
        await interaction.response.send_modal(modal)

# =====================================================
#  🎯  ОСНОВНЫЕ КОМАНДЫ
# =====================================================

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📡 Серверов: {len(bot.guilds)}')
    
    if WEBDAV_LOGIN and WEBDAV_PASSWORD:
        try:
            client = get_webdav_client()
            if client:
                client.list()
                print('☁️ WebDAV: ✅ Подключено!')
        except Exception as e:
            print(f'☁️ WebDAV: ❌ {e}')
    else:
        print('☁️ WebDAV: ❌ Не настроен')
    
    print('=' * 50)
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="🎯 Уровни | /profile"
    ))
    
    try:
        await bot.tree.sync()
        print("✅ Слеш-команды синхронизированы глобально!")
        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                print(f"   ✅ Синхронизировано для {guild.name}")
            except Exception as e:
                print(f"   ❌ Ошибка для {guild.name}: {e}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
    auto_save.start()
    auto_reload_data.start()
    print("💾 Автосохранение запущено (каждую минуту)")
    print("🔄 Автообновление запущено (каждые 5 минут)")

# =====================================================
#  🎨  КРАСИВЫЙ ПРОФИЛЬ
# =====================================================

@bot.tree.command(name="profile", description="📊 Показать красивый профиль")
@app_commands.describe(member="Участник (опционально)")
async def slash_profile(interaction: discord.Interaction, member: discord.Member = None):
    if not member:
        member = interaction.user
    
    data = load_level_data()
    user_id = str(member.id)
    guild_id = str(interaction.guild.id)
    
    profile = get_user_profile(member.id, interaction.guild.id)
    name = profile.get("name", member.display_name)
    age = profile.get("age", "Не указан")
    gender = profile.get("gender", "Не указан")
    bio = profile.get("bio", "Не указана")
    
    if guild_id not in data:
        data[guild_id] = {}
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {"xp": 0, "level": 0, "messages": 0}
        save_level_data(data)
    
    user_data = data[guild_id][user_id]
    level = user_data.get("level", 0)
    xp = user_data.get("xp", 0)
    next_xp = get_xp_for_level(level)
    progress = get_progress(user_data)
    rank = get_rank(member.id, interaction.guild.id)
    voice_time = get_voice_time(member.id, interaction.guild.id)
    messages_count = user_data.get("messages", 0)
    
    color = get_level_color(level)
    rank_emoji = get_level_rank_emoji(level)
    xp_emoji = get_xp_emoji(progress)
    
    embed = discord.Embed(
        title=f"{rank_emoji} Профиль {member.display_name}",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    embed.add_field(
        name="📇 **Имя**",
        value=f"**{name}**",
        inline=True
    )
    embed.add_field(
        name="🎂 **Возраст**",
        value=f"**{age}**",
        inline=True
    )
    embed.add_field(
        name="⚧ **Пол**",
        value=f"**{gender}**",
        inline=True
    )
    
    embed.add_field(
        name="💬 **Сообщений**",
        value=f"**{messages_count}** 💬",
        inline=True
    )
    embed.add_field(
        name="🎤 **Голосовое время**",
        value=f"**{format_time(voice_time)}** 🎵",
        inline=True
    )
    embed.add_field(
        name="🏆 **Место**",
        value=f"**#{rank if rank else '—'}** 🏅",
        inline=True
    )
    
    if bio and bio != "Не указана":
        embed.add_field(
            name="📝 **Биография**",
            value=f"_{bio}_",
            inline=False
        )
    
    bar = create_progress_bar(progress)
    embed.add_field(
        name=f"{xp_emoji} **Прогресс до следующего уровня**",
        value=f"{bar} **{progress:.1f}%**",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **Уровень**",
        value=f"**{level}**",
        inline=True
    )
    embed.add_field(
        name="⭐ **XP**",
        value=f"**{xp}** / {next_xp}",
        inline=True
    )
    embed.add_field(
        name="📊 **Прогресс**",
        value=f"**{progress:.1f}%**",
        inline=True
    )
    
    embed.set_footer(
        text=f"🆔 {member.id} • Запрошено: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    view = ProfileView(member.id, interaction.guild.id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="top", description="🏆 Топ пользователей")
async def slash_top(interaction: discord.Interaction):
    data = load_level_data()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in data or not data[guild_id]:
        await interaction.response.send_message("📭 Нет активных пользователей")
        return
    
    sorted_users = sorted(
        data[guild_id].items(),
        key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
        reverse=True
    )
    
    embed = discord.Embed(
        title="🏆 Топ пользователей",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    
    for i, (uid, user_data) in enumerate(sorted_users[:10], 1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        level = user_data.get("level", 0)
        xp = user_data.get("xp", 0)
        voice_time = get_voice_time(int(uid), interaction.guild.id)
        
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"🎯 Уровень **{level}** | ⭐ {xp} XP\n🎤 {format_time(voice_time)}",
            inline=False
        )
    
    if len(sorted_users) > 10:
        embed.set_footer(text=f"И ещё {len(sorted_users)-10} участников...")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="server_stats", description="📊 Статистика сервера")
async def slash_server_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    
    data = load_level_data()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in data or not data[guild_id]:
        await interaction.followup.send("📭 Нет данных о пользователях")
        return
    
    users_data = data[guild_id]
    total_users = len(users_data)
    total_xp = sum(u.get("xp", 0) for u in users_data.values())
    total_messages = sum(u.get("messages", 0) for u in users_data.values())
    max_level = max((u.get("level", 0) for u in users_data.values()), default=0)
    
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
        reverse=True
    )
    
    embed = discord.Embed(
        title="📊 Статистика сервера",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    
    embed.add_field(
        name="👥 **Всего участников**",
        value=f"**{total_users}**",
        inline=True
    )
    embed.add_field(
        name="⭐ **Всего XP**",
        value=f"**{total_xp}**",
        inline=True
    )
    embed.add_field(
        name="👑 **Макс. уровень**",
        value=f"**{max_level}**",
        inline=True
    )
    
    embed.add_field(
        name="💬 **Всего сообщений**",
        value=f"**{total_messages}**",
        inline=True
    )
    embed.add_field(
        name="📊 **Средний уровень**",
        value=f"**{total_xp // total_users if total_users > 0 else 0}**",
        inline=True
    )
    embed.add_field(
        name="🏅 **Активных участников**",
        value=f"**{len([u for u in users_data.values() if u.get('messages', 0) > 0])}**",
        inline=True
    )
    
    top_text = ""
    for i, (uid, user_data) in enumerate(sorted_users[:3], 1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        level = user_data.get("level", 0)
        medals = ["🥇", "🥈", "🥉"]
        top_text += f"{medals[i-1]} **{name}** - Уровень {level}\n"
    
    if top_text:
        embed.add_field(
            name="🏆 **Топ участников**",
            value=top_text,
            inline=False
        )
    
    embed.set_footer(
        text=f"🆔 {interaction.guild.id}",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ping", description="🏓 Проверить работу бота")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Понг! {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="level", description="🎯 Открыть меню")
async def slash_level(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎯 Система уровней",
        description="💬 За сообщения + 🎤 За голосовой канал",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 **Доступные команды**",
        value="`/profile` - 📊 Красивый профиль\n"
              "`/top` - 🏆 Топ пользователей\n"
              "`/server_stats` - 📊 Статистика сервера\n"
              "`/ping` - 🏓 Проверить работу бота",
        inline=False
    )
    embed.add_field(
        name="🔧 **Администраторские**",
        value="`/webdav` - ☁️ Проверка WebDAV\n"
              "`/sync` - 🔄 Синхронизация команд",
        inline=False
    )
    embed.set_footer(text="💡 Будьте активны и повышайте свой уровень!")
    await interaction.response.send_message(embed=embed)

# =====================================================
#  ☁️  WEBDAV КОМАНДА
# =====================================================

@bot.tree.command(name="webdav", description="☁️ Проверить WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="☁️ Диагностика WebDAV",
        color=discord.Color.blue()
    )
    
    if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        embed.add_field(
            name="❌ WebDAV не настроен",
            value="Установите переменные:\n`WEBDAV_LOGIN` и `WEBDAV_PASSWORD`",
            inline=False
        )
        embed.color = discord.Color.red()
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    embed.add_field(
        name="🔐 Настройки",
        value=f"URL: {WEBDAV_URL}\nПуть: {WEBDAV_BASE}\nЛогин: {'✅' if WEBDAV_LOGIN else '❌'}\nПароль: {'✅' if WEBDAV_PASSWORD else '❌'}",
        inline=False
    )
    
    try:
        client = get_webdav_client()
        if client:
            files = list_webdav_files()
            embed.add_field(
                name="📡 Подключение",
                value=f"✅ Подключено! Файлов: {len(files)}",
                inline=False
            )
            
            if files:
                embed.add_field(
                    name="📁 Файлы",
                    value="\n".join(files[:15]),
                    inline=False
                )
        else:
            embed.add_field(
                name="📡 Подключение",
                value="❌ Не удалось подключиться",
                inline=False
            )
            embed.color = discord.Color.red()
    except Exception as e:
        embed.add_field(
            name="📡 Подключение",
            value=f"❌ Ошибка: {e}",
            inline=False
        )
        embed.color = discord.Color.red()
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# =====================================================
#  🔄  СИНХРОНИЗАЦИЯ
# =====================================================

@bot.tree.command(name="sync", description="🔄 Синхронизировать команды (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        await bot.tree.sync()
        for guild in bot.guilds:
            await bot.tree.sync(guild=guild)
        
        embed = discord.Embed(
            title="✅ Команды синхронизированы!",
            color=discord.Color.green()
        )
        commands_list = [cmd.name for cmd in bot.tree.get_commands()]
        embed.add_field(
            name="📋 Команды",
            value="\n".join(commands_list),
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

# =====================================================
#  📝  ПРЕФИКСНЫЕ КОМАНДЫ
# =====================================================

@bot.command(name='ping')
async def ping_command(ctx):
    await ctx.send(f"🏓 Понг! {round(bot.latency * 1000)}ms")

@bot.command(name='profile')
async def profile_command(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author
    
    data = load_level_data()
    user_id = str(member.id)
    guild_id = str(ctx.guild.id)
    
    profile = get_user_profile(member.id, ctx.guild.id)
    name = profile.get("name", member.display_name)
    age = profile.get("age", "Не указан")
    gender = profile.get("gender", "Не указан")
    bio = profile.get("bio", "Не указана")
    
    if guild_id not in data:
        data[guild_id] = {}
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {"xp": 0, "level": 0, "messages": 0}
        save_level_data(data)
    
    user_data = data[guild_id][user_id]
    level = user_data.get("level", 0)
    xp = user_data.get("xp", 0)
    next_xp = get_xp_for_level(level)
    progress = get_progress(user_data)
    rank = get_rank(member.id, ctx.guild.id)
    voice_time = get_voice_time(member.id, ctx.guild.id)
    messages_count = user_data.get("messages", 0)
    
    color = get_level_color(level)
    rank_emoji = get_level_rank_emoji(level)
    xp_emoji = get_xp_emoji(progress)
    
    embed = discord.Embed(
        title=f"{rank_emoji} Профиль {member.display_name}",
        color=color,
        timestamp=datetime.now()
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    embed.add_field(
        name="📇 **Имя**",
        value=f"**{name}**",
        inline=True
    )
    embed.add_field(
        name="🎂 **Возраст**",
        value=f"**{age}**",
        inline=True
    )
    embed.add_field(
        name="⚧ **Пол**",
        value=f"**{gender}**",
        inline=True
    )
    
    embed.add_field(
        name="💬 **Сообщений**",
        value=f"**{messages_count}** 💬",
        inline=True
    )
    embed.add_field(
        name="🎤 **Голосовое время**",
        value=f"**{format_time(voice_time)}** 🎵",
        inline=True
    )
    embed.add_field(
        name="🏆 **Место**",
        value=f"**#{rank if rank else '—'}** 🏅",
        inline=True
    )
    
    if bio and bio != "Не указана":
        embed.add_field(
            name="📝 **Биография**",
            value=f"_{bio}_",
            inline=False
        )
    
    bar = create_progress_bar(progress)
    embed.add_field(
        name=f"{xp_emoji} **Прогресс до следующего уровня**",
        value=f"{bar} **{progress:.1f}%**",
        inline=False
    )
    
    embed.add_field(
        name="🎯 **Уровень**",
        value=f"**{level}**",
        inline=True
    )
    embed.add_field(
        name="⭐ **XP**",
        value=f"**{xp}** / {next_xp}",
        inline=True
    )
    embed.add_field(
        name="📊 **Прогресс**",
        value=f"**{progress:.1f}%**",
        inline=True
    )
    
    embed.set_footer(
        text=f"🆔 {member.id} • Запрошено: {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    view = ProfileView(member.id, ctx.guild.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name='top')
async def top_command(ctx):
    data = load_level_data()
    guild_id = str(ctx.guild.id)
    
    if guild_id not in data or not data[guild_id]:
        await ctx.send("📭 Нет активных пользователей")
        return
    
    sorted_users = sorted(
        data[guild_id].items(),
        key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
        reverse=True
    )
    
    embed = discord.Embed(
        title="🏆 Топ пользователей",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    
    for i, (uid, user_data) in enumerate(sorted_users[:10], 1):
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        level = user_data.get("level", 0)
        xp = user_data.get("xp", 0)
        voice_time = get_voice_time(int(uid), ctx.guild.id)
        
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"🎯 Уровень **{level}** | ⭐ {xp} XP\n🎤 {format_time(voice_time)}",
            inline=False
        )
    
    if len(sorted_users) > 10:
        embed.set_footer(text=f"И ещё {len(sorted_users)-10} участников...")
    
    await ctx.send(embed=embed)

@bot.command(name='server_stats')
async def server_stats_command(ctx):
    data = load_level_data()
    guild_id = str(ctx.guild.id)
    
    if guild_id not in data or not data[guild_id]:
        await ctx.send("📭 Нет данных о пользователях")
        return
    
    users_data = data[guild_id]
    total_users = len(users_data)
    total_xp = sum(u.get("xp", 0) for u in users_data.values())
    total_messages = sum(u.get("messages", 0) for u in users_data.values())
    max_level = max((u.get("level", 0) for u in users_data.values()), default=0)
    
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
        reverse=True
    )
    
    embed = discord.Embed(
        title="📊 Статистика сервера",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    
    embed.add_field(
        name="👥 **Всего участников**",
        value=f"**{total_users}**",
        inline=True
    )
    embed.add_field(
        name="⭐ **Всего XP**",
        value=f"**{total_xp}**",
        inline=True
    )
    embed.add_field(
        name="👑 **Макс. уровень**",
        value=f"**{max_level}**",
        inline=True
    )
    
    embed.add_field(
        name="💬 **Всего сообщений**",
        value=f"**{total_messages}**",
        inline=True
    )
    embed.add_field(
        name="📊 **Средний уровень**",
        value=f"**{total_xp // total_users if total_users > 0 else 0}**",
        inline=True
    )
    embed.add_field(
        name="🏅 **Активных участников**",
        value=f"**{len([u for u in users_data.values() if u.get('messages', 0) > 0])}**",
        inline=True
    )
    
    top_text = ""
    for i, (uid, user_data) in enumerate(sorted_users[:3], 1):
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        level = user_data.get("level", 0)
        medals = ["🥇", "🥈", "🥉"]
        top_text += f"{medals[i-1]} **{name}** - Уровень {level}\n"
    
    if top_text:
        embed.add_field(
            name="🏆 **Топ участников**",
            value=top_text,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='webdav')
@commands.has_permissions(administrator=True)
async def webdav_command(ctx):
    await ctx.send("🔍 Проверка WebDAV...")
    
    if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        await ctx.send("❌ WebDAV не настроен!")
        return
    
    try:
        client = get_webdav_client()
        if not client:
            await ctx.send("❌ Не удалось подключиться!")
            return
        
        files = list_webdav_files()
        embed = discord.Embed(
            title="☁️ Диагностика WebDAV",
            color=discord.Color.green() if files else discord.Color.blue()
        )
        
        embed.add_field(
            name="📡 Подключение",
            value="✅ Подключено успешно!",
            inline=False
        )
        
        embed.add_field(
            name="📁 Файлов на сервере",
            value=str(len(files)),
            inline=True
        )
        
        if files:
            embed.add_field(
                name="📋 Список файлов",
                value="\n".join(files[:10]),
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Список файлов",
                value="Папка пуста",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command(name='sync')
@commands.has_permissions(administrator=True)
async def sync_commands(ctx):
    await ctx.send("🔄 Синхронизация команд...")
    
    try:
        await bot.tree.sync()
        await ctx.send("✅ Глобальная синхронизация выполнена!")
        
        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                await ctx.send(f"   ✅ Синхронизировано для {guild.name}")
            except Exception as e:
                await ctx.send(f"   ❌ Ошибка для {guild.name}: {e}")
        
        commands_list = [cmd.name for cmd in bot.tree.get_commands()]
        await ctx.send(f"📋 Команды: {', '.join(commands_list)}")
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

# =====================================================
#  💬  XP ЗА СООБЩЕНИЯ
# =====================================================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return
    
    config = load_config()
    message_xp = config.get('message_xp', 1)
    cooldown = config.get('message_cooldown', 60)
    
    user_id = str(message.author.id)
    guild_id = str(message.guild.id)
    
    if user_id not in message_tracker:
        message_tracker[user_id] = {}
    
    last_time = message_tracker[user_id].get(guild_id)
    if last_time and (datetime.now() - last_time).seconds < cooldown:
        await bot.process_commands(message)
        return
    
    message_tracker[user_id][guild_id] = datetime.now()
    
    data = load_level_data()
    if guild_id not in data:
        data[guild_id] = {}
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {"xp": 0, "level": 0, "messages": 0}
    
    data[guild_id][user_id]["xp"] += message_xp
    data[guild_id][user_id]["messages"] = data[guild_id][user_id].get("messages", 0) + 1
    
    current_level = data[guild_id][user_id]["level"]
    new_level = get_level_from_xp(data[guild_id][user_id]["xp"])
    
    if new_level > current_level:
        data[guild_id][user_id]["level"] = new_level
        if config.get('level_up_message', True):
            try:
                channel_id = config.get('level_up_channel')
                channel = message.guild.get_channel(channel_id) if channel_id else message.guild.system_channel
                if channel:
                    embed = discord.Embed(
                        title="🎉 Повышение уровня!",
                        description=f"{message.author.mention} достиг **{new_level}** уровня!",
                        color=discord.Color.gold()
                    )
                    await channel.send(embed=embed)
            except:
                pass
    
    save_level_data(data)
    await bot.process_commands(message)

# =====================================================
#  🎵  XP ЗА ГОЛОС
# =====================================================

async def give_voice_xp():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            config = load_config()
            voice_xp = config.get('voice_xp', 2)
            interval = config.get('voice_interval', 60)
            
            data = load_level_data()
            voice_data = load_voice_time()
            
            for guild in bot.guilds:
                guild_id = str(guild.id)
                
                if guild_id not in data:
                    data[guild_id] = {}
                if guild_id not in voice_data:
                    voice_data[guild_id] = {}
                
                for member in guild.members:
                    if member.voice and member.voice.channel:
                        user_id = str(member.id)
                        
                        if user_id not in voice_tracker:
                            voice_tracker[user_id] = {}
                        if guild_id not in voice_tracker[user_id]:
                            voice_tracker[user_id][guild_id] = datetime.now()
                            continue
                        
                        last_time = voice_tracker[user_id][guild_id]
                        seconds_passed = (datetime.now() - last_time).seconds
                        
                        if seconds_passed < interval:
                            continue
                        
                        voice_tracker[user_id][guild_id] = datetime.now()
                        
                        if user_id not in voice_data[guild_id]:
                            voice_data[guild_id][user_id] = 0
                        voice_data[guild_id][user_id] += interval
                        save_voice_time(voice_data)
                        
                        if user_id not in data[guild_id]:
                            data[guild_id][user_id] = {"xp": 0, "level": 0}
                        
                        data[guild_id][user_id]["xp"] += voice_xp
                        
                        current_level = data[guild_id][user_id]["level"]
                        new_level = get_level_from_xp(data[guild_id][user_id]["xp"])
                        
                        if new_level > current_level:
                            data[guild_id][user_id]["level"] = new_level
                            if config.get('level_up_message', True):
                                try:
                                    channel_id = config.get('level_up_channel')
                                    channel = guild.get_channel(channel_id) if channel_id else guild.system_channel
                                    if channel:
                                        embed = discord.Embed(
                                            title="🎉 Повышение уровня!",
                                            description=f"{member.mention} достиг **{new_level}** уровня в голосовом!",
                                            color=discord.Color.gold()
                                        )
                                        await channel.send(embed=embed)
                                except:
                                    pass
                        
                        save_level_data(data)
                        
        except Exception as e:
            print(f"❌ Ошибка голосового XP: {e}")
        
        await asyncio.sleep(interval)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel and not after.channel:
        user_id = str(member.id)
        guild_id = str(member.guild.id)
        if user_id in voice_tracker and guild_id in voice_tracker[user_id]:
            del voice_tracker[user_id][guild_id]
            if not voice_tracker[user_id]:
                del voice_tracker[user_id]

# =====================================================
#  🚀  ЗАПУСК
# =====================================================

async def main():
    async with bot:
        print("🔄 Запуск Mohist_Level...")
        bot.loop.create_task(give_voice_xp())
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        print("❌ Неверный токен!")
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
