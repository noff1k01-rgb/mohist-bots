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
    print("⚠️ webdavclient3 не установлен!")

# =====================================================
#  ☁️  РАБОТА С WEBDAV
# =====================================================

def get_webdav_client():
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

def upload_to_webdav(filename, data):
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return False
    
    try:
        client = get_webdav_client()
        if not client:
            return False
        
        content = json.dumps(data, indent=4, ensure_ascii=False)
        try:
            client.download(filename)
            client.upload(filename, content.encode('utf-8'))
        except:
            client.upload(filename, content.encode('utf-8'))
        return True
    except Exception as e:
        print(f"❌ WebDAV ошибка {filename}: {e}")
        return False

def download_from_webdav(filename):
    if not WEBDAV_AVAILABLE or not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        return None
    
    try:
        client = get_webdav_client()
        if not client:
            return None
        content = client.download(filename)
        return json.loads(content.decode('utf-8'))
    except:
        return None

# =====================================================
#  🔄  KEEP-ALIVE
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "✅ Mohist_Level работает!"

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

def load_level_data():
    data = download_from_webdav("level_data.json")
    if data is not None:
        return data
    try:
        with open(LEVEL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_level_data(data):
    try:
        with open(LEVEL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    upload_to_webdav("level_data.json", data)

def load_voice_time():
    data = download_from_webdav("voice_time.json")
    if data is not None:
        return data
    try:
        with open(VOICE_TIME_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_voice_time(data):
    try:
        with open(VOICE_TIME_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    upload_to_webdav("voice_time.json", data)

def load_profiles():
    data = download_from_webdav("user_profiles.json")
    if data is not None:
        return data
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_profiles(data):
    try:
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    upload_to_webdav("user_profiles.json", data)

def load_config():
    data = download_from_webdav("level_config.json")
    if data is not None:
        return data
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
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
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    upload_to_webdav("level_config.json", data)

# =====================================================
#  📊  ФУНКЦИИ
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
#  💾  АВТОСОХРАНЕНИЕ
# =====================================================

@tasks.loop(minutes=1.0)
async def auto_save():
    try:
        save_config(load_config())
        save_level_data(load_level_data())
        save_voice_time(load_voice_time())
        save_profiles(load_profiles())
    except Exception as e:
        print(f"❌ Автосохранение: {e}")

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
    
    # Проверка WebDAV
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
    
    # СИНХРОНИЗАЦИЯ КОМАНД - ВАЖНО!
    try:
        await bot.tree.sync()
        print("✅ Слеш-команды синхронизированы глобально!")
        
        # Синхронизируем для каждого сервера
        for guild in bot.guilds:
            try:
                await bot.tree.sync(guild=guild)
                print(f"   ✅ Синхронизировано для {guild.name}")
            except Exception as e:
                print(f"   ❌ Ошибка синхронизации для {guild.name}: {e}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
    
    auto_save.start()
    print("💾 Автосохранение запущено!")

# =====================================================
#  🎯  КОМАНДЫ
# =====================================================

@bot.tree.command(name="ping", description="🏓 Проверить работу бота")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Понг! {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="profile", description="📊 Показать профиль")
@app_commands.describe(member="Участник (опционально)")
async def slash_profile(interaction: discord.Interaction, member: discord.Member = None):
    if not member:
        member = interaction.user
    
    data = load_level_data()
    user_id = str(member.id)
    guild_id = str(interaction.guild.id)
    
    profile = get_user_profile(member.id, interaction.guild.id)
    name = profile.get("name", member.display_name)
    
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
    
    embed = discord.Embed(
        title=f"📊 Профиль {member.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="📇 Имя", value=f"**{name}**", inline=True)
    embed.add_field(name="🎯 Уровень", value=f"**{level}**", inline=True)
    embed.add_field(name="⭐ XP", value=f"**{xp}** / {next_xp}", inline=True)
    
    bar = create_progress_bar(progress)
    embed.add_field(
        name="📊 Прогресс",
        value=f"{bar} **{progress:.1f}%**",
        inline=False
    )
    embed.add_field(name="🏆 Место", value=f"**#{rank if rank else '—'}**", inline=True)
    embed.add_field(name="🎤 Голосовое время", value=format_time(voice_time), inline=True)
    embed.add_field(name="💬 Сообщений", value=f"**{user_data.get('messages', 0)}**", inline=True)
    
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
        
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"🎯 Уровень {level} | ⭐ {xp} XP",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="webdav", description="☁️ Проверить WebDAV (админ)")
@app_commands.default_permissions(administrator=True)
async def slash_webdav(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not WEBDAV_LOGIN or not WEBDAV_PASSWORD:
        await interaction.followup.send("❌ WebDAV не настроен!", ephemeral=True)
        return
    
    try:
        client = get_webdav_client()
        if not client:
            await interaction.followup.send("❌ Не удалось подключиться!", ephemeral=True)
            return
        
        files = client.list()
        embed = discord.Embed(
            title="☁️ WebDAV работает!",
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
        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

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
