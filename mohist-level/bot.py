#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TOKEN = "ваш тикет бота в дискорд понели"

import discord
from discord.ext import commands
from discord import ui, ButtonStyle, SelectOption, app_commands
import json
import asyncio
import math
from datetime import datetime, timedelta

# =====================================================
#  📁  РАБОТА С ДАННЫМИ
# =====================================================

LEVEL_FILE = "level_data.json"
CONFIG_FILE = "level_config.json"
VOICE_TIME_FILE = "voice_time.json"
PROFILE_FILE = "user_profiles.json"

def load_level_data():
    try:
        with open(LEVEL_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_level_data(data):
    with open(LEVEL_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_voice_time():
    try:
        with open(VOICE_TIME_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_voice_time(data):
    with open(VOICE_TIME_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_profiles():
    try:
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_profiles(data):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

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

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "message_xp": 1,
            "voice_xp": 2,
            "voice_interval": 60,
            "level_up_message": True,
            "level_up_channel": None,
            "roles": {}
        }

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours} дн {hours} ч {minutes} мин {secs} сек" if hours > 24 else f"{hours} ч {minutes} мин {secs} сек"
    elif minutes > 0:
        return f"{minutes} мин {secs} сек"
    else:
        return f"{secs} сек"

def create_progress_bar(progress, length=15):
    filled = int(progress / 100 * length)
    empty = length - filled
    return f"`{'█' * filled}{'░' * empty}`"

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
    progress = (xp - current_level_xp) / (next_level_xp - current_level_xp) * 100
    return min(progress, 100)

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
#  🎯  КРАСИВЫЙ ПРОФИЛЬ
# =====================================================

@bot.tree.command(name="profile", description="📊 Показать красивый профиль")
@app_commands.describe(member="Участник (опционально)")
async def slash_profile(interaction: discord.Interaction, member: discord.Member = None):
    if not member:
        member = interaction.user
    
    data = load_level_data()
    voice_data = load_voice_time()
    user_id = str(member.id)
    guild_id = str(interaction.guild.id)
    
    profile = get_user_profile(member.id, interaction.guild.id)
    name = profile.get("name", member.display_name)
    age = profile.get("age", "Не указан")
    gender = profile.get("gender", "Не указан")
    bio = profile.get("bio", "Не указана")
    
    if guild_id not in data or user_id not in data[guild_id]:
        data[guild_id] = data.get(guild_id, {})
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
    embed.add_field(name="💬 Активность", value=f"за всё время было отправлено **{messages_count}** сообщений", inline=False)
    embed.add_field(name="🎤 Голосовая активность", value=f"**{format_time(voice_time)}**", inline=False)
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

# =====================================================
#  🏆  ТОП И РЕЙТИНГ
# =====================================================

@bot.tree.command(name="level", description="🎯 Открыть меню")
async def slash_level(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎯 Система уровней",
        description="💬 За сообщения + 🎤 За голосовой канал",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Команды",
        value="`/level` - Меню\n`/profile` - Красивый профиль\n`/top` - Топ\n`/rank` - Рейтинг\n`/settings` - Настройки (админ)",
        inline=False
    )
    embed.set_footer(text="💡 Будьте активны!")
    await interaction.response.send_message(embed=embed, view=LevelMainMenu())

class LevelMainMenu(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
    
    @ui.button(label="📊 Профиль", style=ButtonStyle.primary, row=0)
    async def profile(self, interaction: discord.Interaction, button: ui.Button):
        await slash_profile.callback(interaction)
    
    @ui.button(label="🏆 Топ", style=ButtonStyle.primary, row=0)
    async def top(self, interaction: discord.Interaction, button: ui.Button):
        await slash_top(interaction)
    
    @ui.button(label="⚙️ Настройки", style=ButtonStyle.secondary, row=1)
    async def settings(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return
        await slash_settings.callback(interaction)

@bot.tree.command(name="top", description="🏆 Топ пользователей")
async def slash_top(interaction: discord.Interaction):
    data = load_level_data()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in data:
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
              f"⏱️ Интервал: **{config.get('voice_interval', 60)}** сек",
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
        
        self.add_item(ui.Button(
            label=f"💬 XP за сообщ: {config.get('message_xp', 1)}",
            style=ButtonStyle.primary,
            row=0,
            custom_id="msg_xp"
        ))
        self.add_item(ui.Button(
            label=f"🎵 XP за голос: {config.get('voice_xp', 2)}",
            style=ButtonStyle.primary,
            row=0,
            custom_id="voice_xp"
        ))
        self.add_item(ui.Button(
            label=f"⏱️ Интервал: {config.get('voice_interval', 60)}с",
            style=ButtonStyle.primary,
            row=1,
            custom_id="interval_settings"
        ))
        
        status = "✅ Вкл" if config.get('level_up_message', True) else "❌ Выкл"
        self.add_item(ui.Button(
            label=f"📢 Оповещения: {status}",
            style=ButtonStyle.success if config.get('level_up_message', True) else ButtonStyle.danger,
            row=1,
            custom_id="notify_settings"
        ))
        self.add_item(ui.Button(
            label="📌 Канал оповещений",
            style=ButtonStyle.secondary,
            row=2,
            custom_id="channel_settings"
        ))
        self.add_item(ui.Button(
            label="📊 Статистика",
            style=ButtonStyle.secondary,
            row=2,
            custom_id="stats_settings"
        ))
        self.add_item(ui.Button(
            label="🗑️ Сбросить всё",
            style=ButtonStyle.danger,
            row=3,
            custom_id="reset_settings"
        ))
        self.add_item(ui.Button(
            label="❌ Закрыть",
            style=ButtonStyle.danger,
            row=3,
            custom_id="close_settings"
        ))
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id')
        
        if custom_id == "msg_xp":
            await self.msg_xp_menu(interaction)
        elif custom_id == "voice_xp":
            await self.voice_xp_menu(interaction)
        elif custom_id == "interval_settings":
            await self.interval_menu(interaction)
        elif custom_id == "notify_settings":
            await self.toggle_notify(interaction)
        elif custom_id == "channel_settings":
            await self.set_channel(interaction)
        elif custom_id == "stats_settings":
            await self.show_stats(interaction)
        elif custom_id == "reset_settings":
            await self.reset_data(interaction)
        elif custom_id == "close_settings":
            await interaction.message.delete()
            await interaction.response.send_message("✅ Меню закрыто", ephemeral=True)
    
    async def msg_xp_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = MsgXPView()
        embed = discord.Embed(
            title="💬 XP за сообщения",
            description="Выберите XP за одно сообщение",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def voice_xp_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = VoiceXPView()
        embed = discord.Embed(
            title="🎵 XP за голосовой канал",
            description="Выберите XP за минуту в голосовом",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def interval_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = IntervalView()
        embed = discord.Embed(
            title="⏱️ Интервал проверки",
            description="Выберите интервал в секундах",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view)
    
    async def toggle_notify(self, interaction: discord.Interaction):
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
    
    async def set_channel(self, interaction: discord.Interaction):
        modal = ChannelModal()
        await interaction.response.send_modal(modal)
    
    async def show_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = load_level_data()
        guild_id = str(interaction.guild.id)
        total_users = len(data.get(guild_id, {}))
        total_xp = sum(u.get("xp", 0) for u in data.get(guild_id, {}).values())
        max_level = max((u.get("level", 0) for u in data.get(guild_id, {}).values()), default=0)
        embed = discord.Embed(
            title="📊 Статистика сервера",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Участников", value=str(total_users), inline=True)
        embed.add_field(name="⭐ Всего XP", value=str(total_xp), inline=True)
        embed.add_field(name="🎯 Макс. уровень", value=str(max_level), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def reset_data(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Подтверждение",
            description="Вы уверены, что хотите сбросить ВСЕ данные?",
            color=discord.Color.red()
        )
        view = ConfirmResetView()
        await interaction.response.edit_message(embed=embed, view=view)

class MsgXPView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for val in [1, 2, 3, 4, 5, 8, 10]:
            self.add_item(ui.Button(
                label=f"{val} XP",
                style=ButtonStyle.primary if val == load_config().get('message_xp', 1) else ButtonStyle.secondary,
                row=0 if val <= 5 else 1,
                custom_id=f"msgxp_{val}"
            ))
        self.add_item(ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back"))
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id')
        if custom_id == "back":
            await interaction.response.defer()
            await interaction.followup.send(embed=discord.Embed(title="⚙️ Настройки", color=discord.Color.blue()), view=FullSettingsView())
            return
        val = int(custom_id.split("_")[1])
        config = load_config()
        config['message_xp'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь за сообщение даётся **{val}** XP",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=MsgXPView())

class VoiceXPView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for val in [1, 2, 3, 4, 5, 8, 10, 15, 20]:
            self.add_item(ui.Button(
                label=f"{val} XP",
                style=ButtonStyle.primary if val == load_config().get('voice_xp', 2) else ButtonStyle.secondary,
                row=0 if val <= 5 else 1,
                custom_id=f"voicexp_{val}"
            ))
        self.add_item(ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back"))
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id')
        if custom_id == "back":
            await interaction.response.defer()
            await interaction.followup.send(embed=discord.Embed(title="⚙️ Настройки", color=discord.Color.blue()), view=FullSettingsView())
            return
        val = int(custom_id.split("_")[1])
        config = load_config()
        config['voice_xp'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь за минуту в голосовом даётся **{val}** XP",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=VoiceXPView())

class IntervalView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for val in [15, 30, 45, 60, 90, 120, 180, 300]:
            self.add_item(ui.Button(
                label=f"{val}с",
                style=ButtonStyle.primary if val == load_config().get('voice_interval', 60) else ButtonStyle.secondary,
                row=0 if val <= 60 else 1,
                custom_id=f"int_{val}"
            ))
        self.add_item(ui.Button(label="🔙 Назад", style=ButtonStyle.danger, row=2, custom_id="back"))
    
    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return False
        return True
    
    async def callback(self, interaction: discord.Interaction):
        custom_id = interaction.data.get('custom_id')
        if custom_id == "back":
            await interaction.response.defer()
            await interaction.followup.send(embed=discord.Embed(title="⚙️ Настройки", color=discord.Color.blue()), view=FullSettingsView())
            return
        val = int(custom_id.split("_")[1])
        config = load_config()
        config['voice_interval'] = val
        save_config(config)
        embed = discord.Embed(
            title="✅ Обновлено!",
            description=f"Теперь проверка каждые **{val}** секунд",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=IntervalView())

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

class ConfirmResetView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @ui.button(label="✅ Да, сбросить", style=ButtonStyle.danger, row=0)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только администраторы!", ephemeral=True)
            return
        data = load_level_data()
        voice_data = load_voice_time()
        guild_id = str(interaction.guild.id)
        if guild_id in data:
            del data[guild_id]
            save_level_data(data)
        if guild_id in voice_data:
            del voice_data[guild_id]
            save_voice_time(voice_data)
        embed = discord.Embed(
            title="🗑️ Данные сброшены!",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @ui.button(label="❌ Отмена", style=ButtonStyle.secondary, row=0)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="✅ Отменено",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=FullSettingsView())

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

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📡 Серверов: {len(bot.guilds)}')
    print('=' * 50)
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="🎯 Уровни | /profile"
    ))
    try:
        await bot.tree.sync()
        print("✅ Команды синхронизированы!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# =====================================================
#  🔄  KEEP-ALIVE ДЛЯ RENDER
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "🎯 Mohist_Level работает!"

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
