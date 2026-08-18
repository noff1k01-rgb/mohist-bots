#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TOKEN = "ваш тикет бота в дискорд понели"

import discord
from discord.ext import commands
from discord import ui, ButtonStyle, SelectOption, app_commands
import yt_dlp
import asyncio
import os
import json
import random
import re
from datetime import datetime

# =====================================================
#  🎵  НАСТРОЙКИ YT-DLP
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
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['hls', 'dash'],
        }
    }
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

PLAYLISTS_FILE = "playlists.json"
LANG_FILE = "language.json"

def load_playlists():
    try:
        with open(PLAYLISTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_playlists(data):
    with open(PLAYLISTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_language():
    try:
        with open(LANG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_language(data):
    with open(LANG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_lang(guild_id):
    data = load_language()
    return data.get(str(guild_id), "ru")

def set_lang(guild_id, lang):
    data = load_language()
    data[str(guild_id)] = lang
    save_language(data)

# =====================================================
#  🌍  ПЕРЕВОДЫ
# =====================================================

TEXTS = {
    "ru": {
        "now_playing": "🎵 Сейчас играет",
        "artist": "👤 Исполнитель",
        "duration": "⏱️ Длительность",
        "in_queue": "📋 В очереди",
        "queue_empty": "📭 Очередь пуста",
        "nothing_playing": "❌ Ничего не играет",
        "not_in_voice": "❌ Вы не в голосовом канале!",
        "playlist_added": "📋 Плейлист добавлен в очередь",
        "tracks": "треков",
        "added_to_queue": "🎵 Добавлено в очередь",
        "loop_mode": "🔁 Режим повтора",
        "loop_off": "Выкл",
        "loop_track": "Трек",
        "loop_playlist": "Плейлист",
        "paused": "⏸️ Пауза!",
        "resumed": "▶️ Возобновлено!",
        "skipped": "⏭️ Пропущено!",
        "stopped": "⏹️ Остановлено!",
        "cleared": "🗑️ Очищено {count} треков!",
        "shuffled": "🔀 Очередь перемешана!",
        "volume": "🔊 Громкость: {level}%",
        "menu_closed": "✅ Меню закрыто",
        "queue": "📋 Очередь",
        "playlists": "📁 Плейлисты",
        "no_playlists": "📭 У вас нет плейлистов!",
        "playlist_created": "✅ Плейлист **{name}** создан!",
        "playlist_deleted": "🗑️ Плейлист **{name}** удалён!",
        "playlist_exists": "❌ Плейлист **{name}** уже существует!",
        "playlist_not_found": "❌ Плейлист **{name}** не найден!",
        "playlist_empty": "📭 Плейлист **{name}** пуст!",
        "added_to_playlist": "✅ Добавлено в **{name}**: {track}",
        "removed_from_playlist": "🗑️ Удалён: **{title}**",
        "track_not_found": "❌ Трек с номером {num} не найден!",
        "specify_name": "❌ Укажите название: `/playlist create <название>`",
        "specify_name_play": "❌ Укажите название: `/playlist play <название>`",
        "specify_name_delete": "❌ Укажите название: `/playlist delete <название>`",
        "usage_add": "❌ Использование: `/playlist add <название> <трек>`",
        "usage_remove": "❌ Использование: `/playlist remove <название> <номер>`",
        "failed_find": "❌ Не удалось найти трек: {track}",
        "connection_error": "❌ Ошибка подключения: {error}",
        "not_found": "❌ Не удалось обработать: **{query}**",
        "nothing_found": "❌ Ничего не найдено: **{query}**",
        "track_added": "✅ Добавлено: **{title}**",
        "menu_updated": "🔄 Меню обновлено!",
        "playlist_added_queue": "📋 Плейлист добавлен в очередь",
        "track_added_queue": "🎵 Трек добавлен в очередь",
        "language_changed": "🌍 Язык изменён на **Русский**!",
        "language_select": "🌍 Выберите язык / Select language:",
        "select_track": "🎵 Выберите трек из очереди",
        "track_position": "Позиция {pos} из {total}",
        "no_queue": "📭 Очередь пуста",
    },
    "en": {
        "now_playing": "🎵 Now Playing",
        "artist": "👤 Artist",
        "duration": "⏱️ Duration",
        "in_queue": "📋 In queue",
        "queue_empty": "📭 Queue is empty",
        "nothing_playing": "❌ Nothing is playing",
        "not_in_voice": "❌ You are not in a voice channel!",
        "playlist_added": "📋 Playlist added to queue",
        "tracks": "tracks",
        "added_to_queue": "🎵 Added to queue",
        "loop_mode": "🔁 Loop mode",
        "loop_off": "Off",
        "loop_track": "Track",
        "loop_playlist": "Playlist",
        "paused": "⏸️ Paused!",
        "resumed": "▶️ Resumed!",
        "skipped": "⏭️ Skipped!",
        "stopped": "⏹️ Stopped!",
        "cleared": "🗑️ Cleared {count} tracks!",
        "shuffled": "🔀 Queue shuffled!",
        "volume": "🔊 Volume: {level}%",
        "menu_closed": "✅ Menu closed",
        "queue": "📋 Queue",
        "playlists": "📁 Playlists",
        "no_playlists": "📭 You have no playlists!",
        "playlist_created": "✅ Playlist **{name}** created!",
        "playlist_deleted": "🗑️ Playlist **{name}** deleted!",
        "playlist_exists": "❌ Playlist **{name}** already exists!",
        "playlist_not_found": "❌ Playlist **{name}** not found!",
        "playlist_empty": "📭 Playlist **{name}** is empty!",
        "added_to_playlist": "✅ Added to **{name}**: {track}",
        "removed_from_playlist": "🗑️ Removed: **{title}**",
        "track_not_found": "❌ Track number {num} not found!",
        "specify_name": "❌ Specify name: `/playlist create <name>`",
        "specify_name_play": "❌ Specify name: `/playlist play <name>`",
        "specify_name_delete": "❌ Specify name: `/playlist delete <name>`",
        "usage_add": "❌ Usage: `/playlist add <name> <track>`",
        "usage_remove": "❌ Usage: `/playlist remove <name> <number>`",
        "failed_find": "❌ Failed to find track: {track}",
        "connection_error": "❌ Connection error: {error}",
        "not_found": "❌ Failed to process: **{query}**",
        "nothing_found": "❌ Nothing found: **{query}**",
        "track_added": "✅ Added: **{title}**",
        "menu_updated": "🔄 Menu updated!",
        "playlist_added_queue": "📋 Playlist added to queue",
        "track_added_queue": "🎵 Track added to queue",
        "language_changed": "🌍 Language changed to **English**!",
        "language_select": "🌍 Select language / Выберите язык:",
        "select_track": "🎵 Select track from queue",
        "track_position": "Position {pos} of {total}",
        "no_queue": "📭 Queue is empty",
    }
}

def t(guild_id, key, **kwargs):
    lang = get_lang(guild_id)
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# =====================================================
#  🌍  ВЫБОР ЯЗЫКА
# =====================================================

class LanguageSelect(ui.Select):
    def __init__(self, guild_id):
        options = [
            SelectOption(label="🇷🇺 Русский", value="ru", description="Русский язык"),
            SelectOption(label="🇬🇧 English", value="en", description="English language"),
        ]
        super().__init__(placeholder="Выберите язык / Select language...", options=options, row=0)
        self.guild_id = guild_id
    
    async def callback(self, interaction: discord.Interaction):
        set_lang(self.guild_id, self.values[0])
        lang_text = "🇷🇺 Русский" if self.values[0] == "ru" else "🇬🇧 English"
        await interaction.response.send_message(
            f"🌍 Язык изменён на **{lang_text}**!\nLanguage changed to **{lang_text}**!",
            ephemeral=True
        )

class LanguageView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.add_item(LanguageSelect(guild_id))

# =====================================================
#  🎵  КНОПКИ УПРАВЛЕНИЯ (С ПОДПИСЯМИ)
# =====================================================

class MusicMenuView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.update_loop_button()
    
    def update_loop_button(self):
        if self.guild_id in players:
            mode = players[self.guild_id].loop_mode
            labels = {0: "🔁 Повтор: Выкл", 1: "🔂 Повтор: Трек", 2: "🔁 Повтор: Плейлист"}
            styles = {0: ButtonStyle.secondary, 1: ButtonStyle.success, 2: ButtonStyle.primary}
            for item in self.children[:]:
                if item.label and "Повтор" in item.label:
                    self.remove_item(item)
            self.loop_btn = ui.Button(label=labels.get(mode, "🔁 Повтор: Выкл"), style=styles.get(mode, ButtonStyle.secondary), row=1, custom_id="loop")
            self.loop_btn.callback = self.loop_callback
            self.add_item(self.loop_btn)
    
    @ui.button(label="⏸️ Пауза", style=ButtonStyle.secondary, row=0)
    async def pause_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.pause()
            await interaction.response.send_message(t(guild.id, "paused"), ephemeral=True)
        else:
            await interaction.response.send_message(t(guild.id, "nothing_playing"), ephemeral=True)
    
    @ui.button(label="▶️ Возобновить", style=ButtonStyle.success, row=0)
    async def resume_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_paused():
            guild.voice_client.resume()
            await interaction.response.send_message(t(guild.id, "resumed"), ephemeral=True)
        else:
            await interaction.response.send_message(t(guild.id, "nothing_playing"), ephemeral=True)
    
    @ui.button(label="⏭️ Пропустить", style=ButtonStyle.primary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        if guild and guild.voice_client and guild.voice_client.is_playing():
            guild.voice_client.stop()
            await interaction.response.send_message(t(guild.id, "skipped"), ephemeral=True)
        else:
            await interaction.response.send_message(t(guild.id, "nothing_playing"), ephemeral=True)
    
    @ui.button(label="⏹️ Остановить", style=ButtonStyle.danger, row=0)
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
            await interaction.response.send_message(t(guild_id, "stopped"), ephemeral=True)
        else:
            await interaction.response.send_message(t(guild_id, "nothing_playing"), ephemeral=True)
    
    async def loop_callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in players:
            players[guild_id] = MusicPlayer()
        players[guild_id].loop_mode = (players[guild_id].loop_mode + 1) % 3
        modes = {0: t(guild_id, "loop_off"), 1: t(guild_id, "loop_track"), 2: t(guild_id, "loop_playlist")}
        await interaction.response.send_message(
            f"{t(guild_id, 'loop_mode')}: {modes[players[guild_id].loop_mode]}",
            ephemeral=True
        )
        self.update_loop_button()
        await interaction.message.edit(view=self)
    
    @ui.button(label="📋 Очередь", style=ButtonStyle.secondary, row=1)
    async def queue_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild_id = interaction.guild.id
        queue = queues.get(guild_id, [])
        if not queue:
            await interaction.response.send_message(t(guild_id, "no_queue"), ephemeral=True)
            return
        
        # Создаём меню с выбором трека
        view = QueueSelectView(guild_id)
        embed = discord.Embed(
            title=t(guild_id, "select_track"),
            description=f"Всего {len(queue)} треков",
            color=discord.Color.blue()
        )
        for i, (title, _, duration) in enumerate(queue[:10], 1):
            embed.add_field(
                name=f"{i}. {title[:50]}",
                value=f"⏱️ {format_duration(duration)}",
                inline=False
            )
        if len(queue) > 10:
            embed.set_footer(text=f"И ещё {len(queue)-10} треков...")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @ui.button(label="➕ Добавить трек", style=ButtonStyle.success, row=1)
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddTrackModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="📁 Плейлисты", style=ButtonStyle.primary, row=2)
    async def playlists_btn(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        playlists = load_playlists()
        if user_id not in playlists or not playlists[user_id]:
            await interaction.response.send_message(t(interaction.guild.id, "no_playlists"), ephemeral=True)
            return
        embed = discord.Embed(title=t(interaction.guild.id, "playlists"), color=discord.Color.blue())
        for pl_name, tracks in playlists[user_id].items():
            embed.add_field(name=f"📁 {pl_name}", value=f"🎵 {len(tracks)} {t(interaction.guild.id, 'tracks')}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @ui.button(label="❌ Закрыть", style=ButtonStyle.danger, row=2)
    async def close_btn(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await interaction.message.delete()
            await interaction.response.send_message(t(interaction.guild.id, "menu_closed"), ephemeral=True)
        except:
            await interaction.response.send_message(t(interaction.guild.id, "menu_closed"), ephemeral=True)

# =====================================================
#  🎵  МЕНЮ ВЫБОРА ТРЕКА ИЗ ОЧЕРЕДИ
# =====================================================

class QueueSelectView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.page = 0
        self.update_buttons()
    
    def get_queue_page(self):
        queue = queues.get(self.guild_id, [])
        start = self.page * 10
        end = start + 10
        return queue[start:end], len(queue)
    
    def update_buttons(self):
        # Очищаем старые кнопки
        for item in self.children[:]:
            self.remove_item(item)
        
        queue, total = self.get_queue_page()
        
        if queue:
            options = []
            for i, (title, _, duration) in enumerate(queue, start=self.page * 10 + 1):
                dur = format_duration(duration)
                options.append(SelectOption(
                    label=f"{i}. {title[:45]}",
                    description=f"⏱️ {dur}",
                    value=str(i),
                    emoji="🎵"
                ))
            
            if options:
                self.select = ui.Select(
                    placeholder=f"Выберите трек ({self.page*10+1}-{min(self.page*10+10, total)} из {total})",
                    options=options[:10],
                    row=0
                )
                self.select.callback = self.select_callback
                self.add_item(self.select)
        
        # Навигация
        if self.page > 0:
            prev = ui.Button(label="⬅️ Назад", style=ButtonStyle.secondary, row=1, custom_id="prev")
            prev.callback = self.prev_callback
            self.add_item(prev)
        
        if total > (self.page + 1) * 10:
            next_btn = ui.Button(label="➡️ Вперёд", style=ButtonStyle.secondary, row=1, custom_id="next")
            next_btn.callback = self.next_callback
            self.add_item(next_btn)
        
        close = ui.Button(label="❌ Закрыть", style=ButtonStyle.danger, row=1, custom_id="close")
        close.callback = self.close_callback
        self.add_item(close)
    
    async def select_callback(self, interaction: discord.Interaction):
        try:
            selected = int(self.select.values[0]) - 1
            queue = queues.get(self.guild_id, [])
            if 0 <= selected < len(queue):
                title, url, duration = queue[selected]
                
                # Проверяем, есть ли голосовой канал
                if not interaction.user.voice:
                    await interaction.response.send_message(t(self.guild_id, "not_in_voice"), ephemeral=True)
                    return
                
                await interaction.response.defer(ephemeral=True)
                
                # Удаляем всё из очереди до выбранного трека
                new_queue = queue[selected:]
                queues[self.guild_id] = new_queue
                
                # Если сейчас что-то играет, останавливаем
                voice_client = interaction.guild.voice_client
                if voice_client and voice_client.is_playing():
                    voice_client.stop()
                    await asyncio.sleep(1)
                
                # Подключаемся к голосовому каналу
                if not voice_client:
                    try:
                        await interaction.user.voice.channel.connect()
                    except Exception as e:
                        await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)
                        return
                
                # Начинаем воспроизведение
                await play_next(interaction.guild)
                
                await interaction.followup.send(f"✅ Воспроизводится: **{title}**", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {t(self.guild_id, 'track_not_found', num=selected+1)}", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Ошибка!", ephemeral=True)
    
    async def prev_callback(self, interaction: discord.Interaction):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(view=self)
    
    async def next_callback(self, interaction: discord.Interaction):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(view=self)
    
    async def close_callback(self, interaction: discord.Interaction):
        try:
            await interaction.message.delete()
            await interaction.response.send_message("✅ Очередь закрыта", ephemeral=True)
        except:
            await interaction.response.send_message("✅ Очередь закрыта", ephemeral=True)

# =====================================================
#  ➕  МОДАЛЬНОЕ ОКНО ДЛЯ ДОБАВЛЕНИЯ ТРЕКА
# =====================================================

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
                await interaction.followup.send(t(guild_id, "not_found", query=query), ephemeral=True)
                return
        else:
            result = await search_youtube(query)
            if not result:
                await interaction.followup.send(t(guild_id, "nothing_found", query=query), ephemeral=True)
                return
        if result.get('type') == 'playlist':
            tracks = result['tracks']
            for track in tracks:
                queues[guild_id].append((track['title'], track['url'], track.get('duration', 0)))
            await interaction.followup.send(f"✅ {t(guild_id, 'playlist_added')}: {len(tracks)} {t(guild_id, 'tracks')}", ephemeral=True)
        else:
            title = result.get('title', 'Неизвестно')
            url = result.get('url', query)
            duration = result.get('duration', 0)
            queues[guild_id].append((title, url, duration))
            await interaction.followup.send(f"✅ {t(guild_id, 'track_added', title=title)}", ephemeral=True)
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                try:
                    await interaction.user.voice.channel.connect()
                except:
                    pass
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)

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
#  🔍  ОБРАБОТКА ТРЕКОВ
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
        title=t(guild_id, "now_playing"),
        description=f"**{title}**",
        color=discord.Color.blue()
    )
    if uploader and uploader != "Неизвестно":
        embed.add_field(name=t(guild_id, "artist"), value=uploader, inline=True)
    if duration:
        embed.add_field(name=t(guild_id, "duration"), value=format_duration(duration), inline=True)
    queue = queues.get(guild_id, [])
    if queue:
        embed.add_field(name=t(guild_id, "in_queue"), value=f"{len(queue)} {t(guild_id, 'tracks')}", inline=True)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text="🎵 Управляйте кнопками ниже" if get_lang(guild_id) == "ru" else "🎵 Use buttons below")
    
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
        description=f"Всего: {len(tracks)} {t(guild_id, 'tracks')}",
        color=discord.Color.blue()
    )
    for i, track in enumerate(tracks[:10], 1):
        embed.add_field(
            name=f"{i}. {track['title'][:50]}",
            value=f"⏱️ {format_duration(track.get('duration', 0))}",
            inline=False
        )
    if len(tracks) > 10:
        embed.set_footer(text=f"И ещё {len(tracks)-10} треков..." if get_lang(guild_id) == "ru" else f"And {len(tracks)-10} more...")
    
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

@bot.tree.command(name="language", description="🌍 Выбрать язык / Select language")
async def slash_language(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌍 Выберите язык / Select language",
        description="Нажмите на кнопку ниже / Click the button below",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=LanguageView(interaction.guild.id))

@bot.tree.command(name="play", description="🎵 Воспроизвести трек или плейлист")
@app_commands.describe(query="Название трека или ссылка YouTube")
async def slash_play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if not interaction.user.voice:
        await interaction.followup.send(t(guild_id, "not_in_voice"))
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
            await interaction.followup.send(t(guild_id, "not_found", query=query))
            return
    else:
        result = await search_youtube(query)
        if not result:
            await interaction.followup.send(t(guild_id, "nothing_found", query=query))
            return
    
    if result.get('type') == 'playlist':
        tracks = result['tracks']
        for track in tracks:
            queues[guild_id].append((track['title'], track['url'], track.get('duration', 0)))
        
        embed = discord.Embed(
            title=t(guild_id, "playlist_added_queue"),
            description=f"**{result.get('name', 'Плейлист')}**",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        await show_playlist_menu(guild_id, result.get('name', 'Плейлист'), tracks)
        
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(t(guild_id, "connection_error", error=str(e)))
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
            title=t(guild_id, "track_added_queue"),
            description=f"**{title}**",
            color=discord.Color.green()
        )
        embed.add_field(name=t(guild_id, "duration"), value=format_duration(duration), inline=True)
        await interaction.followup.send(embed=embed)
        
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(t(guild_id, "connection_error", error=str(e)))
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
        await interaction.response.send_message(t(guild_id, "nothing_playing"), ephemeral=True)
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
        await interaction.response.send_message(t(guild_id, "skipped"))
    else:
        await interaction.response.send_message(t(guild_id, "nothing_playing"))

@bot.tree.command(name="pause", description="⏸️ Пауза")
async def slash_pause(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.response.send_message(t(guild_id, "paused"))
    else:
        await interaction.response.send_message(t(guild_id, "nothing_playing"))

@bot.tree.command(name="resume", description="▶️ Возобновить")
async def slash_resume(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.response.send_message(t(guild_id, "resumed"))
    else:
        await interaction.response.send_message(t(guild_id, "nothing_playing"))

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
        await interaction.response.send_message(t(guild_id, "stopped"))
    else:
        await interaction.response.send_message(t(guild_id, "nothing_playing"))

@bot.tree.command(name="queue", description="📋 Показать очередь")
async def slash_queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    queue = queues.get(guild_id, [])
    if not queue:
        await interaction.response.send_message(t(guild_id, "queue_empty"))
        return
    
    embed = discord.Embed(
        title=t(guild_id, "select_track"),
        description=f"Всего {len(queue)} треков",
        color=discord.Color.blue()
    )
    for i, (title, _, duration) in enumerate(queue[:10], 1):
        embed.add_field(
            name=f"{i}. {title[:50]}",
            value=f"⏱️ {format_duration(duration)}",
            inline=False
        )
    if len(queue) > 10:
        embed.set_footer(text=f"И ещё {len(queue)-10} треков...")
    
    view = QueueSelectView(guild_id)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="loop", description="🔁 Переключить повтор")
async def slash_loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in players:
        players[guild_id] = MusicPlayer()
    players[guild_id].loop_mode = (players[guild_id].loop_mode + 1) % 3
    modes = {0: t(guild_id, "loop_off"), 1: t(guild_id, "loop_track"), 2: t(guild_id, "loop_playlist")}
    await interaction.response.send_message(f"{t(guild_id, 'loop_mode')}: {modes[players[guild_id].loop_mode]}")

@bot.tree.command(name="volume", description="🔊 Громкость (1-100)")
@app_commands.describe(level="Громкость от 1 до 100")
async def slash_volume(interaction: discord.Interaction, level: int):
    guild_id = interaction.guild.id
    if 1 <= level <= 100:
        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            interaction.guild.voice_client.source.volume = level / 100
            await interaction.response.send_message(t(guild_id, "volume", level=level))
        else:
            await interaction.response.send_message(t(guild_id, "nothing_playing"))
    else:
        await interaction.response.send_message("❌ От 1 до 100!" if get_lang(guild_id) == "ru" else "❌ Must be 1-100!")

@bot.tree.command(name="clear", description="🗑️ Очистить очередь")
async def slash_clear(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queues:
        count = len(queues[guild_id])
        queues[guild_id] = []
        await interaction.response.send_message(t(guild_id, "cleared", count=count))
    else:
        await interaction.response.send_message(t(guild_id, "queue_empty"))

@bot.tree.command(name="shuffle", description="🔀 Перемешать очередь")
async def slash_shuffle(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queues and queues[guild_id]:
        random.shuffle(queues[guild_id])
        await interaction.response.send_message(t(guild_id, "shuffled"))
    else:
        await interaction.response.send_message(t(guild_id, "queue_empty"))

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
            await interaction.response.send_message(t(guild_id, "specify_name"))
            return
        if name in playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "playlist_exists", name=name))
            return
        playlists[user_id][name] = []
        save_playlists(playlists)
        await interaction.response.send_message(t(guild_id, "playlist_created", name=name))
    
    elif action == "add":
        if not name or not track:
            await interaction.response.send_message(t(guild_id, "usage_add"))
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "playlist_not_found", name=name))
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
                await interaction.followup.send(t(guild_id, "added_to_playlist", name=name, track=result['title']))
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
                await interaction.followup.send(t(guild_id, "added_to_playlist", name=name, track=track_data['title']))
                return
        await interaction.followup.send(t(guild_id, "failed_find", track=track))
    
    elif action == "list":
        if not playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "no_playlists"))
            return
        embed = discord.Embed(title=t(guild_id, "playlists"), color=discord.Color.blue())
        for pl_name, tracks in playlists[user_id].items():
            embed.add_field(name=f"📁 {pl_name}", value=f"🎵 {len(tracks)} {t(guild_id, 'tracks')}", inline=False)
        await interaction.response.send_message(embed=embed)
    
    elif action == "play":
        if not name:
            await interaction.response.send_message(t(guild_id, "specify_name_play"))
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "playlist_not_found", name=name))
            return
        if not playlists[user_id][name]:
            await interaction.response.send_message(t(guild_id, "playlist_empty", name=name))
            return
        if not interaction.user.voice:
            await interaction.response.send_message(t(guild_id, "not_in_voice"))
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
            title=t(guild_id, "playlist_added_queue"),
            description=f"**{name}**",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        await show_playlist_menu(guild_id, name, playlists[user_id][name])
        if not interaction.guild.voice_client:
            try:
                await channel.connect()
            except Exception as e:
                await interaction.followup.send(t(guild_id, "connection_error", error=str(e)))
                return
        if not currently_playing.get(guild_id):
            await play_next(interaction.guild)
    
    elif action == "delete":
        if not name:
            await interaction.response.send_message(t(guild_id, "specify_name_delete"))
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "playlist_not_found", name=name))
            return
        del playlists[user_id][name]
        save_playlists(playlists)
        await interaction.response.send_message(t(guild_id, "playlist_deleted", name=name))
    
    elif action == "remove":
        if not name or not track:
            await interaction.response.send_message(t(guild_id, "usage_remove"))
            return
        if name not in playlists[user_id]:
            await interaction.response.send_message(t(guild_id, "playlist_not_found", name=name))
            return
        try:
            index = int(track) - 1
            if 0 <= index < len(playlists[user_id][name]):
                removed = playlists[user_id][name].pop(index)
                save_playlists(playlists)
                await interaction.response.send_message(t(guild_id, "removed_from_playlist", title=removed['title']))
            else:
                await interaction.response.send_message(t(guild_id, "track_not_found", num=track))
        except ValueError:
            await interaction.response.send_message("❌ Укажите номер трека!" if get_lang(guild_id) == "ru" else "❌ Specify track number!")
    
    else:
        await interaction.response.send_message(
            "❌ Доступные действия: `create`, `add`, `list`, `play`, `delete`, `remove`" if get_lang(guild_id) == "ru" else
            "❌ Available actions: `create`, `add`, `list`, `play`, `delete`, `remove`"
        )

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
#  🚀  ЗАПУСК
# =====================================================

if __name__ == "__main__":
    try:
        print("🔄 Запуск Mohist_Music...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Неверный токен!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
