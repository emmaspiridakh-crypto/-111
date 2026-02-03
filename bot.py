import discord
from discord.ext import commands
import random
import os
from datetime import datetime, timedelta
from discord.ui import View, Button

# IDs
SPIN_CHANNEL_ID = 1467585068934500618
LOG_CHANNEL_ID = 1467584551261049097
PANEL_CHANNEL_ID = 1467585068934500618

# Cooldown 4 ώρες
COOLDOWN_HOURS = 4
user_cooldowns = {}

# Rewards
rewards = [
    ("try again later", 65),
    ("VIP role", 25),
    ("custom logo", 5),
    ("custom background", 5),
]

# Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Επιλογή reward
def pick_reward():
    items = [r[0] for r in rewards]
    weights = [r[1] for r in rewards]
    return random.choices(items, weights=weights, k=1)[0]


# ---------------- BUTTON ----------------
class SpinButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(
            label="🎰 Spin!",
            style=discord.ButtonStyle.green,
            custom_id="spin_button"
        ))


# ---------------- PANEL COMMAND ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def spinpanel(ctx):
    if ctx.channel.id != PANEL_CHANNEL_ID:
        return

    embed = discord.Embed(
        title="🎰 Spin The Wheel",
        description="Πάτα το κουμπί για να γυρίσεις τον τροχό!",
        color=discord.Color.gold()
    )
    embed.set_image(url="https://i.imgur.com/Aq9eZcn.jpeg")

    await ctx.send(embed=embed, view=SpinButton())


# ---------------- BUTTON INTERACTION ----------------
@bot.event
async def on_interaction(interaction):
    if interaction.data.get("custom_id") == "spin_button":
        user = interaction.user
        now = datetime.utcnow()

        # Cooldown check
        if user.id in user_cooldowns:
            last_spin = user_cooldowns[user.id]
            diff = now - last_spin

            if diff < timedelta(hours=COOLDOWN_HOURS):
                remaining = timedelta(hours=COOLDOWN_HOURS) - diff
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)

                return await interaction.response.send_message(
                    f"⏳ Πρέπει να περιμένεις **{hours} ώρες και {minutes} λεπτά** πριν ξανακάνεις spin.",
                    ephemeral=True
                )

        # Δώσε reward
        reward = pick_reward()
        user_cooldowns[user.id] = now

        await interaction.response.send_message(
            f"🎉 {user.mention}, κέρδισες: **{reward}**!",
            ephemeral=True
        )

        # Log
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"⚠️ {user} έκανε spin και κέρδισε: **{reward}**")


# ---------------- RUN BOT ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import os
from datetime import datetime, timedelta

# --- Bot Setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Channel & Role IDs ---
SUPPORT_CATEGORY_ID = 1465366628622667830
BUY_CATEGORY_ID = 1465375930321997986
SUPPORT_CALL_VC_ID = 1465375930321997986

LOGS_CHANNEL_ID = 1465370236243939379

CEO_ROLE_ID = 1465345034030157834
OWNER_ROLE_ID = 1465345430392017091
MANAGEMENT_ROLE_ID = 1465360458537111582
STAFF_ROLE_ID = 1467220345126654185

AUTO_ROLE_ID = 1465360458537111582  # Αυτόματο role σε νέο μέλος

# --- Helper Functions ---
async def create_ticket_channel(member, category_id, name_prefix, allowed_roles):
    guild = member.guild
    category = guild.get_channel(category_id)
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), member: discord.PermissionOverwrite(read_messages=True)}
    for role_id in allowed_roles:
        overwrites[guild.get_role(role_id)] = discord.PermissionOverwrite(read_messages=True)
    channel = await guild.create_text_channel(name=f"{name_prefix}-{member.name}", category=category, overwrites=overwrites)
    log_channel = guild.get_channel(LOGS_CHANNEL_ID)
    await log_channel.send(f"✅ Ticket opened by {member.mention}: {channel.mention}")
    close_button = Button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id=f"close_ticket_{channel.id}")
    view = View()
    view.add_item(close_button)
    await channel.send("Πατήστε για να κλείσετε το ticket.", view=view)
    return channel

# --- Panels ---
async def create_support_panel(channel):
    embed = discord.Embed(title="Support Panel", description="Πατήστε το κουμπί για να ανοίξετε ticket.", color=0x00ff00)
    owner_button = Button(label="Owner Ticket", style=discord.ButtonStyle.red, custom_id="open_owner_ticket")
    support_button = Button(label="Support Ticket", style=discord.ButtonStyle.green, custom_id="open_support_ticket")
    view = View()
    view.add_item(owner_button)
    view.add_item(support_button)
    await channel.send(embed=embed, view=view)

async def create_buy_panel(channel):
    embed = discord.Embed(title="Buy Ticket Panel", description="Πατήστε το κουμπί για να ανοίξετε ticket.", color=0x00ff00)
    buy_button = Button(label="Buy", style=discord.ButtonStyle.green, custom_id="open_buy_ticket")
    order_button = Button(label="Order", style=discord.ButtonStyle.blurple, custom_id="open_order_ticket")
    reward_button = Button(label="Claim Reward", style=discord.ButtonStyle.gold, custom_id="open_reward_ticket")
    view = View()
    view.add_item(buy_button)
    view.add_item(order_button)
    view.add_item(reward_button)
    await channel.send(embed=embed, view=view)

# --- Events ---
@bot.event
async def on_member_join(member):
    # Auto-role
    role = member.guild.get_role(AUTO_ROLE_ID)
    await member.add_roles(role)
    log_channel = member.guild.get_channel(LOGS_CHANNEL_ID)
    await log_channel.send(f"➕ {member.mention} joined and got role {role.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Link protection
    if "http" in message.content or "www" in message.content:
        allowed_roles = [CEO_ROLE_ID, OWNER_ROLE_ID]
        if not any(role.id in allowed_roles for role in message.author.roles):
            await message.delete()
            await message.author.send("❌ Δεν επιτρέπονται links στο server.")
            log_channel = message.guild.get_channel(LOGS_CHANNEL_ID)
            await log_channel.send(f"⚠️ {message.author.mention} έστειλε link και διαγράφηκε.")
    await bot.process_commands(message)

# Temporary VC για Support Call
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    guild = member.guild
    vc_category = guild.get_channel(SUPPORT_CATEGORY_ID)
    # Δημιουργία Temporary VC όταν μπαίνει στο Support Call
    if after.channel and after.channel.id == SUPPORT_CALL_VC_ID:
        overwrites = {guild.default_role: discord.PermissionOverwrite(connect=False), member: discord.PermissionOverwrite(connect=True)}
        temp_vc = await guild.create_voice_channel(name=f"{member.name}-support", category=vc_category, overwrites=overwrites)
        await member.move_to(temp_vc)
        await log_channel.send(f"🎤 Temporary VC created for {member.mention}")
    # Διαγραφή empty temp VC
    for channel in guild.voice_channels:
        if channel.category and channel.category.id == SUPPORT_CATEGORY_ID and len(channel.members) == 0 and channel.name.endswith("-support"):
            await channel.delete()
            await log_channel.send(f"❌ Temporary VC {channel.name} deleted")

# --- Interactions (Tickets) ---
@bot.event
async def on_interaction(interaction):
    member = interaction.user
    guild = interaction.guild

    # Support Tickets
    if interaction.data["custom_id"] == "open_owner_ticket":
        await create_ticket_channel(member, SUPPORT_CATEGORY_ID, "owner-ticket", [OWNER_ROLE_ID, CEO_ROLE_ID])
        await interaction.response.send_message("Owner ticket created!", ephemeral=True)

    elif interaction.data["custom_id"] == "open_support_ticket":
        await create_ticket_channel(member, SUPPORT_CATEGORY_ID, "support-ticket", [MANAGEMENT_ROLE_ID, STAFF_ROLE_ID, OWNER_ROLE_ID, CEO_ROLE_ID])
        await interaction.response.send_message("Support ticket created!", ephemeral=True)

    # Buy Tickets
    elif interaction.data["custom_id"] == "open_buy_ticket":
        await create_ticket_channel(member, BUY_CATEGORY_ID, "buy-ticket", [MANAGEMENT_ROLE_ID, STAFF_ROLE_ID])
        await interaction.response.send_message("Buy ticket created!", ephemeral=True)

    elif interaction.data["custom_id"] == "open_order_ticket":
        await create_ticket_channel(member, BUY_CATEGORY_ID, "order-ticket", [MANAGEMENT_ROLE_ID, STAFF_ROLE_ID])
        await interaction.response.send_message("Order ticket created!", ephemeral=True)

    elif interaction.data["custom_id"] == "open_reward_ticket":
        await create_ticket_channel(member, BUY_CATEGORY_ID, "reward-ticket", [MANAGEMENT_ROLE_ID, STAFF_ROLE_ID])
        await interaction.response.send_message("Reward ticket created!", ephemeral=True)

    # Close Ticket
    elif interaction.data["custom_id"].startswith("close_ticket_"):
        ticket_id = int(interaction.data["custom_id"].split("_")[-1])
        ticket_channel = guild.get_channel(ticket_id)
        if ticket_channel:
            await ticket_channel.delete()
            log_channel = guild.get_channel(LOGS_CHANNEL_ID)
            await log_channel.send(f"❌ Ticket closed by {member.mention}")

# --- Admin Commands ---
@bot.command()
async def say(ctx, *, message):
    allowed_roles = [CEO_ROLE_ID, OWNER_ROLE_ID]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("❌ Δεν έχεις permission.")
    await ctx.send(message)

@bot.command()
async def dmall(ctx, *, message):
    allowed_roles = [CEO_ROLE_ID, OWNER_ROLE_ID]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("❌ Δεν έχεις permission.")
    for member in ctx.guild.members:
        if not member.bot:
            try:
                await member.send(message)
            except:
                pass
    await ctx.send("✅ DM sent to all members.")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    allowed_roles = [CEO_ROLE_ID, OWNER_ROLE_ID]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("❌ Δεν έχεις permission.")
    await member.ban(reason=reason)
    log_channel = ctx.guild.get_channel(LOGS_CHANNEL_ID)
    await log_channel.send(f"⛔ {member.mention} banned by {ctx.author.mention} Reason: {reason}")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    allowed_roles = [CEO_ROLE_ID, OWNER_ROLE_ID]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("❌ Δεν έχεις permission.")
    await member.kick(reason=reason)
    log_channel = ctx.guild.get_channel(LOGS_CHANNEL_ID)
    await log_channel.send(f"👢 {member.mention} kicked by {ctx.author.mention} Reason: {reason}")

# --- Commands για να στέλνεις τα Panels ---
@bot.command()
@commands.has_any_role(CEO_ROLE_ID, OWNER_ROLE_ID)
async def send_support_panel(ctx):
    await create_support_panel(ctx.channel)
    await ctx.send("✅ Support panel sent!", delete_after=5)

@bot.command()
@commands.has_any_role(CEO_ROLE_ID, OWNER_ROLE_ID)
async def send_buy_panel(ctx):
    await create_buy_panel(ctx.channel)
    await ctx.send("✅ Buy panel sent!", delete_after=5)

# --- Run Bot ---
bot.run("PUT_YOUR_TOKEN_HERE")



