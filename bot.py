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


