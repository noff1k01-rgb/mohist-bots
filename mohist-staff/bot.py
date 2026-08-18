#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TOKEN = "ваш тикет бота в дискорд понели"

import discord
from discord.ext import commands
from discord import ui, ButtonStyle, SelectOption, app_commands
import json
import asyncio
from datetime import datetime

# =====================================================
#  📁  РАБОТА С ДАННЫМИ
# =====================================================

STAFF_FILE = "staff_data.json"
REQUESTS_FILE = "requests.json"
ACTIONS_FILE = "actions.json"

def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def load_staff():
    return load_json(STAFF_FILE)

def save_staff(data):
    save_json(STAFF_FILE, data)

def load_requests():
    return load_json(REQUESTS_FILE)

def save_requests(data):
    save_json(REQUESTS_FILE, data)

def load_actions():
    return load_json(ACTIONS_FILE)

def save_actions(data):
    save_json(ACTIONS_FILE, data)

def log_action(mod_id, action, target, reason=""):
    actions = load_actions()
    if str(mod_id) not in actions:
        actions[str(mod_id)] = []
    actions[str(mod_id)].append({
        "action": action,
        "target": target,
        "reason": reason,
        "date": datetime.now().isoformat()
    })
    save_actions(actions)

# =====================================================
#  🎮  БОТ
# =====================================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📡 Серверов: {len(bot.guilds)}')
    print('=' * 50)
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="👮 Управление персоналом | /staff"
    ))
    try:
        await bot.tree.sync()
        print("✅ Слеш-команды синхронизированы!")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")

# =====================================================
#  🎯  КЛАССЫ ДЛЯ МЕНЮ
# =====================================================

class StaffMainMenu(ui.View):
    """Главное меню управления персоналом"""
    def __init__(self):
        super().__init__(timeout=180)
    
    @ui.button(label="👮 Назначение/увольнение", style=ButtonStyle.primary, row=0)
    async def staff_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            "👮 **Управление персоналом**\nВыберите действие:",
            view=StaffManagementView(interaction.user.id)
        )
    
    @ui.button(label="⚔️ Наказания", style=ButtonStyle.danger, row=0)
    async def punish_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            "⚔️ **Выдача наказания**\nВыберите тип наказания:",
            view=PunishmentView(interaction.user.id)
        )
    
    @ui.button(label="📝 Заявки", style=ButtonStyle.secondary, row=1)
    async def requests_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            "📝 **Управление заявками**\nВыберите действие:",
            view=RequestsView(interaction.user.id)
        )
    
    @ui.button(label="📢 Рассылки", style=ButtonStyle.secondary, row=1)
    async def broadcast_btn(self, interaction: discord.Interaction, button: ui.Button):
        modal = BroadcastModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="📋 Журнал действий", style=ButtonStyle.primary, row=2)
    async def actions_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        actions = load_actions()
        if not actions:
            await interaction.followup.send("📭 Журнал действий пуст")
            return
        
        embed = discord.Embed(
            title="📋 Журнал действий",
            description="Последние действия",
            color=discord.Color.blue()
        )
        
        all_actions = []
        for mod_id, acts in actions.items():
            for act in acts:
                all_actions.append((act["date"], mod_id, act))
        
        all_actions.sort(reverse=True)
        
        # Показываем только последние 10 действий (по 1 полю на каждое)
        for date, mod_id, act in all_actions[:10]:
            embed.add_field(
                name=f"{act['action']}",
                value=f"👮 <@{mod_id}>\n🎯 {act['target']}\n📅 {date[:16]}",
                inline=False
            )
        await interaction.followup.send(embed=embed)
    
    @ui.button(label="🔐 Роли", style=ButtonStyle.primary, row=2)
    async def roles_btn(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="🔐 Управление ролями",
            description="Используйте команды для управления ролями",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📋 Команды",
            value="`/role add <участник> <роль>` - Выдать роль\n"
                  "`/role remove <участник> <роль>` - Убрать роль\n"
                  "`/role list` - Список ролей\n"
                  "`/role create <название>` - Создать роль",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    
    @ui.button(label="📊 Статистика", style=ButtonStyle.success, row=2)
    async def stats_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        staff = load_staff()
        actions = load_actions()
        
        embed = discord.Embed(
            title="📊 Статистика персонала",
            color=discord.Color.blue()
        )
        
        # Общая статистика
        embed.add_field(
            name="👥 Всего сотрудников",
            value=str(len(staff)),
            inline=True
        )
        
        # Статистика по ролям
        roles_stats = {}
        for uid, data in staff.items():
            role = data.get("role", "Неизвестно")
            roles_stats[role] = roles_stats.get(role, 0) + 1
        
        roles_text = "\n".join([f"{role}: {count}" for role, count in list(roles_stats.items())[:10]])
        if len(roles_stats) > 10:
            roles_text += f"\nИ ещё {len(roles_stats)-10} должностей..."
        
        embed.add_field(
            name="📋 По ролям",
            value=roles_text if roles_text else "Нет данных",
            inline=True
        )
        
        # Количество действий
        total_actions = sum(len(acts) for acts in actions.values())
        embed.add_field(
            name="📋 Всего действий",
            value=str(total_actions),
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

# =====================================================
#  👮  УПРАВЛЕНИЕ ПЕРСОНАЛОМ
# =====================================================

class StaffManagementView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        
        options = [
            SelectOption(label="📥 Назначить", value="hire", description="Назначить сотрудника", emoji="📥"),
            SelectOption(label="📤 Уволить", value="fire", description="Уволить сотрудника", emoji="📤"),
            SelectOption(label="📋 Список", value="list", description="Показать всех сотрудников", emoji="📋"),
        ]
        self.select = ui.Select(placeholder="Выберите действие...", options=options, row=0)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
        close = ui.Button(label="❌ Закрыть", style=ButtonStyle.danger, row=1)
        close.callback = self.close_callback
        self.add_item(close)
    
    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        
        action = self.select.values[0]
        
        if action == "hire":
            modal = HireModal()
            await interaction.response.send_modal(modal)
        elif action == "fire":
            modal = FireModal()
            await interaction.response.send_modal(modal)
        elif action == "list":
            await interaction.response.defer()
            staff = load_staff()
            if not staff:
                await interaction.followup.send("📭 Нет сотрудников")
                return
            
            embed = discord.Embed(
                title="👮 Список сотрудников",
                color=discord.Color.blue()
            )
            for uid, data in list(staff.items())[:15]:
                member = interaction.guild.get_member(int(uid))
                name = member.mention if member else f"<@{uid}>"
                embed.add_field(
                    name=f"📌 {data.get('role', 'Без роли')}",
                    value=f"{name}\n📅 {data.get('hired', 'Неизвестно')[:16]}",
                    inline=False
                )
            if len(staff) > 15:
                embed.set_footer(text=f"И ещё {len(staff)-15} сотрудников...")
            await interaction.followup.send(embed=embed)
    
    async def close_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        await interaction.message.delete()

class HireModal(ui.Modal, title="📥 Назначение сотрудника"):
    member_id = ui.TextInput(
        label="ID участника",
        placeholder="Введите ID пользователя...",
        required=True,
        style=discord.TextStyle.short
    )
    role = ui.TextInput(
        label="Должность",
        placeholder="Введите должность...",
        required=True,
        style=discord.TextStyle.short
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
        except:
            await interaction.followup.send("❌ Участник не найден!", ephemeral=True)
            return
        
        staff = load_staff()
        if str(member.id) in staff:
            await interaction.followup.send(f"⚠️ {member.mention} уже является сотрудником!", ephemeral=True)
            return
        
        staff[str(member.id)] = {
            "role": self.role.value,
            "hired": datetime.now().isoformat(),
            "hired_by": interaction.user.id
        }
        save_staff(staff)
        log_action(interaction.user.id, "назначение", member.name, self.role.value)
        
        embed = discord.Embed(
            title="✅ Сотрудник назначен!",
            description=f"{member.mention} назначен на должность **{self.role.value}**",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class FireModal(ui.Modal, title="📤 Увольнение сотрудника"):
    member_id = ui.TextInput(
        label="ID участника",
        placeholder="Введите ID пользователя...",
        required=True,
        style=discord.TextStyle.short
    )
    reason = ui.TextInput(
        label="Причина",
        placeholder="Введите причину...",
        required=False,
        style=discord.TextStyle.short,
        default="Не указана"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
        except:
            await interaction.followup.send("❌ Участник не найден!", ephemeral=True)
            return
        
        staff = load_staff()
        if str(member.id) not in staff:
            await interaction.followup.send(f"⚠️ {member.mention} не является сотрудником!", ephemeral=True)
            return
        
        role = staff[str(member.id)]["role"]
        del staff[str(member.id)]
        save_staff(staff)
        log_action(interaction.user.id, "увольнение", member.name, self.reason.value)
        
        embed = discord.Embed(
            title="❌ Сотрудник уволен!",
            description=f"{member.mention} уволен с должности **{role}**",
            color=discord.Color.red()
        )
        embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

# =====================================================
#  ⚔️  НАКАЗАНИЯ
# =====================================================

class PunishmentView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        
        options = [
            SelectOption(label="⚠️ Предупреждение", value="warn", emoji="⚠️"),
            SelectOption(label="🔇 Мут", value="mute", emoji="🔇"),
            SelectOption(label="⛔ Кик", value="kick", emoji="⛔"),
            SelectOption(label="❌ Бан", value="ban", emoji="❌"),
        ]
        self.select = ui.Select(placeholder="Выберите наказание...", options=options, row=0)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
        close = ui.Button(label="❌ Закрыть", style=ButtonStyle.danger, row=1)
        close.callback = self.close_callback
        self.add_item(close)
    
    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        
        punishment = self.select.values[0]
        modal = PunishmentModal(punishment)
        await interaction.response.send_modal(modal)
    
    async def close_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        await interaction.message.delete()

class PunishmentModal(ui.Modal, title="⚔️ Выдача наказания"):
    def __init__(self, punishment_type):
        super().__init__(title=f"⚔️ {punishment_type.upper()}")
        self.punishment_type = punishment_type
        
        self.member_id = ui.TextInput(
            label="ID участника",
            placeholder="Введите ID пользователя...",
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.member_id)
        
        self.reason = ui.TextInput(
            label="Причина",
            placeholder="Введите причину...",
            required=False,
            style=discord.TextStyle.short,
            default="Нарушение правил"
        )
        self.add_item(self.reason)
        
        if punishment_type == "mute":
            self.duration = ui.TextInput(
                label="Длительность (минуты)",
                placeholder="Например: 10, 60, 1440",
                required=False,
                style=discord.TextStyle.short,
                default="10"
            )
            self.add_item(self.duration)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            member = await interaction.guild.fetch_member(int(self.member_id.value))
        except:
            await interaction.followup.send("❌ Участник не найден!", ephemeral=True)
            return
        
        punishment_names = {
            "warn": "Предупреждение",
            "mute": "Мут",
            "kick": "Кик",
            "ban": "Бан"
        }
        
        log_action(interaction.user.id, punishment_names[self.punishment_type], member.name, self.reason.value)
        
        embed = discord.Embed(
            title="✅ Наказание выдано!",
            description=f"{member.mention} получил **{punishment_names[self.punishment_type]}**",
            color=discord.Color.red()
        )
        embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
        
        if self.punishment_type == "mute":
            duration = int(self.duration.value) if self.duration.value else 10
            await member.timeout(duration * 60, reason=self.reason.value)
            embed.add_field(name="⏱️ Длительность", value=f"{duration} минут", inline=True)
        elif self.punishment_type == "kick":
            await member.kick(reason=self.reason.value)
        elif self.punishment_type == "ban":
            await member.ban(reason=self.reason.value)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# =====================================================
#  📝  ЗАЯВКИ
# =====================================================

class RequestsView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        
        options = [
            SelectOption(label="📝 Создать заявку", value="create", emoji="📝"),
            SelectOption(label="📋 Мои заявки", value="my", emoji="📋"),
            SelectOption(label="✅ Все заявки", value="all", emoji="✅"),
        ]
        self.select = ui.Select(placeholder="Выберите действие...", options=options, row=0)
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
        close = ui.Button(label="❌ Закрыть", style=ButtonStyle.danger, row=1)
        close.callback = self.close_callback
        self.add_item(close)
    
    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        
        action = self.select.values[0]
        
        if action == "create":
            modal = RequestModal()
            await interaction.response.send_modal(modal)
        elif action == "my":
            await interaction.response.defer()
            requests = load_requests()
            user_requests = [r for r in requests.values() if r.get("author") == str(interaction.user.id)]
            
            if not user_requests:
                await interaction.followup.send("📭 У вас нет заявок")
                return
            
            embed = discord.Embed(
                title="📋 Мои заявки",
                color=discord.Color.blue()
            )
            for req in user_requests[-5:]:
                embed.add_field(
                    name=f"#{req.get('id', '?')} - {req.get('status', 'Неизвестно')}",
                    value=f"📝 {req.get('text', '')[:50]}...\n📅 {req.get('date', '')[:16]}",
                    inline=False
                )
            await interaction.followup.send(embed=embed)
        elif action == "all":
            await interaction.response.defer()
            requests = load_requests()
            if not requests:
                await interaction.followup.send("📭 Нет заявок")
                return
            
            embed = discord.Embed(
                title="✅ Все заявки",
                color=discord.Color.blue()
            )
            for req_id, req in list(requests.items())[-10:]:
                embed.add_field(
                    name=f"#{req_id} - {req.get('status', 'Неизвестно')}",
                    value=f"👤 <@{req.get('author', '?')}>\n📝 {req.get('text', '')[:50]}...",
                    inline=False
                )
            await interaction.followup.send(embed=embed)
    
    async def close_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return
        await interaction.message.delete()

class RequestModal(ui.Modal, title="📝 Создание заявки"):
    title = ui.TextInput(
        label="Тема",
        placeholder="Кратко опишите тему...",
        required=True,
        style=discord.TextStyle.short
    )
    text = ui.TextInput(
        label="Текст заявки",
        placeholder="Подробно опишите вашу заявку...",
        required=True,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        requests = load_requests()
        req_id = str(len(requests) + 1)
        
        requests[req_id] = {
            "id": req_id,
            "title": self.title.value,
            "text": self.text.value,
            "author": str(interaction.user.id),
            "status": "Новая",
            "date": datetime.now().isoformat()
        }
        save_requests(requests)
        
        embed = discord.Embed(
            title=f"📝 Новая заявка #{req_id}",
            description=self.text.value,
            color=discord.Color.blue()
        )
        embed.add_field(name="📌 Тема", value=self.title.value, inline=False)
        embed.add_field(name="👤 Автор", value=interaction.user.mention, inline=True)
        embed.add_field(name="📅 Дата", value=datetime.now().strftime("%d.%m.%Y %H:%M"), inline=True)
        
        for channel in interaction.guild.text_channels:
            if "заявк" in channel.name.lower() or "request" in channel.name.lower():
                await channel.send(embed=embed)
                break
        
        await interaction.followup.send(f"✅ Заявка #{req_id} создана!", ephemeral=True)

# =====================================================
#  📢  РАССЫЛКИ
# =====================================================

class BroadcastModal(ui.Modal, title="📢 Отправить рассылку"):
    channel_id = ui.TextInput(
        label="ID канала",
        placeholder="Введите ID канала...",
        required=True,
        style=discord.TextStyle.short
    )
    message = ui.TextInput(
        label="Сообщение",
        placeholder="Введите текст рассылки...",
        required=True,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.guild.get_channel(int(self.channel_id.value))
            if not channel:
                await interaction.followup.send("❌ Канал не найден!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📢 Важное сообщение",
                description=self.message.value,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Отправлено: {interaction.user.display_name}")
            
            await channel.send(embed=embed)
            log_action(interaction.user.id, "рассылка", channel.name, self.message.value[:50])
            
            await interaction.followup.send(f"✅ Рассылка отправлена в <#{self.channel_id.value}>!", ephemeral=True)
        except:
            await interaction.followup.send("❌ Ошибка! Проверьте ID канала.", ephemeral=True)

# =====================================================
#  🔐  КОМАНДЫ РОЛЕЙ
# =====================================================

@bot.tree.command(name="role", description="🔐 Управление ролями")
@app_commands.describe(
    action="Действие: add, remove, list, create",
    member="Участник (для add/remove)",
    role="Название роли или @упоминание",
    name="Название для создания"
)
async def slash_role(interaction: discord.Interaction, action: str, member: discord.Member = None, role: str = None, name: str = None):
    if action == "add":
        if not member or not role:
            await interaction.response.send_message("❌ Использование: `/role add <участник> <роль>`")
            return
        
        role_obj = discord.utils.get(interaction.guild.roles, name=role)
        if not role_obj:
            await interaction.response.send_message(f"❌ Роль **{role}** не найдена!")
            return
        
        await member.add_roles(role_obj)
        log_action(interaction.user.id, "выдача роли", member.name, role)
        await interaction.response.send_message(f"✅ Роль **{role}** выдана {member.mention}!")
    
    elif action == "remove":
        if not member or not role:
            await interaction.response.send_message("❌ Использование: `/role remove <участник> <роль>`")
            return
        
        role_obj = discord.utils.get(interaction.guild.roles, name=role)
        if not role_obj:
            await interaction.response.send_message(f"❌ Роль **{role}** не найдена!")
            return
        
        await member.remove_roles(role_obj)
        log_action(interaction.user.id, "удаление роли", member.name, role)
        await interaction.response.send_message(f"✅ Роль **{role}** убрана у {member.mention}!")
    
    elif action == "list":
        embed = discord.Embed(
            title="🔐 Список ролей",
            description="Список всех ролей на сервере",
            color=discord.Color.blue()
        )
        
        roles = [r for r in interaction.guild.roles if r.name != "@everyone"]
        roles.sort(key=lambda x: x.position, reverse=True)
        
        if not roles:
            embed.description = "📭 На сервере нет ролей (кроме @everyone)"
            await interaction.response.send_message(embed=embed)
            return
        
        # Показываем первые 25 ролей
        for r in roles[:25]:
            member_count = len(r.members)
            embed.add_field(
                name=r.name,
                value=f"ID: {r.id}\n👥 {member_count} чел.",
                inline=True
            )
        
        if len(roles) > 25:
            embed.set_footer(text=f"И ещё {len(roles)-25} ролей...")
        
        await interaction.response.send_message(embed=embed)
    
    elif action == "create":
        if not name:
            await interaction.response.send_message("❌ Использование: `/role create <название>`")
            return
        
        role = await interaction.guild.create_role(name=name)
        log_action(interaction.user.id, "создание роли", name, "")
        await interaction.response.send_message(f"✅ Роль **{name}** создана (ID: {role.id})!")
    
    else:
        await interaction.response.send_message("❌ Доступные действия: `add`, `remove`, `list`, `create`")

# =====================================================
#  🎯  ОСНОВНАЯ КОМАНДА
# =====================================================

@bot.tree.command(name="staff", description="👮 Открыть панель управления персоналом")
async def slash_staff(interaction: discord.Interaction):
    embed = discord.Embed(
        title="👮 Панель управления персоналом",
        description="Управляйте персоналом и модерацией",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Доступные действия",
        value="• 👮 Назначение/увольнение\n"
              "• ⚔️ Наказания\n"
              "• 📝 Заявки\n"
              "• 📢 Рассылки\n"
              "• 📋 Журнал действий\n"
              "• 🔐 Управление ролями\n"
              "• 📊 Статистика",
        inline=False
    )
    embed.set_footer(text="Для управления используйте кнопки ниже")
    
    await interaction.response.send_message(embed=embed, view=StaffMainMenu())

# =====================================================
#  🔄  KEEP-ALIVE ДЛЯ RENDER
# =====================================================

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "👮 Mohist_Staff работает!"

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
        # Запускаем фоновую задачу
        bot.loop.create_task(give_xp())
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.LoginFailure:
        print("❌ Неверный токен!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
