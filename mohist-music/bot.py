#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Токен не найден! Установите переменную окружения TOKEN")

import discord
from discord.ext import commands
from discord import ui, ButtonStyle, SelectOption, app_commands
import yt_dlp
import asyncio
import json
import random
import re
from datetime import datetime

# =====================================================
#  🔄  KEEP-ALIVE ДЛЯ RENDER
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "🎵 Mohist_Music работает!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()
print("✅ Keep-Alive запущен!")

# =====================================================
#  🎵  НАСТРОЙКИ YT-DLP (ПОЛНОСТЬЮ ОПТИМИЗИРОВАННЫЕ)
# =====================================================

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    # ✅ Cookies файл (создайте файл cookies.txt в этой же папке)
    'cookiefile': 'cookies.txt',
    # ✅ Правильные заголовки как у браузера
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
    },
    # ✅ Разные клиенты YouTube (mweb помогает обойти блокировку)
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb', 'android', 'web'],
            'skip': ['hls', 'dash'],
            'player_skip': ['configs'],
        }
    },
    # ✅ Задержки для обхода блокировки YouTube
    'sleep_interval': 10,
    'max_sleep_interval': 15,
    'sleep_interval_requests': 2,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# =====================================================
#  📁  РАБОТА С ПЛЕЙЛИСТАМИ
# =====================================================

PLAYLISTS_FILE = "playlists.json"

def load_playlists():
    try:
        with open(PLAYLISTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_playlists(data):
    with open(PLAYLISTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# =====================================================
#  🤖  БОТ
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

queues = {}
currently_playing = {}
players = {}
history = {}
now_playing_messages = {}
channel_map = {}

class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.is_playing = False
        self.loop_mode = 0
        self.current_url = None
        self.current_title = None
        self.current_thumbnail = None

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📡 Серверов: {len(bot.guilds)}')
    print('=' * 50)
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="🎵 YouTube | /play"
    ))
    try:
        await bot.tree.sync()
        print("✅ Слеш-команды синхронизированы!")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")

# =====================================================
#  🔍  ОБРАБОТКА ТРЕКОВ (С ЗАДЕРЖКАМИ)
# =====================================================

async def get_thumbnail(video_id):
    return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

async def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def process_youtube(query):
    """Обрабатывает URL с задержкой и cookies"""
    await asyncio.sleep(3)  # ✅ Задержка перед запросом
    try:
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(query, download=False)
        )
        if not data or not isinstance(data, dict):
            return None
        if 'entries' in data and data['entries']:
            tracks = []
            for entry in data['entries']:
                if entry and isinstance(entry, dict) and entry.get('title'):
                    video_id = await extract_video_id(entry.get('webpage_url', ''))
                    tracks.append({
                        'title': entry.get('title', 'Неизвестно'),
                        'url': entry.get('webpage_url') or entry.get('url'),
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Неизвестно'),
                        'video_id': video_id,
                        'thumbnail': await get_thumbnail(video_id) if video_id else None
                    })
            if tracks:
                return {'type': 'playlist', 'name': data.get('title', 'Плейлист'), 'tracks': tracks, 'count': len(tracks)}
            return None
        else:
            if isinstance(data, dict) and data.get('title'):
                video_id = await extract_video_id(data.get('webpage_url', ''))
                return {
                    'type': 'track',
                    'title': data.get('title', 'Неизвестно'),
                    'url': data.get('webpage_url') or data.get('url'),
                    'duration': data.get('duration', 0),
                    'uploader': data.get('uploader', 'Неизвестно'),
                    'video_id': video_id,
                    'thumbnail': await get_thumbnail(video_id) if video_id else None
                }
            return None
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return None

async def search_youtube(query):
    """Поиск трека с задержкой"""
    await asyncio.sleep(3)  # ✅ Задержка перед поиском
    try:
        search_query = f"ytsearch5:{query}"
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(search_query, download=False)
        )
        if not data or not isinstance(data, dict) or not data.get('entries'):
            return None
        tracks = []
        for entry in data['entries']:
            if entry and isinstance(entry, dict) and entry.get('title'):
                video_id = await extract_video_id(entry.get('webpage_url', ''))
                tracks.append({
                    'title': entry.get('title', 'Неизвестно'),
                    'url': entry.get('webpage_url') or entry.get('url'),
                    'duration': entry.get('duration', 0),
                    'uploader': entry.get('uploader', 'Неизвестно'),
                    'video_id': video_id,
                    'thumbnail': await get_thumbnail(video_id) if video_id else None
                })
        if tracks:
            return {'type': 'search', 'query': query, 'tracks': tracks}
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None

def format_duration(seconds):
    if not seconds:
        return "Неизвестно"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

# =====================================================
#  🎵  КЛАССЫ ДЛЯ МЕНЮ
# =====================================================

class MusicMenuView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.update_loop_button()
    
    def update_loop_button(self):
        if self.guild_id in players:
            mode = players[self.guild_id].loop_mode
            labels = {0: "🔁", 1: "🔂", 2: "🔁"}
            styles = {0: ButtonStyle.secondary, 1: ButtonStyle.success, 2: ButtonStyle.primary}
            for item in self.children[:]:
                if item.label and item.label in ["🔁", "🔂"]:
                    self.remove_item(item)
            self.loop_btn = ui.Button(label=labels.get(mode, "🔁"), style=styles.get(mode, ButtonStyle.secondary), row=1, custom_id="loop")
            self.loop_btn.callback = self.loop_callback
            self.add_item(self.loop_btn)
    
    @ui.button(label="⏸️", style=ButtonStyle.secondary, row=0)
    async def pause_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.pause()
            await interaction.response.send_message("⏸️ Пауза!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ничего не играет", ephemeral=True)
    
    @ui.button(label="▶️", style=ButtonStyle.success, row=0)
    async def resume_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_paused():
            guild.voice_client.resume()
            await interaction.response.send_message("▶️ Возобновлено!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ничего не на паузе", ephemeral=True)
    
    @ui.button(label="⏭️", style=ButtonStyle.primary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.stop()
            await interaction.response.send_message("⏭️ Пропущено!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ничего не играет", ephemeral=True)
    
    @ui.button(label="⏹️", style=ButtonStyle.danger, row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        guild_id = interaction.guild.id
        if guild and guild.voice_client:
            queues[guild_id] = []
            currently_playing[guild_id] = None
            if guild_id in players:
                players[guild_id].loop_mode = 0
            guild.voice_client.stop()
            await guild.voice_client.disconnect()
            if guild_id in now_playing_messages:
                try:
                    await now_playing_messages[guild_id].delete()
                except:
                    pass
                del now_playing_messages[guild_id]
            if guild_id in channel_map:
                del channel_map[guild_id]
            await interaction.response.send_message("⏹️ Остановлено!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Бот не в голосовом канале", ephemeral=True)
    
    async def loop_callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in players:
            players[guild_id] = MusicPlayer()
        players[guild_id].loop_mode = (players[guild_id].loop_mode + 1) % 3
        modes = {0: "Выкл", 1: "Трек", 2: "Плейлист"}
        await interaction.response.send_message(f"🔁 Режим повтора: {modes[players[guild_id].loop_mode]}", ephemeral=True)
        self.update_loop_button()
        await interaction.message.edit(view=self)
    
    @ui.button(label="📋 Очередь", style=ButtonStyle.secondary, row=1)
    async def queue_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild_id = interaction.guild.id
        queue = queues.get(guild_id, [])
        if not queue:
            await interaction.response.send_message("📭 Очередь пуста", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Очередь", color=discord.Color.blue())
        for i, (title, _, duration) in enumerate(queue[:15], 1):
            embed.add_field(name=f"{i}. {title[:50]}", value=f"⏱️ {format_duration(duration)}", inline=False)
        if len(queue) > 15:
            embed.set_footer(text=f"И ещё {len(queue)-15} треков...")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @ui.button(label="➕ Добавить", style=ButtonStyle.success, row=1)
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddTrackModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="📁 Плейлисты", style=ButtonStyle.primary, row=2)
    async def playlists_btn(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        playlists = load_playlists()
        if user_id not in playlists or not playlists[user_id]:
            await interaction.response.send_message(
                "📭 У вас нет плейлистов!\nСоздайте: `/playlist создать <название>`",
                ephemeral=True
            )
            return
        embed = discord.Embed(title="📁 Ваши плейлисты", color=discord.Color.blue())
        for pl_name, tracks in playlists[user_id].items():
            embed.add_field(name=f"📁 {pl_name}", value=f"🎵 {len(tracks)} треков", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @ui.button(label="❌ Закрыть", style=ButtonStyle.danger, row=2)
    async def close_btn(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await interaction.message.delete()
            await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)
        except:
            await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)

class AddTrackModal(ui.Modal, title="🎵 Добавить трек"):
    track = ui.TextInput(
        label="Название трека или ссылка YouTube",
        placeholder="Введите название или ссылку...",
        required=True,
        style=discord.TextStyle.short,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id
        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in players:
            players[guild_id] = MusicPlayer()
        query = self.track.value
        if 'http' in query:
            result = await process_youtube(query)
            if not result:
                await interaction.followup.send(f"❌ Не удалось обработать ссылку", ephemeral=True)
                return
        else:
            result = await search_youtube(query)
            if not result:
                await interaction.followup.send(f"❌ Ничего не найдено", ephemeral=True)
                return
        if result.get('type') == 'playlist':
            tracks = result['tracks']
            for track in tracks:
                queues[guild_id].append((track['title'], track['url'], track.get('duration', 0)))
            await interaction.followup.send(f"✅ Добавлено {len(tracks)} треков из плейлиста!", ephemeral=True)
        else:
            title = result.get('title', 'Неизвестно')
            url = result.get('url', query)
            duration = result.get('duration', 0)
            queues[guild_id].append((title, url, duration))
            await interaction.followup.send(f"✅ Добавлено: **{title}**", ephemeral=True)
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                try:
                    await interaction.user.voice.channel.connect()
                except:
                    pass
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)

# =====================================================
#  ▶️  ВОСПРОИЗВЕДЕНИЕ
# =====================================================

async def send_now_playing(guild_id, title, uploader, duration, thumbnail=None):
    channel = channel_map.get(guild_id)
    if not channel:
        for guild in bot.guilds:
            if guild.id == guild_id:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        channel_map[guild_id] = ch
                        break
                break
    
    if not channel:
        return None
    
    embed = discord.Embed(
        title="🎵 Сейчас играет",
        description=f"**{title}**",
        color=discord.Color.blue()
    )
    if uploader and uploader != "Неизвестно":
        embed.add_field(name="👤 Исполнитель", value=uploader, inline=True)
    if duration:
        embed.add_field(name="⏱️ Длительность", value=format_duration(duration), inline=True)
    queue = queues.get(guild_id, [])
    if queue:
        embed.add_field(name="📋 В очереди", value=f"{len(queue)} треков", inline=True)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text="🎵 Управляйте кнопками ниже")
    
    view = MusicMenuView(guild_id)
    
    if guild_id in now_playing_messages:
        try:
            await now_playing_messages[guild_id].delete()
        except:
            pass
        del now_playing_messages[guild_id]
    
    msg = await channel.send(embed=embed, view=view)
    now_playing_messages[guild_id] = msg
    return msg

async def show_playlist_menu(guild_id, playlist_name, tracks):
    channel = channel_map.get(guild_id)
    if not channel:
        for guild in bot.guilds:
            if guild.id == guild_id:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        channel_map[guild_id] = ch
                        break
                break
    
    if not channel:
        return None
    
    embed = discord.Embed(
        title=f"📁 {playlist_name}",
        description=f"Всего: {len(tracks)} треков",
        color=discord.Color.blue()
    )
    for i, track in enumerate(tracks[:10], 1):
        embed.add_field(
            name=f"{i}. {track['title'][:50]}",
            value=f"⏱️ {format_duration(track.get('duration', 0))}",
            inline=False
        )
    if len(tracks) > 10:
        embed.set_footer(text=f"И ещё {len(tracks)-10} треков...")
    
    if guild_id in now_playing_messages:
        try:
            await now_playing_messages[guild_id].delete()
        except:
            pass
        del now_playing_messages[guild_id]
    
    msg = await channel.send(embed=embed)
    now_playing_messages[guild_id] = msg
    return msg

async def play_next(guild):
    guild_id = guild.id
    
    queue = queues.get(guild_id, [])
    
    if guild_id in players and players[guild_id].loop_mode == 1 and currently_playing.get(guild_id):
        if guild_id in history and history[guild_id]:
            last_track = history[guild_id][-1]
            queue.insert(0, last_track)
    
    if not queue:
        currently_playing[guild_id] = None
        if guild_id in now_playing_messages:
            try:
                await now_playing_messages[guild_id].delete()
            except:
                pass
            del now_playing_messages[guild_id]
        if guild_id in channel_map:
            del channel_map[guild_id]
        return
    
    title, url, duration = queue.pop(0)
    currently_playing[guild_id] = title
    
    if guild_id not in history:
        history[guild_id] = []
    history[guild_id].append((title, url, duration))
    
    voice_client = guild.voice_client
    if not voice_client:
        return
    
    try:
        # ✅ Задержка перед получением аудио
        await asyncio.sleep(3)
        
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )
        if not data or not isinstance(data, dict):
            print(f"⚠️ Не удалось получить аудио для: {title}")
            await play_next(guild)
            return
        audio_url = data.get('url')
        if not audio_url:
            formats = data.get('formats', [])
            for fmt in formats:
                if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                    audio_url = fmt.get('url')
                    break
            if not audio_url:
                print(f"⚠️ Нет аудио URL для: {title}")
                await play_next(guild)
                return
        uploader = data.get('uploader', 'Неизвестно')
        video_id = await extract_video_id(url)
        thumbnail = await get_thumbnail(video_id) if video_id else None
        
        await send_now_playing(guild_id, title, uploader, duration, thumbnail)
        
        def after_playing(error):
            if error:
                print(f"❌ Ошибка воспроизведения: {error}")
            if guild_id in players and players[guild_id].loop_mode == 2:
                if guild_id in history and history[guild_id]:
                    last_track = history[guild_id][-1]
                    queues[guild_id].append(last_track)
            asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)
        
        voice_client.play(
            discord.FFmpegPCMAudio(audio_url, **ffmpeg_options),
            after=after_playing
        )
    except Exception as e:
        print(f"❌ Ошибка воспроизведения: {e}")
        await play_next(guild)

# =====================================================
#  🎯  КОМАНДЫ
# =====================================================

@bot.tree.command(name="play", description="🎵 Воспроизвести трек или плейлист")
@app_commands.describe(query="Название трека или ссылка YouTube")
async def slash_play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if not interaction.user.voice:
        await interaction.followup.send("❌ Вы не в голосовом канале!")
        return
    
    channel_map[guild_id] = interaction.channel
    
    channel = interaction.user.voice.channel
    if guild_id not in queues:
        queues[guild_id] = []
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    
    if 'http' in query:
        result = await process_youtube(query)
        if not result:
            await interaction.followup.send(f"❌ Не удалось обработать: **{query}**")
            return
    else:
        result = await search_youtube(query)
        if not result:
            await interaction.followup.send(f"❌ Ничего не найдено: **{query}**")
            return
    
    if result.get('type') == 'playlist':
        tracks = result['tracks']
        for track in tracks:
            queues[guild_id].append((track['title'], track['url'], track.get('duration', 0)))
        
        embed = discord.Embed(
            title="📋 Плейлист добавлен в очередь",
            description=f"**{result.get('name', 'Плейлист')}**",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        await show_playlist_menu(guild_id, result.get('name', 'Плейлист'), tracks)
        
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка подключения: {e}")
                return
        
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)
        
        await asyncio.sleep(2)
        current = currently_playing.get(guild_id)
        if current:
            await send_now_playing(guild_id, current, "Неизвестно", None, None)
    
    else:
        title = result.get('title', 'Неизвестно')
        url = result.get('url', query)
        duration = result.get('duration', 0)
        queues[guild_id].append((title, url, duration))
        
        embed = discord.Embed(
            title="🎵 Добавлено в очередь",
            description=f"**{title}**",
            color=discord.Color.green()
        )
        embed.add_field(name="⏱️ Длительность", value=format_duration(duration), inline=True)
        await interaction.followup.send(embed=embed)
        
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка подключения: {e}")
                return
        
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)
        
        await asyncio.sleep(2)
        current = currently_playing.get(guild_id)
        if current:
            await send_now_playing(guild_id, current, result.get('uploader', 'Неизвестно'), duration, result.get('thumbnail'))

@bot.tree.command(name="menu", description="🎮 Открыть меню управления")
async def slash_menu(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    current = currently_playing.get(guild_id)
    if not current:
        await interaction.response.send_message("❌ Ничего не играет!", ephemeral=True)
        return
    
    channel_map[guild_id] = interaction.channel
    await send_now_playing(guild_id, current, "Неизвестно", None, None)
    await interaction.response.send_message("🔄 Меню обновлено!", ephemeral=True)

# ----- УПРАВЛЕНИЕ -----
@bot.tree.command(name="skip", description="⏭️ Пропустить")
async def slash_skip(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ Пропущено!")
    else:
        await interaction.response.send_message("❌ Ничего не играет!")

@bot.tree.command(name="pause", description="⏸️ Пауза")
async def slash_pause(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.response.send_message("⏸️ Пауза!")
    else:
        await interaction.response.send_message("❌ Ничего не играет!")

@bot.tree.command(name="resume", description="▶️ Возобновить")
async def slash_resume(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.response.send_message("▶️ Возобновлено!")
    else:
        await interaction.response.send_message("❌ Ничего не на паузе!")

@bot.tree.command(name="stop", description="⏹️ Остановить")
async def slash_stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client:
        queues[guild_id] = []
        currently_playing[guild_id] = None
        if guild_id in players:
            players[guild_id].loop_mode = 0
        await interaction.guild.voice_client.disconnect()
        if guild_id in now_playing_messages:
            try:
                await now_playing_messages[guild_id].delete()
            except:
                pass
            del now_playing_messages[guild_id]
        if guild_id in channel_map:
            del channel_map[guild_id]
        await interaction.response.send_message("⏹️ Остановлено!")
    else:
        await interaction.response.send_message("❌ Бот не в голосовом канале!")

@bot.tree.command(name="queue", description="📋 Показать очередь")
async def slash_queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    queue = queues.get(guild_id, [])
    if not queue:
        await interaction.response.send_message("📭 Очередь пуста")
        return
    embed = discord.Embed(title="📋 Очередь", color=discord.Color.blue())
    for i, (title, _, duration) in enumerate(queue[:15], 1):
        embed.add_field(name=f"{i}. {title[:50]}", value=f"⏱️ {format_duration(duration)}", inline=False)
    if len(queue) > 15:
        embed.set_footer(text=f"И ещё {len(queue)-15} треков...")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="loop", description="🔁 Переключить повтор")
async def slash_loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    players[guild_id].loop_mode = (players[guild_id].loop_mode + 1) % 3
    modes = {0: "❌ Выкл", 1: "🔂 Трек", 2: "🔁 Плейлист"}
    await interaction.response.send_message(f"🔁 Режим повтора: {modes[players[guild_id].loop_mode]}")

@bot.tree.command(name="volume", description="🔊 Громкость (1-100)")
@app_commands.describe(level="Громкость от 1 до 100")
async def slash_volume(interaction: discord.Interaction, level: int):
    guild_id = interaction.guild.id
    if 1 <= level <= 100:
        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            interaction.guild.voice_client.source.volume = level / 100
            await interaction.response.send_message(f"🔊 Громкость: {level}%")
        else:
            await interaction.response.send_message("❌ Ничего не играет!")
    else:
        await interaction.response.send_message("❌ От 1 до 100!")

@bot.tree.command(name="clear", description="🗑️ Очистить очередь")
async def slash_clear(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queues:
        count = len(queues[guild_id])
        queues[guild_id] = []
        await interaction.response.send_message(f"🗑️ Очищено {count} треков!")
    else:
        await interaction.response.send_message("📭 Очередь пуста")

@bot.tree.command(name="shuffle", description="🔀 Перемешать очередь")
async def slash_shuffle(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queues and queues[guild_id]:
        random.shuffle(queues[guild_id])
        await interaction.response.send_message("🔀 Очередь перемешана!")
    else:
        await interaction.response.send_message("📭 Очередь пуста")

# ----- ПЛЕЙЛИСТЫ -----
@bot.tree.command(name="playlist", description="📋 Управление плейлистами")
@app_commands.describe(
    action="Действие: create, add, list, play, delete, remove",
    name="Название плейлиста",
    track="Название трека или ссылка"
)
async def slash_playlist(interaction: discord.Interaction, action: str, name: str = None, track: str = None):
    guild_id = interaction.guild.id
    user_id = str(interaction.user.id)
    playlists = load_playlists()
    if user_id not in playlists:
        playlists[user_id] = {}
    
    if action == "create":
        if not name:
            await interaction.response.send_message("❌ Укажите название: `/playlist create <название>`")
            return
        if name in playlists[user_id]:
            await interaction.response.send_message(f"❌ Плейлист **{name}** уже существует!")
            return
        playlists[user_id][name] = []
        save_playlists(playlists)
        await interaction.response.send_message(f"✅ Плейлист **{name}** создан!")
    
    elif action == "add":
        if not name or not track:
            await interaction.response.send_message("❌ Использование: `/playlist add <название> <трек>`")
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(f"❌ Плейлист **{name}** не найден!")
            return
        await interaction.response.defer()
        if 'http' in track:
            result = await process_youtube(track)
            if result and result.get('type') == 'track':
                playlists[user_id][name].append({
                    'title': result['title'],
                    'url': result['url'],
                    'duration': result.get('duration', 0)
                })
                save_playlists(playlists)
                await interaction.followup.send(f"✅ Добавлено в **{name}**: {result['title']}")
                return
        else:
            result = await search_youtube(track)
            if result and result.get('tracks'):
                track_data = result['tracks'][0]
                playlists[user_id][name].append({
                    'title': track_data['title'],
                    'url': track_data['url'],
                    'duration': track_data.get('duration', 0)
                })
                save_playlists(playlists)
                await interaction.followup.send(f"✅ Добавлено в **{name}**: {track_data['title']}")
                return
        await interaction.followup.send(f"❌ Не удалось найти трек: {track}")
    
    elif action == "list":
        if not playlists[user_id]:
            await interaction.response.send_message("📭 У вас нет плейлистов.")
            return
        embed = discord.Embed(title="📁 Ваши плейлисты", color=discord.Color.blue())
        for pl_name, tracks in playlists[user_id].items():
            embed.add_field(name=f"📁 {pl_name}", value=f"🎵 {len(tracks)} треков", inline=False)
        await interaction.response.send_message(embed=embed)
    
    elif action == "play":
        if not name:
            await interaction.response.send_message("❌ Укажите название: `/playlist play <название>`")
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(f"❌ Плейлист **{name}** не найден!")
            return
        if not playlists[user_id][name]:
            await interaction.response.send_message(f"📭 Плейлист **{name}** пуст!")
            return
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Вы не в голосовом канале!")
            return
        await interaction.response.defer()
        
        channel_map[guild_id] = interaction.channel
        
        channel = interaction.user.voice.channel
        if guild_id not in queues:
            queues[guild_id] = []
        if guild_id not in players:
            players[guild_id] = MusicPlayer()
        for track in playlists[user_id][name]:
            queues[guild_id].append((track['title'], track['url'], track.get('duration', 0)))
        embed = discord.Embed(
            title="📋 Плейлист добавлен в очередь",
            description=f"**{name}**",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        await show_playlist_menu(guild_id, name, playlists[user_id][name])
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка подключения: {e}")
                return
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)
    
    elif action == "delete":
        if not name:
            await interaction.response.send_message("❌ Укажите название: `/playlist delete <название>`")
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(f"❌ Плейлист **{name}** не найден!")
            return
        del playlists[user_id][name]
        save_playlists(playlists)
        await interaction.response.send_message(f"🗑️ Плейлист **{name}** удалён!")
    
    elif action == "remove":
        if not name or not track:
            await interaction.response.send_message("❌ Использование: `/playlist remove <название> <номер>`")
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(f"❌ Плейлист **{name}** не найден!")
            return
        try:
            index = int(track) - 1
            if 0 <= index < len(playlists[user_id][name]):
                removed = playlists[user_id][name].pop(index)
                save_playlists(playlists)
                await interaction.response.send_message(f"🗑️ Удалён: **{removed['title']}**")
            else:
                await interaction.response.send_message(f"❌ Трек с номером {track} не найден!")
        except ValueError:
            await interaction.response.send_message("❌ Укажите номер трека!")
    
    else:
        await interaction.response.send_message(
            "❌ Доступные действия: `create`, `add`, `list`, `play`, `delete`, `remove`"
        )

# =====================================================
#  🚀  ЗАПУСК
# =====================================================

async def main():
    async with bot:
        print("🔄 Запуск Mohist_Music...")
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
