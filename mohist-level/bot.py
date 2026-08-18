#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import discord
from discord.ext import commands, tasks
from discord import ui, ButtonStyle, SelectOption, app_commands
import json
import asyncio
import math
import time
from datetime import datetime, timedelta

# =====================================================
#  🔐  ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# =====================================================

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Токен не найден! Установите переменную окружения TOKEN")

WEBDAV_URL = os.getenv("WEBDAV_URL", "https://tentacis.netcraze.pro:8083/webdav/%D0%BB%D0%B8%D1%86%D0%BD%D0%BE%D0%B5/Divace/server/")
WEBDAV_LOGIN = os.getenv("WEBDAV_LOGIN")
WEBDAV_PASSWORD = os.getenv("WEBDAV_PASSWORD")

# =====================================================
#  📦  ИМПОРТ WEBDAV
# =====================================================

try:
    from webdav3.client import Client
    WEBDAV_AVAILABLE = True
except ImportError:
    WEBDAV_AVAILABLE = False
    print("⚠️ webdavclient3 не установлен! Установите: pip install webdavclient3")

# =====================================================
#  ☁️  РАБОТА С WEBDAV (УЛУЧШЕННАЯ)
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

def upload_to_webdav(filename, data, retry=3):
    """Загружает данные на WebDAV с повторными попытками"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return False
    
    for attempt in range(retry):
        try:
            client = get_webdav_client()
            if not client:
                return False
            
            content = json.dumps(data, indent=4, ensure_ascii=False)
            
            try:
                client.download(filename)
                client.upload(filename, content.encode('utf-8'))
                print(f"✅ Обновлён на WebDAV: {filename}")
            except:
                client.upload(filename, content.encode('utf-8'))
                print(f"✅ Создан на WebDAV: {filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Попытка {attempt+1}/{retry} загрузки {filename}: {e}")
            if attempt < retry - 1:
                time.sleep(2 ** attempt)
    
    print(f"❌ Не удалось загрузить {filename} после {retry} попыток")
    return False

def download_from_webdav(filename, retry=3):
    """Скачивает данные с WebDAV с повторными попытками"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return None
    
    for attempt in range(retry):
        try:
            client = get_webdav_client()
            if not client:
                return None
            
            content = client.download(filename)
            data = json.loads(content.decode('utf-8'))
            print(f"✅ Загружен с WebDAV: {filename}")
            return data
            
        except Exception as e:
            print(f"⚠️ Попытка {attempt+1}/{retry} загрузки {filename}: {e}")
            if attempt < retry - 1:
                time.sleep(2 ** attempt)
    
    print(f"⚠️ Файл {filename} не найден на WebDAV")
    return None

def test_webdav_connection():
    """Проверяет подключение к WebDAV"""
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return False, "WebDAV не настроен"
    
    try:
        client = get_webdav_client()
        if not client:
            return False, "Не удалось создать клиент"
        
        client.list()
        return True, "Подключено успешно"
    except Exception as e:
        return False, f"Ошибка: {str(e)}"

# =====================================================
#  🔄  KEEP-ALIVE ДЛЯ RENDER
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "🎯 Mohist_Level работает!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=10000, debug=False)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
print("✅ Keep-Alive запущен!")

# =====================================================
#  📁  РАБОТА С ДАННЫМИ
# =====================================================

LEVEL_FILE = "level_data.json"
CONFIG_FILE = "level_config.json"
VOICE_TIME_FILE = "voice_time.json"
PROFILE_FILE = "user_profiles.json"

def load_level_data():
    """Загружает данные - сначала с WebDAV, потом локально"""
    data = download_from_webdav("level_data.json")
    if data is not None:
        return data
    
    try:
        with open(LEVEL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📂 Загружено локально: {LEVEL_FILE}")
            upload_to_webdav("level_data.json", data)
            return data
    except FileNotFoundError:
        print(f"📭 Создаю новый файл: {LEVEL_FILE}")
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки {LEVEL_FILE}: {e}")
        return {}

def save_level_data(data):
    """Сохраняет данные на WebDAV и локально"""
    try:
        with open(LEVEL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Локально сохранено: {LEVEL_FILE}")
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    
    upload_to_webdav("level_data.json", data)

def load_voice_time():
    data = download_from_webdav("voice_time.json")
    if data is not None:
        return data
    try:
        with open(VOICE_TIME_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            upload_to_webdav("voice_time.json", data)
            return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки {VOICE_TIME_FILE}: {e}")
        return {}

def save_voice_time(data):
    try:
        with open(VOICE_TIME_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Локально сохранено: {VOICE_TIME_FILE}")
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("voice_time.json", data)

def load_profiles():
    data = download_from_webdav("user_profiles.json")
    if data is not None:
        return data
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            upload_to_webdav("user_profiles.json", data)
            return data
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки {PROFILE_FILE}: {e}")
        return {}

def save_profiles(data):
    try:
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Локально сохранено: {PROFILE_FILE}")
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("user_profiles.json", data)

def load_config():
    data = download_from_webdav("level_config.json")
    if data is not None:
        return data
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            upload_to_webdav("level_config.json", data)
            return data
    except FileNotFoundError:
        default_config = {
            "message_xp": 1,
            "voice_xp": 2,
            "voice_interval": 60,
            "level_up_message": True,
            "level_up_channel": None,
            "roles": {},
            "message_cooldown": 60
        }
        save_config(default_config)
        return default_config
    except Exception as e:
        print(f"❌ Ошибка загрузки {CONFIG_FILE}: {e}")
        return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Локально сохранено: {CONFIG_FILE}")
    except Exception as e:
        print(f"❌ Ошибка локального сохранения: {e}")
    upload_to_webdav("level_config.json", data)

# =====================================================
#  💾  АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ
# =====================================================

@tasks.loop(minutes=1.0)
async def auto_save():
    """Автоматически сохраняет данные каждую минуту"""
    try:
        print(f"💾 Автосохранение начато: {datetime.now().strftime('%H:%M:%S')}")
        
        config = load_config()
        save_config(config)
        
        data = load_level_data()
        save_level_data(data)
        
        voice_data = load_voice_time()
        save_voice_time(voice_data)
        
        profiles = load_profiles()
        save_profiles(profiles)
        
        print(f"💾 Автосохранение завершено: {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Ошибка автосохранения: {e}")

@tasks.loop(minutes=5.0)
async def auto_save_webdav():
    """Автоматически сохраняет данные на WebDAV каждые 5 минут"""
    try:
        if WEBDAV_LOGIN and WEBDAV_PASSWORD:
            print(f"☁️ WebDAV автосохранение: {datetime.now().strftime('%H:%M:%S')}")
            
            data = load_level_data()
            upload_to_webdav("level_data.json", data)
            
            voice_data = load_voice_time()
            upload_to_webdav("voice_time.json", voice_data)
            
            profiles = load_profiles()
            upload_to_webdav("user_profiles.json", profiles)
            
            config = load_config()
            upload_to_webdav("level_config.json", config)
    except Exception as e:
        print(f"❌ Ошибка WebDAV автосохранения: {e}")

# =====================================================
#  📊  ФУНКЦИИ ДЛЯ XP И УРОВНЕЙ
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

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📡 Серверов: {len(bot.guilds)}')
    
    print('☁️ Проверка WebDAV...')
    success, message = test_webdav_connection()
    if success:
        print(f'☁️ WebDAV: ✅ {message}')
        try:
            client = get_webdav_client()
            if client:
                files = client.list()
                required = ["level_data.json", "voice_time.json", "user_profiles.json", "level_config.json"]
                for f in required:
                    if f in files:
                        print(f'   ✅ {f} найден')
                    else:
                        print(f'   ⚠️ {f} отсутствует (будет создан)')
        except Exception as e:
            print(f'   ⚠️ Ошибка при проверке файлов: {e}')
    else:
        print(f'☁️ WebDAV: ❌ {message}')
    
    print('=' * 50)
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="🎯 Уровни | /profile"
    ))
    
    try:
        await bot.tree.sync()
        print("✅ Слеш-команды синхронизированы!")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
    auto_save.start()
    auto_save_webdav.start()
    print("💾 Автосохранение запущено (каждую минуту)")
    print("☁️ WebDAV автосохранение запущено (каждые 5 минут)")

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
            label="Имя",
            placeholder="Введите ваше имя...",
            default=profile.get("name", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=50
        )
        self.add_item(self.name)
        
        self.age = ui.TextInput(
            label="Возраст",
            placeholder="Введите ваш возраст...",
            default=profile.get("age", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=3
        )
        self.add_item(self.age)
        
        self.gender = ui.TextInput(
            label="Пол",
            placeholder="Муж / Жен / Другой...",
            default=profile.get("gender", ""),
            required=False,
            style=discord.TextStyle.short,
            max_length=20
        )
        self.add_item(self.gender)
        
        self.bio = ui.TextInput(
            label="Биография",
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
    
    embed = discord.Embed(
        title=f"📊 Профиль участника {member.display_name}",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    embed.add_field(name="📇 Имя", value=f"**{name}**", inline=True)
    embed.add_field(name="🎂 Возраст", value=f"**{age}**", inline=True)
    embed.add_field(name="⚧ Пол", value=f"**{gender}**", inline=True)
    embed.add_field(name="💬 Сообщений", value=f"**{messages_count}**", inline=True)
    embed.add_field(name="🎤 Голосовое время", value=f"**{format_time(voice_time)}**", inline=True)
    embed.add_field(name="📝 Биография", value=bio if bio and bio != "Не указана" else "Не указана", inline=False)
    
    bar = create_progress_bar(progress)
    embed.add_field(
        name="📊 Прогресс до следующего уровня",
        value=f"{bar} **{progress:.1f}%**",
        inline=False
    )
    
    embed.add_field(name="🎯 Уровень", value=f"**{level}**", inline=True)
    embed.add_field(name="⭐ XP", value=f"**{xp}** / {next_xp}", inline=True)
    embed.add_field(name="🏆 Место", value=f"**#{rank if rank else '—'}**", inline=True)
    
    embed.set_footer(
        text=f"🆔 {member.id} • Запрошено: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    view = ProfileView(member.id, interaction.guild.id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="level", description="🎯 Открыть меню")
async def slash_level(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎯 Система уровней",
        description="💬 За сообщения + 🎤 За голосовой канал",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Команды",
        value="`/profile` - Красивый профиль\n"
              "`/top` - Топ пользователей\n"
              "`/rank` - Ваше место\n"
              "`/voice_stats` - Голосовая статистика\n"
              "`/ping` - Проверить работу бота\n"
              "`/settings` - Настройки (админ)\n"
              "`/webdav` - Проверка WebDAV (админ)\n"
              "`/webdav_test` - Тест WebDAV (админ)\n"
              "`/webdav_files` - Файлы на WebDAV (админ)\n"
              "`/webdav_sync` - Синхронизация с WebDAV (админ)\n"
              "`/sync_commands` - Синхронизация команд (админ)\n"
              "`/autosave` - Управление автосохранением (админ)\n"
              "`/level_reload` - Перезагрузить данные (админ)\n"
              "`/level_save` - Сохранить данные (админ)",
        inline=False
    )
    embed.set_footer(text="💡 Будьте активны!")
    await interaction.response.send_message(embed=embed)

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
        color=discord.Color.gold()
    )
    
    for i, (uid, user_data) in enumerate(sorted_users[:10], 1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"<@{uid}>"
        level = user_data.get("level", 0)
        xp = user_data.get("xp", 0)
        voice_time = get_voice_time(int(uid), interaction.guild.id)
        
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"🎯 Уровень {level} | ⭐ {xp} XP\n🎤 {format_time(voice_time)}",
            inline=False
        )
    
    if len(sorted_users) > 10:
        embed.set_footer(text=f"И ещё {len(sorted_users)-10} участников...")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rank", description="🏆 Ваше место в рейтинге")
async def slash_rank(interaction: discord.Interaction):
    data = load_level_data()
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    
    if guild_id not in data or user_id not in data[guild_id]:
        await interaction.response.send_message("📭 У вас пока нет XP!", ephemeral=True)
        return
    
    rank = get_rank(interaction.user.id, interaction.guild.id)
    user_data = data[guild_id][user_id]
    total = len(data[guild_id])
    voice_time = get_voice_time(interaction.user.id, interaction.guild.id)
    
    embed = discord.Embed(
        title="🏆 Ваш рейтинг",
        color=discord.Color.blue()
    )
    embed.add_field(name="📊 Место", value=f"**#{rank}** из {total}", inline=True)
    embed.add_field(name="🎯 Уровень", value=f"**{user_data.get('level', 0)}**", inline=True)
    embed.add_field(name="⭐ XP", value=f"**{user_data.get('xp', 0)}**", inline=True)
    embed.add_field(name="🎤 Время в голосовых", value=format_time(voice_time), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="voice_stats", description="🎤 Статистика голосовой активности")
@app_commands.describe(member="Участник (опционально)")
async def slash_voice_stats(interaction: discord.Interaction, member: discord.Member = None):
    if not member:
        member = interaction.user
    
    voice_time = get_voice_time(member.id, interaction.guild.id)
    
    embed = discord.Embed(
        title=f"🎤 Голосовая статистика {member.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(
        name="⏱️ Общее время",
        value=f"**{format_time(voice_time)}**",
        inline=True
    )
    
    if member.voice and member.voice.channel:
        embed.add_field(
            name="🔊 Сейчас в канале",
            value=f"**{member.voice.channel.name}**",
            inline=True
        )
        embed.color = discord.Color.green()
    else:
        embed.add_field(
            name="🔇 Статус",
            value="Не в голосовом канале",
            inline=True
        )
        embed.color = discord.Color.grey()
    
    embed.set_footer(text=f"🆔 {member.id}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="🏓 Проверить работу бота")
async def slash_ping(interaction: discord.Interaction):
    """Простая команда для проверки"""
    await interaction.response.send_message(f"🏓 Понг! Задержка: {round(bot.latency * 1000)}ms", ephemeral=True)

# =====================================================
#  ⚙️  НАСТРОЙКИ
# =====================================================

@bot.tree.command(name="settings", description="⚙️ Настройки (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_settings(interaction: discord.Interaction):
    await interaction.response.defer()
    config = load_config()
    embed = discord.Embed(
        title="⚙️ Настройки",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📊 Текущие настройки",
        value=f"💬 XP за сообщение: **{config.get('message_xp', 1)}**\n"
              f"🎵 XP за голос: **{config.get('voice_xp', 2)}**\n"
              f"⏱️ Интервал: **{config.get('voice_interval', 60)}** сек\n"
              f"📢 Оповещения: **{'Вкл' if config.get('level_up_message', True) else 'Выкл'}**",
        inline=False
    )
    await interaction.followup.send(embed=embed, view=FullSettingsView())

class FullSettingsView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.update_buttons()
    
    def update_buttons(self):
        for item in self.children[:]:
            self.remove_item(item)
        
        config = load_config()
        
        xp_btn = ui.Button(
            label=f"💬 XP за сообщ: {config.get('message_xp', 1)}",
            style=ButtonStyle.primary,
            row=0,
            custom_id="msg_xp"
        )
        xp_btn.callback = self.msg_xp_callback
        self.add_item(xp_btn)
        
        voice_btn = ui.Button(
            label=f"🎵 XP за голос: {config.get('voice_xp', 2)}",
            style=ButtonStyle.primary,
            row=0,
            custom_id="voice_xp"
        )
        voice_btn.callback = self.voice_xp_callback
        self.add_item(voice_btn)
        
        int_btn = ui.Button(
            label=f"⏱️ Интервал: {config.get('voice_interval', 60)}с",
            style=ButtonStyle.primary,
            row=1,
            custom_id="interval_settings"
        )
        int_btn.callback = self.interval_callback
        self.add_item(int_btn)
        
        status = "✅ Вкл" if config.get('level_up_message', True) else "❌ Выкл"
        notify_btn = ui.Button(
            label=f"📢 Оповещения: {status}",
            style=ButtonStyle.success if config.get('level_up_message', True) else ButtonStyle.danger,
            row=1,
            custom_id="notify_settings"
        )
        notify_btn.callback = self.notify_callback
        self.add_item(notify_btn)
        
        channel_btn = ui.Button(
            label="📌 Канал оповещений",
            style=ButtonStyle.secondary,
            row=2,
            custom_id="channel_settings"
        )
        channel_btn.callback = self.channel_callback
        self.add_item(channel_btn)
        
        close_btn = ui.Button(
            label="❌ Закрыть",
            style=ButtonStyle.danger,
            row=2,
            custom_id="close_settings"
        )
        close_btn.callback = self.close_callback
        self.add_item(close_btn)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def msg_xp_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = MsgXPView()
        embed = discord.Embed(
            title="💬 XP за сообщения",
            description="Выберите XP за одно сообщение",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def voice_xp_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = VoiceXPView()
        embed = discord.Embed(
            title="🎵 XP за голосовой канал",
            description="Выберите XP за минуту в голосовом",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def interval_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = IntervalView()
        embed = discord.Embed(
            title="⏱️ Интервал проверки",
            description="Выберите интервал в секундах",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def notify_callback(self, interaction: discord.Interaction):
        config = load_config()
        config['level_up_message'] = not config.get('level_up_message', True)
        save_config(config)
        self.update_buttons()
        status = "Включены" if config['level_up_message'] else "Выключены"
        embed = discord.Embed(
            title="📢 Оповещения",
            description=f"Оповещения **{status}**",
            color=discord.Color.green() if config['level_up_message'] else discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def channel_callback(self, interaction: discord.Interaction):
        modal = ChannelModal()
        await interaction.response.send_modal(modal)
    
    async def close_callback(self, interaction: discord.Interaction):
        await interaction.message.delete()
        await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)

class MsgXPView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        current = load_config().get('message_xp', 1)
        for val in [1, 2, 3, 4, 5, 8, 10]:
            btn = ui.Button(
                label=f"{val} XP",
                style=ButtonStyle.primary if val == current else ButtonStyle.secondary,
                row=0 if val <= 5 else 1,
                custom_id=f"msgxp_{val}"
            )
            btn.callback = self.callback
            self.add_item(btn)
        back_btn = ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back")
        back_btn.callback = self.back_callback
        self.add_item(back_btn)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        val = int(interaction.data.get('custom_id').split("_")[1])
        config = load_config()
        config['message_xp'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь за сообщение даётся **{val}** XP",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=MsgXPView())
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="⚙️ Настройки",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=FullSettingsView())

class VoiceXPView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        current = load_config().get('voice_xp', 2)
        for val in [1, 2, 3, 4, 5, 8, 10, 15, 20]:
            btn = ui.Button(
                label=f"{val} XP",
                style=ButtonStyle.primary if val == current else ButtonStyle.secondary,
                row=0 if val <= 5 else 1,
                custom_id=f"voicexp_{val}"
            )
            btn.callback = self.callback
            self.add_item(btn)
        back_btn = ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back")
        back_btn.callback = self.back_callback
        self.add_item(back_btn)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        val = int(interaction.data.get('custom_id').split("_")[1])
        config = load_config()
        config['voice_xp'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь за минуту в голосовом даётся **{val}** XP",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=VoiceXPView())
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="⚙️ Настройки",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=FullSettingsView())

class IntervalView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        current = load_config().get('voice_interval', 60)
        for val in [15, 30, 45, 60, 90, 120, 180, 300]:
            btn = ui.Button(
                label=f"{val}с",
                style=ButtonStyle.primary if val == current else ButtonStyle.secondary,
                row=0 if val <= 60 else 1,
                custom_id=f"int_{val}"
            )
            btn.callback = self.callback
            self.add_item(btn)
        back_btn = ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back")
        back_btn.callback = self.back_callback
        self.add_item(back_btn)
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        val = int(interaction.data.get('custom_id').split("_")[1])
        config = load_config()
        config['voice_interval'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь проверка каждые **{val}** секунд",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=IntervalView())
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="⚙️ Настройки",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=FullSettingsView())

class ChannelModal(ui.Modal, title="📌 Канал оповещений"):
    channel_id = ui.TextInput(
        label="ID канала",
        placeholder="Введите ID...",
        required=False,
        style=discord.TextStyle.short
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if self.channel_id.value:
            try:
                channel_id = int(self.channel_id.value)
                channel = interaction.guild.get_channel(channel_id)
                if not channel:
                    await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
                    return
                config['level_up_channel'] = channel_id
                save_config(config)
                await interaction.response.send_message(f"✅ Канал установлен: {channel.mention}", ephemeral=True)
            except:
                await interaction.response.send_message("❌ Неверный ID!", ephemeral=True)
        else:
            config['level_up_channel'] = None
            save_config(config)
            await interaction.response.send_message("✅ Канал сброшен", ephemeral=True)

# =====================================================
#  ☁️  КОМАНДЫ WEBDAV
# =====================================================

@bot.tree.command(name="webdav", description="☁️ Проверить подключение к WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    success, message = test_webdav_connection()
    
    if success:
        embed = discord.Embed(
            title="☁️ WebDAV подключён!",
            description=f"Сервер: {WEBDAV_URL}",
            color=discord.Color.green()
        )
        try:
            client = get_webdav_client()
            if client:
                files = client.list()
                if files:
                    embed.add_field(
                        name="📁 Файлы на сервере",
                        value="\n".join(files[:10]) if files else "Папка пуста",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📁 Файлы на сервере",
                        value="Папка пуста",
                        inline=False
                    )
        except Exception as e:
            embed.add_field(
                name="⚠️ Ошибка получения списка",
                value=str(e),
                inline=False
            )
    else:
        embed = discord.Embed(
            title="❌ WebDAV не подключён!",
            description=message,
            color=discord.Color.red()
        )
        embed.add_field(
            name="💡 Решение",
            value="Проверьте:\n1. Логин и пароль\n2. URL сервера\n3. Доступность сервера",
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="webdav_test", description="🧪 Тест WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav_test(interaction: discord.Interaction):
    """Упрощённая проверка WebDAV"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
            await interaction.followup.send(
                "❌ WebDAV не настроен!\n"
                "Установите переменные:\n"
                "`WEBDAV_LOGIN` и `WEBDAV_PASSWORD`",
                ephemeral=True
            )
            return
        
        client = get_webdav_client()
        if not client:
            await interaction.followup.send("❌ Не удалось создать клиент WebDAV", ephemeral=True)
            return
        
        try:
            files = client.list()
            embed = discord.Embed(
                title="✅ WebDAV работает!",
                description=f"Найдено файлов: {len(files)}",
                color=discord.Color.green()
            )
            if files:
                embed.add_field(
                    name="📁 Файлы",
                    value="\n".join(files[:10]),
                    inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ошибка при получении списка файлов:\n```\n{str(e)}\n```",
                ephemeral=True
            )
            
    except Exception as e:
        await interaction.followup.send(
            f"❌ Критическая ошибка:\n```\n{str(e)}\n```",
            ephemeral=True
        )

@bot.tree.command(name="webdav_files", description="📁 Показать файлы на WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav_files(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        await interaction.followup.send("❌ WebDAV не настроен!", ephemeral=True)
        return
    
    try:
        client = get_webdav_client()
        if not client:
            await interaction.followup.send("❌ Не удалось подключиться к WebDAV", ephemeral=True)
            return
        
        files = client.list()
        
        embed = discord.Embed(
            title="📁 Файлы на WebDAV",
            description=f"Сервер: {WEBDAV_URL}",
            color=discord.Color.blue()
        )
        
        if files:
            required_files = ["level_data.json", "voice_time.json", "user_profiles.json", "level_config.json"]
            status = []
            for f in required_files:
                if f in files:
                    status.append(f"✅ {f}")
                else:
                    status.append(f"❌ {f}")
            
            embed.add_field(
                name="📋 Статус файлов",
                value="\n".join(status),
                inline=False
            )
            
            embed.add_field(
                name="📁 Все файлы",
                value="\n".join(files[:15]) if files else "Папка пуста",
                inline=False
            )
        else:
            embed.add_field(
                name="📁 Файлы",
                value="Папка пуста",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

@bot.tree.command(name="webdav_sync", description="🔄 Синхронизировать данные с WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav_sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        await interaction.followup.send("❌ WebDAV не настроен!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🔄 Синхронизация с WebDAV",
        color=discord.Color.blue()
    )
    
    try:
        data = download_from_webdav("level_data.json")
        if data:
            save_level_data(data)
            embed.add_field("✅ level_data.json", "Синхронизирован", inline=False)
        else:
            data = load_level_data()
            upload_to_webdav("level_data.json", data)
            embed.add_field("📤 level_data.json", "Загружен на WebDAV", inline=False)
        
        voice = download_from_webdav("voice_time.json")
        if voice:
            save_voice_time(voice)
            embed.add_field("✅ voice_time.json", "Синхронизирован", inline=False)
        else:
            voice = load_voice_time()
            upload_to_webdav("voice_time.json", voice)
            embed.add_field("📤 voice_time.json", "Загружен на WebDAV", inline=False)
        
        profiles = download_from_webdav("user_profiles.json")
        if profiles:
            save_profiles(profiles)
            embed.add_field("✅ user_profiles.json", "Синхронизирован", inline=False)
        else:
            profiles = load_profiles()
            upload_to_webdav("user_profiles.json", profiles)
            embed.add_field("📤 user_profiles.json", "Загружен на WebDAV", inline=False)
        
        config = download_from_webdav("level_config.json")
        if config:
            save_config(config)
            embed.add_field("✅ level_config.json", "Синхронизирован", inline=False)
        else:
            config = load_config()
            upload_to_webdav("level_config.json", config)
            embed.add_field("📤 level_config.json", "Загружен на WebDAV", inline=False)
        
        embed.color = discord.Color.green()
        embed.description = "✅ Все данные синхронизированы!"
        
    except Exception as e:
        embed.color = discord.Color.red()
        embed.description = f"❌ Ошибка: {e}"
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# =====================================================
#  💾  УПРАВЛЕНИЕ АВТОСОХРАНЕНИЕМ
# =====================================================

@bot.tree.command(name="autosave", description="💾 Управление автосохранением (админ)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(action="start, stop, status")
async def slash_autosave(interaction: discord.Interaction, action: str):
    await interaction.response.defer(ephemeral=True)
    
    if action.lower() == "start":
        if auto_save.is_running():
            await interaction.followup.send("ℹ️ Автосохранение уже запущено!", ephemeral=True)
            return
        auto_save.start()
        auto_save_webdav.start()
        await interaction.followup.send("✅ Автосохранение запущено!", ephemeral=True)
    
    elif action.lower() == "stop":
        if not auto_save.is_running():
            await interaction.followup.send("ℹ️ Автосохранение уже остановлено!", ephemeral=True)
            return
        auto_save.cancel()
        auto_save_webdav.cancel()
        await interaction.followup.send("⏹️ Автосохранение остановлено!", ephemeral=True)
    
    elif action.lower() == "status":
        embed = discord.Embed(
            title="💾 Статус автосохранения",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📁 Локальное сохранение",
            value="✅ Запущено (каждую минуту)" if auto_save.is_running() else "❌ Остановлено",
            inline=True
        )
        embed.add_field(
            name="☁️ WebDAV сохранение",
            value="✅ Запущено (каждые 5 минут)" if auto_save_webdav.is_running() else "❌ Остановлено",
            inline=True
        )
        embed.add_field(
            name="💾 Последнее сохранение",
            value=datetime.now().strftime("%H:%M:%S"),
            inline=True
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    else:
        await interaction.followup.send("❌ Доступные действия: `start`, `stop`, `status`", ephemeral=True)

# =====================================================
#  🔄  СИНХРОНИЗАЦИЯ КОМАНД
# =====================================================

@bot.tree.command(name="sync_commands", description="🔄 Синхронизировать команды (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_sync_commands(interaction: discord.Interaction):
    """Принудительная синхронизация команд"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        await bot.tree.sync()
        
        guild = interaction.guild
        await bot.tree.sync(guild=guild)
        
        embed = discord.Embed(
            title="✅ Команды синхронизированы!",
            description=f"Команды обновлены для сервера {guild.name}",
            color=discord.Color.green()
        )
        
        commands_list = [cmd.name for cmd in bot.tree.get_commands()]
        embed.add_field(
            name="📋 Доступные команды",
            value="\n".join(commands_list[:15]),
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(
            f"❌ Ошибка синхронизации:\n```\n{str(e)}\n```",
            ephemeral=True
        )

# =====================================================
#  📝  КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ДАННЫМИ
# =====================================================

@bot.tree.command(name="level_reload", description="🔄 Перезагрузить данные (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_level_reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        config = load_config()
        data = load_level_data()
        
        embed = discord.Embed(
            title="🔄 Данные перезагружены!",
            description="✅ Конфиг и данные успешно перезагружены",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Конфиг",
            value=f"XP за сообщ: {config.get('message_xp', 1)}\nXP за голос: {config.get('voice_xp', 2)}\nИнтервал: {config.get('voice_interval', 60)} сек",
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

@bot.tree.command(name="level_save", description="💾 Сохранить данные (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_level_save(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        config = load_config()
        save_config(config)
        data = load_level_data()
        save_level_data(data)
        voice_data = load_voice_time()
        save_voice_time(voice_data)
        profiles = load_profiles()
        save_profiles(profiles)
        
        embed = discord.Embed(
            title="💾 Данные сохранены!",
            description="✅ Все данные сохранены локально и на WebDAV",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

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
#  🎵  XP ЗА ГОЛОСОВОЙ КАНАЛ
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
                                            description=f"{member.mention} достиг **{new_level}** уровня в голосовом канале!",
                                            color=discord.Color.gold()
                                        )
                                        await channel.send(embed=embed)
                                except:
                                    pass
                        
                        save_level_data(data)
                        
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
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
